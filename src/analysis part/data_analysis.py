
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
import sys
import io
warnings.filterwarnings('ignore')

# 强制使用UTF-8编码输出
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sns.set_style("whitegrid")
# 基础分析函数
def load_and_preprocess_data(input_file):
    """加载并预处理数据"""
    # 尝试不同的编码方式读取
    for encoding in ['utf-8-sig', 'utf-8', 'gbk', 'gb18030']:
        try:
            df = pd.read_csv(input_file, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        # 如果所有编码都失败，使用错误处理模式
        df = pd.read_csv(input_file, encoding='utf-8', errors='ignore')
    
    # 计算折扣率
    df['discount_rate'] = ((df['original_price'] - df['current_price']) / df['original_price'] * 100).fillna(0)
    # 处理发售日期
    df['released'] = pd.to_datetime(df['released'], errors='coerce')
    df['days_since_release'] = (datetime.now() - df['released']).dt.days
    # 处理标签
    df['tag_count'] = df['tags'].str.count(',') + 1
    df['tag_count'] = df['tag_count'].fillna(0)
    return df

#免费游戏里热度排行图
def show_free_rank(input_file, ax):
    df = load_and_preprocess_data(input_file)
    free_games = df[df["current_price"] == 0.0].head(10)
    if len(free_games) == 0:
        ax.text(0.5, 0.5, '没有免费游戏数据', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 使用索引作为排名（越小排名越高）
    ranks = range(1, len(free_games) + 1)
    bars = ax.bar(range(len(free_games)), ranks, color='#4DAF4A', alpha=0.7)
    ax.set_title("免费游戏热度排行图")
    ax.set_xticks(range(len(free_games)))
    ax.set_xticklabels(free_games["title"], rotation=20, ha='right')
    ax.set_ylabel("排名")
    ax.invert_yaxis()  # 反转y轴，让排名1在顶部
    
    # 添加数值标签
    for i, bar in enumerate(bars):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, 
                f'{ranks[i]}', ha='center', va='center')

#输入一个标签,该标签里热度排行图
def show_tag_rank(input_file, tag, ax):
    df = load_and_preprocess_data(input_file)
    pattern = '|'.join(tag)
    tag_games = df[df['tags'].str.contains(pattern, regex=True, na=False)].head(10)
    
    if len(tag_games) == 0:
        ax.text(0.5, 0.5, f'没有包含{tag}标签的游戏', ha='center', va='center', transform=ax.transAxes)
        return
    
    ranks = range(1, len(tag_games) + 1)
    showtag = ','.join(tag[:3]) + ('...' if len(tag) > 3 else '')
    
    bars = ax.bar(range(len(tag_games)), ranks, color='#CEEA66', alpha=0.7)
    ax.set_title(f"含有{showtag}标签的游戏排行图")
    ax.set_xticks(range(len(tag_games)))
    ax.set_xticklabels(tag_games["title"], rotation=45, ha='right')
    ax.set_ylabel("排名")
    ax.invert_yaxis()

#折扣力度榜
def show_discount_rank(input_file, ax):
    df = load_and_preprocess_data(input_file)
    # 只显示有折扣的游戏
    discounted = df[df['discount_rate'] > 0].nlargest(10, 'discount_rate')
    
    if len(discounted) == 0:
        ax.text(0.5, 0.5, '没有折扣游戏数据', ha='center', va='center', transform=ax.transAxes)
        return
    
    bars = ax.barh(range(len(discounted)), discounted['discount_rate'], 
                   color='#FF6B6B', alpha=0.7)
    ax.set_title("游戏折扣力度排行榜")
    ax.set_yticks(range(len(discounted)))
    ax.set_yticklabels(discounted['title'])
    ax.set_xlabel("折扣率 (%)")
    
    # 添加数值标签
    for i, bar in enumerate(bars):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                f'{discounted.iloc[i]["discount_rate"]:.1f}%', 
                ha='left', va='center')

# 创新性深度分析函数

