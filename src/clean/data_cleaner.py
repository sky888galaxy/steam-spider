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
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            raw_data = list(reader)
    except FileNotFoundError:
        print(f"错误：找不到文件 {INPUT_FILE}")
        return
    except Exception as e:
        print(f"错误：读取文件失败 - {e}")
        return
    cleaned_data = []
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
    seen_appids = set()
    unique_data = []
    for row in cleaned_data:
        appid = row['appid']
        if appid not in seen_appids:
            seen_appids.add(appid)
            unique_data.append(row)
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        fieldnames = ['appid', 'title', 'released', 'current_price', 
                     'original_price', 'tags']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_data)


if __name__ == "__main__":
    clean_data()