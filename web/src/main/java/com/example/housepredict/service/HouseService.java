package com.example.housepredict.service;

import com.example.housepredict.dto.HouseQuery;
import com.example.housepredict.dto.PageResult;
import com.example.housepredict.entity.House;
import java.math.BigDecimal;
import java.util.List;

public interface HouseService {
    PageResult<House> findHouses(HouseQuery query, int maxPageSize);

    House findWithCityAndDistrictById(Long houseId);

    List<House> findSimilarHouses(Long districtId, Long excludeId, int limit);

    BigDecimal avgUnitPriceByDistrictId(Long districtId);
}
