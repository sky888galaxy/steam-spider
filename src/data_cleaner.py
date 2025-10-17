#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam游戏数据清理工具 - 简化版
用于清洗从Steam提取的游戏数据
适合课程设计使用
"""

import csv
import re
import os
from datetime import datetime

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

def clean_title(title):
    """
    清理游戏标题
    - 去除多余空格
    - 去除特殊字符
    - 统一格式
    """
    if not title:
        return ""
    
    # 去除首尾空格
    title = title.strip()
    
    # 去除多余的空格
    title = re.sub(r'\s+', ' ', title)
    
    # 去除一些特殊字符（但保留基本标点）
    title = re.sub(r'[™®©]', '', title)
    
    # 去除HTML标签（如果有）
    title = re.sub(r'<[^>]+>', '', title)
    
    return title

def clean_price(price_str):
    """
    清理价格数据
    - 统一格式
    - 处理异常值
    - 转换为数字
    """
    if not price_str:
        return 0.0
    
    # 去除空格和特殊字符
    price_str = str(price_str).strip()
    
    # 处理"Free"等免费标识
    if price_str.lower() in ['free', 'free to play', '免费', '0']:
        return 0.0
    
    # 提取数字
    numbers = re.findall(r'\d+\.?\d*', price_str)
    if numbers:
        try:
            return float(numbers[-1])  # 取最后一个数字
        except ValueError:
            return 0.0
    
    return 0.0

def clean_release_date(date_str):
    """
    清理发布日期
    - 统一日期格式
    - 处理异常日期
    """
    if not date_str:
        return ""
    
    date_str = date_str.strip()
    
    # 常见的无效日期标识
    invalid_dates = ['Coming Soon', '即将推出', 'TBA', 'To be announced']
    if any(invalid in date_str for invalid in invalid_dates):
        return "未发布"
    
    # 简单的日期格式清理
    # 这里只做基本清理，保持原格式
    return date_str

def clean_tags(tags_str):
    """
    清理游戏标签
    - 去除重复标签
    - 标准化格式
    - 去除无效标签
    """
    if not tags_str:
        return ""
    
    # 分割标签
    tags = [tag.strip() for tag in tags_str.split(',')]
    
    # 去除空标签和过长的标签
    tags = [tag for tag in tags if tag and len(tag) <= 30]
    
    # 去除重复（保持顺序）
    unique_tags = []
    for tag in tags:
        if tag not in unique_tags:
            unique_tags.append(tag)
    
    # 限制标签数量（最多10个）
    if len(unique_tags) > 10:
        unique_tags = unique_tags[:10]
    
    return ", ".join(unique_tags)

def validate_appid(appid):
    """
    验证Steam应用ID
    """
    if not appid:
        return False
    
    # Steam应用ID应该是纯数字
    return appid.isdigit() and len(appid) > 0

def detect_duplicates(data_list):
    """
    检测重复数据
    返回重复项的索引列表
    """
    seen_appids = {}
    seen_titles = {}
    duplicates = []
    
    for i, row in enumerate(data_list):
        appid = row.get('appid', '')
        title = row.get('title', '')
        
        # 检查appid重复
        if appid and appid in seen_appids:
            duplicates.append(i)
        elif appid:
            seen_appids[appid] = i
        
        # 检查标题重复（可能是同一游戏的不同版本）
        if title and title in seen_titles:
            # 这里不直接标记为重复，而是记录相似度高的
            pass
        elif title:
            seen_titles[title] = i
    
    return duplicates

def clean_steam_data(input_file, output_file=None):
    """
    主要的数据清理函数
    """
    # 如果是相对路径，转换为基于脚本目录的绝对路径
    if not os.path.isabs(input_file):
        input_file = os.path.join(script_dir, input_file)
    
    if not os.path.exists(input_file):
        print(f"错误：找不到输入文件 {input_file}")
        return
    
    if output_file is None:
        # 确保输出文件也在data目录
        if input_file.endswith('.csv'):
            base_name = os.path.basename(input_file).replace('.csv', '_cleaned.csv')
            data_dir = os.path.join(os.path.dirname(script_dir), 'data')
            output_file = os.path.join(data_dir, base_name)
        else:
            output_file = input_file.replace('.csv', '_cleaned.csv')
    elif not os.path.isabs(output_file):
        # 如果是相对路径，也放到data目录
        data_dir = os.path.join(os.path.dirname(script_dir), 'data')
        output_file = os.path.join(data_dir, output_file)
    
    print(f"开始清理数据文件: {input_file}")
    print("=" * 50)
    
    # 读取原始数据
    original_data = []
    try:
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                original_data.append(row)
    except Exception as e:
        print(f"读取文件出错: {e}")
        return
    
    print(f"原始数据条数: {len(original_data)}")
    
    # 清理数据
    cleaned_data = []
    invalid_count = 0
    
    for i, row in enumerate(original_data):
        # 验证appid
        if not validate_appid(row.get('appid', '')):
            invalid_count += 1
            print(f"跳过无效记录 #{i+1}: appid无效")
            continue
        
        # 清理各个字段
        cleaned_row = {
            'appid': row.get('appid', '').strip(),
            'title': clean_title(row.get('title', '')),
            'released': clean_release_date(row.get('released', '')),
            'current_price': clean_price(row.get('current_price', '')),
            'original_price': clean_price(row.get('original_price', '')),
            'tags': clean_tags(row.get('tags', ''))
        }
        
        # 验证清理后的数据
        if not cleaned_row['title']:
            invalid_count += 1
            print(f"跳过无效记录 #{i+1}: 标题为空")
            continue
        
        cleaned_data.append(cleaned_row)
    
    # 检测重复数据
    duplicate_indices = detect_duplicates(cleaned_data)
    if duplicate_indices:
        print(f"发现 {len(duplicate_indices)} 条重复数据，正在移除...")
        cleaned_data = [row for i, row in enumerate(cleaned_data) if i not in duplicate_indices]
    
    # 数据质量统计
    print("\n数据清理统计:")
    print(f"  原始记录数: {len(original_data)}")
    print(f"  无效记录数: {invalid_count}")
    print(f"  重复记录数: {len(duplicate_indices)}")
    print(f"  清理后记录数: {len(cleaned_data)}")
    
    # 价格统计
    free_games = sum(1 for row in cleaned_data if row['current_price'] == 0.0)
    paid_games = len(cleaned_data) - free_games
    print(f"  免费游戏: {free_games} 个")
    print(f"  付费游戏: {paid_games} 个")
    
    # 保存清理后的数据
    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['appid', 'title', 'released', 'current_price', 'original_price', 'tags']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_data)
        
        print(f"\n✓ 清理完成！数据已保存到: {output_file}")
        
    except Exception as e:
        print(f"保存文件出错: {e}")

def generate_data_report(csv_file):
    """
    生成数据质量报告
    """
    # 如果是相对路径，转换为基于脚本目录的绝对路径
    if not os.path.isabs(csv_file):
        csv_file = os.path.join(script_dir, csv_file)
    
    if not os.path.exists(csv_file):
        print(f"文件不存在: {csv_file}")
        return
    
    print(f"\n生成数据报告: {csv_file}")
    print("=" * 50)
    
    data = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    if not data:
        print("数据为空")
        return
    
    # 基本统计
    total_games = len(data)
    free_games = sum(1 for row in data if float(row.get('current_price', 0)) == 0.0)
    
    # 价格分析
    prices = []
    for row in data:
        price = float(row.get('current_price', 0))
        if price > 0:
            prices.append(price)
    
    # 标签分析
    all_tags = []
    for row in data:
        tags = row.get('tags', '')
        if tags:
            all_tags.extend([tag.strip() for tag in tags.split(',')])
    
    # 统计最常见的标签
    tag_count = {}
    for tag in all_tags:
        if tag:
            tag_count[tag] = tag_count.get(tag, 0) + 1
    
    top_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # 输出报告
    print(f"总游戏数: {total_games}")
    print(f"免费游戏: {free_games} ({free_games/total_games*100:.1f}%)")
    print(f"付费游戏: {total_games-free_games} ({(total_games-free_games)/total_games*100:.1f}%)")
    
    if prices:
        print(f"\n价格统计 (付费游戏):")
        print(f"  最低价格: ¥{min(prices):.2f}")
        print(f"  最高价格: ¥{max(prices):.2f}")
        print(f"  平均价格: ¥{sum(prices)/len(prices):.2f}")
    
    if top_tags:
        print(f"\n最常见标签 (前10):")
        for tag, count in top_tags:
            print(f"  {tag}: {count} 次")

def main():
    """
    主程序
    """
    print("Steam游戏数据清理工具")
    print("适用于课程设计")
    print()
    
    # 查找输入文件
    default_file = "../data/steam_topsellers_simple.csv"
    
    while True:
        print("请选择操作:")
        print("1. 清理数据")
        print("2. 生成数据报告")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == '1':
            # 数据清理
            input_file = input(f"请输入CSV文件名 (默认: {default_file}): ").strip()
            if not input_file:
                input_file = default_file
            
            output_file = input("请输入输出文件名 (默认: 自动生成): ").strip()
            if not output_file:
                output_file = None
            
            clean_steam_data(input_file, output_file)
            
        elif choice == '2':
            # 生成报告
            input_file = input(f"请输入CSV文件名 (默认: {default_file}): ").strip()
            if not input_file:
                input_file = default_file
            
            generate_data_report(input_file)
            
        elif choice == '3':
            print("感谢使用，再见！")
            break
            
        else:
            print("无效选择，请重新输入")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    main()