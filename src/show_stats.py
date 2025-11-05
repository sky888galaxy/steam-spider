#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單數據統計和概覽腳本
快速查看收集到的數據概況
"""

import pandas as pd
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

def show_data_overview():
    """顯示數據概覽"""
    print("🔍 Steam遊戲數據概覽")
    print("=" * 50)
    
    # 檢查文件
    files = {
        "原始數據": BASE_DIR / "data" / "steam_topsellers_simple.csv",
        "清洗數據": BASE_DIR / "data" / "steam_topsellers_simple_cleaned.csv", 
        "評論分析": BASE_DIR / "data" / "comment_analysis_results.csv"
    }
    
    for name, filepath in files.items():
        if filepath.exists():
            try:
                df = pd.read_csv(filepath)
                print(f"✅ {name}: {len(df)} 條記錄")
                
                # 詳細統計
                if name == "清洗數據":
                    show_game_stats(df)
                elif name == "評論分析":
                    show_comment_stats(df)
                    
            except Exception as e:
                print(f"❌ {name}: 讀取失敗 - {e}")
        else:
            print(f"❌ {name}: 文件不存在")

def show_game_stats(df):
    """顯示遊戲數據統計"""
    print("  📊 遊戲數據統計:")
    
    # 基本統計
    total = len(df)
    print(f"    總遊戲數: {total}")
    
    # 價格統計
    try:
        paid_games = df[pd.to_numeric(df['original_price'], errors='coerce') > 0]
        free_games = df[pd.to_numeric(df['original_price'], errors='coerce') == 0]
        
        print(f"    付費遊戲: {len(paid_games)} ({len(paid_games)/total*100:.1f}%)")
        print(f"    免費遊戲: {len(free_games)} ({len(free_games)/total*100:.1f}%)")
        
        if len(paid_games) > 0:
            avg_price = pd.to_numeric(paid_games['original_price'], errors='coerce').mean()
            print(f"    平均價格: ${avg_price:.2f}")
            
            # 價格範圍
            prices = pd.to_numeric(paid_games['original_price'], errors='coerce').dropna()
            if len(prices) > 0:
                print(f"    價格範圍: ${prices.min():.2f} - ${prices.max():.2f}")
    except Exception as e:
        print(f"    價格統計錯誤: {e}")
    
    # 折扣統計
    try:
        if 'discounts' in df.columns:
            discounted = df[pd.to_numeric(df['discounts'], errors='coerce') > 0]
            print(f"    有折扣遊戲: {len(discounted)} ({len(discounted)/total*100:.1f}%)")
            
            if len(discounted) > 0:
                avg_discount = pd.to_numeric(discounted['discounts'], errors='coerce').mean()
                print(f"    平均折扣: {avg_discount:.1f}%")
    except Exception as e:
        print(f"    折扣統計錯誤: {e}")

def show_comment_stats(df):
    """顯示評論分析統計"""
    print("  💬 評論分析統計:")
    
    try:
        total_games = len(df)
        print(f"    分析遊戲數: {total_games}")
        
        # 總評論數
        if 'total_reviews' in df.columns:
            total_reviews = pd.to_numeric(df['total_reviews'], errors='coerce').sum()
            print(f"    總評論數: {total_reviews}")
            
            avg_reviews = pd.to_numeric(df['total_reviews'], errors='coerce').mean()
            print(f"    平均每遊戲評論數: {avg_reviews:.1f}")
        
        # 威脅統計
        if 'threat_rate' in df.columns:
            # 處理百分比字符串
            threat_rates = df['threat_rate'].str.replace('%', '').astype(float)
            avg_threat = threat_rates.mean()
            max_threat = threat_rates.max()
            
            print(f"    平均威脅率: {avg_threat:.1f}%")
            print(f"    最高威脅率: {max_threat:.1f}%")
            
            # 高威脅遊戲
            high_threat = df[threat_rates > 10]
            print(f"    高威脅遊戲(>10%): {len(high_threat)}")
        
        # 語言統計
        if 'chinese_reviews' in df.columns and 'english_reviews' in df.columns:
            chinese_total = pd.to_numeric(df['chinese_reviews'], errors='coerce').sum()
            english_total = pd.to_numeric(df['english_reviews'], errors='coerce').sum()
            
            print(f"    中文評論: {chinese_total}")
            print(f"    英文評論: {english_total}")
            
    except Exception as e:
        print(f"    評論統計錯誤: {e}")

def show_top_games():
    """顯示熱門遊戲"""
    cleaned_file = BASE_DIR / "data" / "steam_topsellers_simple_cleaned.csv"
    
    if not cleaned_file.exists():
        print("❌ 找不到清洗數據文件")
        return
    
    try:
        df = pd.read_csv(cleaned_file)
        print("\n🏆 TOP 10 熱門遊戲:")
        print("-" * 50)
        
        for i, row in df.head(10).iterrows():
            title = row.get('title', 'N/A')
            price = row.get('original_price', 0)
            discount = row.get('discounts', 0)
            
            try:
                price = float(price) if price != '' else 0
                discount = float(discount) if discount != '' else 0
            except:
                price, discount = 0, 0
            
            print(f"{i+1:2d}. {title[:40]:<40}")
            if price > 0:
                if discount > 0:
                    current_price = price * (1 - discount/100)
                    print(f"    💰 ${current_price:.2f} (原價${price:.2f}, 折扣{discount:.0f}%)")
                else:
                    print(f"    💰 ${price:.2f}")
            else:
                print(f"    🆓 免費")
                
    except Exception as e:
        print(f"❌ 讀取遊戲列表失敗: {e}")

def main():
    """主函數"""
    print("📈 Steam遊戲數據統計工具")
    print("=" * 60)
    
    # 顯示數據概覽
    show_data_overview()
    
    # 顯示熱門遊戲
    show_top_games()
    
    print("\n" + "=" * 60)
    print("✅ 統計完成！")
    
if __name__ == "__main__":
    main()