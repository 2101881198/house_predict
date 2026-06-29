package com.example.housepredict.service;

import com.example.housepredict.entity.City;
import com.example.housepredict.entity.House;
import com.example.housepredict.repository.CityRepository;
import com.example.housepredict.repository.HouseRepository;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
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
    public Map<String, Object> overview() {
        List<House> houses = houseRepository.findAll();
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("total_houses", houses.size());
        data.put("city_count", cityRepository.count());
        data.put("avg_total_price", avg(houses.stream().map(House::getTotalPrice).toList()));
        data.put("avg_unit_price", avg(houses.stream().map(House::getUnitPrice).toList()));
        data.put("city_distribution", cityDistribution(houses));
        data.put("hot_districts", hotDistricts(houses));
        data.put("city_price_rankings", cityPriceRankings(houses));
        data.put("map_points", mapPoints(houses));
        return data;
    }

    @Transactional(readOnly = true)
    public Map<String, Object> provinceStats() {
        return Map.of("cities", cityDistribution(houseRepository.findAll()));
    }

    @Transactional(readOnly = true)
    public Map<String, Object> cityStats(Long cityId) {
        City city = cityRepository.findById(cityId).orElseThrow();
        List<House> houses = houseRepository.findAll().stream()
                .filter(house -> house.getCity().getId().equals(cityId))
                .toList();
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("city", Map.of("id", city.getId(), "name", city.getName()));
        data.put("summary", Map.of(
                "total_houses", houses.size(),
                "district_count", houses.stream().map(h -> h.getDistrict().getId()).distinct().count(),
                "avg_total_price", avg(houses.stream().map(House::getTotalPrice).toList()),
                "avg_unit_price", avg(houses.stream().map(House::getUnitPrice).toList())
        ));
        data.put("districts", houses.stream()
                .collect(Collectors.groupingBy(h -> h.getDistrict().getName()))
                .entrySet()
                .stream()
                .map(entry -> {
                    List<House> rows = entry.getValue();
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("id", rows.get(0).getDistrict().getId());
                    row.put("name", entry.getKey());
                    row.put("count", rows.size());
                    row.put("avg_total_price", avg(rows.stream().map(House::getTotalPrice).toList()));
                    row.put("avg_unit_price", avg(rows.stream().map(House::getUnitPrice).toList()));
                    return row;
                })
                .sorted(Comparator.comparing(row -> -((Integer) row.get("count"))))
                .toList());
        return data;
    }

    @Transactional(readOnly = true)
    public List<Map<String, Object>> priceBuckets(Long cityId) {
        List<House> houses = scoped(cityId);
        return List.of(
                bucket("100万以下", houses, null, BigDecimal.valueOf(100)),
                bucket("100-150万", houses, BigDecimal.valueOf(100), BigDecimal.valueOf(150)),
                bucket("150-200万", houses, BigDecimal.valueOf(150), BigDecimal.valueOf(200)),
                bucket("200-300万", houses, BigDecimal.valueOf(200), BigDecimal.valueOf(300)),
                bucket("300万以上", houses, BigDecimal.valueOf(300), null)
        );
    }

    @Transactional(readOnly = true)
    public List<Map<String, Object>> areaBuckets(Long cityId) {
        List<House> houses = scoped(cityId);
        return List.of(
                bucketByArea("60㎡以下", houses, null, BigDecimal.valueOf(60)),
                bucketByArea("60-90㎡", houses, BigDecimal.valueOf(60), BigDecimal.valueOf(90)),
                bucketByArea("90-120㎡", houses, BigDecimal.valueOf(90), BigDecimal.valueOf(120)),
                bucketByArea("120-150㎡", houses, BigDecimal.valueOf(120), BigDecimal.valueOf(150)),
                bucketByArea("150㎡以上", houses, BigDecimal.valueOf(150), null)
        );
    }

    @Transactional(readOnly = true)
    public List<Map<String, Object>> roomTypeDistribution(Long cityId) {
        return groupCount(scoped(cityId), House::getRoomType, "room_type");
    }

    @Transactional(readOnly = true)
    public List<Map<String, Object>> decorationDistribution(Long cityId) {
        return groupCount(scoped(cityId).stream().filter(h -> hasText(h.getDecoration())).toList(), House::getDecoration, "decoration");
    }

    private List<House> scoped(Long cityId) {
        List<House> houses = houseRepository.findAll();
        if (cityId == null) {
            return houses;
        }
        return houses.stream().filter(house -> house.getCity().getId().equals(cityId)).toList();
    }

    private List<Map<String, Object>> cityDistribution(List<House> houses) {
        return houses.stream()
                .collect(Collectors.groupingBy(h -> h.getCity().getName()))
                .entrySet()
                .stream()
                .map(entry -> {
                    List<House> rows = entry.getValue();
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("city", entry.getKey());
                    row.put("name", entry.getKey());
                    row.put("count", rows.size());
                    row.put("avg_total_price", avg(rows.stream().map(House::getTotalPrice).toList()));
                    row.put("avg_unit_price", avg(rows.stream().map(House::getUnitPrice).toList()));
                    row.put("max_total_price", max(rows.stream().map(House::getTotalPrice).toList()));
                    row.put("min_total_price", min(rows.stream().map(House::getTotalPrice).toList()));
                    return row;
                })
                .sorted(Comparator.comparing(row -> -((Integer) row.get("count"))))
                .toList();
    }

    private List<Map<String, Object>> hotDistricts(List<House> houses) {
        return houses.stream()
                .collect(Collectors.groupingBy(h -> h.getCity().getName() + "|" + h.getDistrict().getName()))
                .entrySet()
                .stream()
                .map(entry -> {
                    List<House> rows = entry.getValue();
                    String[] names = entry.getKey().split("\\|", 2);
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("city", names[0]);
                    row.put("district", names[1]);
                    row.put("count", rows.size());
                    row.put("avg_unit_price", avg(rows.stream().map(House::getUnitPrice).toList()));
                    return row;
                })
                .sorted(Comparator.comparing(row -> -((Integer) row.get("count"))))
                .limit(8)
                .toList();
    }

    private List<Map<String, Object>> cityPriceRankings(List<House> houses) {
        return cityDistribution(houses).stream()
                .sorted(Comparator.comparing(row -> (BigDecimal) row.get("avg_unit_price"), Comparator.reverseOrder()))
                .limit(10)
                .toList();
    }

    private List<Map<String, Object>> mapPoints(List<House> houses) {
        return houses.stream()
                .filter(h -> h.getLongitude() != null && h.getLatitude() != null)
                .limit(200)
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

    private List<Map<String, Object>> groupCount(List<House> houses, java.util.function.Function<House, String> getter, String key) {
        return houses.stream()
                .filter(house -> hasText(getter.apply(house)))
                .collect(Collectors.groupingBy(getter))
                .entrySet()
                .stream()
                .map(entry -> {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put(key, entry.getKey());
                    row.put("count", entry.getValue().size());
                    return row;
                })
                .sorted(Comparator.comparing(row -> -((Integer) row.get("count"))))
                .toList();
    }

    private Map<String, Object> bucket(String label, List<House> houses, BigDecimal min, BigDecimal max) {
        long count = houses.stream().filter(h -> inRange(h.getTotalPrice(), min, max)).count();
        return Map.of("label", label, "count", count);
    }

    private Map<String, Object> bucketByArea(String label, List<House> houses, BigDecimal min, BigDecimal max) {
        long count = houses.stream().filter(h -> inRange(h.getArea(), min, max)).count();
        return Map.of("label", label, "count", count);
    }

    private boolean inRange(BigDecimal value, BigDecimal min, BigDecimal max) {
        return (min == null || value.compareTo(min) >= 0) && (max == null || value.compareTo(max) < 0);
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
