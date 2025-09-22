import asyncio
import logging
from pathlib import Path
from random import randint
from playwright.async_api import ElementHandle, Page, async_playwright
from services.ymaps_parser import helper, scripts
from services.ymaps_parser.accumulator import *
from services.ymaps_parser.api_scanner import ApiScanner


class YMapsParser:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.user_data_dir = str(Path(__file__).parent / "chrome-data")
        self.playwright = None
        self.context = None
        self.page: Optional[Page] = None
        self.last_mouse_pos = (randint(300, 1600), randint(300, 900))
        self.acc = Accumulator()
        self.api_scanner = ApiScanner(self.acc, logger)

    async def __aenter__(self):
        await self.launch()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def launch(self):
        self.logger.info("Запускаю браузер...")
        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
            headless=False,
            user_data_dir=self.user_data_dir,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU",
        )
        self.page = await self.context.new_page()
        await self.page.add_init_script(helper.MOUSE_TRACKER_SCRIPT)

        async def on_response(response):
            try:
                url = response.url
                if not url.startswith("https://yandex.com/maps/api"):
                    return

                status = response.status
                if status == 200:
                    body = await response.body()
                    self.api_scanner.on_response(url, body)

            except Exception as e:
                self.logger.error(f"Не смог обработать ответ: {e}")

        self.page.on("response", on_response)

    async def mousemove(self, pos):
        await helper.sim_mouse_move_to(self.page, self.last_mouse_pos, pos)
        self.last_mouse_pos = pos

    async def click(self, button="left"):
        await helper.sim_click(self.page, button)

    async def random_wait(self, min_delay, max_delay):
        await asyncio.sleep(randint(min_delay, max_delay) / 1000.0)

    async def scroll_down(self, n=4, distance=100):
        for _ in range(n):
            await self.page.mouse.wheel(0, distance)
            await self.random_wait(100, 200)

    async def scroll_up(self, n=4, distance=100):
        for _ in range(n):
            await self.page.mouse.wheel(0, -distance)
            await self.random_wait(100, 200)

    async def move_cursor_to_element(self, element: ElementHandle):
        # Get bounding box of the element
        box = await element.bounding_box()
        if not box:
            raise ValueError("Element not found or has no bounding box")
        x = randint(int(box["x"]), int(box["x"] + box["width"]) - 1)
        y = randint(int(box["y"]), int(box["y"] + box["height"]) - 1)
        await self.mousemove((x, y))

    async def click_element(self, element, button="left"):
        await self.move_cursor_to_element(element)
        await self.click(button)

    async def try_query_selector(
        self, selector: str, parent: ElementHandle = None, retries=3, delay=600
    ):
        attempt = 0
        element = None
        while attempt < retries:
            element = await (parent or self.page).query_selector(selector)
            if element is not None:
                return element
            attempt += 1
            await asyncio.sleep(delay / 1000.0)
        return None

    async def run_parser(self, script: str):
        # Run parsing in the browser context and get results as JSON
        results = await self.page.evaluate(script)
        if isinstance(results, list):
            for item in results:
                if "org_id" in item:
                    self.acc.update(**item)
        elif isinstance(results, dict):
            if "org_id" in results:
                self.acc.update(**results)

    async def parse_config_script(self):
        config_script = await self.page.query_selector("script.state-view")
        if config_script:
            config_text = await config_script.inner_text()
            self.logger.info("Читаю конфиг из страницы")
            config = json.loads(config_text)
            stack = config.get("stack", None)
            if stack and len(stack) > 0:
                for el in stack:
                    if el.get("mode") == "search":
                        results = el.get("results", {})
                        total_count = results.get("totalResultCount", 0)
                        # Можно использовать для расчета ETA
                        self.logger.info(f"Всего организаций: {total_count}")
                        items = results.get("items", [])
                        self.api_scanner.parse_search_results(items)
                        return total_count

            self.logger.error("Не смог получить количество организаций")
        else:
            self.logger.error("Не удалось спарсить конфиг, могут быть ошибки")
        
        return 0

    async def parse(self, url: str):
        if self.page is None:
            raise RuntimeError("Call launch() before parse()")

        self.logger.info(f"Сканирую {url}")
        await self.page.goto(url)
        await self.page.wait_for_timeout(5000)

        self.acc.set_url(url)
        await self.run_parser(scripts.SEARCH_RESULTS_PARSER)
        total_count = await self.parse_config_script()
        
        num_retries = 0
        visited_ids = set()
        while True:
            snippets = await self.page.query_selector_all(
                ".search-snippet-view__body[data-id]"
            )
            ids = []
            for snippet in snippets:
                data_id = await snippet.get_attribute("data-id")
                if data_id and data_id not in visited_ids:
                    ids.append((data_id, snippet))
            if not ids:
                if len(visited_ids) < total_count and num_retries < 8:
                    await asyncio.sleep(1000)
                    num_retries += 1
                    continue
                else:
                    break
            num_retries = 0

            data_id, snippet = ids[0]
            visited_ids.add(data_id)
            self.logger.info(f"Сканирую организацию ID: {data_id}")
            self.api_scanner.current_org_id = data_id

            title = await self.try_query_selector(
                ".search-business-snippet-view__title", parent=snippet
            )
            if title is None:
                self.logger.error(f"Не смог найти заголовок для ID {data_id}, пропускаю")
                continue

            try:
                await self.click_element(title)
                await self.random_wait(700, 1100)

                # … твои действия с кнопками …

                await self.run_parser(scripts.SEARCH_RESULTS_PARSER)
                await self.parse_config_script()

            except Exception as e:
                self.logger.error(f"Ошибка при сканировании ID {data_id}: {e}")

        # 🔹 Возвращаем всё накопленное
        return self.acc.data

    async def close(self):
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
