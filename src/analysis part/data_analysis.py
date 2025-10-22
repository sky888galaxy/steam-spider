import numpy as np
import pandas as pd
import matplotlib.pyplot as mpl
import re


mpl.rcParams["font.family"] = ["Microsoft YaHei"]
#免费游戏里热度排行图
def show_free_rank(input_file,ax):
    dataf = pd.read_csv(input_file)
    free_top = dataf[dataf["current_price"] == 0.0]
    ranks = free_top['rank']
    ranks = list(ranks)[::-1]
    ax.bar(list(free_top["title"]),ranks,width=0.4,color='#4DAF4A')
    ax.set_title("免费游戏热度排行图")
    ax.tick_params(axis='x',rotation=21.1,labelsize=10)
    ax.set_yticks([])
    ax.set_xlabel("游戏名")
    ax.set_ylabel("热度")

#输入一个标签,该标签里热度排行图
def show_tag_rank(input_file,tag,ax):
    dataf = pd.read_csv(input_file)
    #忽略没有标签/没有爬到标签的数据
    qualified_game = (dataf[dataf['tags'] != np.nan]).fillna('None')
    pattern = '|'.join(tag)
    tag_rank = qualified_game[qualified_game['tags'].str.contains(pattern,regex=True)]
    ranks = list(tag_rank['rank'])[::-1]
    showtag = ''
    #标签大于5个时后面的不显示了
    for i,gt in enumerate(tag):
        if(i==0):
            showtag = gt
        elif(i<5):
            showtag = showtag + ',' + gt
        else:
            showtag = showtag + '...'
            break
    ax.barh(tag_rank["title"],ranks,height=0.4,color='#CEEA66',edgecolor='#CEEA66')
    ax.set_title(f"含有{showtag}标签的游戏热度排行图")
    ax.tick_params(axis='x', labelsize=10)
    ax.set_xticks([])
    ax.set_xlabel("热度")
    ax.set_ylabel("游戏名")
#折扣力度榜
def show_discount_rank(input_file,ax):
    dataf = pd.read_csv(input_file)
    #去掉本来就是免费的游戏/没有折扣的游戏
    qualified_game = dataf[dataf['discounts'] != 0.0]
    discounts = list(qualified_game['discounts'])
    ax.barh(list(qualified_game['title']),discounts, height=0.4, color='#4DAF4A',edgecolor='#4DAF4A')
    ax.set_title("折扣力度游戏榜")
    ax.tick_params(axis='y', labelsize=10)
    ax.set_xlabel("折扣力度")
    ax.set_ylabel("游戏名")

def show_pictures(input_file,tag):
    fig, axes = mpl.subplots(2, 2,figsize=(14,10))
    show_free_rank(input_file,axes[0,1])
    show_tag_rank(input_file, tag,axes[0,0])
    show_discount_rank(input_file,axes[1,0])
    mpl.tight_layout()
    mpl.show()

import csv
#简单处理
#给清理后的数据挨个加上排名以及折扣率
def primary_process(input_file):
    output_file = "analysis_use.csv"
    with open(input_file, 'r',encoding="utf-8") as uncleaned, \
            open(output_file, 'w',encoding="utf-8") as cleaned:
        reader = csv.reader(uncleaned)
        writer = csv.writer(cleaned)
        newtitle = [h for h in next(reader)]+['rank','discounts']
        writer.writerow(newtitle)
        for i,row in enumerate(reader,start=1):
            rank = str(i)
            #是否是免费游戏，不然除数不能为0
            if row[4] == str(0.0):
                discount = '0.0'
            else:
                discount = str(round(1-(float(row[3])/float(row[4])),3)*100)
            newrow = row + [rank,discount]
            writer.writerow(newrow)
#测试用的
if __name__ == '__main__':
    primary_process('../data/steam_topsellers_simple_cleaned.csv')
    show_pictures('analysis_use.csv',["Action"])