# -*- coding:utf-8 -*-
import time
import sys
import codecs
import os
import io
import urllib.parse
import urllib.request
import json
import random
import hashlib
import requests

import logging
from datetime import datetime
from convertor import *

from sqlalchemy.sql import text
from sqlalchemy import create_engine

logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %Y-%m-%d %H:%M:%S',
                filename='app.log',
                filemode='w')
               
#同时输出到文件和屏幕
#定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

INPUT_STOP_FILE = '/home/sutpc/data/transit/sz_transit_1903/config/transit_stop_with_stopid.txt'
INPUT_SHAPE_FILE = '/home/sutpc/data/transit/sz_transit_1903/config/transit_shape.txt'
CONN_STRING = 'postgresql://postgres:Sutpc123@10.10.160.1:5432/trans_pass_info'
UPDATE_DATE=20190601

# def getLineNames(filePath):
#     lineNames = []
#     with codecs.open(filePath, 'r', 'utf-8') as f:
#         for line in f:
#             lineNames.append(line.strip())
#     return lineNames

def convertShape(shape):
    coords = shape.split("|")
    new_coords = []
    for coord in coords:
        flds = coord.split('_')
        lng_mars = float(flds[0])
        lat_mars = float(flds[1])
        lat, lng = mars2Wgs(float(lat_mars), float(lng_mars))   
        new_coord = "%.6f %.6f"%(lng, lat)            
        new_coords.append(new_coord)


    return "LINESTRING(%s)"%(",".join(new_coords))

def get_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()
   
    
def main():
    startTime = time.time()  # 返回当前的Unix 时间戳，单位秒
    
    routes = {}
    route_stops = []
    stops = {}
    with codecs.open(INPUT_STOP_FILE, 'r', 'utf-8') as f:
        # 122路,122路(塘朗小学--荔山工业园总站),5,平山村南,113.968163,22.582947,平山村南_S2
        for line in f:
            flds = line.replace("\ufeff", "").split(",")
            line_name = flds[0].strip()
            route_name = flds[1].strip()
            route_id = get_hash(route_name)
            stop_index = int(flds[2])
            stop_name = flds[3].strip()            
            lng_mars = float(flds[4])
            lat_mars = float(flds[5])
            lat, lng = mars2Wgs(float(lat_mars), float(lng_mars))
            stop_id = get_hash(flds[6].strip())

            route = {}
            route['line_name'] = line_name
            route['route_id'] = route_id
            route['route_name'] = route_name

            route_name_split = []
            if (')(' in route_name):
                route_name_split = route_name.split(")(")
            else:
                route_name_split = route_name.split("(")
            
            terminals = ("".join(route_name_split[1:])).strip().replace(")", "")
            terminals_flds = terminals.split("--")
            from_stop_name = terminals_flds[0].strip()
            to_stop_name = terminals_flds[1].strip()

            route['from_stop_name'] = from_stop_name
            route['to_stop_name'] = to_stop_name
            

            routes[route_name] = route

            stops.setdefault(stop_id, []).append((stop_name, lng, lat))

            route_stop = {}
            route_stop['route_id'] = route_id
            route_stop['stop_index'] = stop_index-1 # index从0开始
            route_stop['stop_id'] = stop_id
            route_stop['update'] = UPDATE_DATE
            route_stops.append(route_stop)

    new_stops = []
    for stop_id in stops:
        stop = {}
        stop['stop_id'] = stop_id
        stop['stop_name'] = stops[stop_id][0][0]
        lngs = [x[1] for x in stops[stop_id]]
        lats = [x[2] for x in stops[stop_id]]
        stop['lon'] = sum(lngs)/len(lngs)
        stop['lat'] = sum(lats)/len(lats)
        stop['wkt'] = "POINT(%.6f %.6f)"%(stop['lon'],stop['lat'])
        stop['update'] = UPDATE_DATE
        new_stops.append(stop)


    lines = set()
    for route_id in routes:
        route = routes[route_id]
        line_name = route['line_name']
        if (line_name not in lines):
                route['direction_id'] = 0                
                lines.add(line_name)
        else:
            route['direction_id'] = 1        
    
    shapes = []
    lines = {}
    with codecs.open(INPUT_SHAPE_FILE, 'r', 'utf-8') as f:
        for line in f:
            flds = line.replace("\ufeff", "").split(",")
            if (len(flds) == 8):
                route_name = flds[1].strip()
                start_time = flds[2].strip()
                end_time = flds[3].strip()
                basic_price = flds[4].strip()
                total_price = flds[5].strip()

                route = routes[route_name]
                route['start_time'] = start_time
                route['end_time'] = end_time
                route['basic_price'] = basic_price
                route['total_price'] = total_price

                route['wkt'] = convertShape(flds[7].strip())
                route['update'] = UPDATE_DATE

                line = {}
                line['line_name'] = flds[0].strip()
                line['company'] = flds[6].strip()
                line['line_type'] = 1 if ('地铁' in flds[0] and '号线' in flds[0]) else 3          
                line['update'] = UPDATE_DATE
                lines[flds[0].strip()] = line
    
    engine = create_engine(CONN_STRING)
    
    with engine.connect() as conn:  
        for line_name in lines:
            conn.execute(text("INSERT INTO transit_info_line(line_name, company, line_type,update_date) values(:line_name, :company, :line_type, :update)"), **lines[line_name])

        for route_name in routes:        
            conn.execute(text("INSERT INTO transit_info_route(line_name, route_id,direction_id,route_name,from_stop_name,to_stop_name,basic_price,total_price,start_time,end_time,geom_wkt,update_date) values(:line_name, :route_id,:direction_id,:route_name,:from_stop_name,:to_stop_name,:basic_price,:total_price,:start_time,:end_time,:wkt,:update)"), **routes[route_name])

        for stop in new_stops:
            conn.execute(text("INSERT INTO transit_info_stop(stop_id,stop_name,lat,lon,geom_wkt,update_date) values(:stop_id,:stop_name,:lat,:lon,:wkt,:update)"), **stop)
     
        for route_stop in route_stops:
            conn.execute(text("INSERT INTO transit_info_route_stop(route_id, stop_index, stop_id,update_date) values(:route_id, :stop_index, :stop_id, :update)"), **route_stop)
              
        
    endTime = time.time()
    logging.info("Complete in %.5f minutes." % ((endTime - startTime)/60.0))


if __name__ == '__main__':
    main()