#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam评论威胁分析模块 - 课设版
功能：独立的评论爬取与信息安全威胁分析模块
可被其他程序调用，也可独立运行
"""

import re
import requests
import time
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 威胁检测规则
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


def detect_threats(text):
    """
    检测文本中的安全威胁
    参数: text - 评论文本
    返回: 字典包含威胁统计
    """
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
    """
    核心功能：根据appid爬取游戏评论
    参数: 
        app_id - Steam游戏ID
        max_reviews - 最多爬取评论数
    返回: 评论列表 [{'content': '评论文本', 'page': 页码, 'helpful': 有用数, 'language': 语言}, ...]
    """
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
                
                # 获取评论文本
                content_elem = container.select_one('div.apphub_CardTextContent')
                if not content_elem:
                    continue
                    
                text = content_elem.get_text(strip=True)
                if not text:
                    continue
                
                # 获取有用数（简单提取数字）
                helpful = 0
                helpful_elem = container.select_one('div.found_helpful')
                if helpful_elem:
                    helpful_text = helpful_elem.get_text()
                    import re
                    numbers = re.findall(r'\d+', helpful_text)
                    if numbers:
                        helpful = int(numbers[0])
                
                # 检测语言（简单判断）
                language = 'unknown'
                if any(ord(char) > 127 for char in text[:100]):  # 包含非ASCII字符
                    if any('\u4e00' <= char <= '\u9fff' for char in text[:100]):  # 中文字符
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
    """
    主函数：分析单款游戏的评论威胁
    这是供外部调用的主要接口
    
    参数:
        app_id - Steam游戏ID
        game_title - 游戏名称
        max_reviews - 最多分析评论数
    
    返回: 字典包含完整的威胁分析结果
    {
        'appid': '游戏ID',
        'title': '游戏名',
        'total_reviews': 总评论数,
        'suspicious_reviews': 可疑评论数,
        'threat_stats': {
            'links': 外部链接数,
            'keywords': 可疑关键词数,
            'contacts': 联系方式数
        },
        'threat_rate': 威胁比例,
        'language_stats': {'chinese': 数量, 'english': 数量, 'other': 数量},
        'avg_helpful': 平均有用数,
        'details': [前5条可疑评论详情]
    }
    """
    # 1. 爬取评论
    reviews = fetch_reviews(app_id, max_reviews)
    if not reviews:
        return None
    
    # 2. 威胁检测与统计
    threat_stats = {'links': 0, 'keywords': 0, 'contacts': 0}
    language_stats = {'chinese': 0, 'english': 0, 'other': 0, 'unknown': 0}
    total_helpful = 0
    suspicious_reviews = []
    
    for i, review in enumerate(reviews):
        threats = detect_threats(review['content'])
        
        # 累计统计
        for key in threat_stats:
            threat_stats[key] += threats[key]
        
        # 语言统计
        lang = review.get('language', 'unknown')
        if lang in language_stats:
            language_stats[lang] += 1
        else:
            language_stats['unknown'] += 1
        
        # 有用数统计
        total_helpful += review.get('helpful', 0)
        
        # 记录可疑评论
        if threats['links'] or threats['keywords'] or threats['contacts']:
            suspicious_reviews.append({
                'index': i + 1,
                'content': review['content'][:100] + '...' if len(review['content']) > 100 else review['content'],
                'page': review['page'],
                'helpful': review.get('helpful', 0),
                'language': review.get('language', 'unknown'),
                'threats': threats
            })
    
    # 3. 返回分析结果
    return {
        'appid': app_id,
        'title': game_title,
        'total_reviews': len(reviews),
        'suspicious_reviews': len(suspicious_reviews),
        'threat_stats': threat_stats,
        'threat_rate': len(suspicious_reviews) / len(reviews) if reviews else 0,
        'language_stats': language_stats,
        'avg_helpful': total_helpful / len(reviews) if reviews else 0,
        'details': suspicious_reviews[:5]  # 只返回前5条详情
    }


def print_analysis_result(result):
    """格式化打印分析结果"""
    if not result:
        print("无分析结果")
        return
    
    print("\n" + "=" * 60)
    print(f"游戏: {result['title']} (ID: {result['appid']})")
    print(f"总评论数: {result['total_reviews']}")
    print(f"可疑评论: {result['suspicious_reviews']} ({result['threat_rate']*100:.2f}%)")
    print(f"\n威胁统计:")
    print(f"  外部链接: {result['threat_stats']['links']}")
    print(f"  可疑关键词: {result['threat_stats']['keywords']}")
    print(f"  联系方式: {result['threat_stats']['contacts']}")
    
    if result['details']:
        print(f"\n可疑评论示例 (前{len(result['details'])}条):")
        for detail in result['details']:
            threats_desc = []
            if detail['threats']['links']:
                threats_desc.append(f"链接×{detail['threats']['links']}")
            if detail['threats']['keywords']:
                threats_desc.append(f"关键词×{detail['threats']['keywords']}")
            if detail['threats']['contacts']:
                threats_desc.append(f"联系×{detail['threats']['contacts']}")
            print(f"\n  [{detail['index']}] 威胁: {', '.join(threats_desc)}")
            print(f"      {detail['content']}")
    print("=" * 60)


def main():
    """
    独立运行示例
    演示如何使用本模块分析单款游戏
    """
    print("Steam评论威胁分析模块 (课设版)")
    print("=" * 60)
    
    # 示例：分析Counter-Strike 2
    print("\n示例：分析 Counter-Strike 2")
    app_id = input("请输入游戏ID (默认730): ").strip() or "730"
    title = input("请输入游戏名 (默认Counter-Strike 2): ").strip() or "Counter-Strike 2"
    max_reviews = input("分析评论数 (默认30): ").strip()
    
    try:
        max_reviews = int(max_reviews) if max_reviews else 30
    except ValueError:
        max_reviews = 30
    
    print(f"\n开始分析 {title} (ID: {app_id})...")
    result = analyze_game_threats(app_id, title, max_reviews)
    print_analysis_result(result)


if __name__ == "__main__":
    main()
