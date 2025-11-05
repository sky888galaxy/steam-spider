import csv
#简单处理
#给清理后的数据挨个加上排名以及折扣率
def primary_process(input_file):
    output_file = "data/analysis_use.csv"
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
                discount = '100'
            else:
                discount = str(round((float(row[3])/float(row[4])),3)*100)
            newrow = row + [rank,discount]
            writer.writerow(newrow)

# 测试用1
if __name__ == '__main__':
    primary_process('steam_topsellers_simple_cleaned.csv')