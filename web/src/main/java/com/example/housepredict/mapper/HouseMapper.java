package com.example.housepredict.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.housepredict.dto.HouseQuery;
import com.example.housepredict.entity.House;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface HouseMapper extends BaseMapper<House> {
    House selectBySourceUrl(@Param("sourceUrl") String sourceUrl);

    House selectWithCityAndDistrictById(@Param("id") Long id);

    List<House> selectSimilarByDistrict(@Param("districtId") Long districtId, @Param("excludeId") Long excludeId, @Param("limit") int limit);

    List<House> selectRecentWithCityAndDistrict(@Param("limit") int limit);

    long countByQuery(@Param("query") HouseQuery query);

    List<House> selectByQuery(@Param("query") HouseQuery query, @Param("offset") int offset, @Param("limit") int limit, @Param("orderBy") String orderBy);

    BigDecimal avgUnitPriceByDistrictId(@Param("districtId") Long districtId);

    BigDecimal avgUnitPriceByCityName(@Param("city") String city);

    BigDecimal avgUnitPriceByCityAndDistrictName(@Param("city") String city, @Param("district") String district);

    BigDecimal avgUnitPrice();

    BigDecimal avgTotalPrice();

    long countByPriceBucket(@Param("cityId") Long cityId, @Param("minPrice") BigDecimal minPrice, @Param("maxPrice") BigDecimal maxPrice);

    long countByAreaBucket(@Param("cityId") Long cityId, @Param("minArea") BigDecimal minArea, @Param("maxArea") BigDecimal maxArea);

    List<Map<String, Object>> cityDistributionRows();

    List<Map<String, Object>> districtRowsByCity(@Param("cityId") Long cityId);

    List<Map<String, Object>> hotDistrictRows(@Param("limit") int limit);

    List<Map<String, Object>> roomTypeRows();

    List<Map<String, Object>> roomTypeRowsByCity(@Param("cityId") Long cityId);

    List<Map<String, Object>> decorationRows();

    List<Map<String, Object>> decorationRowsByCity(@Param("cityId") Long cityId);

    List<Map<String, Object>> trendRows();

    List<Map<String, Object>> trendRowsByCity(@Param("cityId") Long cityId);

    List<Map<String, Object>> cityTrendRows();

    List<House> mapPointRows(@Param("limit") int limit);

    List<String> findRoomTypes();

    List<String> findFloors();

    List<String> findDirections();

    List<String> findDecorations();
}
