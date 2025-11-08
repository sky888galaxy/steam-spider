import sys
import time
import csv
import re
import os

try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    print("请先安装依赖：pip install requests beautifulsoup4")
    sys.exit(1)

BASE_SEARCH = "https://store.steampowered.com/search/"
APP_URL = "https://store.steampowered.com/app/{appid}/"
APPDETAILS_API = "https://store.steampowered.com/api/appdetails"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

OUT_CSV = "steam_topsellers_simple.csv"
PAGES_TO_SCRAPE = 1
DELAY = 1.0


def fetch_search_page(page=1, filter_name="topsellers"):
    params = {"filter": filter_name, "page": page}
    r = requests.get(BASE_SEARCH, params=params, headers=HEADERS, timeout=(8, 30))
    r.raise_for_status()
    return r.text

def parse_search_html(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("a.search_result_row")
    out = []
    for a in rows:
        appid = a.get("data-ds-appid") or a.get("data-ds-packageid") or ""
        title = a.select_one(".title").get_text(strip=True) if a.select_one(".title") else ""
        released = a.select_one(".search_released").get_text(strip=True) if a.select_one(".search_released") else ""
        price_text = ""
        pe = a.select_one(".search_price")
        if pe:
            price_text = " ".join(pe.get_text(" ", strip=True).split())
        tags_text = ""
        te = a.select_one(".search_tags")
        if te:
            tags_text = ", ".join(t.strip() for t in te.get_text(separator="|").split("|") if t.strip())
        out.append({
            "appid": appid,
            "title": title,
            "released": released,
            "price_text": price_text,
            "tags_text": tags_text
        })
    return out

def get_price_from_api(appid, cc="CN", lang="schinese"):
    try:
        resp = requests.get(APPDETAILS_API, params={"appids": appid, "cc": cc, "l": lang},
                            headers=HEADERS, timeout=(8, 15))
        resp.raise_for_status()
        data = resp.json()
        info = data.get(str(appid), {})
        if not info.get("success"):
            return None
        d = info.get("data", {})
        po = d.get("price_overview")
        if not po:
            return None
        return {
            "currency": po.get("currency"),
            "initial": po.get("initial")/100.0 if po.get("initial") is not None else None,
            "final": po.get("final")/100.0 if po.get("final") is not None else None,
            "discount_percent": po.get("discount_percent")
        }
    except Exception:
        return None

def get_tags_from_app_page(appid):
    try:
        url = APP_URL.format(appid=appid)
        r = requests.get(url, params={"l":"english"}, headers=HEADERS, timeout=(8, 20))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tags = []
        for a in soup.select("div.glance_tags.popular_tags a.app_tag"):
            t = a.get_text(strip=True)
            if t:
                tags.append(t)
        if not tags:
            for a in soup.select("div.glance_tags a"):
                t = a.get_text(strip=True)
                if t and len(t) < 40:
                    tags.append(t)
        tags = list(dict.fromkeys(tags))
        return ", ".join(tags)
    except Exception:
        return ""

def merge_tags(search_tags, page_tags):
    seen = []
    for t in (search_tags or "").split(","):
        t = t.strip()
        if t and t not in seen:
            seen.append(t)
    for t in (page_tags or "").split(","):
        t = t.strip()
        if t and t not in seen:
            seen.append(t)
    return ", ".join(seen)

def price_fallback_from_text(price_text):
    if not price_text:
        return ("","")
    s = price_text.replace("\u2009", " ").strip()
    if any(tok.lower().startswith("free") for tok in s.split()):
        return ("0", "0")
    nums = re.findall(r"[\d\.,]+", s)
    if not nums:
        return (s, "")
    if len(nums) == 1:
        return (nums[0].replace(",", ""), "")
    original = nums[-2].replace(",", "")
    current = nums[-1].replace(",", "")
    return (current, original)

def save_csv(rows, filename=OUT_CSV):
    keys = ["appid","title","released","current_price","original_price","tags"]
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    with open(filename, "w", newline='', encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "appid": r.get("appid",""),
                "title": r.get("title",""),
                "released": r.get("released",""),
                "current_price": r.get("current_price",""),
                "original_price": r.get("original_price",""),
                "tags": r.get("tags","")
            })
