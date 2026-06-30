package com.example.housepredict.controller;

import com.example.housepredict.service.LookupService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
@Tag(name = "后台页面路由", description = "管理员后台页面入口。")
public class AdminPageController {
    private final LookupService lookupService;

    public AdminPageController(LookupService lookupService) {
        this.lookupService = lookupService;
    }

    // 管理后台首页：展示统计摘要、最近房源、采集任务和预测记录。
    @Operation(summary = "管理后台首页", description = "展示城市数量、房源数量、最近房源、采集任务和预测记录。")
    @GetMapping("/admin/")
    public String admin(@Parameter(hidden = true) Model model) {
        model.addAttribute("cityCount", lookupService.cityCount());
        model.addAttribute("houseCount", lookupService.houseCount());
        model.addAttribute("cities", lookupService.findAllCities());
        model.addAttribute("recentHouses", lookupService.recentHouses(20));
        model.addAttribute("crawlTasks", lookupService.recentCrawlTasks());
        model.addAttribute("recentPredictions", lookupService.recentPredictions(10));
        return "houses/admin";
    }
}
