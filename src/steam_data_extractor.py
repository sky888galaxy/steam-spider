#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版（初学友好）Steam 热榜抓取脚本
逻辑：抓 search 页 -> 提取 appid/title/released/price_text/tags_text -> 逐个调用 appdetails API 获取结构化价格 -> 抓详情页标签并合并 -> 保存 CSV
去掉了 session/retry 等进阶用法，保留主流程，便于学习与理解。
"""

import sys
import time
import csv
import re
import os

# 依赖检查（更简单的方式：如果缺包，提示安装并退出）
try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    print("请先安装依赖：pip install requests beautifulsoup4")
    sys.exit(1)

# ---------------- 常量（可修改） ----------------
BASE_SEARCH = "https://store.steampowered.com/search/"
APP_URL = "https://store.steampowered.com/app/{appid}/"
APPDETAILS_API = "https://store.steampowered.com/api/appdetails"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

OUT_CSV = "steam_topsellers_simple.csv"
PAGES_TO_SCRAPE = 1       # 抓取第几页（默认 1）
DELAY = 1.0               # 请求间隔（秒），课堂练习用小延迟即可
# ------------------------------------------------

# ---------------- 基本网络函数（第1-5章、7章） ----------------
def fetch_search_page(page=1, filter_name="topsellers"):
    """抓取 Steam 搜索页 HTML（使用简单的 requests.get）"""
    params = {"filter": filter_name, "page": page}
    r = requests.get(BASE_SEARCH, params=params, headers=HEADERS, timeout=(8, 30))
    r.raise_for_status()
    return r.text

def parse_search_html(html):
    """
    解析搜索页（BeautifulSoup）—— 返回按顺序的条目字典列表
    字段：appid, title, released, price_text, tags_text
    （对应第4章 字符串与容器，第7章 BeautifulSoup/字符串处理）
    """
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
            # 把换行与多空格规整掉
            price_text = " ".join(pe.get_text(" ", strip=True).split())
        tags_text = ""
        te = a.select_one(".search_tags")
        if te:
            # 用竖线分割并转成逗号分隔
            tags_text = ", ".join(t.strip() for t in te.get_text(separator="|").split("|") if t.strip())
        out.append({
            "appid": appid,
            "title": title,
            "released": released,
            "price_text": price_text,
            "tags_text": tags_text
        })
    return out

# ---------------- API / 详情页抓取（第1-5章） ----------------
def get_price_from_api(appid, cc="CN", lang="schinese"):
    """
    调用 appdetails API，若返回 price_overview 则解析并返回字典。
    返回 None 表示没有 price_overview（例如免费或 API 不提供）。
    """
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
        # 这里用简单的异常处理，便于初学者看到失败时的行为
        return None

def get_tags_from_app_page(appid):
    """抓取详情页的热门标签（简单实现，主要目的是得到页面上的标签）"""
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
            # 备用选择器：有时候结构变化，退化为更宽泛的选择器
            for a in soup.select("div.glance_tags a"):
                t = a.get_text(strip=True)
                if t and len(t) < 40:
                    tags.append(t)
        # 去重并保持顺序
        tags = list(dict.fromkeys(tags))
        return ", ".join(tags)
    except Exception:
        return ""

# ---------------- 工具函数（第4章，第7章） ----------------
def merge_tags(search_tags, page_tags):
    """简单合并去重，保持出现顺序"""
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
    """
    简单回退：从搜索页 price_text 中用正则提取数字，用于初学者练习正则（第7章）
    如果包含 Free/免费，则返回 ('0','0')
    """
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

# ---------------- 保存 CSV（第8章） ----------------
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

# ---------------- 主流程（第2、3章：程序结构） ----------------
def main():
    print("当前 Python 解释器：", sys.executable)
    all_items = []
    for p in range(1, PAGES_TO_SCRAPE + 1):
        print(f"抓取搜索页 page {p} ...")
        try:
            html = fetch_search_page(page=p, filter_name="topsellers")
            items = parse_search_html(html)
            all_items.extend(items)
            print(f"本页抓到 {len(items)} 条")
        except Exception as e:
            print("抓取搜索页出错：", e)
        time.sleep(DELAY)

    out = []
    for i, it in enumerate(all_items, 1):
        appid = it.get("appid","").strip()
        title = it.get("title","").strip()
        print(f"[{i}/{len(all_items)}] {title[:60]}  (appid={appid})")
        record = {"appid": appid, "title": title, "released": it.get("released",""),
                  "current_price": "", "original_price": "", "tags": ""}

        if appid:
            # 尝试 API（优先）
            price_info = get_price_from_api(appid, cc="CN", lang="schinese")
            if price_info and price_info.get("final") is not None:
                record["current_price"] = str(price_info.get("final"))
                record["original_price"] = str(price_info.get("initial")) if price_info.get("initial") is not None else ""
            else:
                # API 不可用时回退到搜索页的价格文本
                cur, orig = price_fallback_from_text(it.get("price_text",""))
                record["current_price"] = cur
                record["original_price"] = orig

            # 抓详情页标签并合并（若失败则使用搜索页标签）
            tags_page = get_tags_from_app_page(appid)
            merged = merge_tags(it.get("tags_text",""), tags_page)
            record["tags"] = merged
        else:
            # 无 appid（bundle/package），使用搜索页信息回退
            cur, orig = price_fallback_from_text(it.get("price_text",""))
            record["current_price"] = cur
            record["original_price"] = orig
            record["tags"] = it.get("tags_text","")

        out.append(record)
        time.sleep(DELAY)

    save_csv(out)
    print(f"完成，保存 {len(out)} 条到 {OUT_CSV}")

if __name__ == "__main__":
    main()
