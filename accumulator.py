from dataclasses import dataclass, field, asdict
import json
from typing import List, Optional
from datetime import datetime


@dataclass
class Review:
    review_id: str
    review_date: str
    stars: int
    text: str
    has_owner_reply: Optional[bool] = None
    owner_reply_text: Optional[str] = None
    owner_reply_date: Optional[str] = None


@dataclass
class Organization:
    org_id: str
    # Лист 1: Выдача
    search_url: Optional[str] = None
    date: Optional[str] = None
    rank: Optional[int] = None
    name: Optional[str] = None
    rubric: Optional[str] = None
    rating: Optional[str] = None
    reviews_count: Optional[str] = None
    short_address: Optional[str] = None
    is_ad: Optional[bool] = None
    promo_text: Optional[str] = None
    badges: Optional[str] = None
    has_online_booking: Optional[bool] = None
    booking_label: Optional[str] = None
    has_prices_button: Optional[bool] = None
    price_service: Optional[str] = None
    price_value: Optional[str] = None
    price_currency: Optional[str] = None
    price_duration: Optional[str] = None

    # Лист 2: Организации
    full_address: Optional[str] = None
    lat: Optional[str] = None
    lon: Optional[str] = None
    phones: Optional[str] = None
    site: Optional[str] = None
    schedule: Optional[str] = None
    is_open_now: Optional[bool] = None
    description: Optional[str] = None
    photos_count: Optional[int] = None
    has_video: Optional[bool] = None
    videos_count: Optional[int] = None
    has_stories: Optional[bool] = None
    stories_titles: Optional[str] = None
    services_count: Optional[int] = None
    services_list: Optional[str] = None
    services_prices: Optional[str] = None
    services_has_photos: Optional[bool] = None
    services_with_photos: Optional[str] = None
    services_has_covers: Optional[bool] = None
    services_description_filled: Optional[bool] = None
    has_news: Optional[bool] = None
    news_count: Optional[int] = None
    news_titles: Optional[str] = None
    news_texts: Optional[str] = None
    news_dates: Optional[str] = None
    has_features: Optional[bool] = None
    features_list: Optional[str] = None
    card_url: Optional[str] = None

    # Лист 3: Отзывы
    reviews: List[Review] = field(default_factory=list)


class Accumulator:
    def __init__(self, search_url=None):
        self.data = {}
        self.search_url = search_url

    def create(self, org_id):
        if org_id not in self.data:
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.data[org_id] = Organization(
                org_id=org_id,
                search_url=self.search_url,
                rank=len(self.data) + 1,
                date=date,
            )
        return self.data[org_id]

    def update(self, org_id, **kwargs):
        org = self.create(org_id)
        for k, v in kwargs.items():
            if hasattr(org, k):
                setattr(org, k, v)

    def add_review(self, org_id, review: Review):
        org = self.create(org_id)
        org.reviews.append(review)

    def dump(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {k: asdict(v) for k, v in self.data.items()},
                f,
                ensure_ascii=False,
                indent=2,
            )
