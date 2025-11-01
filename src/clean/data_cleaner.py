
import csv
import re
import os
from pathlib import Path

# 使用绝对路径，让模块可以从任意位置调用
BASE_DIR = Path(__file__).parent.parent.parent
INPUT_FILE = str(BASE_DIR / "data" / "steam_topsellers_simple.csv")
OUTPUT_FILE = str(BASE_DIR / "data" / "steam_topsellers_simple_cleaned.csv")


def clean_title(title):
    if not title:
        return ""
    
    # 转为字符串并去除首尾空格
    title = str(title).strip()
    # 把所有多余的空格都变成一个空格
    title = re.sub(r'\s+', ' ', title)
    # 删除商标符号
    title = re.sub(r'[™®©]', '', title)
    
    return title


def clean_price(price_str):
    if not price_str:  
        return 0.0
    
    # 转为字符串并去除空格
    price_str = str(price_str).strip()
    
    if not price_str:
        return 0.0
    
    # 直接提取数字（包括小数）
    numbers = re.findall(r'\d+\.?\d*', price_str)
    
    # 如果找到数字，返回第一个（因为每格只有一个价格）
    if numbers:
        return float(numbers[0])
    
    return 0.0


def clean_date(date_str):
   
    if not date_str:
        return ""
    return str(date_str).strip()


def clean_tags(tags_str):
    
    if not tags_str:
        return ""
    
    tags_str = str(tags_str).strip()
    
    # 把其他可能的分隔符替换为英文逗号
    tags_str = tags_str.replace('，', ',').replace('、', ',')
    tags_str = tags_str.replace('|', ',').replace(';', ',')
    
    # 分割并清理每个标签
    tags = []
    for tag in tags_str.split(','):
        tag = tag.strip()
        if tag:  
            tags.append(tag)
    
    # 去重
    unique_tags = []
    for tag in tags:
        if tag not in unique_tags:
            unique_tags.append(tag)
    
    # 用英文逗号和空格连接
    return ", ".join(unique_tags)


def is_valid(row):
 
    if not row['appid'] or not row['appid'].isdigit():
        return False
    
    # title 不能为空
    if not row['title']:
        return False
    
    return True


def clean_data():
  
    print("=" * 60)
    print("Steam游戏数据清理工具")
    print("=" * 60)
    
    # ========== 步骤1：读取原始数据 ==========
    print(f"\n[1/4] 读取文件: {INPUT_FILE}")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            raw_data = list(reader)
    except FileNotFoundError:
        print(f"错误：找不到文件 {INPUT_FILE}")
        print("请确保文件在正确的位置！")
        return
    except Exception as e:
        print(f"错误：读取文件失败 - {e}")
        return
    
    print(f"   原始数据: {len(raw_data)} 条")
    
    # ========== 步骤2：清理数据 ==========
    print(f"\n[2/4] 清理数据...")
    cleaned_data = []
    removed = 0
    
    for row in raw_data:
        # 清理每个字段
        clean_row = {
            'appid': str(row.get('appid', '')).strip(),
            'title': clean_title(row.get('title', '')),
            'released': clean_date(row.get('released', '')),
            'current_price': clean_price(row.get('current_price', '')),
            'original_price': clean_price(row.get('original_price', '')),
            'tags': clean_tags(row.get('tags', ''))
        }
        
        # 验证是否有效
        if is_valid(clean_row):
            cleaned_data.append(clean_row)
        else:
            removed += 1
    
    print(f"   有效数据: {len(cleaned_data)} 条")
    print(f"   移除无效: {removed} 条")
    
    # ========== 步骤3：去除重复 ==========
    print(f"\n[3/4] 去除重复数据...")
    seen_appids = set()
    unique_data = []
    
    for row in cleaned_data:
        appid = row['appid']
        if appid not in seen_appids:
            seen_appids.add(appid)
            unique_data.append(row)
    
    duplicates = len(cleaned_data) - len(unique_data)
    print(f"   去重后: {len(unique_data)} 条")
    print(f"   移除重复: {duplicates} 条")
    
    # ========== 步骤4：保存结果 ==========
    print(f"\n[4/4] 保存文件: {OUTPUT_FILE}")
    try:
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            # 定义列顺序（与原始数据一致）
            fieldnames = ['appid', 'title', 'released', 'current_price', 
                         'original_price', 'tags']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()  # 写入表头
            writer.writerows(unique_data)  # 写入所有数据
        
        print(f"   ✓ 保存成功！")
    except Exception as e:
        print(f"   错误：保存失败 - {e}")
        return
    
    # ========== 显示统计信息 ==========
    print("\n" + "=" * 60)
    print("清理完成！统计信息：")
    print("=" * 60)
    print(f"原始记录数：{len(raw_data)}")
    print(f"有效记录数：{len(unique_data)}")
    print(f"无效记录数：{removed}")
    print(f"重复记录数：{duplicates}")
    print(f"最终保留：{len(unique_data)} 条")
    print("=" * 60)


# 程序入口
if __name__ == "__main__":
    clean_data()
