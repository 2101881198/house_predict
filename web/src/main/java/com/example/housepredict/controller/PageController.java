package com.example.housepredict.controller;

import com.example.housepredict.dto.HouseQuery;
import com.example.housepredict.repository.CityRepository;
import com.example.housepredict.repository.HouseRepository;
import com.example.housepredict.repository.PredictResultRepository;
import com.example.housepredict.service.AnalysisService;
import com.example.housepredict.service.HouseService;
import java.math.BigDecimal;
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
    private final PredictResultRepository predictResultRepository;

    public PageController(AnalysisService analysisService, HouseService houseService, HouseRepository houseRepository, CityRepository cityRepository, PredictResultRepository predictResultRepository) {
        this.analysisService = analysisService;
        this.houseService = houseService;
        this.houseRepository = houseRepository;
        this.cityRepository = cityRepository;
        this.predictResultRepository = predictResultRepository;
    }

    @GetMapping("/")
    public String dashboard(Model model) {
        model.addAttribute("overview", analysisService.overview());
        model.addAttribute("priceBuckets", analysisService.priceBuckets(null));
        model.addAttribute("areaBuckets", analysisService.areaBuckets(null));
        model.addAttribute("roomTypes", analysisService.roomTypeDistribution(null));
        model.addAttribute("decorations", analysisService.decorationDistribution(null));
        model.addAttribute("cities", cityRepository.findAll());
        return "houses/dashboard";
    }

    @GetMapping("/province/")
    public String province(Model model) {
        model.addAttribute("stats", analysisService.provinceStats());
        model.addAttribute("priceBuckets", analysisService.priceBuckets(null));
        model.addAttribute("areaBuckets", analysisService.areaBuckets(null));
        model.addAttribute("roomTypes", analysisService.roomTypeDistribution(null));
        return "houses/province";
    }

    @GetMapping("/cities/{cityId}/")
    public String city(@PathVariable Long cityId, Model model) {
        model.addAttribute("stats", analysisService.cityStats(cityId));
        model.addAttribute("priceBuckets", analysisService.priceBuckets(cityId));
        model.addAttribute("areaBuckets", analysisService.areaBuckets(cityId));
        model.addAttribute("roomTypes", analysisService.roomTypeDistribution(cityId));
        model.addAttribute("decorations", analysisService.decorationDistribution(cityId));
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
        model.addAttribute("cities", cityRepository.findAll());
        model.addAttribute("recentPredictions", predictResultRepository.findByOrderByPredictTimeDesc(PageRequest.of(0, 10)));
        return "houses/predict";
    }
}
