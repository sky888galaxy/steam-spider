import pandas as pd
import matplotlib.pyplot as mpl
import re


mpl.rcParams["font.family"] = ["SimHei"]
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
    pattern = '|'.join(tag)
    tag_rank = dataf[dataf['tags'].str.contains(pattern,regex=True)]
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
    ax.bar(tag_rank["title"],ranks,width=0.4,color='#CEEA66')
    ax.set_title(f"含有{showtag}标签的游戏热度排行图")
    ax.tick_params(axis='x',rotation=21.1, labelsize=10)
    ax.set_yticks([])
    ax.set_xlabel("游戏名")
    ax.set_ylabel("热度")
#折扣力度榜
def show_discount_rank(input_file,ax):
    dataf = pd.read_csv(input_file)
    discounts = list(dataf['discounts'])[::-1]
    #ranks = list(dataf['rank'])[::-1]
    #processed_title= list(dataf['title'])
    ax.barh(list(dataf['title']),discounts , height=0.4, color='#4DAF4A',edgecolor='black')
    ax.set_title("折扣力度游戏榜")
    ax.tick_params(axis='y', rotation=21.1, labelsize=10)
    ax.set_xlabel("游戏名")
    ax.set_ylabel("折扣力度")

def show_pictures(input_file,tag):
    fig, axes = mpl.subplots(2, 2,figsize=(14,6))
    show_free_rank(input_file,axes[0,0])
    show_tag_rank(input_file, tag,axes[0,1])
    show_discount_rank(input_file,axes[1,0])
    mpl.tight_layout()
    mpl.show()
#测试用的
if __name__ == '__main__':
    show_pictures('data/analysis_use.csv',["Action"])