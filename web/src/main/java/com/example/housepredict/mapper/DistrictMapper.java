package com.example.housepredict.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.housepredict.entity.District;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface DistrictMapper extends BaseMapper<District> {
    // 在指定城市下按区县名称查询；新增房源和演示数据导入时用于避免重复创建区县。
    @Select("select * from houses_district where city_id = #{cityId} and name = #{name} limit 1")
    District selectByCityIdAndName(@Param("cityId") Long cityId, @Param("name") String name);

    // 查询某个城市下的所有区县；预测页城市-区县联动下拉框使用。
    @Select("select * from houses_district where city_id = #{cityId} order by name")
    List<District> selectByCityIdOrderByName(@Param("cityId") Long cityId);
}
