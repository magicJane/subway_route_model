-- -- hive窗口函数, 添加O,D,etime字段
-- select move_id, station, line, flag, city, date, stime,
-- last_value(stime) over (partition by uid,date, move_id order by stime rows between unbounded preceding and unbounded following) as etime,
-- first_value(station) over(partition by uid, date, move_id order by stime) as O, 
-- last_value(station) over (partition by uid, date, move_id order by stime rows between unbounded preceding and unbounded following) as D,
-- count(station) over(partition by uid, date, move_id) as stations_cnt
-- from move_subway
-- limit 100


-- 与gaode_stop_pair_route表进行关联操作
drop table if exists move_subway_join_gaode;
create table move_subway_join_gaode as 
select uid, move_id, station, line, flag, city, date, a.time, a.stime, a.etime, a.O, a.D, a.stations_cnt, b.route_id, b.stops
from 
  (select uid, move_id, station, line, flag, city, date, stime as time,    -- 到达每个站点的时间
  first_value(stime) over (partition by uid, date, move_id order by stime) as stime,  -- 行程起始时间
  last_value(stime) over (partition by uid, date, move_id order by stime rows between unbounded preceding and unbounded following) as etime, --行程结束时间
  first_value(station) over(partition by uid, date, move_id order by stime) as O, -- 起点站
  last_value(station) over (partition by uid, date, move_id order by stime rows between unbounded preceding and unbounded following) as D,  -- 终点站
  count(station) over(partition by uid, date, move_id) as stations_cnt  -- 经过站点总数
  from move_subway) a
left join
gaode_stop_pair_route b
on a.O = b.start_station and a.D = b.end_station

select move_id, station, line, flag, city, date, time, stime, etime, O, D, stations_cnt, route_id, stops
from move_subway_join_gaode
limit 20;


-- -- 增加isin字段，判断站点是否在高德爬取的route上
-- select move_id, station, line, flag, city, date, time, stime, etime, O, D, route_id, stops,
-- sum(isin) over (partition by uid, date, move_id,route_id) as stop_cnt
-- from
--   (select uid, move_id, station, line, flag, city, date, time, stime, etime, O, D, route_id, stops,
--     case when stops like concat('%',station,'%') then 1 else 0 
--     end as isin
--   from move_subway_join_gaode) a 
-- limit 100 


-- 匹配联通用户出行路径与高德路径
drop table if exists move_subway_route;
create table move_subway_route as 
select uid, move_id, station, line, flag, city, date, time, stime, etime, O, D, stations_cnt, route_id, stops, isin, isin_cnt
from
  (select uid, move_id, station, line, flag, city, date, time, stime, etime, O, D, stations_cnt, route_id, stops, isin, isin_cnt,
  rank() over(partition by uid, date, move_id order by stop_cnt desc) as r     -- 按 sum(isin)排序，选sum(isin)最大的route_id作为匹配路线
  from
    (select uid, move_id, station, line, flag, city, date, time, stime, etime, O, D, stations_cnt, route_id, stops, isin, 
    sum(isin) over (partition by uid, date, move_id, route_id) as isin_cnt  -- stations 在高德线路上出现的次数之和
    from
      (select uid, move_id, station, line, flag, city, date, time, stime, etime, O, D, stations_cnt, route_id, stops,
        case when stops like concat('%',station,'%') then 1 else 0 
        end as isin  -- isin 站点是否在高德线路上
      from move_subway_join_gaode) a ) b) c
where c.r = 1;

select move_id, station, line, flag, city, date, time, stime, etime, O, D, stations_cnt, route_id, stops, isin, isin_cnt
from move_subway_route
order  by uid, date, move_id, time
limit 500;