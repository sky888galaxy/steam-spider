#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调用示例：如何使用评论威胁分析模块
演示如何在其他程序中导入并使用该模块
"""

import sys
import os
import csv
import time

# 添加路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from comments.simple_steam_crawler_easy import analyze_game_threats, print_analysis_result


def example1_single_game():
    """示例1：分析单款游戏"""
    print("\n" + "="*60)
    print("示例1：分析单款游戏")
    print("="*60)
    
    # 直接调用：传入appid和游戏名
    result = analyze_game_threats(
        app_id="730",
        game_title="Counter-Strike 2",
        max_reviews=20
    )
    
    # 打印结果
    print_analysis_result(result)


def example2_batch_from_csv():
    """示例2：从CSV读取游戏列表，批量分析"""
    print("\n" + "="*60)
    print("示例2：批量分析游戏")
    print("="*60)
    
    csv_file = "data/steam_topsellers_simple.csv"
    
    # 读取CSV
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            games = list(csv.DictReader(f))[:5]  # 只分析前5款
    except FileNotFoundError:
        print(f"找不到文件: {csv_file}")
        return
    
    # 批量分析
    results = []
    for i, game in enumerate(games, 1):
        app_id = game.get('appid', '').strip()
        title = game.get('title', '').strip()
        
        if not app_id or not title:
            continue
        
        print(f"\n[{i}/{len(games)}] 正在分析: {title}")
        result = analyze_game_threats(app_id, title, max_reviews=15)
        
        if result:
            results.append(result)
            print(f"✓ 完成: 分析{result['total_reviews']}条评论, "
                  f"发现{result['suspicious_reviews']}条可疑")
        else:
            print("✗ 无法获取评论")
        
        time.sleep(2)  # 避免请求过快
    
    # 保存结果
    if results:
        output_file = "data/batch_analysis_results.csv"
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['appid', 'title', 'total_reviews', 'suspicious_reviews',
                         'links', 'keywords', 'contacts', 'threat_rate']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for r in results:
                writer.writerow({
                    'appid': r['appid'],
                    'title': r['title'],
                    'total_reviews': r['total_reviews'],
                    'suspicious_reviews': r['suspicious_reviews'],
                    'links': r['threat_stats']['links'],
                    'keywords': r['threat_stats']['keywords'],
                    'contacts': r['threat_stats']['contacts'],
                    'threat_rate': f"{r['threat_rate']*100:.2f}%"
                })
        
        print(f"\n✓ 结果已保存到: {output_file}")


def example3_custom_usage():
    """示例3：自定义使用 - 获取详细威胁信息"""
    print("\n" + "="*60)
    print("示例3：获取详细威胁信息")
    print("="*60)
    
    result = analyze_game_threats("730", "Counter-Strike 2", max_reviews=30)
    
    if result:
        # 自定义处理返回结果
        print(f"\n游戏: {result['title']}")
        print(f"威胁等级评估:")
        
        threat_rate = result['threat_rate']
        if threat_rate > 0.3:
            level = "高危"
        elif threat_rate > 0.1:
            level = "中危"
        else:
            level = "低危"
        
        print(f"  等级: {level} ({threat_rate*100:.2f}%)")
        print(f"  总威胁数: {sum(result['threat_stats'].values())}")
        
        # 输出威胁详情
        if result['details']:
            print(f"\n威胁详情:")
            for detail in result['details']:
                print(f"\n  评论#{detail['index']} (第{detail['page']}页)")
                print(f"  内容: {detail['content']}")
                threats = detail['threats']
                if threats['links']:
                    print(f"  ⚠ 包含{threats['links']}个外部链接")
                if threats['keywords']:
                    print(f"  ⚠ 包含{threats['keywords']}个可疑关键词")
                if threats['contacts']:
                    print(f"  ⚠ 包含{threats['contacts']}个联系方式")


def main():
    """主菜单"""
    print("评论威胁分析模块 - 使用示例")
    print("="*60)
    print("1. 分析单款游戏")
    print("2. 批量分析 (从CSV)")
    print("3. 自定义分析")
    print("4. 运行所有示例")
    
    choice = input("\n请选择示例 (1-4, 默认1): ").strip() or '1'
    
    if choice == '1':
        example1_single_game()
    elif choice == '2':
        example2_batch_from_csv()
    elif choice == '3':
        example3_custom_usage()
    elif choice == '4':
        example1_single_game()
        time.sleep(3)
        example2_batch_from_csv()
        time.sleep(3)
        example3_custom_usage()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
