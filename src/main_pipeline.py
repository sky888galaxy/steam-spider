#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(BASE_DIR / "src"))

from steam_data_extractor import (
    fetch_search_page,
    parse_search_html,
    get_price_from_api,
    get_tags_from_app_page,
    merge_tags,
    price_fallback_from_text,
    save_csv
)
from clean.data_cleaner import clean_data
from comments.simple_steam_crawler_easy import analyze_game_threats


class SteamAnalysisPipeline:

    def __init__(self):
        self.raw_csv = DATA_DIR / "steam_topsellers_simple.csv"
        self.cleaned_csv = DATA_DIR / "steam_topsellers_simple_cleaned.csv"
        self.comment_analysis_csv = DATA_DIR / "comment_analysis_results.csv"
        self.suspicious_reviews_csv = DATA_DIR / "suspicious_reviews_details.csv"
        self.games_data = []

    def step1_extract_games(self, pages=1):
        print("\n" + "=" * 60)
        print("【步骤 1/4】抓取Steam游戏数据")
        print("=" * 60)
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
                "tags": "",
                "release_date": it.get("released", ""),
                "review_score": "",
                "developer": ""
            }
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
        save_csv(out, str(self.raw_csv))
        self.games_data = out
        print(f"\n✓ 完成：保存 {len(out)} 条游戏数据到 {self.raw_csv.name}")
        return out

    def step2_clean_data(self):
        print("\n" + "=" * 60)
        print("【步骤 2/4】清洗数据")
        print("=" * 60)
        import clean.data_cleaner as cleaner
        original_input = getattr(cleaner, "INPUT_FILE", None)
        original_output = getattr(cleaner, "OUTPUT_FILE", None)
        cleaner.INPUT_FILE = str(self.raw_csv)
        cleaner.OUTPUT_FILE = str(self.cleaned_csv)
        try:
            clean_data()
            print(f"\n✓ 完成：清洗后数据保存到 {self.cleaned_csv.name}")
        finally:
            if original_input is not None:
                cleaner.INPUT_FILE = original_input
            if original_output is not None:
                cleaner.OUTPUT_FILE = original_output

    def step3_analyze_comments(self, max_games=5, max_reviews_per_game=20):
        print("\n" + "=" * 60)
        print(f"【步骤 3/4】分析游戏评论威胁（前{max_games}款游戏）")
        print("=" * 60)
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
                      f"({result['threat_rate'] * 100:.1f}%)")
            else:
                print(f"  ✗ 无法获取评论")
            time.sleep(2)
        if results:
            with open(self.comment_analysis_csv, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['appid', 'title', 'total_reviews', 'suspicious_reviews',
                              'threat_rate', 'links', 'keywords', 'contacts', 'avg_helpful',
                              'chinese_reviews', 'english_reviews']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in results:
                    writer.writerow({
                        'appid': r['appid'],
                        'title': r['title'],
                        'total_reviews': r['total_reviews'],
                        'suspicious_reviews': r['suspicious_reviews'],
                        'threat_rate': f"{r['threat_rate'] * 100:.2f}%",
                        'links': r['threat_stats']['links'],
                        'keywords': r['threat_stats']['keywords'],
                        'contacts': r['threat_stats']['contacts'],
                        'avg_helpful': f"{r.get('avg_helpful', 0):.1f}",
                        'chinese_reviews': r.get('language_stats', {}).get('chinese', 0),
                        'english_reviews': r.get('language_stats', {}).get('english', 0)
                    })
            print(f"\n✓ 完成：评论分析结果保存到 {self.comment_analysis_csv.name}")
            suspicious_details = []
            for r in results:
                if 'details' in r and r['details']:
                    for detail in r['details']:
                        suspicious_details.append({
                            'appid': r['appid'],
                            'game_title': r['title'],
                            'review_index': detail['index'],
                            'review_content': detail['content'],
                            'page': detail['page'],
                            'helpful': detail['helpful'],
                            'language': detail['language'],
                            'has_links': '是' if detail['threats']['links'] > 0 else '否',
                            'has_keywords': '是' if detail['threats']['keywords'] > 0 else '否',
                            'has_contacts': '是' if detail['threats']['contacts'] > 0 else '否',
                            'link_count': detail['threats']['links'],
                            'keyword_count': detail['threats']['keywords'],
                            'contact_count': detail['threats']['contacts']
                        })
            if suspicious_details:
                with open(self.suspicious_reviews_csv, 'w', newline='', encoding='utf-8-sig') as f:
                    fieldnames = ['appid', 'game_title', 'review_index', 'review_content', 'page',
                                  'helpful', 'language', 'has_links', 'has_keywords', 'has_contacts',
                                  'link_count', 'keyword_count', 'contact_count']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(suspicious_details)
                print(f"✓ 完成：可疑评论详情保存到 {self.suspicious_reviews_csv.name}")
                print(f"  共记录 {len(suspicious_details)} 条可疑评论")
        return results

    def step4_visualize_analysis(self, show_plots=True):
        print("\n" + "=" * 60)
        print("【步骤 4/4】数据分析与可视化")
        print("=" * 60)
        if not show_plots:
            print(f"✓ 完成：跳过图表显示")
            return
        analysis_dir = BASE_DIR / "src" / "analysis part"
        if str(analysis_dir) not in sys.path:
            sys.path.insert(0, str(analysis_dir))
        try:
            from data_analysis import run_analysis
            run_analysis(str(self.cleaned_csv))
            print(f"\n✓ 完成：数据分析与可视化")
        except Exception as e:
            print(f"⚠ 可视化出错: {e}")
            import traceback
            traceback.print_exc()

    def run_full_pipeline(self, pages=3, max_comment_games=15, max_reviews=50, show_plots=True):
        print("\n" + "=" * 70)
        print("🎮 我超想你steam spider 🕷️")
        print("=" * 70)
        print(f"配置:")
        print(f"  - 抓取页数: {pages}")
        print(f"  - 评论分析游戏数: {max_comment_games}")
        print(f"  - 每款游戏评论数: {max_reviews}")
        print(f"  - 显示图表: {'是' if show_plots else '否'}")
        print("=" * 70)
        start_time = time.time()
        try:
            games = self.step1_extract_games(pages=pages)
            self.step2_clean_data()
            comment_results = self.step3_analyze_comments(
                max_games=max_comment_games,
                max_reviews_per_game=max_reviews
            )
            self.step4_visualize_analysis(show_plots=show_plots)
            elapsed = time.time() - start_time
            print("\n" + "=" * 70)
            print("流水线执行完成！")
            print("=" * 70)
            print(f"总耗时: {elapsed:.1f}秒")
            print(f"游戏数据: {len(games)} 条")
            print(f"评论分析: {len(comment_results)} 款游戏")
            print(f"\n生成文件:")
            print(f"  - {self.raw_csv}")
            print(f"  - {self.cleaned_csv}")
            print(f"  - {self.comment_analysis_csv}")
            if self.suspicious_reviews_csv.exists():
                print(f"  - {self.suspicious_reviews_csv}")
            print("=" * 70)
            print("\n🎉 我超想你steam spider 运行完成！🎉")
            print("=" * 70)
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
    import argparse
    parser = argparse.ArgumentParser(description='Steam数据分析流水线')
    parser.add_argument('--pages', type=int, default=3, help='抓取页数 (默认3)')
    parser.add_argument('--games', type=int, default=15, help='评论分析游戏数 (默认15)')
    parser.add_argument('--reviews', type=int, default=50, help='每款游戏评论数 (默认50)')
    parser.add_argument('--no-plots', action='store_true', help='不显示图表')
    parser.add_argument('--step', type=str, choices=['1', '2', '3', '4', 'all'],
                        default='all', help='执行特定步骤 (1-4) 或全部 (all)')
    args = parser.parse_args()
    pipeline = SteamAnalysisPipeline()
    if args.step == 'all':
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
