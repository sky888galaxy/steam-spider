#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam游戏数据清理模块 - 超简化版
用于自动清洗从Steam提取的游戏数据
供主程序调用，无需手动输入
"""

import csv
import re
import os

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 定义固定的输入输出路径（指向项目根目录的data文件夹）
# src/clean/data_cleaner.py -> ../../data/ -> b-crawler/data/
DEFAULT_INPUT_FILE = os.path.join(SCRIPT_DIR, "../../data/steam_topsellers_simple.csv")
DEFAULT_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "../../data/steam_topsellers_simple_cleaned.csv")


def clean_steam_data_simple():
    """
    简化的数据清理函数 - 直接处理固定路径的文件
    从 ../data/steam_topsellers_simple.csv 读取
    输出到 ../data/steam_topsellers_simple_cleaned.csv
    """
    return clean_steam_data_auto(DEFAULT_INPUT_FILE, DEFAULT_OUTPUT_FILE)


def clean_steam_data_auto(input_file, output_file):
    """
    自动清理Steam游戏数据 - 主要函数
    
    参数：
        input_file: steam_data_extractor生成的CSV文件路径
        output_file: 清理后数据的输出文件路径（供数据分析使用）
    
    返回：
        字典格式的结果：
        - success: 是否成功
        - input_file: 输入文件路径
        - output_file: 输出文件路径
        - original_count: 原始数据条数
        - cleaned_count: 清理后的数据条数
        - removed_count: 移除的无效数据条数
    """
    
    print("开始自动清理Steam数据...")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    
    # 第1步：读取steam_data_extractor生成的CSV文件
    original_data = _read_csv_file(input_file)
    if not original_data:
        return {'success': False, 'error': '无法读取输入文件'}
    
    print(f"原始数据: {len(original_data)} 条")
    
    # 第2步：清理数据
    cleaned_data = []
    removed_count = 0
    
    for row in original_data:
        # 清理每一行数据
        cleaned_row = _clean_single_row(row)
        
        # 验证数据有效性
        if _is_valid_row(cleaned_row):
            cleaned_data.append(cleaned_row)
        else:
            removed_count += 1
    
    # 第3步：去除重复数据
    cleaned_data = _remove_duplicates(cleaned_data)
    
    print(f"清理完成: {len(cleaned_data)} 条有效数据，移除 {removed_count} 条无效数据")
    
    # 第4步：保存清理后的数据供数据分析使用
    success = _save_csv_file(cleaned_data, output_file)
    
    if success:
        print(f"数据清理完成！输出文件已保存，可供数据分析使用")
        return {
            'success': True,
            'input_file': input_file,
            'output_file': output_file,
            'original_count': len(original_data),
            'cleaned_count': len(cleaned_data),
            'removed_count': removed_count
        }
    else:
        return {'success': False, 'error': '保存输出文件失败'}


def _read_csv_file(file_path):
    """内部函数：读取CSV文件"""
    try:
        data = []
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    except Exception as e:
        print(f"读取文件出错: {e}")
        return []


def _clean_single_row(row):
    """内部函数：清理单行数据"""
    return {
        'appid': str(row.get('appid', '')).strip(),
        'title': _clean_title(row.get('title', '')),
        'released': _clean_date(row.get('released', '')),
        'current_price': _clean_price(row.get('current_price', '')),
        'original_price': _clean_price(row.get('original_price', '')),
        'tags': _clean_tags(row.get('tags', ''))
    }


def _clean_title(title):
    """内部函数：清理游戏标题"""
    if not title:
        return ""
    
    title = str(title).strip()
    title = re.sub(r'\s+', ' ', title)  # 去除多余空格
    title = re.sub(r'[™®©]', '', title)  # 去除商标符号
    title = re.sub(r'<[^>]+>', '', title)  # 去除HTML标签
    
    return title


def _clean_price(price_str):
    """内部函数：清理价格"""
    if not price_str:
        return 0.0
    
    price_str = str(price_str).strip().lower()
    
    # 处理免费游戏
    if price_str in ['free', 'free to play', '免费', '0']:
        return 0.0
    
    # 提取数字
    numbers = re.findall(r'\d+\.?\d*', price_str)
    if numbers:
        try:
            return float(numbers[-1])
        except:
            return 0.0
    
    return 0.0


def _clean_date(date_str):
    """内部函数：清理发布日期"""
    if not date_str:
        return ""
    
    date_str = str(date_str).strip()
    
    # 处理未发布的游戏
    if any(word in date_str.lower() for word in ['coming soon', '即将推出', 'tba']):
        return "未发布"
    
    return date_str


def _clean_tags(tags_str):
    """内部函数：清理游戏标签，使用中文逗号分隔"""
    if not tags_str:
        return ""
    
    # 分割标签（处理可能的逗号、空格等分隔符）
    tags_str = str(tags_str)
    # 先统一替换各种分隔符为英文逗号
    tags_str = tags_str.replace('，', ',').replace('、', ',').replace('|', ',').replace(';', ',')
    
    # 分割并清理标签
    tags = [tag.strip() for tag in tags_str.split(',')]
    tags = [tag for tag in tags if tag and len(tag) <= 30]  # 去除空标签和过长标签
    
    # 去重并保持顺序
    unique_tags = []
    for tag in tags:
        if tag not in unique_tags:
            unique_tags.append(tag)
    
    # 使用中文逗号连接，方便后续分析时提取
    return "，".join(unique_tags[:10])  # 最多保留10个标签


def _is_valid_row(row):
    """内部函数：验证数据行是否有效"""
    # 检查必要字段
    if not row['appid'] or not row['appid'].isdigit():
        return False
    
    if not row['title']:
        return False
    
    return True


def _remove_duplicates(data_list):
    """内部函数：去除重复数据"""
    seen_appids = set()
    unique_data = []
    
    for row in data_list:
        appid = row['appid']
        if appid not in seen_appids:
            seen_appids.add(appid)
            unique_data.append(row)
    
    return unique_data


def _save_csv_file(data, output_file):
    """内部函数：保存CSV文件"""
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            if data:
                fieldnames = ['appid', 'title', 'released', 'current_price', 'original_price', 'tags']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        
        print(f"数据已保存到: {output_file}")
        return True
        
    except Exception as e:
        print(f"保存文件出错: {e}")
        return False

# 测试代码（仅在直接运行此文件时执行）
if __name__ == "__main__":
    # 测试数据清理功能
    print("=== Steam游戏数据清理工具 ===")
    print()
    print("正在处理文件...")
    print(f"输入: {DEFAULT_INPUT_FILE}")
    print(f"输出: {DEFAULT_OUTPUT_FILE}")
    print()
    
    # 检查输入文件是否存在
    input_file = DEFAULT_INPUT_FILE
    output_file = DEFAULT_OUTPUT_FILE
    
    # 如果测试文件不存在，创建测试数据
    if not os.path.exists(input_file):
        print("创建测试数据文件...")
        os.makedirs(os.path.dirname(input_file), exist_ok=True)
        
        # 创建测试CSV文件
        import csv
        test_data = [
            {'appid': '570', 'title': 'Dota 2™', 'released': '2013-07-09', 'current_price': 'Free', 'original_price': 'Free', 'tags': 'MOBA,Free to Play,Multiplayer'},
            {'appid': '730', 'title': 'Counter-Strike 2   ', 'released': '2023-09-27', 'current_price': '0', 'original_price': '0', 'tags': 'FPS,Multiplayer,Competitive'},
            {'appid': '', 'title': '', 'released': '', 'current_price': '', 'original_price': '', 'tags': ''},  # 无效数据
            {'appid': '570', 'title': 'Dota 2', 'released': '2013-07-09', 'current_price': 'Free', 'original_price': 'Free', 'tags': 'MOBA,Free to Play'}  # 重复数据
        ]
        
        with open(input_file, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['appid', 'title', 'released', 'current_price', 'original_price', 'tags']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(test_data)
        print(f"测试数据已保存到: {input_file}")
    
    # 执行数据清理 - 使用简化函数
    result = clean_steam_data_simple()
    
    print()
    print("="*50)
    if result.get('success'):
        print("✓ 数据清理成功！")
        print(f"  原始数据: {result['original_count']} 条")
        print(f"  有效数据: {result['cleaned_count']} 条")
        print(f"  移除无效: {result['removed_count']} 条")
        print(f"  输出文件: {result['output_file']}")
    else:
        print("✗ 数据清理失败！")
        print(f"  错误信息: {result.get('error', '未知错误')}")
    print("="*50)