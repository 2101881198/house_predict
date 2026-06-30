package com.example.housepredict.controller;

import com.example.housepredict.service.LookupService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class AdminPageController {
    private final LookupService lookupService;

    public AdminPageController(LookupService lookupService) {
        this.lookupService = lookupService;
    }

    // 管理后台首页：展示统计摘要、最近房源、采集任务和预测记录。
    @GetMapping("/admin/")
    public String admin(Model model) {
        model.addAttribute("cityCount", lookupService.cityCount());
        model.addAttribute("houseCount", lookupService.houseCount());
        model.addAttribute("cities", lookupService.findAllCities());
        model.addAttribute("recentHouses", lookupService.recentHouses(20));
        model.addAttribute("crawlTasks", lookupService.recentCrawlTasks());
        model.addAttribute("recentPredictions", lookupService.recentPredictions(10));
        return "houses/admin";
    }
}
