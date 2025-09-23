import json
from logging import Logger

from services.ymaps_parser.accumulator import Accumulator, Review


class ApiScanner:
    def __init__(self, acc: Accumulator, logger: Logger):
        self.acc = acc
        self.logger = logger.getChild("ApiScanner")
        self.current_org_id = None

    def parse_search_results(self, results):
        self.logger.info(f"Парсим {len(results)} поисковых результатов")
        for item in results:
            org_id = str(item.get("id"))

            name = item.get("title")
            rubric = (
                ";".join(
                    [
                        cat.get("name")
                        for cat in item.get("categories", [])
                        if "name" in cat
                    ]
                )
                if item.get("categories")
                else None
            )
            rating = (
                str(item["ratingData"]["ratingValue"])
                if "ratingData" in item and "ratingValue" in item["ratingData"]
                else None
            )
            reviews_count = (
                str(item["ratingData"]["reviewCount"])
                if "ratingData" in item and "reviewCount" in item["ratingData"]
                else None
            )
            full_address = item.get("fullAddress")
            lat = (
                str(item.get("coordinates", [None, None])[0])
                if "coordinates" in item
                else None
            )
            lon = (
                str(item.get("coordinates", [None, None])[1])
                if "coordinates" in item
                else None
            )
            phones = (
                "".join(
                    [p.get("number") for p in item.get("phones", []) if "number" in p]
                )
                if "phones" in item
                else None
            )
            site = (
                ";".join(item.get("urls", []))
                if "urls" in item and item["urls"]
                else None
            )
            days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
            schedule = None
            if "workingTime" in item and isinstance(item["workingTime"], list):
                schedule_parts = []
                for i, day_slots in enumerate(item["workingTime"]):
                    if not day_slots:
                        continue
                    slots = []
                    for slot in day_slots:
                        from_time = slot.get("from")
                        to_time = slot.get("to")
                        if from_time and to_time:
                            from_str = (
                                f'{from_time["hours"]:02}:{from_time["minutes"]:02}'
                            )
                            to_str = f'{to_time["hours"]:02}:{to_time["minutes"]:02}'
                            slots.append(f"{from_str}-{to_str}")
                    if slots:
                        schedule_parts.append(f"{days_ru[i]}: {', '.join(slots)}")
                if schedule_parts:
                    schedule = "\n".join(schedule_parts)
            else:
                schedule = item.get("workingTimeText")
            is_open_now = (
                item.get("currentWorkingStatus", {}).get("isOpenNow")
                if "currentWorkingStatus" in item
                else None
            )
            if "photos" in item:
                count = item.get("photos", {}).get("count", 0)
                self.acc.update(org_id, photos_count=count)
            if "videos" in item:
                videos = item.get("videos", {}).get("items", [])
                videos_count = len(videos)
                self.acc.update(
                    org_id, has_video=videos_count > 0, videos_count=videos_count
                )

            full_objects = item.get("fullObjects")
            if full_objects and "categories" in full_objects:
                has_photos = False
                has_covers = False
                has_description = False
                services = []
                services_prices = []
                services_with_photos = []
                for cat in full_objects["categories"]:
                    for srv in cat.get("categoryItems", []):
                        title = srv.get("title")
                        if title:
                            services.append(title)
                        price = srv.get("price")
                        currency = srv.get("currency")
                        if price:
                            services_prices.append(
                                f"{str(price)} {currency}" if currency else str(price)
                            )
                        photo = srv.get("photoLink")
                        if photo:
                            has_photos = True
                            services_with_photos.append(title)

                        if srv.get("cover"):
                            has_covers = True
                        if srv.get("description"):
                            has_description = True
                services_count = len(services)
                services_list = ";".join(services)
                services_prices_str = ";".join(services_prices)
                services_with_photos_str = ";".join(services_with_photos)
                self.acc.update(
                    org_id,
                    services_count=services_count,
                    services_list=services_list,
                    services_prices=services_prices_str,
                    services_has_photos=has_photos,
                    services_with_photos=services_with_photos_str,
                    services_has_covers=has_covers,
                    services_description_filled=has_description,
                )

            if "features" in item:
                features = item.get("features", [])
                features_parts = []
                for feature in features:
                    fname = feature.get("name")
                    fval = feature.get("value")
                    if fname is None or fval is None:
                        continue
                    if isinstance(fval, bool):
                        val_str = "да" if fval else "нет"
                    elif isinstance(fval, list):
                        val_str = ", ".join(
                            [
                                v.get("name", "")
                                for v in fval
                                if isinstance(v, dict) and "name" in v
                            ]
                        )
                    else:
                        val_str = str(fval)
                    features_parts.append(f"{fname}: {val_str}")
                features_str = ";".join(features_parts)
                self.acc.update(
                    org_id,
                    has_features=bool(features_parts),
                    features_list=features_str,
                )

            self.acc.update(
                org_id,
                name=name,
                rubric=rubric,
                rating=rating,
                reviews_count=reviews_count,
                full_address=full_address,
                lat=lat,
                lon=lon,
                phones=phones,
                site=site,
                schedule=schedule,
                is_open_now=is_open_now,
            )

    def parse_stories(self, stories):
        self.logger.info(f"Парсим {len(stories)} сторис")
        has_stories = bool(stories)
        stories_titles = (
            ";".join([story.get("title", "") for story in stories]) if stories else ""
        )
        # Use current_org_id if available, otherwise skip updating
        if self.current_org_id:
            self.acc.update(
                self.current_org_id,
                has_stories=has_stories,
                stories_titles=stories_titles,
            )

    def parse_news(self, news_count, news_items):
        self.logger.info(f"Парсим {len(news_items)} новостей")
        news_titles = (
            ";".join([item.get("contentShort", "") for item in news_items])
            if news_items
            else ""
        )
        news_texts = (
            "|||".join([item.get("content", "") for item in news_items])
            if news_items
            else ""
        )
        news_dates = (
            ";".join(
                [
                    (
                        str(item.get("publicationTime", ""))
                        if "publicationTime" in item
                        else ""
                    )
                    for item in news_items
                ]
            )
            if news_items
            else ""
        )

        if self.current_org_id:
            self.acc.update(
                self.current_org_id,
                has_news=news_count > 0,
                news_count=news_count,
                news_titles=news_titles,
                news_texts=news_texts,
                news_dates=news_dates,
            )

    def parse_reviews(self, reviews):
        self.logger.info(f"Парсим {len(reviews)} отзывов")
        for review in reviews:
            review_id = review.get("reviewId")
            review_date = review.get("updatedTime")
            stars = review.get("rating")
            text = review.get("text", "")
            owner_reply = review.get("businessComment")
            has_owner_reply = owner_reply is not None
            owner_reply_text = None
            owner_reply_date = None
            if has_owner_reply:
                owner_reply_date = owner_reply.get("updatedTime")
                owner_reply_text = owner_reply.get("text", "")

            org_id = review.get("businessId") or self.current_org_id
            if not org_id:
                continue

            review_obj = Review(
                review_id=str(review_id),
                review_date=review_date,
                stars=int(stars) if stars is not None else None,
                text=text,
                has_owner_reply=has_owner_reply,
                owner_reply_text=owner_reply_text,
                owner_reply_date=owner_reply_date,
            )
            self.acc.add_review(str(org_id), review_obj)

    def on_response(self, url, response):
        if "/maps/api/" not in url:
            return
        
        _, _, endpoint = url.partition("/maps/api/")
        if endpoint.startswith("location-info"):
            return
        
        # with open("network_log.txt", "ab") as f:
        #     f.write(f"URL: {url}\n".encode())
        #     f.write(b"Response body:\n")
        #     f.write(response)
        #     f.write(b"\n" + b"-" * 80 + b"\n")

        try:
            resp_json = json.loads(response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Не смогу декодировать JSON из {url}: {e}")
            return

        if endpoint.startswith("search"):
            self.logger.info(f"Получил ответ от /api/search")
            if "data" in resp_json:
                items = resp_json["data"].get("items", [])
                self.parse_search_results(items)

        if endpoint.startswith("stories"):
            self.logger.info(f"Получил ответ от /api/stories")
            if "data" in resp_json:
                stories = resp_json["data"].get("stories", [])
                self.parse_stories(stories)

        if endpoint.startswith("posts"):
            self.logger.info(f"Получил ответ от /api/posts")
            if "data" in resp_json:
                news_count = resp_json["data"].get("count", 0)
                news_items = resp_json["data"].get("items", [])
                self.parse_news(news_count, news_items)

        if endpoint.startswith("business/fetchReviews"):
            self.logger.info(f"Получил ответ от /api/business/fetchReviews")
            if "data" in resp_json:
                reviews = resp_json["data"].get("reviews", [])
                self.parse_reviews(reviews)
