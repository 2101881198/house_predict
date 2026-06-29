package com.example.housepredict.service;

import com.example.housepredict.entity.City;
import com.example.housepredict.entity.House;
import com.example.housepredict.repository.CityRepository;
import com.example.housepredict.repository.HouseRepository;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AnalysisService {
    private final HouseRepository houseRepository;
    private final CityRepository cityRepository;

    public AnalysisService(HouseRepository houseRepository, CityRepository cityRepository) {
        this.houseRepository = houseRepository;
        this.cityRepository = cityRepository;
    }

    @Transactional(readOnly = true)
    @Cacheable("overview")
    public Map<String, Object> overview() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("total_houses", houseRepository.count());
        data.put("city_count", cityRepository.count());
        data.put("avg_total_price", round(houseRepository.avgTotalPrice()));
        data.put("avg_unit_price", round(houseRepository.avgUnitPrice()));
        List<Map<String, Object>> cityDistribution = cityDistribution();
        data.put("city_distribution", cityDistribution);
        data.put("hot_districts", hotDistricts());
        data.put("city_price_rankings", cityPriceRankings(cityDistribution));
        data.put("trend", priceTrend(null));
        data.put("city_price_trends", cityPriceTrends());
        data.put("map_points", mapPoints());
        return data;
    }

    @Transactional(readOnly = true)
    @Cacheable("provinceStats")
    public Map<String, Object> provinceStats() {
        return Map.of("cities", cityDistribution());
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "cityStats", key = "#cityId")
    public Map<String, Object> cityStats(Long cityId) {
        City city = cityRepository.findById(cityId).orElseThrow();
        List<Map<String, Object>> districts = districtRows(cityId);
        long totalHouses = districts.stream().mapToLong(row -> ((Number) row.get("count")).longValue()).sum();
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

    @Transactional(readOnly = true)
    @Cacheable(value = "priceBuckets", key = "#cityId == null ? 'all' : #cityId")
    public List<Map<String, Object>> priceBuckets(Long cityId) {
        return List.of(
                bucket("100万以下", houseRepository.countByPriceBucket(cityId, null, BigDecimal.valueOf(100))),
                bucket("100-150万", houseRepository.countByPriceBucket(cityId, BigDecimal.valueOf(100), BigDecimal.valueOf(150))),
                bucket("150-200万", houseRepository.countByPriceBucket(cityId, BigDecimal.valueOf(150), BigDecimal.valueOf(200))),
                bucket("200-300万", houseRepository.countByPriceBucket(cityId, BigDecimal.valueOf(200), BigDecimal.valueOf(300))),
                bucket("300万以上", houseRepository.countByPriceBucket(cityId, BigDecimal.valueOf(300), null))
        );
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "areaBuckets", key = "#cityId == null ? 'all' : #cityId")
    public List<Map<String, Object>> areaBuckets(Long cityId) {
        return List.of(
                bucket("60㎡以下", houseRepository.countByAreaBucket(cityId, null, BigDecimal.valueOf(60))),
                bucket("60-90㎡", houseRepository.countByAreaBucket(cityId, BigDecimal.valueOf(60), BigDecimal.valueOf(90))),
                bucket("90-120㎡", houseRepository.countByAreaBucket(cityId, BigDecimal.valueOf(90), BigDecimal.valueOf(120))),
                bucket("120-150㎡", houseRepository.countByAreaBucket(cityId, BigDecimal.valueOf(120), BigDecimal.valueOf(150))),
                bucket("150㎡以上", houseRepository.countByAreaBucket(cityId, BigDecimal.valueOf(150), null))
        );
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "roomTypes", key = "#cityId == null ? 'all' : #cityId")
    public List<Map<String, Object>> roomTypeDistribution(Long cityId) {
        return groupedRows(cityId == null ? houseRepository.roomTypeRows() : houseRepository.roomTypeRowsByCity(cityId), "room_type");
    }

    @Transactional(readOnly = true)
    @Cacheable(value = "decorations", key = "#cityId == null ? 'all' : #cityId")
    public List<Map<String, Object>> decorationDistribution(Long cityId) {
        return groupedRows(cityId == null ? houseRepository.decorationRows() : houseRepository.decorationRowsByCity(cityId), "decoration");
    }

    private List<Map<String, Object>> cityDistribution() {
        return houseRepository.cityDistributionRows().stream()
                .map(values -> {
                    Map<String, Object> data = new LinkedHashMap<>();
                    data.put("id", values[0]);
                    data.put("city", values[1]);
                    data.put("name", values[1]);
                    data.put("count", ((Number) values[2]).longValue());
                    data.put("avg_total_price", round(values[3]));
                    data.put("avg_unit_price", round(values[4]));
                    data.put("max_total_price", round(values[5]));
                    data.put("min_total_price", round(values[6]));
                    return data;
                })
                .toList();
    }

    private List<Map<String, Object>> districtRows(Long cityId) {
        return houseRepository.districtRowsByCity(cityId).stream()
                .map(values -> {
                    Map<String, Object> data = new LinkedHashMap<>();
                    data.put("id", values[0]);
                    data.put("name", values[1]);
                    data.put("count", ((Number) values[2]).longValue());
                    data.put("avg_total_price", round(values[3]));
                    data.put("avg_unit_price", round(values[4]));
                    return data;
                })
                .toList();
    }

    private List<Map<String, Object>> hotDistricts() {
        return houseRepository.hotDistrictRows(PageRequest.of(0, 8)).stream()
                .map(row -> {
                    Map<String, Object> data = new LinkedHashMap<>();
                    data.put("city", row[0]);
                    data.put("district", row[1]);
                    data.put("count", ((Number) row[2]).longValue());
                    data.put("avg_unit_price", round(row[3]));
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
        List<Object[]> rows = cityId == null ? houseRepository.trendRows() : houseRepository.trendRowsByCity(cityId);
        return rows.stream()
                .map(row -> trendRow(row[0], row[1], row[2]))
                .toList();
    }

    private List<Map<String, Object>> cityPriceTrends() {
        return houseRepository.cityTrendRows().stream()
                .collect(Collectors.groupingBy(row -> String.valueOf(row[0]), LinkedHashMap::new, Collectors.toList()))
                .entrySet()
                .stream()
                .map(entry -> {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("city", entry.getKey());
                    row.put("trend", entry.getValue().stream().map(item -> trendRow(item[1], item[2], item[3])).toList());
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
        return houseRepository.mapPointRows(PageRequest.of(0, 200)).stream()
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

    private List<Map<String, Object>> groupedRows(List<Object[]> rows, String key) {
        return rows.stream()
                .map(values -> {
                    Map<String, Object> data = new LinkedHashMap<>();
                    data.put(key, values[0]);
                    data.put("count", ((Number) values[1]).longValue());
                    return data;
                })
                .toList();
    }

    private Map<String, Object> bucket(String label, long count) {
        return Map.of("label", label, "count", count);
    }

    private BigDecimal weightedAverage(List<Map<String, Object>> rows, String key) {
        long total = rows.stream().mapToLong(row -> ((Number) row.get("count")).longValue()).sum();
        if (total == 0) {
            return BigDecimal.ZERO;
        }
        BigDecimal weighted = rows.stream()
                .map(row -> ((BigDecimal) row.get(key)).multiply(BigDecimal.valueOf(((Number) row.get("count")).longValue())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        return weighted.divide(BigDecimal.valueOf(total), 2, RoundingMode.HALF_UP);
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

    private BigDecimal avg(List<BigDecimal> values) {
        if (values.isEmpty()) {
            return BigDecimal.ZERO;
        }
        BigDecimal sum = values.stream().reduce(BigDecimal.ZERO, BigDecimal::add);
        return sum.divide(BigDecimal.valueOf(values.size()), 2, RoundingMode.HALF_UP);
    }

    private BigDecimal max(List<BigDecimal> values) {
        return values.stream().max(BigDecimal::compareTo).orElse(BigDecimal.ZERO);
    }

    private BigDecimal min(List<BigDecimal> values) {
        return values.stream().min(BigDecimal::compareTo).orElse(BigDecimal.ZERO);
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}