def analyze_discount_vs_release_time(input_file, ax):
    """分析折扣深度与发售时长的关系"""
    df = load_and_preprocess_data(input_file)
    # 过滤有效数据
    valid_data = df[(df['discount_rate'] > 0) & (df['days_since_release'] > 0)].copy()
    
    if len(valid_data) == 0:
        ax.text(0.5, 0.5, '没有足够的折扣数据', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 创建散点图
    scatter = ax.scatter(valid_data['days_since_release'], valid_data['discount_rate'], 
                        c=valid_data['current_price'], cmap='viridis', alpha=0.7, s=60)
    
    # 添加趋势线
    if len(valid_data) >= 2:
        z = np.polyfit(valid_data['days_since_release'], valid_data['discount_rate'], 1)
        p = np.poly1d(z)
        ax.plot(valid_data['days_since_release'], p(valid_data['days_since_release']), 
                "r--", alpha=0.8, linewidth=2)
    
    ax.set_title("折扣深度 vs 发售时长分析")
    ax.set_xlabel("发售天数")
    ax.set_ylabel("折扣率 (%)")
    
    # 添加颜色条
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('当前价格 (¥)')

def analyze_free_vs_paid_characteristics(input_file, ax):
    """分析免费游戏与付费游戏的特征差异"""
    df = load_and_preprocess_data(input_file)
    
    # 分离免费和付费游戏
    free_games = df[df['current_price'] == 0]
    paid_games = df[df['current_price'] > 0]
    
    if len(free_games) == 0 or len(paid_games) == 0:
        ax.text(0.5, 0.5, '数据不足，无法比较', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 比较标签数量
    free_avg_tags = free_games['tag_count'].mean()
    paid_avg_tags = paid_games['tag_count'].mean()
    
    # 获取最热门标签
    free_top_tags = free_games['tags'].str.split(', ').explode().value_counts().head(3)
    paid_top_tags = paid_games['tags'].str.split(', ').explode().value_counts().head(3)
    
    # 创建对比图
    categories = ['平均标签数', '游戏数量']
    free_values = [free_avg_tags, len(free_games)]
    paid_values = [paid_avg_tags, len(paid_games)]
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, free_values, width, label='免费游戏', color='#4CAF50', alpha=0.7)
    bars2 = ax.bar(x + width/2, paid_values, width, label='付费游戏', color='#2196F3', alpha=0.7)
    
    ax.set_title('免费游戏 vs 付费游戏特征对比')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    
    # 添加数值标签
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom')

def analyze_discount_effectiveness(input_file, ax):
    """分析折扣效果：哪些价位的游戏更容易打折"""
    df = load_and_preprocess_data(input_file)
    paid_games = df[df['current_price'] > 0].copy()
    
    if len(paid_games) == 0:
        ax.text(0.5, 0.5, '没有付费游戏数据', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 按原价分组
    price_ranges = [(0, 20, '低价位\n(≤¥20)'), 
                   (20, 50, '中价位\n(¥20-50)'), 
                   (50, float('inf'), '高价位\n(>¥50)')]
    
    discount_data = []
    range_labels = []
    
    for min_price, max_price, label in price_ranges:
        if max_price == float('inf'):
            range_games = paid_games[paid_games['original_price'] >= min_price]
        else:
            range_games = paid_games[(paid_games['original_price'] >= min_price) & 
                                   (paid_games['original_price'] < max_price)]
        
        if len(range_games) > 0:
            # 计算该价位区间有折扣的游戏比例
            discounted_ratio = len(range_games[range_games['discount_rate'] > 0]) / len(range_games) * 100
            discount_data.append(discounted_ratio)
            range_labels.append(label)
    
    if not discount_data:
        ax.text(0.5, 0.5, '没有足够的数据', ha='center', va='center', transform=ax.transAxes)
        return
    
    bars = ax.bar(range_labels, discount_data, color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.7)
    ax.set_title('不同价位游戏的折扣频率')
    ax.set_ylabel('有折扣游戏比例 (%)')
    ax.set_ylim(0, 100)
    
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 2,
               f'{height:.1f}%', ha='center', va='bottom')

def analyze_genre_popularity_trend(input_file, ax):
    """分析游戏类型流行度趋势（基于发售年份）"""
    df = load_and_preprocess_data(input_file)
    
    # 提取年份
    df['release_year'] = df['released'].dt.year
    valid_data = df.dropna(subset=['release_year', 'tags'])
    
    if len(valid_data) == 0:
        ax.text(0.5, 0.5, '没有足够的时间数据', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 选择主要游戏类型
    main_genres = ['Action', 'RPG', 'Strategy', 'Shooter', 'Adventure']
    
    # 按年份统计各类型游戏数量
    year_genre_data = {}
    years = sorted(valid_data['release_year'].unique())
    
    for genre in main_genres:
        genre_counts = []
        for year in years:
            year_games = valid_data[valid_data['release_year'] == year]
            genre_count = len(year_games[year_games['tags'].str.contains(genre, na=False, case=False)])
            genre_counts.append(genre_count)
        year_genre_data[genre] = genre_counts
    
    # 绘制趋势线
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    for i, (genre, counts) in enumerate(year_genre_data.items()):
        if sum(counts) > 0:  # 只显示有数据的类型
            ax.plot(years, counts, marker='o', linewidth=2, 
                   label=genre, color=colors[i % len(colors)])
    
    ax.set_title('游戏类型发展趋势')
    ax.set_xlabel('发售年份')
    ax.set_ylabel('游戏数量')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)

def analyze_tag_discount_pattern(input_file, ax):
    """分析不同标签类型的折扣模式"""
    df = load_and_preprocess_data(input_file)
    
    # 定义主要游戏类型
    main_tags = ['Action', 'RPG', 'Strategy', 'Simulation', 'Adventure', 'Indie', 'FPS']
    tag_discounts = {}
    
    for tag in main_tags:
        tag_games = df[df['tags'].str.contains(tag, na=False, case=False)]
        if len(tag_games) > 0:
            avg_discount = tag_games['discount_rate'].mean()
            tag_discounts[tag] = avg_discount
    
    if not tag_discounts:
        ax.text(0.5, 0.5, '没有足够的标签数据', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 创建条形图
    tags = list(tag_discounts.keys())
    discounts = list(tag_discounts.values())
    
    bars = ax.bar(range(len(tags)), discounts, 
                  color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'])
    ax.set_title("不同游戏类型的平均折扣率")
    ax.set_xticks(range(len(tags)))
    ax.set_xticklabels(tags, rotation=20, ha='right')
    ax.set_ylabel("平均折扣率 (%)")
    
    # 添加数值标签
    for i, bar in enumerate(bars):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{discounts[i]:.1f}%', ha='center', va='bottom')

def analyze_price_distribution_by_category(input_file, ax):
    """分析不同价格区间的游戏分布（更有意义的价格分析）"""
    df = load_and_preprocess_data(input_file)
    paid_games = df[df['current_price'] > 0].copy()
    
    if len(paid_games) == 0:
        ax.text(0.5, 0.5, '没有付费游戏数据', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 定义价格区间
    price_bins = [0, 10, 30, 60, 100, float('inf')]
    price_labels = ['低价\n(≤¥10)', '中低价\n(¥10-30)', '中价\n(¥30-60)', '高价\n(¥60-100)', '超高价\n(>¥100)']
    
    # 计算每个价格区间的游戏数量
    paid_games['price_category'] = pd.cut(paid_games['current_price'], 
                                         bins=price_bins, labels=price_labels, right=False)
    price_counts = paid_games['price_category'].value_counts()
    
    # 创建饼图显示价格分布
    colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC']
    wedges, texts, autotexts = ax.pie(price_counts.values, labels=price_counts.index, 
                                     colors=colors, autopct='%1.1f%%', startangle=90)
    
    ax.set_title("付费游戏价格区间分布")
    
    # 美化文本
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')

def show_comprehensive_analysis(input_file):
    """显示综合分析结果"""
    plt.rcParams['font.family'] = ["SimHei","DejaVu Sans", "STIXGeneral"]
    plt.rcParams['axes.unicode_minus'] = False
    fig = plt.figure(figsize=(16, 12))
    
    # 创建网格布局
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 基础分析
    ax1 = fig.add_subplot(gs[2, 0])
    show_free_rank(input_file, ax1)
    
    ax2 = fig.add_subplot(gs[2, 1])
    show_tag_rank(input_file, ["Action"], ax2)
    
    ax3 = fig.add_subplot(gs[1, 2])
    show_discount_rank(input_file, ax3)
    
    # 深度分析 - 使用新的更有意义的分析
    ax4 = fig.add_subplot(gs[1, 0])
    analyze_discount_vs_release_time(input_file, ax4)
    
    ax5 = fig.add_subplot(gs[1, 1])
    analyze_price_distribution_by_category(input_file, ax5)
    