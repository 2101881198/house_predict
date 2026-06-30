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
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
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
@Tag(name = "房源与统计接口", description = "房源查询、统计分析、价格预测和后台演示任务接口")
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

    // 公开 API：按城市、区县、户型、装修、价格、面积等条件分页查询房源。
    @Operation(summary = "分页查询房源", description = "支持按城市、区县、户型、装修、总价区间、面积区间和排序条件查询房源。")
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

    // 公开 API：根据房源 ID 查询单套房源详情，找不到时返回 404。
    @Operation(summary = "查询房源详情", description = "根据房源 ID 返回单套房源的标题、城市、区县、价格、面积、户型等信息。")
    @GetMapping("/api/houses/{houseId}/")
    public ResponseEntity<ApiResponse<Map<String, Object>>> houseDetail(@PathVariable Long houseId) {
        return houseRepository.findWithCityAndDistrictById(houseId)
                .map(house -> ResponseEntity.ok(ApiResponse.ok(houseMapper.toMap(house))))
                .orElseGet(() -> ResponseEntity.status(404).body(ApiResponse.<Map<String, Object>>error(404, "House not found")));
    }

    // 公开 API：首页总览统计，返回房源总数、均价、城市分布等数据。
    @Operation(summary = "首页总览统计", description = "返回房源总数、城市数量、平均总价、平均单价、城市分布和趋势等总览数据。")
    @GetMapping("/api/statistics/overview/")
    public ApiResponse<Map<String, Object>> overview() {
        return ApiResponse.ok(analysisService.overview());
    }

    // 公开 API：省级统计，返回各城市房源数量和价格对比。
    @Operation(summary = "省级统计", description = "返回山东省各城市的房源数量、平均总价、平均单价、最高价和最低价。")
    @GetMapping("/api/statistics/province/")
    public ApiResponse<Map<String, Object>> province() {
        return ApiResponse.ok(analysisService.provinceStats());
    }

    // 公开 API：城市统计，必须传 city_id，返回城市摘要和区县统计。
    @Operation(summary = "城市统计", description = "根据 city_id 返回某个城市的摘要、区县分布和价格趋势。")
    @GetMapping("/api/statistics/city/")
    public ResponseEntity<ApiResponse<Map<String, Object>>> city(@RequestParam(required = false, name = "city_id") Long cityId) {
        if (cityId == null) {
            return ResponseEntity.badRequest().body(ApiResponse.<Map<String, Object>>error(400, "city_id 参数无效"));
        }
        return ResponseEntity.ok(ApiResponse.ok(analysisService.cityStats(cityId)));
    }

    // 公开 API：提交房屋特征进行价格预测，并保存一条预测记录。
    @Operation(summary = "房价预测", description = "提交城市、区县、面积、户型、楼层、朝向、装修和建造年份，返回参考总价和参考单价。")
    @PostMapping("/api/predict/price/")
    public ApiResponse<?> predict(@RequestBody(required = false) PredictRequest request) {
        return ApiResponse.ok(predictionService.predict(request == null ? new PredictRequest(null, null, null, null, null, null, null, null) : request));
    }

    // 后台 API：查询最近的演示采集任务记录，需要管理员登录。
    @Operation(summary = "查询演示采集任务", description = "管理员登录后查询最近 100 条演示采集任务记录。")
    @GetMapping("/api/admin/crawl-tasks/")
    public ApiResponse<Map<String, Object>> crawlTasks() {
        return ApiResponse.ok(Map.of("items", crawlTaskRepository.findTop100ByOrderByCreatedAtDesc()));
    }

    // 后台 API：创建演示采集任务并导入内置示例数据，需要管理员登录。
    @Operation(summary = "创建演示采集任务", description = "管理员登录后创建一条演示采集任务，并导入内置示例房源数据。")
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
