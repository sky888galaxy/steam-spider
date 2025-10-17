import sys, subprocess, importlib, time, csv
from typing import Optional

def ensure_package(pip_name, import_name=None):
    if import_name is None:
        import_name = pip_name
    try:
        return importlib.import_module(import_name)
    except Exception:
        print(f"模块 {import_name} 未找到，使用 {sys.executable} 安装 {pip_name} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        return importlib.import_module(import_name)

# 依赖
requests = ensure_package("requests", "requests")
bs4 = ensure_package("beautifulsoup4", "bs4")
from bs4 import BeautifulSoup

# 常量
BASE_SEARCH = "https://store.steampowered.com/search/"
APP_URL = "https://store.steampowered.com/app/{appid}/"
APPDETAILS_API = "https://store.steampowered.com/api/appdetails"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 创建稳健 session（不使用系统代理，带重试）
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
session.headers.update(HEADERS)
session.trust_env = False   # 忽略环境代理（如需代理请修改）
session.proxies = {}

retry_strategy = Retry(
    total=4,
    backoff_factor=1,
    status_forcelist=[429,500,502,503,504],
    allowed_methods=["HEAD","GET","OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

def fetch_search_page(page=1, filter_name="topsellers"):
    params = {"filter": filter_name, "page": page}
    timeout = (8, 30)
    r = session.get(BASE_SEARCH, params=params, timeout=timeout)
    r.raise_for_status()
    return r.text

def parse_search_html(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("a.search_result_row")
    out = []
    for a in rows:
        appid = a.get("data-ds-appid") or a.get("data-ds-packageid") or ""
        title = (a.select_one(".title").get_text(strip=True) if a.select_one(".title") else "")
        released = (a.select_one(".search_released").get_text(strip=True) if a.select_one(".search_released") else "")
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

def get_price_from_api(appid: str, cc="US", lang="en") -> Optional[dict]:
    try:
        resp = session.get(APPDETAILS_API, params={"appids": appid, "cc": cc, "l": lang}, timeout=(8,15))
        resp.raise_for_status()
        data = resp.json()
        info = data.get(str(appid), {})
        if not info.get("success"):
            return None
        d = info.get("data", {})
        po = d.get("price_overview")
        if po:
            return {
                "currency": po.get("currency"),
                "initial": po.get("initial")/100.0 if po.get("initial") is not None else None,
                "final": po.get("final")/100.0 if po.get("final") is not None else None,
                "discount_percent": po.get("discount_percent")
            }
        # free / 无 price_overview
        return None
    except Exception:
        return None

def get_tags_from_app_page(appid: str) -> str:
    try:
        url = APP_URL.format(appid=appid)
        r = session.get(url, params={"l":"english"}, timeout=(8,20))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tags = []
        for a in soup.select("div.glance_tags.popular_tags a.app_tag"):
            t = a.get_text(strip=True)
            if t: tags.append(t)
        if not tags:
            for a in soup.select("div.glance_tags a"):
                t = a.get_text(strip=True)
                if t and len(t) < 40: tags.append(t)
        tags = list(dict.fromkeys(tags))
        return ", ".join(tags)
    except Exception:
        return ""

def merge_tags(search_tags: str, page_tags: str) -> str:
    seen = []
    for t in (search_tags or "").split(","):
        t = t.strip()
        if t and t not in seen: seen.append(t)
    for t in (page_tags or "").split(","):
        t = t.strip()
        if t and t not in seen: seen.append(t)
    return ", ".join(seen)

def price_fallback_from_text(price_text: str):
    # 简单回退：若含数字就提取最后一组数字（可能包含货币符），否则返回 empty
    if not price_text:
        return ("","")
    s = price_text.replace("\u2009"," ").strip()  # 去掉特殊空格
    # 常见形式："¥ 68.00", "¥9.00¥ 29.00", "Free", "Free to Play", "On Demand"
    if any(tok.lower().startswith("free") for tok in s.split()):
        return ("0", "0")
    # 如果含两个货币/价位，尝试取最后一个为 current, 前一个为 original
    import re
    nums = re.findall(r"[\d\.,]+", s)
    if not nums:
        return (s, "")
    if len(nums) == 1:
        return (nums[0].replace(",",""), "")
    # >=2
    original = nums[-2].replace(",","")
    current = nums[-1].replace(",","")
    return (current, original)

def save_csv(rows, filename="steam_topsellers_simple.csv"):
    keys = ["appid","title","released","current_price","original_price","tags"]
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

def main():
    print("当前 Python 解释器：", sys.executable)
    pages_to_scrape = 1   # 默认抓第一页，改成 N 抓更多页
    all_items = []
    for p in range(1, pages_to_scrape+1):
        print(f"抓取搜索页 page {p} ...")
        html = fetch_search_page(page=p, filter_name="topsellers")
        items = parse_search_html(html)
        all_items.extend(items)
        time.sleep(1.0)

    out = []
    for i, it in enumerate(all_items, 1):
        appid = it.get("appid","")
        title = it.get("title","")
        print(f"[{i}/{len(all_items)}] {title[:60]}  (appid={appid})")
        record = {"appid": appid, "title": title, "released": it.get("released",""),
                  "current_price": "", "original_price": "", "tags": ""}

        # 价格：优先 API（结构化），失败回退到搜索页文本解析
        if appid:
            price_info = get_price_from_api(appid, cc="CN", lang="schinese")
            if price_info and price_info.get("final") is not None:
                record["current_price"] = str(price_info.get("final"))
                record["original_price"] = str(price_info.get("initial")) if price_info.get("initial") is not None else ""
            else:
                cur, orig = price_fallback_from_text(it.get("price_text",""))
                record["current_price"] = cur
                record["original_price"] = orig
            # 标签：优先详情页的完整标签，若为空用搜索页标签
            tags_page = get_tags_from_app_page(appid)
            merged = merge_tags(it.get("tags_text",""), tags_page)
            record["tags"] = merged
        else:
            # 无 appid（package/bundle）：用搜索页价格文本/标签回退
            cur, orig = price_fallback_from_text(it.get("price_text",""))
            record["current_price"] = cur
            record["original_price"] = orig
            record["tags"] = it.get("tags_text","")

        out.append(record)
        time.sleep(1.0)  # 礼貌延迟

    save_csv(out)
    print(f"完成，保存 {len(out)} 条到 steam_topsellers_simple.csv")

if __name__ == "__main__":
    main()
