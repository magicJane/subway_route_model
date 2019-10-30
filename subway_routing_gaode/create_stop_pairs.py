# -*- coding:utf-8 -*-
import time
import sys
import codecs
import os
import io
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')  # vscode显示中文输出


input_path = 'subway_stop_names.csv'
output_path = 'stop_pairs.txt'
    
def main():
    startTime = time.time()  # 返回当前的Unix 时间戳，单位秒

    stops = []
    with codecs.open(input_path, 'r', 'utf-8') as f:
        for line in f:
            stops.append(line.strip())

    stop_pairs = []
    for start in stops:
        for end in stops:
        #     var points = [{ keyword: '珠光（地铁站）',city:'深圳' },{ keyword: '购物公园（地铁站）',city:'深圳' }]
            if (start != end):
                stop_pairs.append("[{ keyword: '%s（地铁站）',city:'深圳' },{ keyword: '%s（地铁站）',city:'深圳' }]"%(start, end))
    
    with codecs.open(output_path, 'w', 'utf-8') as f:
        f.write("[%s]"%",".join(stop_pairs))


    endTime = time.time()
    print("Complete in %.5f minutes." % ((endTime - startTime)/60.0))


if __name__ == '__main__':
    main()