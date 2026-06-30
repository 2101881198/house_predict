package com.example.housepredict.service.impl;

import com.example.housepredict.entity.City;
import com.example.housepredict.mapper.CityMapper;
import com.example.housepredict.mapper.HouseMapper;
import com.example.housepredict.service.AnalysisService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AnalysisServiceImpl implements AnalysisService {
    private final HouseMapper houseMapper;
    private final CityMapper cityMapper;

    public AnalysisServiceImpl(HouseMapper houseMapper, CityMapper cityMapper) {
        this.houseMapper = houseMapper;
        this.cityMapper = cityMapper;
    }

    @Override
    @Transactional(readOnly = true)
    @Cacheable("overview")
    public Map<String, Object> overview() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("total_houses", houseMapper.selectCount(null));
        data.put("city_count", cityMapper.selectCount(null));
        data.put("avg_total_price", round(houseMapper.avgTotalPrice()));
        data.put("avg_unit_price", round(houseMapper.avgUnitPrice()));
        List<Map<String, Object>> cityDistribution = cityDistribution();
        data.put("city_distribution", cityDistribution);
        data.put("hot_districts", hotDistricts());
        data.put("city_price_rankings", cityPriceRankings(cityDistribution));
        data.put("trend", priceTrend(null));
        data.put("city_price_trends", cityPriceTrends());
        data.put("map_points", mapPoints());
        return data;
    }

    @Override
    @Transactional(readOnly = true)
    @Cacheable("provinceStats")
    public Map<String, Object> provinceStats() {
        return Map.of("cities", cityDistribution());
    }

    @Override
    @Transactional(readOnly = true)
    @Cacheable(value = "cityStats", key = "#cityId")
    public Map<String, Object> cityStats(Long cityId) {
        City city = cityMapper.selectById(cityId);
        if (city == null) {
            throw new IllegalArgumentException("city_id 参数无效");
        }
        List<Map<String, Object>> districts = districtRows(cityId);
        long totalHouses = districts.stream().mapToLong(row -> number(row, "count").longValue()).sum();
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("city", Map.of("id", city.getId(), "name", city.getName()));
        data.put("summary", Map.of(
                "total_houses", totalHouses,
                "district_count", districts.size(),
                "avg_total_price", weightedAverage(districts, "avg_total_price"),
                "avg_unit_price", weightedAverage(districts, "avg_unit_price")
        ));
        data.put("districts", districts);
        data.put("trend", priceTrend(cityId));
        return data;
    }

    @Override
    @Transactional(readOnly = true)
    @Cacheable(value = "priceBuckets", key = "#cityId == null ? 'all' : #cityId")
    public List<Map<String, Object>> priceBuckets(Long cityId) {
        return List.of(
                bucket("100万以下", houseMapper.countByPriceBucket(cityId, null, BigDecimal.valueOf(100))),
                bucket("100-150万", houseMapper.countByPriceBucket(cityId, BigDecimal.valueOf(100), BigDecimal.valueOf(150))),
                bucket("150-200万", houseMapper.countByPriceBucket(cityId, BigDecimal.valueOf(150), BigDecimal.valueOf(200))),
                bucket("200-300万", houseMapper.countByPriceBucket(cityId, BigDecimal.valueOf(200), BigDecimal.valueOf(300))),
                bucket("300万以上", houseMapper.countByPriceBucket(cityId, BigDecimal.valueOf(300), null))
        );
    }

    @Override
    @Transactional(readOnly = true)
    @Cacheable(value = "areaBuckets", key = "#cityId == null ? 'all' : #cityId")
    public List<Map<String, Object>> areaBuckets(Long cityId) {
        return List.of(
                bucket("60㎡以下", houseMapper.countByAreaBucket(cityId, null, BigDecimal.valueOf(60))),
                bucket("60-90㎡", houseMapper.countByAreaBucket(cityId, BigDecimal.valueOf(60), BigDecimal.valueOf(90))),
                bucket("90-120㎡", houseMapper.countByAreaBucket(cityId, BigDecimal.valueOf(90), BigDecimal.valueOf(120))),
                bucket("120-150㎡", houseMapper.countByAreaBucket(cityId, BigDecimal.valueOf(120), BigDecimal.valueOf(150))),
                bucket("150㎡以上", houseMapper.countByAreaBucket(cityId, BigDecimal.valueOf(150), null))
        );
    }

    @Override
    @Transactional(readOnly = true)
    @Cacheable(value = "roomTypes", key = "#cityId == null ? 'all' : #cityId")
    public List<Map<String, Object>> roomTypeDistribution(Long cityId) {
        return groupedRows(cityId == null ? houseMapper.roomTypeRows() : houseMapper.roomTypeRowsByCity(cityId), "room_type");
    }

    @Override
    @Transactional(readOnly = true)
    @Cacheable(value = "decorations", key = "#cityId == null ? 'all' : #cityId")
    public List<Map<String, Object>> decorationDistribution(Long cityId) {
        return groupedRows(cityId == null ? houseMapper.decorationRows() : houseMapper.decorationRowsByCity(cityId), "decoration");
    }

    private List<Map<String, Object>> cityDistribution() {
        return houseMapper.cityDistributionRows().stream()
                .map(values -> {
                    Map<String, Object> data = new LinkedHashMap<>();
                    data.put("id", value(values, "id"));
                    data.put("city", value(values, "name"));
                    data.put("name", value(values, "name"));
                    data.put("count", number(values, "total_count").longValue());
                    data.put("avg_total_price", round(value(values, "avg_total_price")));
                    data.put("avg_unit_price", round(value(values, "avg_unit_price")));
                    data.put("max_total_price", round(value(values, "max_total_price")));
                    data.put("min_total_price", round(value(values, "min_total_price")));
                    return data;
                })
                .toList();
    }

    private List<Map<String, Object>> districtRows(Long cityId) {
        return houseMapper.districtRowsByCity(cityId).stream()
                .map(values -> {
                    Map<String, Object> data = new LinkedHashMap<>();
                    data.put("id", value(values, "id"));
                    data.put("name", value(values, "name"));
                    data.put("count", number(values, "total_count").longValue());
                    data.put("avg_total_price", round(value(values, "avg_total_price")));
                    data.put("avg_unit_price", round(value(values, "avg_unit_price")));
                    return data;
                })
                .toList();
    }

    private List<Map<String, Object>> hotDistricts() {
        return houseMapper.hotDistrictRows(8).stream()
                .map(row -> {
                    Map<String, Object> data = new LinkedHashMap<>();
                    data.put("city", value(row, "city"));
                    data.put("district", value(row, "district"));
                    data.put("count", number(row, "total_count").longValue());
                    data.put("avg_unit_price", round(value(row, "avg_unit_price")));
                    return data;
                })
                .toList();
    }

    private List<Map<String, Object>> cityPriceRankings(List<Map<String, Object>> cityDistribution) {
        return cityDistribution.stream()
                .sorted((left, right) -> ((BigDecimal) right.get("avg_unit_price")).compareTo((BigDecimal) left.get("avg_unit_price")))
                .limit(10)
                .toList();
    }

    private List<Map<String, Object>> priceTrend(Long cityId) {
        List<Map<String, Object>> rows = cityId == null ? houseMapper.trendRows() : houseMapper.trendRowsByCity(cityId);
        return rows.stream()
                .map(row -> trendRow(value(row, "period"), value(row, "total_count"), value(row, "avg_total_price")))
                .toList();
    }

    private List<Map<String, Object>> cityPriceTrends() {
        return houseMapper.cityTrendRows().stream()
                .collect(Collectors.groupingBy(row -> String.valueOf(value(row, "city_name")), LinkedHashMap::new, Collectors.toList()))
                .entrySet()
                .stream()
                .map(entry -> {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("city", entry.getKey());
                    row.put("trend", entry.getValue().stream()
                            .map(item -> trendRow(value(item, "period"), value(item, "total_count"), value(item, "avg_total_price")))
                            .toList());
                    return row;
                })
                .toList();
    }

    private Map<String, Object> trendRow(Object period, Object count, Object average) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("date", period);
        row.put("avg_total_price", round(average));
        row.put("count", ((Number) count).longValue());
        return row;
    }

    private List<Map<String, Object>> mapPoints() {
        return houseMapper.mapPointRows(200).stream()
                .map(h -> {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("title", h.getTitle());
                    row.put("city", h.getCity().getName());
                    row.put("district", h.getDistrict().getName());
                    row.put("longitude", h.getLongitude());
                    row.put("latitude", h.getLatitude());
                    row.put("total_price", h.getTotalPrice());
                    return row;
                })
                .toList();
    }

    private List<Map<String, Object>> groupedRows(List<Map<String, Object>> rows, String key) {
        return rows.stream()
                .map(values -> {
                    Map<String, Object> data = new LinkedHashMap<>();
                    data.put(key, value(values, "name"));
                    data.put("count", number(values, "total_count").longValue());
                    return data;
                })
                .toList();
    }

    private Map<String, Object> bucket(String label, long count) {
        return Map.of("label", label, "count", count);
    }

    private BigDecimal weightedAverage(List<Map<String, Object>> rows, String key) {
        long total = rows.stream().mapToLong(row -> number(row, "count").longValue()).sum();
        if (total == 0) {
            return BigDecimal.ZERO;
        }
        BigDecimal weighted = rows.stream()
                .map(row -> ((BigDecimal) row.get(key)).multiply(BigDecimal.valueOf(number(row, "count").longValue())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        return weighted.divide(BigDecimal.valueOf(total), 2, RoundingMode.HALF_UP);
    }

    private Number number(Map<String, Object> row, String key) {
        Object rawValue = value(row, key);
        return rawValue instanceof Number number ? number : BigDecimal.ZERO;
    }

    private Object value(Map<String, Object> row, String key) {
        Object direct = row.get(key);
        if (direct != null || row.containsKey(key)) {
            return direct;
        }
        String upperKey = key.toUpperCase();
        direct = row.get(upperKey);
        if (direct != null || row.containsKey(upperKey)) {
            return direct;
        }
        String camelKey = underscoreToCamel(key);
        return row.get(camelKey);
    }

    private String underscoreToCamel(String key) {
        StringBuilder builder = new StringBuilder();
        boolean upperNext = false;
        for (char ch : key.toCharArray()) {
            if (ch == '_') {
                upperNext = true;
                continue;
            }
            builder.append(upperNext ? Character.toUpperCase(ch) : ch);
            upperNext = false;
        }
        return builder.toString();
    }

    private BigDecimal round(Object value) {
        if (value == null) {
            return BigDecimal.ZERO;
        }
        if (value instanceof BigDecimal decimal) {
            return decimal.setScale(2, RoundingMode.HALF_UP);
        }
        if (value instanceof Number number) {
            return BigDecimal.valueOf(number.doubleValue()).setScale(2, RoundingMode.HALF_UP);
        }
        return new BigDecimal(String.valueOf(value)).setScale(2, RoundingMode.HALF_UP);
    }
}
