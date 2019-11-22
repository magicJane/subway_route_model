-- 表move_subway与表gaode_stop_pair_route表进行关联操作
drop table if exists move_subway_join_gaode;
create table move_subway_join_gaode as 
select uid, date, move_id, station, line, flag, city, a.time, a.stime, a.etime, a.O, a.D, a.stations_cnt, b.route_id, b.stops, b.stops_cnt, b.travel_time
from 
  (select uid, move_id, station, line, flag, city, date, stime as time,    -- 到达每个站点的时间
  first_value(stime) over (partition by uid, date, move_id order by stime) as stime,  -- 行程起始时间
  last_value(stime) over (partition by uid, date, move_id order by stime rows between unbounded preceding and unbounded following) as etime, -- 行程结束时间
  first_value(station) over(partition by uid, date, move_id order by stime) as O, -- 起点站
  last_value(station) over (partition by uid, date, move_id order by stime rows between unbounded preceding and unbounded following) as D,  -- 终点站
  count(station) over(partition by uid, date, move_id) as stations_cnt  -- 经过站点总数
  from move_subway) a
left join
gaode_stop_pair_route b
on a.O = b.start_station and a.D = b.end_station;


-- 匹配联通用户出行路径与高德路径(1160879)
drop table if exists move_subway_route;
create table move_subway_route as 
select uid, move_id, station, line, flag, city, date, time, stime, etime, O, D, stations_cnt, route_id, stops, stops_cnt, isin, isin_cnt, unix_timestamp(etime)-unix_timestamp(stime) as travel_time_p, travel_time as travel_time_g
from
  (select uid, move_id, station, line, flag, city, date, time, stime, etime, O, D, stations_cnt, route_id, stops, stops_cnt, isin, isin_cnt, travel_time,
  row_number() over(partition by uid, date, move_id order by isin_cnt desc) as r     -- 按 sum(isin)排序，选sum(isin)最大的route_id作为匹配路线，
  from
    (select uid, move_id, station, line, flag, city, date, time, stime, etime, O, D, stations_cnt, route_id, stops, stops_cnt, isin, travel_time,
    sum(isin) over (partition by uid, date, move_id, route_id) as isin_cnt  -- stations 在高德线路上出现的次数之和
    from
      (select uid, move_id, station, line, flag, city, date, time, stime, etime, O, D, stations_cnt, route_id, stops, stops_cnt, travel_time,
        case when stops like concat('%',station,'%') then 1 else 0 
        end as isin  -- isin 站点是否在高德线路上
      from move_subway_join_gaode) a ) b) c
where c.r = 1;


-- 关联 user_attribute 表 (1102327)
drop table if exists move_subway_route_user;
create table move_subway_route_user as 
select a.uid, move_id, station, line, flag, a.city, a.date, time, stime, etime, O, D, stations_cnt, route_id, stops, stops_cnt, isin, isin_cnt, 
    travel_time_p, travel_time_g, abs(travel_time_p -travel_time_g) as time_diff, b.gender, b.age
from 
  (select uid, move_id, station, line, flag, city, date, time, stime, etime, O, D, stations_cnt, route_id, stops, stops_cnt, isin, isin_cnt, 
    travel_time_p, travel_time_g, abs(travel_time_p -travel_time_g) as time_diff
  from move_subway_route) a
left join 
(select uid, gender, age
from user_attribute 
where  city = 'V0440300' and date = 20190401) b
on a.uid = b.uid


-- 数据清洗 (772382)
drop table if exists move_subway_trip;
create table move_subway_trip as 
select uid, gender, age, date, move_id, city, stime, etime, O, D, route_id, stops, travel_time_g as travel_time, 
case 
  when hour(stime) >= 7 and hour(stime) < 9 then '早高峰'
  when hour(stime) >= 17 and hour(stime) < 19  then '晚高峰'
  else '平峰' end as period
from move_subway_route_user 
where  flag = '进站'
    and O <> D                                          -- 进出站不同
    and abs(stations_cnt - stops_cnt) <= 5               -- 途径站点数量差异在5个以内
    and abs(travel_time_p -travel_time_g) <= 60 * 20      -- 两种数据出行时间相差20min以内
    

-- 集计汇总，数据导出
drop table if exists subway_trip;
create table subway_trip as
select date, O, D, period, gender, route_id, stops, count(period) as cnt, city
from move_subway_trip 
group by city, date, O, D, period, gender, route_id, stops
order by city, date, O, D, period, gender, route_id

-- select city, date, O, D, period, gender, route_id, stops, cnt from subway_trip limit 400;  
-- select count(*) from subway_trip  -- 176909
-- select period, sum(cnt) as cnt from subway_trip group by period 




