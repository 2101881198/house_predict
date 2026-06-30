package com.example.housepredict.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.housepredict.entity.PredictResult;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface PredictResultMapper extends BaseMapper<PredictResult> {
    // 查询最近的预测记录；预测页和后台首页用于展示历史预测。
    @Select("select * from houses_predictresult order by predict_time desc limit #{limit}")
    List<PredictResult> selectRecent(@Param("limit") int limit);
}
