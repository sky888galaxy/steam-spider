#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam游戏评论爬虫模块 - 超简化版
用于课程设计，作为模块被主程序调用
功能：爬取Steam游戏评论并检测可疑内容
"""

import re
import requests
import time
from bs4 import BeautifulSoup


def get_steam_comments(game_id, comment_count=20):
    """
    爬取Steam游戏评论并检测可疑内容 - 主要函数
    
    参数：
        game_id: Steam游戏ID，例如"570"（Dota2的ID）
        comment_count: 要爬取的评论数量，默认20条
    
    返回：
        字典格式的结果，包含：
        - success: 是否成功 (True/False)
        - game_id: 游戏ID
        - total_comments: 总评论数
        - link_count: 外部链接数量
        - keyword_count: 可疑关键词数量  
        - contact_count: 联系方式数量
        - problem_comments: 有问题的评论列表
    """
    
    print(f"开始分析游戏ID: {game_id}")
    
    # 直接用传入的游戏ID爬取评论
    comments = _crawl_comments(game_id, comment_count)
    if not comments:
        return {'success': False, 'error': '未获取到评论'}
    print(f"成功爬取 {len(comments)} 条评论")
    
    # 检测可疑内容
    result = _analyze_comments(comments)
    result['success'] = True
    result['game_id'] = game_id
    
    print(f"检测完成 - 链接:{result['link_count']}, 关键词:{result['keyword_count']}, 联系方式:{result['contact_count']}")
    return result


def get_steam_comments_by_name(game_name, comment_count=20):
    """
    通过游戏名称爬取评论 - 备用函数
    
    参数：
        game_name: 游戏名称，例如"dota2"
        comment_count: 要爬取的评论数量，默认20条
    
    返回：
        字典格式的结果，与get_steam_comments相同
    """
    
    print(f"开始搜索游戏: {game_name}")
    
    # 第1步：搜索游戏，获取游戏ID
    game_id = _search_game(game_name)
    if not game_id:
        return {'success': False, 'error': '未找到游戏'}
    print(f"找到游戏ID: {game_id}")
    
    # 第2步：调用主函数
    result = get_steam_comments(game_id, comment_count)
    result['game_name'] = game_name  # 添加游戏名称
    
    return result


def _search_game(game_name):
    """
    内部函数：搜索游戏获取ID
    
    参数：game_name - 游戏名称
    返回：游戏ID字符串，失败返回None
    """
    try:
        # 1. 构造搜索网址
        url = "https://store.steampowered.com/search/"
        params = {'term': game_name, 'l': 'schinese'}  # l=schinese表示中文
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        # 2. 发送HTTP请求获取网页
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # 3. 用BeautifulSoup解析HTML网页
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 4. 找到搜索结果的第一个游戏链接
        first_game = soup.find('a', class_='search_result_row')
        if not first_game:
            return None
        
        # 5. 从链接中提取游戏ID（数字）
        game_url = first_game.get('href', '')
        match = re.search(r'/app/(\d+)/', game_url)  # 正则表达式匹配数字
        
        return match.group(1) if match else None
        
    except Exception as e:
        print(f"搜索游戏出错: {e}")
        return None


def _crawl_comments(game_id, max_count):
    """
    内部函数：爬取游戏评论
    
    参数：
        game_id - 游戏ID
        max_count - 最大评论数
    返回：评论列表
    """
    comments = []
    
    try:
        # 1. 构造评论页面网址
        url = f"https://steamcommunity.com/app/{game_id}/reviews/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        page = 1  # 从第1页开始
        
        # 2. 循环爬取多页评论，直到达到数量要求
        while len(comments) < max_count and page <= 3:  # 最多爬3页
            
            # 3. 设置请求参数
            params = {
                'browsefilter': 'mostrecent',    # 最新评论
                'filterLanguage': 'schinese',    # 中文评论
                'p': page                        # 页码
            }
            
            # 4. 发送请求获取评论页面
            response = requests.get(url, params=params, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 5. 找到页面中所有评论内容
            review_divs = soup.find_all('div', class_='apphub_CardTextContent')
            if not review_divs:
                break  # 没有评论了，退出循环
            
            # 6. 提取每条评论的文字内容
            for div in review_divs:
                if len(comments) >= max_count:
                    break
                
                text = div.get_text(strip=True)  # 获取纯文本，去掉HTML标签
                if text:
                    comments.append(text)
            
            page += 1
            time.sleep(1)  # 暂停1秒，避免请求太快被封
        
        return comments
        
    except Exception as e:
        print(f"爬取评论出错: {e}")
        return []


def _analyze_comments(comments):
    """
    内部函数：分析评论内容
    
    参数：comments - 评论列表
    返回：分析结果字典
    """
    # 1. 定义检测规则（正则表达式）
    link_patterns = [
        r"https?://[^\s]+",              # http或https开头的链接
        r"www\.[^\s]+\.[a-zA-Z]{2,}"     # www开头的网址
    ]
    
    keywords = [
        "外挂", "挂机", "脚本", "破解", "hack", "cheat", "bot",
        "免费送", "免费皮肤", "抽奖", "代练", "低价", 
        "加群", "私聊", "联系我"
    ]
    
    contact_patterns = [
        r"1[3-9]\d{9}",                                          # 手机号
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"      # 邮箱
    ]
    
    # 2. 初始化统计结果
    link_count = 0
    keyword_count = 0  
    contact_count = 0
    problem_comments = []
    
    # 3. 逐条检测每个评论
    for i, comment in enumerate(comments):
        comment_links = 0
        comment_keywords = 0
        comment_contacts = 0
        
        # 检测链接
        for pattern in link_patterns:
            matches = re.findall(pattern, comment, re.IGNORECASE)  # 不区分大小写
            comment_links += len(matches)
        
        # 检测关键词
        for keyword in keywords:
            if keyword.lower() in comment.lower():  # 转小写比较
                comment_keywords += 1
        
        # 检测联系方式
        for pattern in contact_patterns:
            matches = re.findall(pattern, comment)
            comment_contacts += len(matches)
        
        # 4. 累加总数
        link_count += comment_links
        keyword_count += comment_keywords
        contact_count += comment_contacts
        
        # 5. 记录有问题的评论
        if comment_links > 0 or comment_keywords > 0 or comment_contacts > 0:
            problem_comments.append({
                'index': i + 1,
                'content': comment[:80] + '...' if len(comment) > 80 else comment,
                'links': comment_links,
                'keywords': comment_keywords,
                'contacts': comment_contacts
            })
    
    # 6. 返回统计结果
    return {
        'total_comments': len(comments),
        'link_count': link_count,
        'keyword_count': keyword_count,
        'contact_count': contact_count,
        'problem_comments': problem_comments[:5]  # 只返回前5个问题评论
    }


# 测试代码（仅在直接运行此文件时执行）
if __name__ == "__main__":
    # 测试主函数（用游戏ID）
    print("=== 测试用游戏ID爬取评论 ===")
    result1 = get_steam_comments("570", 5)  # 570是Dota2的ID
    print("测试结果:", result1)
    
    print("\n=== 测试用游戏名称爬取评论 ===")
    result2 = get_steam_comments_by_name("dota2", 5)
    print("测试结果:", result2)
