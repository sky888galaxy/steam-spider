
import re
import requests
import time
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 检测规则 
EXTERNAL_LINKS = [
    r"https?://[^\s]+",
    r"www\.[^\s]+\.[a-zA-Z]{2,}"
]

SUSPICIOUS_KEYWORDS = [
    "外挂", "挂机", "脚本", "破解", "免费获得", "代挂",
    "hack", "cheat", "bot", "script", "crack",
    "免费送", "限时优惠", "点击领取", "立即获得",
    "稀有皮肤", "免费皮肤", "开箱", "抽奖",
    "代练", "低价出售", "便宜卖", "代打",
    "加群", "进群", "关注", "私聊", "联系我"
]

CONTACT_PATTERNS = [
    r"1[3-9]\d{9}", 
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" 
]


def detect_suspicious_content(text):

    result = {
        'links': 0,
        'keywords': 0,
        'contacts': 0,
        'found_items': []
    }
    
    # 检测外部链接
    for pattern in EXTERNAL_LINKS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result['links'] += len(matches)
            result['found_items'].extend(matches)
    
    # 检测可疑关键词
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword.lower() in text.lower():
            result['keywords'] += 1
            result['found_items'].append(keyword)
    
    # 检测联系方式
    for pattern in CONTACT_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            result['contacts'] += len(matches)
            result['found_items'].extend(matches)
    
    return result


def search_steam_game(game_name):

    try:
        print(f"正在搜索游戏: {game_name}")
        
        # Steam搜索URL
        search_url = "https://store.steampowered.com/search/"
        params = {
            'term': game_name,
            'category1': 998, 
            'l': 'schinese'  
        }
        
        # 发送请求
        response = requests.get(search_url, params=params, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"搜索请求失败，状态码: {response.status_code}")
            return None
        
        # 解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        search_results = soup.find_all('a', class_='search_result_row')
        
        if not search_results:
            print("没有找到搜索结果")
            return None
        
        # 获取第一个结果
        first_result = search_results[0]
        game_url = first_result.get('href', '')
        
        # 提取游戏ID
        game_id_match = re.search(r'/app/(\d+)/', game_url)
        if not game_id_match:
            print("无法提取游戏ID")
            return None
        
        game_id = game_id_match.group(1)
        
        # 提取游戏名称
        title_elem = first_result.find('span', class_='title')
        game_title = title_elem.text.strip() if title_elem else "未知游戏"
        
        return {
            'id': game_id,
            'name': game_title
        }
        
    except Exception as e:
        print(f"搜索游戏时出错: {e}")
        return None


