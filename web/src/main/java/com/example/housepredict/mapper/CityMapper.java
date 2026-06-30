package com.example.housepredict.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.housepredict.entity.City;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface CityMapper extends BaseMapper<City> {
    // 根据城市名称查询城市记录；新增房源和演示数据导入时用于避免重复创建城市。
    @Select("select * from houses_city where name = #{name} limit 1")
    City selectByName(@Param("name") String name);
}
