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

    @Query("select avg(h.unitPrice) from House h where h.district = :district")
    BigDecimal avgUnitPriceByDistrict(@Param("district") District district);

    @Query("select avg(h.unitPrice) from House h where h.city.name = :city")
    BigDecimal avgUnitPriceByCityName(@Param("city") String city);

    @Query("select avg(h.unitPrice) from House h where h.city.name = :city and h.district.name = :district")
    BigDecimal avgUnitPriceByCityAndDistrictName(@Param("city") String city, @Param("district") String district);

    @Query("select avg(h.unitPrice) from House h")
    BigDecimal avgUnitPrice();

    @Query("select distinct h.roomType from House h where h.roomType <> '' order by h.roomType")
    List<String> findRoomTypes();
}
