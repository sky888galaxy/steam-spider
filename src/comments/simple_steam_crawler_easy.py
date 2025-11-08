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
    found = []
    for p in patterns:
        found.extend(re.findall(p, text, flags))
    return found


def detect_threats(text):
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


def fetch_reviews(app_id, max_reviews=30):
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
            review_containers = soup.select('div.apphub_Card')
            if not review_containers:
                break
            for container in review_containers:
                if len(reviews) >= max_reviews:
                    break
                content_elem = container.select_one('div.apphub_CardTextContent')
                if not content_elem:
                    continue
                text = content_elem.get_text(strip=True)
                if not text:
                    continue
                helpful = 0
                helpful_elem = container.select_one('div.found_helpful')
                if helpful_elem:
                    helpful_text = helpful_elem.get_text()
                    import re
                    numbers = re.findall(r'\d+', helpful_text)
                    if numbers:
                        helpful = int(numbers[0])
                language = 'unknown'
                if any(ord(char) > 127 for char in text[:100]):
                    if any('\u4e00' <= char <= '\u9fff' for char in text[:100]):
                        language = 'chinese'
                    else:
                        language = 'other'
                else:
                    language = 'english'
                reviews.append({
                    'content': text, 
                    'page': page,
                    'helpful': helpful,
                    'language': language
                })
            page += 1
            time.sleep(1.5)
        return reviews
    except Exception as e:
        print(f"抓取评论时出错: {e}")
        return reviews


def analyze_game_threats(app_id, game_title, max_reviews=30):
    reviews = fetch_reviews(app_id, max_reviews)
    if not reviews:
        return None
    threat_stats = {'links': 0, 'keywords': 0, 'contacts': 0}
    language_stats = {'chinese': 0, 'english': 0, 'other': 0, 'unknown': 0}
    total_helpful = 0
    suspicious_reviews = []
    for i, review in enumerate(reviews):
        threats = detect_threats(review['content'])
        for key in threat_stats:
            threat_stats[key] += threats[key]
        lang = review.get('language', 'unknown')
        if lang in language_stats:
            language_stats[lang] += 1
        else:
            language_stats['unknown'] += 1
        total_helpful += review.get('helpful', 0)
        if threats['links'] or threats['keywords'] or threats['contacts']:
            suspicious_reviews.append({
                'index': i + 1,
                'content': review['content'][:100] + '...' if len(review['content']) > 100 else review['content'],
                'page': review['page'],
                'helpful': review.get('helpful', 0),
                'language': review.get('language', 'unknown'),
                'threats': threats
            })
    return {
        'appid': app_id,
        'title': game_title,
        'total_reviews': len(reviews),
        'suspicious_reviews': len(suspicious_reviews),
        'threat_stats': threat_stats,
        'threat_rate': len(suspicious_reviews) / len(reviews) if reviews else 0,
        'language_stats': language_stats,
        'avg_helpful': total_helpful / len(reviews) if reviews else 0,
        'details': suspicious_reviews[:5]
    }
