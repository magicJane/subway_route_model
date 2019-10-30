# 轨道路径选择模型

## `subway_routing_gaode`

使用高德JavaScript API 爬取 深圳市所有轨道站点对之间的出行路线

* `subway_stop_names.csv` 所有深圳轨道交通站点名称集合

* 程序`create_stop_pairs.py` 生成所有轨道站点对（共167*166对），结果输出到`stop_pairs.txt`

* `create_model.py` 通过python `Template`将`stop_pairs`写入`subway_route_template.html`中，生成`subway_route.html`，并打开浏览器执行`subway_route.html`文件

* 程序`subway_route.html` 爬取轨道站点间所有的轨道出行线路，结果输出到`gaode_stop_pair_route.txt`文件（保存位置取决于浏览器下载位置设置）

* 程序 `FileSaver.js` 保存结果到文件的程序

* 返回结果格式为

  `start_station, end_station, route_id, time, price, distance, walking_distance, lines, stops`

  eg. `大学城(地铁站),科苑(地铁站),0,2185.0,5.0,16486.0,0.0,地铁5号线(环中线)(黄贝岭--赤湾)|地铁7号线(西丽线)(西丽湖--太安)|地铁2号线(蛇口线)(新秀--赤湾),大学城_西丽|西丽_茶光_珠光_龙井_桃源村_深云_安托山|安托山_深康_侨城北_世界之窗_红树湾_科苑`

