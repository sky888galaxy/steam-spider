import csv
import re
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_FILE = os.path.join(BASE_DIR, "data", "steam_topsellers_simple.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "steam_topsellers_simple_cleaned.csv")


def clean_title(title):
    if not title:
        return ""
    title = str(title).strip()
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'[™®©]', '', title)
    return title


def clean_price(price_str):
    if not price_str:  
        return 0.0
    price_str = str(price_str).strip()
    if not price_str:
        return 0.0
    numbers = re.findall(r'\d+\.?\d*', price_str)
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
    tags_str = tags_str.replace('，', ',').replace('、', ',')
    tags_str = tags_str.replace('|', ',').replace(';', ',')
    tags = []
    for tag in tags_str.split(','):
        tag = tag.strip()
        if tag:  
            tags.append(tag)
    unique_tags = []
    for tag in tags:
        if tag not in unique_tags:
            unique_tags.append(tag)
    return ", ".join(unique_tags)


def is_valid(row):
    if not row['appid'] or not row['appid'].isdigit():
        return False
    if not row['title']:
        return False
    return True


def clean_data():
    print("=" * 60)
    print("Steam游戏数据清理工具")
    print("=" * 60)
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
    print(f"\n[2/4] 清理数据...")
    cleaned_data = []
    removed = 0
    for row in raw_data:
        clean_row = {
            'appid': str(row.get('appid', '')).strip(),
            'title': clean_title(row.get('title', '')),
            'released': clean_date(row.get('released', '')),
            'current_price': clean_price(row.get('current_price', '')),
            'original_price': clean_price(row.get('original_price', '')),
            'tags': clean_tags(row.get('tags', ''))
        }
        if is_valid(clean_row):
            cleaned_data.append(clean_row)
        else:
            removed += 1
    print(f"   有效数据: {len(cleaned_data)} 条")
    print(f"   移除无效: {removed} 条")
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
    print(f"\n[4/4] 保存文件: {OUTPUT_FILE}")
    try:
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['appid', 'title', 'released', 'current_price', 
                         'original_price', 'tags']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_data)
        print(f"   ✓ 保存成功！")
    except Exception as e:
        print(f"   错误：保存失败 - {e}")
        return
    print("\n" + "=" * 60)
    print("清理完成！统计信息：")
    print("=" * 60)
    print(f"原始记录数：{len(raw_data)}")
    print(f"有效记录数：{len(unique_data)}")
    print(f"无效记录数：{removed}")
    print(f"重复记录数：{duplicates}")
    print(f"最终保留：{len(unique_data)} 条")
    print("=" * 60)


if __name__ == "__main__":
    clean_data()