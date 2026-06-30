package com.example.housepredict.controller;

import com.example.housepredict.entity.City;
import com.example.housepredict.entity.District;
import com.example.housepredict.entity.House;
import com.example.housepredict.repository.CityRepository;
import com.example.housepredict.repository.DistrictRepository;
import com.example.housepredict.repository.HouseRepository;
import com.example.housepredict.service.DemoDataService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
public class AdminHouseController {
    private final CityRepository cityRepository;
    private final DistrictRepository districtRepository;
    private final HouseRepository houseRepository;
    private final DemoDataService demoDataService;

    public AdminHouseController(CityRepository cityRepository, DistrictRepository districtRepository, HouseRepository houseRepository, DemoDataService demoDataService) {
        this.cityRepository = cityRepository;
        this.districtRepository = districtRepository;
        this.houseRepository = houseRepository;
        this.demoDataService = demoDataService;
    }

    // 后台表单：新增房源，自动复用/创建城市区县，并根据总价和面积计算单价。
    @PostMapping("/admin/houses/")
    public String createHouse(
            @RequestParam String title,
            @RequestParam String city,
            @RequestParam String district,
            @RequestParam(name = "total_price") BigDecimal totalPrice,
            @RequestParam BigDecimal area,
            @RequestParam(name = "room_type", required = false, defaultValue = "") String roomType,
            @RequestParam(required = false, defaultValue = "") String floor,
            @RequestParam(required = false, defaultValue = "") String direction,
            @RequestParam(required = false, defaultValue = "") String decoration,
            @RequestParam(name = "build_year", required = false) Integer buildYear,
            @RequestParam(required = false, defaultValue = "") String address,
            RedirectAttributes redirectAttributes) {
        if (title.isBlank() || city.isBlank() || district.isBlank()) {
            redirectAttributes.addFlashAttribute("error", "标题、城市和区县不能为空");
            return "redirect:/admin/";
        }
        if (totalPrice.compareTo(BigDecimal.ZERO) <= 0 || area.compareTo(BigDecimal.ZERO) <= 0) {
            redirectAttributes.addFlashAttribute("error", "总价和面积必须大于 0");
            return "redirect:/admin/";
        }

        City cityEntity = cityRepository.findByName(city.trim()).orElseGet(() -> {
            City created = new City();
            created.setName(city.trim());
            return cityRepository.save(created);
        });
        District districtEntity = districtRepository.findByCityAndName(cityEntity, district.trim()).orElseGet(() -> {
            District created = new District();
            created.setCity(cityEntity);
            created.setName(district.trim());
            return districtRepository.save(created);
        });

        House house = new House();
        house.setTitle(title.trim());
        house.setCity(cityEntity);
        house.setDistrict(districtEntity);
        house.setTotalPrice(totalPrice);
        house.setArea(area);
        house.setUnitPrice(totalPrice.multiply(BigDecimal.valueOf(10000)).divide(area, 2, RoundingMode.HALF_UP));
        house.setRoomType(roomType.trim());
        house.setFloor(floor.trim());
        house.setDirection(direction.trim());
        house.setDecoration(decoration.trim());
        house.setBuildYear(buildYear);
        house.setAddress(address.isBlank() ? cityEntity.getName() + " " + districtEntity.getName() + " " + title.trim() : address.trim());
        house.setCrawlTime(LocalDateTime.now());
        houseRepository.save(house);

        redirectAttributes.addFlashAttribute("message", "房源添加成功：" + house.getTitle());
        return "redirect:/admin/";
    }

    // 后台表单：删除指定房源，删除后回到管理后台并显示操作结果。
    @PostMapping("/admin/houses/{houseId}/delete")
    public String deleteHouse(@PathVariable Long houseId, RedirectAttributes redirectAttributes) {
        if (!houseRepository.existsById(houseId)) {
            redirectAttributes.addFlashAttribute("error", "房源不存在，无法删除");
            return "redirect:/admin/";
        }
        houseRepository.deleteById(houseId);
        redirectAttributes.addFlashAttribute("message", "房源已删除");
        return "redirect:/admin/";
    }

    // 后台表单：创建演示采集任务，导入内置示例数据，不访问真实网站。
    @PostMapping("/admin/crawl-tasks/")
    public String createCrawlTask(
            @RequestParam(name = "target_city", defaultValue = "济南") String targetCity,
            @RequestParam(name = "target_district", defaultValue = "") String targetDistrict,
            @RequestParam(name = "page_count", defaultValue = "1") int pageCount,
            RedirectAttributes redirectAttributes) {
        demoDataService.runDemoCrawler(targetCity, targetDistrict, Math.max(1, pageCount));
        redirectAttributes.addFlashAttribute("message", "演示爬取任务已创建");
        return "redirect:/admin/";
    }
}
