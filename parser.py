from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import asyncio
from pathlib import Path
import helper
from accumulator import *


class YMapsParser:
    def __init__(self):
        self.user_data_dir = str(Path(__file__).parent / "chrome-data")
        self.context = None
        self.page = None
        self.last_mouse_pos = (helper.rd(300, 1600), helper.rd(300, 900))

    async def launch(self):
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

    async def mousemove(self, pos):
        await helper.sim_mouse_move_to(self.page, self.last_mouse_pos, pos)
        self.last_mouse_pos = pos
    
    async def click(self, button="left", pause_after_mouse_up=False):
        await helper.sim_click(self.page, button, pause_after_mouse_up)
    
    async def scroll_down(self, n=4, distance=200):
        for _ in range(n):
            await self.page.mouse.wheel(0, distance)
            await asyncio.sleep(helper.rd(50, 100) / 1000.0)
    
    async def scroll_up(self, n=4, distance=200):
        for _ in range(n):
            await self.page.mouse.wheel(0, -distance)
            await asyncio.sleep(helper.rd(50, 100) / 1000.0)

    async def parse(self, url):
        if self.page is None:
            raise RuntimeError("Call launch() before parse()")

        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(5000)

        acc = Accumulator(url)

        html = await self.page.content()
        soup = BeautifulSoup(html, "html.parser")
        self.parse_search_results(soup, acc)

        acc.dump("output.json")

        await self.mousemove((100, 100))

        await asyncio.sleep(100000)
    
    def parse_search_results(self, soup: BeautifulSoup, acc: Accumulator):
        ul = soup.find("ul", class_="search-list-view__list")
        if not ul:
            return

        for li in ul.find_all("li", class_="search-snippet-view"):
            body = li.find("div", class_="search-snippet-view__body")
            org_id = body.get("data-id")
            coordinates = body.get("data-coordinates")
            title_tag = li.find("a", class_="link-overlay")
            name = title_tag.get_text(strip=True)
            url_ = title_tag["href"]
            rating_tag = li.find(
                "span", class_="business-rating-badge-view__rating-text"
            )
            rating = rating_tag.get_text(strip=True) if rating_tag else None
            rating_count_tag = li.find("span", class_="business-rating-amount-view")
            if not rating_count_tag:
                rating_count_tag = li.find(
                    "div", class_="business-rating-with-text-view__count"
                )
                if rating_count_tag:
                    rating_count_tag = rating_count_tag.find("div")
            rating_count = (
                rating_count_tag.get_text(strip=True) if rating_count_tag else None
            )
            address_tag = li.find("a", class_="search-business-snippet-view__address")
            address = address_tag.get_text(strip=True) if address_tag else None
            cats = [
                cat.get_text(strip=True)
                for cat in li.select(".search-business-snippet-view__category")
            ]
            awards = [
                award.get_text(strip=True)
                for award in li.select(".business-header-awards-view__award-text")
            ]
            hours_tag = li.find("div", class_="business-working-status-view")
            working_hours = hours_tag.get_text(strip=True) if hours_tag else None
            price_title = li.find(
                "span", class_="search-business-snippet-subtitle-view__title"
            )
            price_desc = li.find(
                "span", class_="search-business-snippet-subtitle-view__description"
            )
            service = price_title.get_text(strip=True) if price_title else None
            price = price_desc.get_text(strip=True) if price_desc else None
            ad_badge = li.find("span", class_="search-advert-badge__title")
            ad = ad_badge.get_text(strip=True) if ad_badge else None

            acc.update(
                org_id,
                name=name,
                rubric=", ".join(cats) if cats else None,
                rating=rating,
                reviews_count=rating_count,
                short_address=address,
                is_ad=bool(ad),
                promo_text=ad,
                badges=", ".join(awards) if awards else None,
                has_online_booking=False,
                booking_label=None,
                has_prices_button=bool(price),
                price_service=service,
                price_value=None,
                price_currency=None,
                price_duration=price,
                schedule=working_hours,
                lat=(coordinates.split(",")[0]) if coordinates else None,
                lon=(coordinates.split(",")[1]) if coordinates else None,
                card_url="https://yandex.ru" + url_ if url_ else None,
            )

    async def close(self):
        if self.context:
            await self.context.close()
        if hasattr(self, "playwright"):
            await self.playwright.stop()


if __name__ == "__main__":
    url = "https://yandex.ru/maps/2/saint-petersburg/category/beauty_salon/184105814/?ll=30.332682%2C59.943331&sll=30.332682%2C59.943309&z=12"
    parser = YMapsParser()

    async def main():
        await parser.launch()
        await parser.parse(url)
        await parser.close()

    asyncio.new_event_loop().run_until_complete(main())