def get_steam_reviews(app_id, max_reviews=30):

    reviews = []
    
    try:
        print(f"开始获取游戏 {app_id} 的评论...")
        
        # Steam评论页面URL
        reviews_url = f"https://steamcommunity.com/app/{app_id}/reviews/"
        
        page = 1
        max_pages = (max_reviews // 10) + 1 
        
        while page <= max_pages and len(reviews) < max_reviews:
            print(f"正在获取第 {page} 页评论...")
            
            params = {
                'browsefilter': 'mostrecent',
                'filterLanguage': 'schinese',
                'p': page
            }
            
            response = requests.get(reviews_url, params=params, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                print(f"获取评论失败，状态码: {response.status_code}")
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            review_elements = soup.find_all('div', class_='apphub_CardTextContent')
            
            if not review_elements:
                print("没有找到更多评论")
                break
            
            # 提取评论文本
            for review_elem in review_elements:
                if len(reviews) >= max_reviews:
                    break
                
                review_text = review_elem.get_text(strip=True)
                if review_text:
                    reviews.append({
                        'content': review_text,
                        'page': page
                    })
            
            page += 1
            time.sleep(2) 
        
        print(f"成功获取 {len(reviews)} 条评论")
        return reviews
        
    except Exception as e:
        print(f"获取评论时出错: {e}")
        return []


def analyze_game_reviews(game_name, max_reviews=30):

    print("=" * 50)
    print(f"开始分析游戏: {game_name}")
    print("=" * 50)
    
    # 第一步：搜索游戏
    game_info = search_steam_game(game_name)
    if not game_info:
        print("无法找到游戏，请检查游戏名称")
        return None
    
    print(f"找到游戏: {game_info['name']} (ID: {game_info['id']})")
    
    # 第二步：获取评论
    reviews = get_steam_reviews(game_info['id'], max_reviews)
    if not reviews:
        print("无法获取评论")
        return None
    
    # 第三步：分析评论内容
    print("\n开始分析评论内容...")
    
    total_stats = {
        'links': 0,
        'keywords': 0,
        'contacts': 0
    }
    
    problem_reviews = []
    
    for i, review in enumerate(reviews):
        content = review['content']
        detection = detect_suspicious_content(content)
        
        # 累计统计
        total_stats['links'] += detection['links']
        total_stats['keywords'] += detection['keywords']
        total_stats['contacts'] += detection['contacts']
        
        # 记录有问题的评论
        if detection['links'] > 0 or detection['keywords'] > 0 or detection['contacts'] > 0:
            problem_reviews.append({
                'index': i + 1,
                'content': content[:100] + '...' if len(content) > 100 else content,
                'page': review['page'],
                'issues': detection
            })
    
    # 返回分析结果
    return {
        'game_info': game_info,
        'total_reviews': len(reviews),
        'stats': total_stats,
        'problem_reviews': problem_reviews[:5] 
    }


def print_analysis_result(result):

    if not result:
        return
    
    print("\n" + "=" * 50)
    print("分析结果")
    print("=" * 50)
    
    print(f"游戏名称: {result['game_info']['name']}")
    print(f"Steam ID: {result['game_info']['id']}")
    print(f"分析评论数: {result['total_reviews']}")
    print()
    
    print("检测统计:")
    print(f"  外部链接: {result['stats']['links']} 个")
    print(f"  可疑关键词: {result['stats']['keywords']} 个")
    print(f"  联系方式: {result['stats']['contacts']} 个")
    
    # 显示有问题的评论
    if result['problem_reviews']:
        print(f"\n发现问题评论 {len(result['problem_reviews'])} 条:")
        print("-" * 30)
        
        for review in result['problem_reviews']:
            print(f"\n评论 #{review['index']} (第{review['page']}页):")
            
            issues = []
            if review['issues']['links'] > 0:
                issues.append(f"链接{review['issues']['links']}个")
            if review['issues']['keywords'] > 0:
                issues.append(f"关键词{review['issues']['keywords']}个")
            if review['issues']['contacts'] > 0:
                issues.append(f"联系方式{review['issues']['contacts']}个")
            
            print(f"  问题: {', '.join(issues)}")
            print(f"  内容: {review['content']}")
    else:
        print("\n✓ 没有发现问题评论")


def main():

    print("Steam游戏评论分析工具 - 简化版")
    print("功能: 爬取Steam游戏评论并检测可疑内容")
    print("适用于课程设计")
    print()
    
    while True:
        print("\n请输入游戏名称 (输入 'q' 退出):")
        game_name = input("> ").strip()
        
        if game_name.lower() == 'q':
            print("感谢使用，再见！")
            break
        
        if not game_name:
            print("请输入有效的游戏名称")
            continue
        
        print("\n请输入要分析的评论数量 (默认30条，最多50条):")
        count_input = input("> ").strip()
        
        try:
            max_reviews = int(count_input) if count_input else 30
            max_reviews = min(max_reviews, 50)  # 限制最大数量
        except ValueError:
            print("输入无效，使用默认值30")
            max_reviews = 30
        
        # 执行分析
        result = analyze_game_reviews(game_name, max_reviews)
        
        # 显示结果
        print_analysis_result(result)
        
        print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
