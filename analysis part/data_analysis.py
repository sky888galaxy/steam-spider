import pandas as pd
import matplotlib.pyplot as mpl


mpl.rcParams["font.family"] = ["SimHei"]
#免费游戏里热度排行图
def show_free_rank(input_file,ax):
    dataf = pd.read_csv(input_file)
    free_top = dataf[dataf["current_price"] == 0]
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
    tag_rank = dataf[dataf['tags'].isin(list(tag))]
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
    ax.bar(list(tag_rank['title']),ranks,width=0.4,color='#CEEA66')
    ax.set_title(f"含有{showtag}标签的游戏热度排行图")
    ax.tick_params(axis='x',rotation=21.1, labelsize=10)
    ax.set_yticks([])
    ax.set_xlabel("游戏名")
    ax.set_ylabel("热度")

def show_pictures(input_file,tag):
    fig, axes = mpl.subplots(1, 2,figsize=(14,6))
    show_free_rank(input_file,axes[0])
    show_tag_rank(input_file, tag,axes[1])
    mpl.tight_layout()
    mpl.show()
#测试用的
if __name__ == '__main__':
    show_pictures('primary_cleaned.csv',['FPS'])