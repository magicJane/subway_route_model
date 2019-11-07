select move_id, stime, station, line, flag, city, date from move_subway where date= 20190415 order by uid, move_id, stime limit 100;

-- 数据检查
select count(*) from move_subway;   -- 8643174条记录

-- 出行记录总数
select count(*) from
(select uid, move_id, day(stime)
from move_subway
group by uid, move_id,day(stime)) a;   -- 1160879
-- 时间范围
select distinct to_date(stime) from move_subway  -- 2019-04-15 2019-04-16 2019-04-17
-- 所有轨道站点
select distinct station from move_subway -- 168 

-- 重复记录
select move_id, station, line, flag, city, date, stime 
from move_subway
where stime = '2019-04-16 12:38:57' and station = '少年宫站'

