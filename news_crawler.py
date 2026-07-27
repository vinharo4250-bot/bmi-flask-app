from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

SEARCH_URL = "https://search.naver.com/search.naver"
RESULTS_PER_PAGE = 10
MAX_PAGES = 3


def _date_range(days):
    end = datetime.now()
    start = end - timedelta(days=days)
    return start.strftime("%Y.%m.%d"), end.strftime("%Y.%m.%d")


def _clean_text(tag):
    if tag is None:
        return ""
    text = tag.get_text(strip=True)
    for phrase in ("새 창 이동", "새 창 열림"):
        text = text.replace(phrase, "")
    return text.strip()


def _parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    seen_urls = set()

    for title_tag in soup.select('a[data-heatmap-target=".tit"]'):
        try:
            url = title_tag.get("href")
            if not url or url in seen_urls:
                continue

            title = _clean_text(title_tag)

            profile = title_tag.find_previous(attrs={"data-sds-comp": "Profile"})
            press = ""
            date = ""

            if profile:
                prof_anchors = profile.select('a[data-heatmap-target=".prof"]')
                for prof_anchor in prof_anchors:
                    candidate = _clean_text(prof_anchor)
                    if candidate:
                        press = candidate
                        break

                subtexts = profile.select(".sds-comps-profile-info-subtext")
                if subtexts:
                    date = _clean_text(subtexts[0])

            seen_urls.add(url)
            items.append({
                "title": title,
                "url": url,
                "press": press,
                "date": date,
            })
        except Exception:
            continue

    return items


def search_news(keyword, days):
    start_date, end_date = _date_range(days)
    all_items = []

    for page in range(MAX_PAGES):
        start = page * RESULTS_PER_PAGE + 1
        params = {
            "where": "news",
            "query": keyword,
            "pd": 3,
            "ds": start_date,
            "de": end_date,
            "start": start,
        }

        response = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()

        page_items = _parse_page(response.text)
        if not page_items:
            break

        all_items.extend(page_items)

    return all_items
