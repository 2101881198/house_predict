package com.example.housepredict.service.impl;

import com.example.housepredict.dto.HouseQuery;
import com.example.housepredict.dto.PageResult;
import com.example.housepredict.entity.House;
import com.example.housepredict.mapper.HouseMapper;
import com.example.housepredict.service.HouseService;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import org.springframework.stereotype.Service;

@Service
public class HouseServiceImpl implements HouseService {
    private static final Map<String, String> SORT_FIELDS = Map.of(
            "total_price", "h.total_price",
            "unit_price", "h.unit_price",
            "area", "h.area",
            "crawl_time", "h.crawl_time"
    );

    private final HouseMapper houseMapper;

    public HouseServiceImpl(HouseMapper houseMapper) {
        this.houseMapper = houseMapper;
    }

    @Override
    public PageResult<House> findHouses(HouseQuery query, int maxPageSize) {
        int page = query.safePage();
        int size = query.safePageSize(maxPageSize);
        int offset = (page - 1) * size;
        long total = houseMapper.countByQuery(query);
        List<House> houses = houseMapper.selectByQuery(query, offset, size, resolveOrderBy(query.sort()));
        return new PageResult<>(houses, total, page - 1, size);
    }

    @Override
    public House findWithCityAndDistrictById(Long houseId) {
        House house = houseMapper.selectWithCityAndDistrictById(houseId);
        if (house == null) {
            throw new NoSuchElementException("House not found");
        }
        return house;
    }

    @Override
    public List<House> findSimilarHouses(Long districtId, Long excludeId, int limit) {
        return houseMapper.selectSimilarByDistrict(districtId, excludeId, limit);
    }

    @Override
    public BigDecimal avgUnitPriceByDistrictId(Long districtId) {
        return houseMapper.avgUnitPriceByDistrictId(districtId);
    }

    private String resolveOrderBy(String rawSort) {
        String sort = hasText(rawSort) ? rawSort : "-crawl_time";
        boolean descending = sort.startsWith("-");
        String key = descending ? sort.substring(1) : sort;
        String column = SORT_FIELDS.getOrDefault(key, "h.crawl_time");
        return column + (descending ? " desc" : " asc");
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}
