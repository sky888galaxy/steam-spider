import re
import requests
import time
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
EXTERNAL_LINKS = [r"https?://[^\s]+", r"www\.[^\s]+\.[a-zA-Z]{2,}"]
SUSPICIOUS_KEYWORDS = [
    "外挂", "挂机", "脚本", "破解", "免费获得", "代挂",
    "hack", "cheat", "bot", "script", "crack",
    "免费送", "限时优惠", "点击领取", "立即获得",
    "稀有皮肤", "免费皮肤", "开箱", "抽奖",
    "代练", "低价出售", "便宜卖", "代打",
    "加群", "进群", "关注", "私聊", "联系我"
]
CONTACT_PATTERNS = [r"1[3-9]\d{9}", r"[\w._%+-]+@[\w.-]+\.[a-zA-Z]{2,}"]


def _find_regex(patterns, text, flags=0):
    """辅助函数：统一处理正则匹配"""
    found = []
    for p in patterns:
        found.extend(re.findall(p, text, flags))
    return found


def detect_suspicious_content(text):
    text = text or ""
    links = _find_regex(EXTERNAL_LINKS, text, re.IGNORECASE)
    contacts = _find_regex(CONTACT_PATTERNS, text)
    keywords = [k for k in SUSPICIOUS_KEYWORDS if k.lower() in text.lower()]
    return {
        'links': len(links),
        'keywords': len(keywords),
        'contacts': len(contacts),
        'found_items': links + contacts + keywords
    }


def search_steam_game(game_name):
    try:
        url = "https://store.steampowered.com/search/"
        params = {'term': game_name, 'category1': 998, 'l': 'schinese'}
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        
        soup = BeautifulSoup(r.content, 'html.parser')
        el = soup.select_one('a.search_result_row')
        if not el:
            return None
        
        href = el.get('href', '')
        m = re.search(r'/app/(\d+)/', href)
        if not m:
            return None
        
        title = el.select_one('span.title')
        return {'id': m.group(1), 'name': title.text.strip() if title else '未知'}
    except Exception:
        return None


def get_steam_reviews(app_id, max_reviews=30):
    reviews = []
    url = f"https://steamcommunity.com/app/{app_id}/reviews/"
    page = 1
    
    try:
        while len(reviews) < max_reviews:
            params = {'browsefilter': 'mostrecent', 'filterLanguage': 'schinese', 'p': page}
            r = requests.get(url, params=params, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                break
            
            soup = BeautifulSoup(r.content, 'html.parser')
            elems = soup.select('div.apphub_CardTextContent')
            if not elems:
                break
            
            for e in elems:
                if len(reviews) >= max_reviews:
                    break
                text = e.get_text(strip=True)
                if text:
                    reviews.append({'content': text, 'page': page})
            
            page += 1
            time.sleep(1.5)
        return reviews
    except Exception:
        return reviews


def analyze_game_reviews(game_name, max_reviews=30):
    info = search_steam_game(game_name)
    if not info:
        return None
    
    reviews = get_steam_reviews(info['id'], max_reviews)
    if not reviews:
        return None
    
    stats = {'links': 0, 'keywords': 0, 'contacts': 0}
    problems = []
    
    for i, r in enumerate(reviews):
        d = detect_suspicious_content(r['content'])
        for k in stats:
            stats[k] += d[k]
        if d['links'] or d['keywords'] or d['contacts']:
            snippet = r['content'][:100] + '...' if len(r['content']) > 100 else r['content']
            problems.append({'index': i+1, 'page': r['page'], 'content': snippet, 'issues': d})
    
    return {
        'game_info': info,
        'total_reviews': len(reviews),
        'stats': stats,
        'problem_reviews': problems[:5]
    }


def print_analysis_result(res):
    if not res:
        print("无结果")
        return
    
    print("\n" + "=" * 40)
    print(f"游戏: {res['game_info']['name']} (ID: {res['game_info']['id']})")
    print(f"分析评论数: {res['total_reviews']}")
    print(f"检测统计: {res['stats']}")
    
    if res['problem_reviews']:
        print(f"\n问题评论 ({len(res['problem_reviews'])} 条):")
        for p in res['problem_reviews']:
            issues = []
            if p['issues']['links']:
                issues.append(f"链接{p['issues']['links']}")
            if p['issues']['keywords']:
                issues.append(f"关键词{p['issues']['keywords']}")
            if p['issues']['contacts']:
                issues.append(f"联系{p['issues']['contacts']}")
            print(f"\n#{p['index']} (页{p['page']}) [{', '.join(issues)}]")
            print(f"{p['content']}")
    else:
        print("\n✓ 未发现问题评论")


def main():
    print("Steam评论分析工具 (课设版)")
    while True:
        name = input("\n游戏名称 (q退出): ").strip()
        if name.lower() == 'q':
            break
        if not name:
            continue
        
        cnt = input("评论数量 (默认30, 最多50): ").strip()
        try:
            cnt = int(cnt) if cnt else 30
        except ValueError:
            cnt = 30
        cnt = min(cnt, 50)
        
        result = analyze_game_reviews(name, cnt)
        print_analysis_result(result)
        print("=" * 40)


if __name__ == "__main__":
    main()
