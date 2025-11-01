#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam数据分析主流程控制器
功能：编排数据抓取→清洗→评论分析→数据分析的完整流程
"""

import os
import sys
import time
import csv
from pathlib import Path

# 添加路径以便导入模块
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(BASE_DIR / "src"))

# 导入各模块
from steam_data_extractor import fetch_search_page, parse_search_html, get_price_from_api, get_tags_from_app_page, merge_tags, price_fallback_from_text, save_csv
from clean.data_cleaner import clean_data
from comments.simple_steam_crawler_easy import analyze_game_threats, print_analysis_result


class SteamAnalysisPipeline:
    """Steam数据分析流水线"""
    
    def __init__(self):
        self.raw_csv = DATA_DIR / "steam_topsellers_simple.csv"
        self.cleaned_csv = DATA_DIR / "steam_topsellers_simple_cleaned.csv"
        self.comment_analysis_csv = DATA_DIR / "comment_analysis_results.csv"
        self.games_data = []  # 存储游戏数据，用于传递参数
        
    def step1_extract_games(self, pages=1):
        """步骤1: 抓取Steam游戏数据"""
        print("\n" + "="*60)
        print("【步骤 1/4】抓取Steam游戏数据")
        print("="*60)
        
        all_items = []
        for p in range(1, pages + 1):
            print(f"抓取搜索页 page {p} ...")
            html = fetch_search_page(page=p, filter_name="topsellers")
            items = parse_search_html(html)
            all_items.extend(items)
            time.sleep(1.0)
        
        out = []
        for i, it in enumerate(all_items, 1):
            appid = it.get("appid", "")
            title = it.get("title", "")
            print(f"[{i}/{len(all_items)}] {title[:50]}  (appid={appid})")
            
            record = {
                "appid": appid,
                "title": title,
                "released": it.get("released", ""),
                "current_price": "",
                "original_price": "",
                "tags": ""
            }
            
            # 获取价格和标签
            if appid:
                price_info = get_price_from_api(appid, cc="US", lang="en")
                if price_info and price_info.get("final") is not None:
                    record["current_price"] = str(price_info.get("final"))
                    record["original_price"] = str(price_info.get("initial")) if price_info.get("initial") is not None else ""
                else:
                    cur, orig = price_fallback_from_text(it.get("price_text", ""))
                    record["current_price"] = cur
                    record["original_price"] = orig
                
                tags_page = get_tags_from_app_page(appid)
                merged = merge_tags(it.get("tags_text", ""), tags_page)
                record["tags"] = merged
            else:
                cur, orig = price_fallback_from_text(it.get("price_text", ""))
                record["current_price"] = cur
                record["original_price"] = orig
                record["tags"] = it.get("tags_text", "")
            
            out.append(record)
            time.sleep(1.0)
        
        # 保存原始数据
        save_csv(out, str(self.raw_csv))
        self.games_data = out
        
        print(f"\n✓ 完成：保存 {len(out)} 条游戏数据到 {self.raw_csv.name}")
        return out
    
    def step2_clean_data(self):
        """步骤2: 清洗数据"""
        print("\n" + "="*60)
        print("【步骤 2/4】清洗数据")
        print("="*60)
        
        # 调用清洗模块（修改其内部路径为使用实例变量）
        import clean.data_cleaner as cleaner
        original_input = cleaner.INPUT_FILE
        original_output = cleaner.OUTPUT_FILE
        
        # 临时修改路径
        cleaner.INPUT_FILE = str(self.raw_csv)
        cleaner.OUTPUT_FILE = str(self.cleaned_csv)
        
        try:
            clean_data()
            print(f"\n✓ 完成：清洗后数据保存到 {self.cleaned_csv.name}")
        finally:
            # 恢复原路径
            cleaner.INPUT_FILE = original_input
            cleaner.OUTPUT_FILE = original_output
    
    def step3_analyze_comments(self, max_games=5, max_reviews_per_game=20):
        """步骤3: 分析评论威胁（批量）"""
        print("\n" + "="*60)
        print(f"【步骤 3/4】分析游戏评论威胁（前{max_games}款游戏）")
        print("="*60)
        
        # 读取清洗后的数据
        try:
            with open(self.cleaned_csv, 'r', encoding='utf-8-sig') as f:
                games = list(csv.DictReader(f))[:max_games]
        except FileNotFoundError:
            print(f"错误：找不到清洗后的文件 {self.cleaned_csv}")
            return []
        
        results = []
        for i, game in enumerate(games, 1):
            app_id = game.get('appid', '').strip()
            title = game.get('title', '').strip()
            
            if not app_id or not title:
                continue
            
            print(f"\n[{i}/{len(games)}] 正在分析: {title}")
            result = analyze_game_threats(app_id, title, max_reviews_per_game)
            
            if result:
                results.append(result)
                print(f"  ✓ 完成: 分析{result['total_reviews']}条评论, "
                      f"发现{result['suspicious_reviews']}条可疑 "
                      f"({result['threat_rate']*100:.1f}%)")
            else:
                print(f"  ✗ 无法获取评论")
            
            time.sleep(2)  # 避免请求过快
        
        # 保存结果
        if results:
            with open(self.comment_analysis_csv, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['appid', 'title', 'total_reviews', 'suspicious_reviews',
                             'threat_rate', 'links', 'keywords', 'contacts']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for r in results:
                    writer.writerow({
                        'appid': r['appid'],
                        'title': r['title'],
                        'total_reviews': r['total_reviews'],
                        'suspicious_reviews': r['suspicious_reviews'],
                        'threat_rate': f"{r['threat_rate']*100:.2f}%",
                        'links': r['threat_stats']['links'],
                        'keywords': r['threat_stats']['keywords'],
                        'contacts': r['threat_stats']['contacts']
                    })
            
            print(f"\n✓ 完成：评论分析结果保存到 {self.comment_analysis_csv.name}")
        
        return results
    
    def step4_visualize_analysis(self, show_plots=True):
        """步骤4: 数据分析与可视化"""
        print("\n" + "="*60)
        print("【步骤 4/4】数据分析与可视化")
        print("="*60)
        
        # 使用sys.path添加analysis part路径
        analysis_dir = BASE_DIR / "src" / "analysis part"
        if str(analysis_dir) not in sys.path:
            sys.path.insert(0, str(analysis_dir))
        
        import data_analysis
        from data_analysis import primary_process, show_pictures
        
        # 生成分析用数据（添加rank和discount列）
        analysis_file_path = BASE_DIR / "src" / "analysis_part" / "analysis_use.csv"
        print(f"生成分析用数据文件...")
        primary_process(str(self.cleaned_csv))
        
        if show_plots:
            print(f"生成可视化图表...")
            try:
                show_pictures(str(analysis_file_path), ["Action", "Adventure"])
                print(f"✓ 完成：图表已显示")
            except Exception as e:
                print(f"⚠ 可视化出错: {e}")
        else:
            print(f"✓ 完成：分析数据已生成（跳过图表显示）")
    
    def run_full_pipeline(self, pages=1, max_comment_games=5, max_reviews=20, show_plots=True):
        """运行完整流水线"""
        print("\n" + "="*70)
        print("Steam数据分析完整流水线")
        print("="*70)
        print(f"配置:")
        print(f"  - 抓取页数: {pages}")
        print(f"  - 评论分析游戏数: {max_comment_games}")
        print(f"  - 每款游戏评论数: {max_reviews}")
        print(f"  - 显示图表: {'是' if show_plots else '否'}")
        print("="*70)
        
        start_time = time.time()
        
        try:
            # 步骤1: 抓取游戏数据
            games = self.step1_extract_games(pages=pages)
            
            # 步骤2: 清洗数据
            self.step2_clean_data()
            
            # 步骤3: 分析评论
            comment_results = self.step3_analyze_comments(
                max_games=max_comment_games,
                max_reviews_per_game=max_reviews
            )
            
            # 步骤4: 数据分析与可视化
            self.step4_visualize_analysis(show_plots=show_plots)
            
            # 总结
            elapsed = time.time() - start_time
            print("\n" + "="*70)
            print("流水线执行完成！")
            print("="*70)
            print(f"总耗时: {elapsed:.1f}秒")
            print(f"游戏数据: {len(games)} 条")
            print(f"评论分析: {len(comment_results)} 款游戏")
            print(f"\n生成文件:")
            print(f"  - {self.raw_csv}")
            print(f"  - {self.cleaned_csv}")
            print(f"  - {self.comment_analysis_csv}")
            print("="*70)
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n用户中断执行")
            return False
        except Exception as e:
            print(f"\n\n错误: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数：直接运行完整流水线（可通过命令行参数配置）"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Steam数据分析流水线')
    parser.add_argument('--pages', type=int, default=1, help='抓取页数 (默认1)')
    parser.add_argument('--games', type=int, default=5, help='评论分析游戏数 (默认5)')
    parser.add_argument('--reviews', type=int, default=20, help='每款游戏评论数 (默认20)')
    parser.add_argument('--no-plots', action='store_true', help='不显示图表')
    parser.add_argument('--step', type=str, choices=['1', '2', '3', '4', 'all'], 
                       default='all', help='执行特定步骤 (1-4) 或全部 (all)')
    
    args = parser.parse_args()
    
    pipeline = SteamAnalysisPipeline()
    
    if args.step == 'all':
        # 运行完整流水线
        pipeline.run_full_pipeline(
            pages=args.pages,
            max_comment_games=args.games,
            max_reviews=args.reviews,
            show_plots=not args.no_plots
        )
    elif args.step == '1':
        pipeline.step1_extract_games(args.pages)
    elif args.step == '2':
        pipeline.step2_clean_data()
    elif args.step == '3':
        pipeline.step3_analyze_comments(args.games, args.reviews)
    elif args.step == '4':
        pipeline.step4_visualize_analysis(not args.no_plots)


if __name__ == "__main__":
    main()
