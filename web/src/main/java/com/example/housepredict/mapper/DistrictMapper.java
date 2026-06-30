package com.example.housepredict.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.housepredict.entity.District;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface DistrictMapper extends BaseMapper<District> {
    @Select("select * from houses_district where city_id = #{cityId} and name = #{name} limit 1")
    District selectByCityIdAndName(@Param("cityId") Long cityId, @Param("name") String name);

    @Select("select * from houses_district where city_id = #{cityId} order by name")
    List<District> selectByCityIdOrderByName(@Param("cityId") Long cityId);
}
