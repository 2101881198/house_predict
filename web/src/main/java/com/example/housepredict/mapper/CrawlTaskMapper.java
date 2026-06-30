package com.example.housepredict.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.housepredict.entity.CrawlTask;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface CrawlTaskMapper extends BaseMapper<CrawlTask> {
    // 查询最近 100 条采集任务；后台首页和后台 API 用于展示任务记录。
    @Select("select * from houses_crawltask order by created_at desc limit 100")
    List<CrawlTask> selectRecent100();
}
