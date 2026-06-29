package com.example.housepredict.controller;

import com.example.housepredict.entity.District;
import com.example.housepredict.dto.HouseQuery;
import com.example.housepredict.repository.CityRepository;
import com.example.housepredict.repository.DistrictRepository;
import com.example.housepredict.repository.HouseRepository;
import com.example.housepredict.repository.PredictResultRepository;
import com.example.housepredict.service.AnalysisService;
import com.example.housepredict.service.HouseService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.util.Map;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class PageController {
    private final AnalysisService analysisService;
    private final HouseService houseService;
    private final HouseRepository houseRepository;
    private final CityRepository cityRepository;
    private final DistrictRepository districtRepository;
    private final PredictResultRepository predictResultRepository;
    private final ObjectMapper objectMapper;

    public PageController(AnalysisService analysisService, HouseService houseService, HouseRepository houseRepository, CityRepository cityRepository, DistrictRepository districtRepository, PredictResultRepository predictResultRepository, ObjectMapper objectMapper) {
        this.analysisService = analysisService;
        this.houseService = houseService;
        this.houseRepository = houseRepository;
        this.cityRepository = cityRepository;
        this.districtRepository = districtRepository;
        this.predictResultRepository = predictResultRepository;
        this.objectMapper = objectMapper;
    }

    @GetMapping("/")
    public String dashboard(Model model) {
        var overview = analysisService.overview();
        var priceBuckets = analysisService.priceBuckets(null);
        var areaBuckets = analysisService.areaBuckets(null);
        var roomTypes = analysisService.roomTypeDistribution(null);
        var decorations = analysisService.decorationDistribution(null);
        model.addAttribute("overview", overview);
        model.addAttribute("priceBuckets", priceBuckets);
        model.addAttribute("areaBuckets", areaBuckets);
        model.addAttribute("roomTypes", roomTypes);
        model.addAttribute("decorations", decorations);
        model.addAttribute("overviewJson", toJson(overview));
        model.addAttribute("priceBucketsJson", toJson(priceBuckets));
        model.addAttribute("areaBucketsJson", toJson(areaBuckets));
        model.addAttribute("roomTypesJson", toJson(roomTypes));
        model.addAttribute("decorationsJson", toJson(decorations));
        model.addAttribute("cities", cityRepository.findAll());
        return "houses/dashboard";
    }

    @GetMapping("/province/")
    public String province(Model model) {
        var stats = analysisService.provinceStats();
        var priceBuckets = analysisService.priceBuckets(null);
        var areaBuckets = analysisService.areaBuckets(null);
        var roomTypes = analysisService.roomTypeDistribution(null);
        var mapMeta = Map.of("province_map_name", "shandong", "city_map_base_url", "/houses/maps/");
        model.addAttribute("stats", stats);
        model.addAttribute("priceBuckets", priceBuckets);
        model.addAttribute("areaBuckets", areaBuckets);
        model.addAttribute("roomTypes", roomTypes);
        model.addAttribute("statsJson", toJson(stats));
        model.addAttribute("priceBucketsJson", toJson(priceBuckets));
        model.addAttribute("areaBucketsJson", toJson(areaBuckets));
        model.addAttribute("roomTypesJson", toJson(roomTypes));
        model.addAttribute("mapMetaJson", toJson(mapMeta));
        return "houses/province";
    }

    @GetMapping("/cities/{cityId}/")
    public String city(@PathVariable Long cityId, Model model) {
        var stats = analysisService.cityStats(cityId);
        var priceBuckets = analysisService.priceBuckets(cityId);
        var areaBuckets = analysisService.areaBuckets(cityId);
        var roomTypes = analysisService.roomTypeDistribution(cityId);
        var decorations = analysisService.decorationDistribution(cityId);
        var cityName = String.valueOf(((Map<?, ?>) stats.get("city")).get("name"));
        var mapMeta = Map.of("city_name", cityName, "city_map_file", cityMapFile(cityName), "city_map_base_url", "/houses/maps/");
        model.addAttribute("stats", stats);
        model.addAttribute("priceBuckets", priceBuckets);
        model.addAttribute("areaBuckets", areaBuckets);
        model.addAttribute("roomTypes", roomTypes);
        model.addAttribute("decorations", decorations);
        model.addAttribute("statsJson", toJson(stats));
        model.addAttribute("priceBucketsJson", toJson(priceBuckets));
        model.addAttribute("areaBucketsJson", toJson(areaBuckets));
        model.addAttribute("roomTypesJson", toJson(roomTypes));
        model.addAttribute("decorationsJson", toJson(decorations));
        model.addAttribute("mapMetaJson", toJson(mapMeta));
        return "houses/city";
    }

    @GetMapping("/houses/")
    public String houses(
            @RequestParam(required = false) String city,
            @RequestParam(required = false) String district,
            @RequestParam(required = false, name = "room_type") String roomType,
            @RequestParam(required = false) String decoration,
            @RequestParam(required = false, name = "min_price") BigDecimal minPrice,
            @RequestParam(required = false, name = "max_price") BigDecimal maxPrice,
            @RequestParam(required = false, name = "min_area") BigDecimal minArea,
            @RequestParam(required = false, name = "max_area") BigDecimal maxArea,
            @RequestParam(required = false) String sort,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10", name = "page_size") int pageSize,
            Model model) {
        HouseQuery query = new HouseQuery(city, district, roomType, decoration, minPrice, maxPrice, minArea, maxArea, sort, page, pageSize);
        model.addAttribute("page", houseService.findHouses(query, 50));
        model.addAttribute("cities", cityRepository.findAll());
        model.addAttribute("roomTypes", houseRepository.findRoomTypes());
        return "houses/house_list";
    }

    @GetMapping("/houses/{houseId}/")
    public String houseDetail(@PathVariable Long houseId, Model model) {
        var house = houseRepository.findWithCityAndDistrictById(houseId).orElseThrow();
        model.addAttribute("house", house);
        model.addAttribute("similarHouses", houseRepository.findByDistrictAndIdNotOrderByCrawlTimeDescIdDesc(house.getDistrict(), house.getId(), PageRequest.of(0, 6)));
        model.addAttribute("districtAvgUnitPrice", houseRepository.avgUnitPriceByDistrict(house.getDistrict()));
        return "houses/house_detail";
    }

    @GetMapping("/predict/")
    public String predict(Model model) {
        var cities = cityRepository.findAll();
        var cityDistricts = cities.stream()
                .map(city -> Map.of(
                        "name", city.getName(),
                        "districts", districtRepository.findByCityOrderByName(city).stream()
                                .map(District::getName)
                                .toList()))
                .toList();
        model.addAttribute("cities", cities);
        model.addAttribute("cityDistrictsJson", toJson(cityDistricts));
        model.addAttribute("recentPredictions", predictResultRepository.findByOrderByPredictTimeDesc(PageRequest.of(0, 10)));
        return "houses/predict";
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException ex) {
            return "{}";
        }
    }

    private String cityMapFile(String cityName) {
        return switch (cityName) {
            case "济南" -> "jinan.json";
            case "青岛" -> "qingdao.json";
            case "烟台" -> "yantai.json";
            case "潍坊" -> "weifang.json";
            case "威海" -> "weihai.json";
            case "菏泽" -> "heze.json";
            case "临沂" -> "linyi.json";
            case "淄博" -> "zibo.json";
            case "济宁" -> "jining.json";
            case "泰安" -> "taian.json";
            default -> "";
        };
    }
}
