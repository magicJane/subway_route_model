
# -*- coding:utf-8 -*-
import time
import sys
import codecs
import os
import io
import math
import numpy as np
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')  # vscode显示中文输出

if len(sys.argv) < 4:
    print ("输入3个参数：stop, shape文件以及输出文件路径")
    exit()

# inputDir = sys.argv[1]
# outputDir = sys.argv[2]    

input_stop = sys.argv[1] #'./transit_stop.txt'
input_shape = sys.argv[2] #'./transit_shape.txt'
output_stop = sys.argv[3] #'./transit_stop_with_stopid.txt'

DIRECTION_THRESHOLD = 60
DISTANCE_THRESHOLD = 0.00030

import logging

logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %Y-%m-%d %H:%M:%S',
                filename='add_stop_id.log',
                filemode='w')


# input: 同名站点列表 (route_name, trip_name, stop_index, stop_name, lng, lat)
# 12路,12路(福田农批市场--火车站),17,地王大厦,114.109962,22.541693
# output: 带stop_id的同名站点列表 (route_name, trip_name, stop_index, stop_name, lng, lat, stop_id)
def add_stop_id(stops):
    groups = {}
    for stop in stops:
        curr_key = get_group_key(groups, stop)
        if (curr_key > 0):
            groups[curr_key].append(stop)
        else:
            groups.setdefault(len(groups) + 1, []).append(stop)
    output_stops = []
    for key in groups:
        lng, lat = get_stop_coord(groups[key])
        for stop in groups[key]:
            output_stops.append((stop[0], stop[1], stop[2], stop[3], lng, lat, "%s_S%d"%(stop[3], key))) 
    return output_stops

# 针对地铁站点，只调整坐标，stop_id同站点名
def add_stop_id_subway(stops):
    output_stops = []
    lng, lat = get_stop_coord(stops)
    for stop in stops:
        output_stops.append((stop[0], stop[1], stop[2], stop[3], lng, lat, stop[3])) 

    return output_stops



def get_stop_coord(stops):
    lngs = []
    lats = []
    for stop in stops:
        lngs.append(stop[4])
        lats.append(stop[5])
    return (np.percentile(np.array(lngs), 50), np.percentile(np.array(lats), 50))
        
def get_group_key (groups, stop):    
    for key in groups:
        match = 0
        stops_in_group = groups[key]
        for s in stops_in_group:
            if (cal_distance((stop[4], stop[5]), (s[4], s[5])) < DISTANCE_THRESHOLD and cal_angle(stop[6], s[6]) < DIRECTION_THRESHOLD):
                match += 1
        if match == len(stops_in_group):
            return key
    return -1

def cal_distance(pt1, pt2):
    return math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)

def cal_angle(dir1, dir2):
    diff = abs(dir1 - dir2)
    angle = diff if diff < 180 else 360 - diff
    return angle

def calculate_direction(coord1, coord2):
    radians = 180 / math.pi * math.atan2(coord2[0] - coord1[0], coord2[1] - coord1[1])
    if radians < 0:
        return int(radians) + 360
    else:
        return int(radians)

# shape: list of (lng, lat)
# stop: (route_name, trip_name, stop_index, stop_name, lng, lat)
def get_direction(stop, shape):
    min_distance = 0.3 * DISTANCE_THRESHOLD
    min_shape_index = -1
    for ipt in range(len(shape)):
        d = cal_distance((stop[4], stop[5]), shape[ipt])
        if (d < min_distance):
            min_distance = d
            min_shape_index = ipt
    
    if (min_shape_index >= 0):
        if min_shape_index >= (len(shape) - 3): #接近终点站，往回搜索gps点
            tocoord = shape[min_shape_index]
            isearch = 1
            fromcoord = shape[min_shape_index - isearch]
            while cal_distance(fromcoord, tocoord) < 0.3*DISTANCE_THRESHOLD:
                isearch += 1
                fromcoord = shape[min_shape_index - isearch]

            return calculate_direction(fromcoord, tocoord)
        else:
            fromcoord = shape[min_shape_index]
            isearch = 1
            tocoord = shape[min_shape_index + isearch]
            while cal_distance(fromcoord, tocoord) < 0.3*DISTANCE_THRESHOLD:
                isearch += 1
                tocoord = shape[min_shape_index + isearch]
            return calculate_direction(fromcoord, tocoord)

    else:
        logging.warn("未找到行驶方向角：%s", stop)
        return -1

def get_shape_by_trip_name(file):
    shape = {}
    with codecs.open(file, 'r', 'utf-8') as f:
        for line in f:            
            flds = line.replace("\ufeff", '').split(",")
            if (len(flds) == 8):
                trip_name = flds[1].strip()            
                coords = flds[7].strip().split("|")
                for coord in coords:
                    coord_flds = coord.split("_")
                    shape.setdefault(trip_name, []).append((float(coord_flds[0]), float(coord_flds[1])))
    return shape
                

def main():
    startTime = time.time()  # 返回当前的Unix 时间戳，单位秒
    shape_by_trip_name = get_shape_by_trip_name(input_shape)

    stops_by_name = {}
    subway_stops_by_name = {}
    icount = 0
    with codecs.open(input_stop, 'r', 'utf-8') as f:
        # N4路,N4路(火车站--南海粮食),24,世界之窗1,113.975105,22.536854
        for line in f:
            flds = line.replace("\ufeff", '').split(",")
            if (len(flds) == 6):  
                icount += 1             
                (route_name, trip_name, stop_index, stop_name, lng_str, lat_str) = flds
                lng = float(lng_str)
                lat = float(lat_str)
                direction = get_direction((route_name, trip_name, stop_index, stop_name, lng, lat), shape_by_trip_name[trip_name])
                if (direction >= 0):
                    if '地铁' in route_name and '号线' in route_name:
                        subway_stops_by_name.setdefault(stop_name, []).append((route_name, trip_name, stop_index, stop_name, lng, lat, direction))                    
                    else:
                        stops_by_name.setdefault(stop_name, []).append((route_name, trip_name, stop_index, stop_name, lng, lat, direction))
            else:
                print('异常站点记录：%s'%line)
    print("读取了%d个站点."%icount)
    output_stops = []
    for stop_name in stops_by_name:
        stops = add_stop_id(stops_by_name[stop_name])
        output_stops = output_stops + stops

    for stop_name in subway_stops_by_name:
        stops = add_stop_id_subway(subway_stops_by_name[stop_name])
        output_stops = output_stops + stops
    
    with codecs.open(output_stop, 'w', 'utf-8') as f:
        for stop in sorted(output_stops):
            f.write("%s,%s,%s,%s,%.6f,%.6f,%s\n"%stop)

    endTime = time.time()
    print("Complete in %.5f minutes." % ((endTime - startTime)/60.0))


if __name__ == '__main__':
    main()