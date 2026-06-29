package com.example.housepredict.controller;

import com.example.housepredict.dto.ApiResponse;
import com.example.housepredict.dto.HouseQuery;
import com.example.housepredict.dto.PredictRequest;
import com.example.housepredict.entity.CrawlTask;
import com.example.housepredict.repository.CrawlTaskRepository;
import com.example.housepredict.repository.HouseRepository;
import com.example.housepredict.service.AnalysisService;
import com.example.housepredict.service.DemoDataService;
import com.example.housepredict.service.HouseMapper;
import com.example.housepredict.service.HouseService;
import com.example.housepredict.service.PredictionService;
import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HouseApiController {
    private final HouseService houseService;
    private final HouseRepository houseRepository;
    private final HouseMapper houseMapper;
    private final AnalysisService analysisService;
    private final PredictionService predictionService;
    private final CrawlTaskRepository crawlTaskRepository;
    private final DemoDataService demoDataService;

    public HouseApiController(HouseService houseService, HouseRepository houseRepository, HouseMapper houseMapper, AnalysisService analysisService, PredictionService predictionService, CrawlTaskRepository crawlTaskRepository, DemoDataService demoDataService) {
        this.houseService = houseService;
        this.houseRepository = houseRepository;
        this.houseMapper = houseMapper;
        this.analysisService = analysisService;
        this.predictionService = predictionService;
        this.crawlTaskRepository = crawlTaskRepository;
        this.demoDataService = demoDataService;
    }

    @GetMapping("/api/houses/")
    public ApiResponse<Map<String, Object>> houses(
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
            @RequestParam(defaultValue = "10", name = "page_size") int pageSize) {
        HouseQuery query = new HouseQuery(city, district, roomType, decoration, minPrice, maxPrice, minArea, maxArea, sort, page, pageSize);
        var housePage = houseService.findHouses(query, 100);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("total", housePage.getTotalElements());
        data.put("page", housePage.getNumber() + 1);
        data.put("page_size", housePage.getSize());
        data.put("items", housePage.getContent().stream().map(houseMapper::toMap).toList());
        return ApiResponse.ok(data);
    }

    @GetMapping("/api/houses/{houseId}/")
    public ResponseEntity<ApiResponse<Map<String, Object>>> houseDetail(@PathVariable Long houseId) {
        return houseRepository.findWithCityAndDistrictById(houseId)
                .map(house -> ResponseEntity.ok(ApiResponse.ok(houseMapper.toMap(house))))
                .orElseGet(() -> ResponseEntity.status(404).body(ApiResponse.<Map<String, Object>>error(404, "House not found")));
    }

    @GetMapping("/api/statistics/overview/")
    public ApiResponse<Map<String, Object>> overview() {
        return ApiResponse.ok(analysisService.overview());
    }

    @GetMapping("/api/statistics/province/")
    public ApiResponse<Map<String, Object>> province() {
        return ApiResponse.ok(analysisService.provinceStats());
    }

    @GetMapping("/api/statistics/city/")
    public ResponseEntity<ApiResponse<Map<String, Object>>> city(@RequestParam(required = false, name = "city_id") Long cityId) {
        if (cityId == null) {
            return ResponseEntity.badRequest().body(ApiResponse.<Map<String, Object>>error(400, "city_id 参数无效"));
        }
        return ResponseEntity.ok(ApiResponse.ok(analysisService.cityStats(cityId)));
    }

    @PostMapping("/api/predict/price/")
    public ApiResponse<?> predict(@RequestBody(required = false) PredictRequest request) {
        return ApiResponse.ok(predictionService.predict(request == null ? new PredictRequest(null, null, null, null, null, null, null, null) : request));
    }

    @GetMapping("/api/admin/crawl-tasks/")
    public ApiResponse<Map<String, Object>> crawlTasks() {
        return ApiResponse.ok(Map.of("items", crawlTaskRepository.findTop100ByOrderByCreatedAtDesc()));
    }

    @PostMapping("/api/admin/crawl-tasks/")
    public ApiResponse<Map<String, Object>> createCrawlTask(@RequestBody(required = false) Map<String, Object> body) {
        String city = value(body, "target_city", "济南");
        String district = value(body, "target_district", "");
        int pages = intValue(body, "page_count", 1);
        CrawlTask task = demoDataService.runDemoCrawler(city, district, pages);
        return ApiResponse.ok(Map.of("id", task.getId(), "status", task.getStatus()));
    }

    private String value(Map<String, Object> body, String key, String defaultValue) {
        if (body == null || body.get(key) == null) {
            return defaultValue;
        }
        String value = String.valueOf(body.get(key));
        return value.isBlank() ? defaultValue : value;
    }

    private int intValue(Map<String, Object> body, String key, int defaultValue) {
        try {
            return body == null || body.get(key) == null ? defaultValue : Integer.parseInt(String.valueOf(body.get(key)));
        } catch (NumberFormatException ex) {
            return defaultValue;
        }
    }
}
