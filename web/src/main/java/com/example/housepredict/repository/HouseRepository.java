package com.example.housepredict.repository;

import com.example.housepredict.entity.District;
import com.example.housepredict.entity.House;
import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface HouseRepository extends JpaRepository<House, Long>, JpaSpecificationExecutor<House> {
    Optional<House> findBySourceUrl(String sourceUrl);

    @EntityGraph(attributePaths = {"city", "district"})
    Optional<House> findWithCityAndDistrictById(Long id);

    List<House> findByDistrictAndIdNotOrderByCrawlTimeDescIdDesc(District district, Long id, Pageable pageable);

    @EntityGraph(attributePaths = {"city", "district"})
    List<House> findTop20ByOrderByCreatedAtDescIdDesc();

    @Query("select avg(h.unitPrice) from House h where h.district = :district")
    BigDecimal avgUnitPriceByDistrict(@Param("district") District district);

    @Query("select avg(h.unitPrice) from House h where h.city.name = :city")
    BigDecimal avgUnitPriceByCityName(@Param("city") String city);

    @Query("select avg(h.unitPrice) from House h where h.city.name = :city and h.district.name = :district")
    BigDecimal avgUnitPriceByCityAndDistrictName(@Param("city") String city, @Param("district") String district);

    @Query("select avg(h.unitPrice) from House h")
    BigDecimal avgUnitPrice();

    @Query("select avg(h.totalPrice) from House h")
    BigDecimal avgTotalPrice();

    @Query("select count(h) from House h where (:cityId is null or h.city.id = :cityId) and (:minPrice is null or h.totalPrice >= :minPrice) and (:maxPrice is null or h.totalPrice < :maxPrice)")
    long countByPriceBucket(@Param("cityId") Long cityId, @Param("minPrice") BigDecimal minPrice, @Param("maxPrice") BigDecimal maxPrice);

    @Query("select count(h) from House h where (:cityId is null or h.city.id = :cityId) and (:minArea is null or h.area >= :minArea) and (:maxArea is null or h.area < :maxArea)")
    long countByAreaBucket(@Param("cityId") Long cityId, @Param("minArea") BigDecimal minArea, @Param("maxArea") BigDecimal maxArea);

    @Query("select h.city.id, h.city.name, count(h), avg(h.totalPrice), avg(h.unitPrice), max(h.totalPrice), min(h.totalPrice) from House h group by h.city.id, h.city.name order by count(h) desc, h.city.name")
    List<Object[]> cityDistributionRows();

    @Query("select h.district.id, h.district.name, count(h), avg(h.totalPrice), avg(h.unitPrice) from House h where h.city.id = :cityId group by h.district.id, h.district.name order by count(h) desc, h.district.name")
    List<Object[]> districtRowsByCity(@Param("cityId") Long cityId);

    @Query("select h.city.name, h.district.name, count(h), avg(h.unitPrice) from House h group by h.city.name, h.district.name order by count(h) desc")
    List<Object[]> hotDistrictRows(Pageable pageable);

    @Query("select h.roomType, count(h) from House h where h.roomType <> '' group by h.roomType order by count(h) desc, h.roomType")
    List<Object[]> roomTypeRows();

    @Query("select h.roomType, count(h) from House h where h.city.id = :cityId and h.roomType <> '' group by h.roomType order by count(h) desc, h.roomType")
    List<Object[]> roomTypeRowsByCity(@Param("cityId") Long cityId);

    @Query("select h.decoration, count(h) from House h where h.decoration <> '' group by h.decoration order by count(h) desc, h.decoration")
    List<Object[]> decorationRows();

    @Query("select h.decoration, count(h) from House h where h.city.id = :cityId and h.decoration <> '' group by h.decoration order by count(h) desc, h.decoration")
    List<Object[]> decorationRowsByCity(@Param("cityId") Long cityId);

    @Query(value = "select period, count(*) as total, avg(total_price) as avg_total_price from (select concat(year(crawl_time), ' Q', quarter(crawl_time)) as period, year(crawl_time) as year_value, quarter(crawl_time) as quarter_value, total_price from houses_house where crawl_time is not null) trend_source group by period, year_value, quarter_value order by year_value, quarter_value", nativeQuery = true)
    List<Object[]> trendRows();

    @Query(value = "select period, count(*) as total, avg(total_price) as avg_total_price from (select concat(year(crawl_time), ' Q', quarter(crawl_time)) as period, year(crawl_time) as year_value, quarter(crawl_time) as quarter_value, total_price from houses_house where city_id = :cityId and crawl_time is not null) trend_source group by period, year_value, quarter_value order by year_value, quarter_value", nativeQuery = true)
    List<Object[]> trendRowsByCity(@Param("cityId") Long cityId);

    @Query(value = "select city_name, period, count(*) as total, avg(total_price) as avg_total_price from (select c.name as city_name, concat(year(h.crawl_time), ' Q', quarter(h.crawl_time)) as period, year(h.crawl_time) as year_value, quarter(h.crawl_time) as quarter_value, h.total_price from houses_house h join houses_city c on c.id = h.city_id join (select city_id from houses_house group by city_id order by count(*) desc limit 5) top_city on top_city.city_id = h.city_id where h.crawl_time is not null) trend_source group by city_name, period, year_value, quarter_value order by city_name, year_value, quarter_value", nativeQuery = true)
    List<Object[]> cityTrendRows();

    @Query("select h from House h join fetch h.city join fetch h.district where h.longitude is not null and h.latitude is not null order by h.crawlTime desc, h.id desc")
    List<House> mapPointRows(Pageable pageable);

    @Query("select distinct h.roomType from House h where h.roomType <> '' order by h.roomType")
    List<String> findRoomTypes();

    @Query("select distinct h.floor from House h where h.floor <> '' order by h.floor")
    List<String> findFloors();

    @Query("select distinct h.direction from House h where h.direction <> '' order by h.direction")
    List<String> findDirections();

    @Query("select distinct h.decoration from House h where h.decoration <> '' order by h.decoration")
    List<String> findDecorations();
}
