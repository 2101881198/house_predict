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
    // 按数据来源链接查询房源；导入演示数据时用于判断是否已经存在。
    House selectBySourceUrl(@Param("sourceUrl") String sourceUrl);

    // 按房源 ID 查询详情，同时关联城市和区县对象；详情页和详情 API 使用。
    House selectWithCityAndDistrictById(@Param("id") Long id);

    // 查询同区县的相似房源，并排除当前房源；详情页的相似推荐使用。
    List<House> selectSimilarByDistrict(@Param("districtId") Long districtId, @Param("excludeId") Long excludeId, @Param("limit") int limit);

    // 查询最近新增的房源，同时关联城市和区县；后台首页最近房源列表使用。
    List<House> selectRecentWithCityAndDistrict(@Param("limit") int limit);

    // 按筛选条件统计房源总数；分页列表需要先用它计算总页数。
    long countByQuery(@Param("query") HouseQuery query);

    // 按筛选条件分页查询房源；房源列表页面和 /api/houses/ 使用。
    List<House> selectByQuery(@Param("query") HouseQuery query, @Param("offset") int offset, @Param("limit") int limit, @Param("orderBy") String orderBy);

    // 计算某个区县的平均单价；房源详情页用于展示区县均价。
    BigDecimal avgUnitPriceByDistrictId(@Param("districtId") Long districtId);

    // 计算某个城市的平均单价；预测结果对比和规则兜底预测使用。
    BigDecimal avgUnitPriceByCityName(@Param("city") String city);

    // 计算某个城市某个区县的平均单价；预测结果对比和规则兜底预测使用。
    BigDecimal avgUnitPriceByCityAndDistrictName(@Param("city") String city, @Param("district") String district);

    // 计算全量房源平均单价；首页总览和预测兜底使用。
    BigDecimal avgUnitPrice();

    // 计算全量房源平均总价；首页总览使用。
    BigDecimal avgTotalPrice();

    // 统计指定总价区间内的房源数量；价格区间图表使用。
    long countByPriceBucket(@Param("cityId") Long cityId, @Param("minPrice") BigDecimal minPrice, @Param("maxPrice") BigDecimal maxPrice);

    // 统计指定面积区间内的房源数量；面积区间图表使用。
    long countByAreaBucket(@Param("cityId") Long cityId, @Param("minArea") BigDecimal minArea, @Param("maxArea") BigDecimal maxArea);

    // 按城市聚合房源数量和价格指标；首页和省级分析使用。
    List<Map<String, Object>> cityDistributionRows();

    // 按区县聚合某个城市内的房源数量和价格指标；城市分析页使用。
    List<Map<String, Object>> districtRowsByCity(@Param("cityId") Long cityId);

    // 查询房源数量最多的热门区县；首页热门区县图表使用。
    List<Map<String, Object>> hotDistrictRows(@Param("limit") int limit);

    // 统计全量房源的户型分布；首页和省级分析图表使用。
    List<Map<String, Object>> roomTypeRows();

    // 统计某个城市的户型分布；城市分析图表使用。
    List<Map<String, Object>> roomTypeRowsByCity(@Param("cityId") Long cityId);

    // 统计全量房源的装修分布；首页图表使用。
    List<Map<String, Object>> decorationRows();

    // 统计某个城市的装修分布；城市分析图表使用。
    List<Map<String, Object>> decorationRowsByCity(@Param("cityId") Long cityId);

    // 按季度统计全量房源均价趋势；首页趋势图使用。
    List<Map<String, Object>> trendRows();

    // 按季度统计某个城市的均价趋势；城市分析趋势图使用。
    List<Map<String, Object>> trendRowsByCity(@Param("cityId") Long cityId);

    // 查询房源数量靠前城市的季度趋势；首页多城市趋势对比图使用。
    List<Map<String, Object>> cityTrendRows();

    // 查询带经纬度的房源点位；地图散点展示使用。
    List<House> mapPointRows(@Param("limit") int limit);

    // 查询已有户型选项；预测页和筛选表单下拉框使用。
    List<String> findRoomTypes();

    // 查询已有楼层选项；预测页下拉框使用。
    List<String> findFloors();

    // 查询已有朝向选项；预测页下拉框使用。
    List<String> findDirections();

    // 查询已有装修选项；预测页和筛选表单下拉框使用。
    List<String> findDecorations();
}
