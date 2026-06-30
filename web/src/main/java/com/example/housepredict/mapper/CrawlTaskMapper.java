package com.example.housepredict.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.housepredict.entity.CrawlTask;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface CrawlTaskMapper extends BaseMapper<CrawlTask> {
    @Select("select * from houses_crawltask order by created_at desc limit 100")
    List<CrawlTask> selectRecent100();
}
