() => {
    const ul = document.querySelector("ul.search-list-view__list");
    if (!ul) return [];
    const result = [];
    const items = ul.querySelectorAll("li.search-snippet-view");
    for (let idx = 0; idx < items.length; idx++) {
        const li = items[idx];
        const body = li.querySelector("div.search-snippet-view__body");
        const org_id = body?.getAttribute("data-id");
        if (!org_id) continue;
        const coordinates = body?.getAttribute("data-coordinates");
        const title_tag = li.querySelector("a.link-overlay");
        const name = title_tag?.innerText.trim();
        const url_ = title_tag?.getAttribute("href");
        let rating_tag = li.querySelector("span.business-rating-badge-view__rating-text");
        const rating = rating_tag ? rating_tag.innerText.replace(",", ".").trim() : null;
        let reviews_count_tag = li.querySelector("span.business-rating-amount-view");
        if (!reviews_count_tag) {
            reviews_count_tag = li.querySelector("div.business-rating-with-text-view__count");
            if (reviews_count_tag) {
                reviews_count_tag = reviews_count_tag.querySelector("div");
            }
        }
        let reviews_count = reviews_count_tag ? reviews_count_tag.innerText.trim() : null;
        if (reviews_count) {
            reviews_count = reviews_count.replace(/[^\d]/g, "");
        }
        const address_tag = li.querySelector("a.search-business-snippet-view__address");
        const address = address_tag ? address_tag.innerText.trim() : null;
        const cats = Array.from(li.querySelectorAll(".search-business-snippet-view__category")).map(cat => cat.innerText.trim());
        const awards = Array.from(li.querySelectorAll(".business-header-awards-view__award-text")).map(award => award.innerText.trim());
        const hours_tag = li.querySelector("div.business-working-status-view");
        const working_status = hours_tag ? hours_tag.innerText.trim() : null;
        const price_title = li.querySelector("span.search-business-snippet-subtitle-view__title");
        const price_desc = li.querySelector("span.search-business-snippet-subtitle-view__description");
        const service = price_title ? price_title.innerText.trim() : null;
        let price_value = null, price_currency = null;
        if (price_desc) {
            const priceText = price_desc.innerText.replace(/\u00A0/g, " ").trim();
            price_currency = priceText.slice(-1);
            price_value = priceText.slice(0, -1).trim();
        }
        const ad_badge = li.querySelector("span.search-advert-badge__title");
        const ad = ad_badge ? ad_badge.innerText.trim() : null;

        let has_online_booking = false, booking_label = null;
        const booking_btn = li.querySelector(".search-snippet-gallery-view__button ._type_booking");
        if (booking_btn) {
            has_online_booking = true;
            const label = booking_btn.querySelector(".button__text .search-snippet-gallery-view__button-text");
            booking_label = label ? label.innerText.trim() : booking_btn.innerText.trim();
        }

        let has_prices_button = false;
        const prices_btn = li.querySelector(".search-snippet-gallery-view__button._type_prices a.button");
        if (prices_btn) {
            has_prices_button = true;
        }

        result.push({
            org_id,
            name,
            rank: idx + 1,
            rubric: cats.length ? cats.join(", ") : null,
            rating,
            reviews_count,
            short_address: address,
            is_ad: !!ad,
            promo_text: ad,
            badges: awards.length ? awards.join("; ") : null,
            has_online_booking,
            booking_label,
            has_prices_button,
            price_service: service,
            price_value,
            price_currency,
            price_duration: null,
            is_open_now: working_status ? !working_status.toLowerCase().includes("закрыто") : null,
            lat: coordinates ? coordinates.split(",")[1] : null,
            lon: coordinates ? coordinates.split(",")[0] : null,
            card_url: url_ ? "https://yandex.ru" + url_ : null,
        });
    }
    return result;
}
