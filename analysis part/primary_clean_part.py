import csv
#简单处理
#给爬虫的数据挨个加上排名以及折扣率,以及把没有数据的位置填上null,到时候分析的时候不会选用这些带null的数据
def primary_clean(input_file):
    output_file = "primary_cleaned.csv"
    with open(input_file, 'r') as uncleaned, \
            open(output_file, 'w') as cleaned:
        reader = csv.reader(uncleaned)
        writer = csv.writer(cleaned)
        newtitle = [h for h in next(reader)]+['rank','discounts']
        writer.writerow(newtitle)
        for i,row in enumerate(reader,start=1):
            rank = str(i)
            #是否是免费游戏，不然除数不能为0
            if row[4] == str(0):
                discount = 1
            else:
                discount = str(float(row[3])/float(row[4]))
            cleaned_row = ['null' if item.strip() == '' else item for item in row]
            newrow = cleaned_row + [rank,discount]
            writer.writerow(newrow)

# 测试用
# if __name__ == '__main__':
#     primary_clean('1.csv')