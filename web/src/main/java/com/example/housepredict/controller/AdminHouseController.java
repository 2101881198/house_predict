package com.example.housepredict.controller;

import com.example.housepredict.service.AdminHouseService;
import com.example.housepredict.service.DemoDataService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.math.BigDecimal;
import java.util.NoSuchElementException;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@Tag(name = "后台表单路由", description = "管理员后台中的房源新增、删除和演示采集表单提交。")
public class AdminHouseController {
    private final AdminHouseService adminHouseService;
    private final DemoDataService demoDataService;

    public AdminHouseController(AdminHouseService adminHouseService, DemoDataService demoDataService) {
        this.adminHouseService = adminHouseService;
        this.demoDataService = demoDataService;
    }

    // 后台表单：新增房源，自动复用/创建城市区县，并根据总价和面积计算单价。
    @Operation(summary = "新增房源", description = "后台提交房源表单，自动复用或创建城市区县，并根据总价和面积计算单价。")
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
            @Parameter(hidden = true) RedirectAttributes redirectAttributes) {
        try {
            String houseTitle = adminHouseService.createHouse(title, city, district, totalPrice, area, roomType, floor, direction, decoration, buildYear, address);
            redirectAttributes.addFlashAttribute("message", "房源添加成功：" + houseTitle);
        } catch (IllegalArgumentException ex) {
            redirectAttributes.addFlashAttribute("error", ex.getMessage());
        }
        return "redirect:/admin/";
    }

    // 后台表单：删除指定房源，删除后回到管理后台并显示操作结果。
    @Operation(summary = "删除房源", description = "后台根据房源 ID 删除指定房源。")
    @PostMapping("/admin/houses/{houseId}/delete")
    public String deleteHouse(@PathVariable Long houseId, @Parameter(hidden = true) RedirectAttributes redirectAttributes) {
        try {
            adminHouseService.deleteHouse(houseId);
            redirectAttributes.addFlashAttribute("message", "房源已删除");
        } catch (NoSuchElementException ex) {
            redirectAttributes.addFlashAttribute("error", ex.getMessage());
        }
        return "redirect:/admin/";
    }

    // 后台表单：创建演示采集任务，导入内置示例数据，不访问真实网站。
    @Operation(summary = "创建演示采集任务", description = "后台创建演示采集任务并导入内置示例数据，不访问真实网站。")
    @PostMapping("/admin/crawl-tasks/")
    public String createCrawlTask(
            @RequestParam(name = "target_city", defaultValue = "济南") String targetCity,
            @RequestParam(name = "target_district", defaultValue = "") String targetDistrict,
            @RequestParam(name = "page_count", defaultValue = "1") int pageCount,
            @Parameter(hidden = true) RedirectAttributes redirectAttributes) {
        demoDataService.runDemoCrawler(targetCity, targetDistrict, Math.max(1, pageCount));
        redirectAttributes.addFlashAttribute("message", "演示爬取任务已创建");
        return "redirect:/admin/";
    }
}
