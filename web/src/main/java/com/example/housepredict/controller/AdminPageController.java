package com.example.housepredict.controller;

import com.example.housepredict.repository.CityRepository;
import com.example.housepredict.repository.CrawlTaskRepository;
import com.example.housepredict.repository.HouseRepository;
import com.example.housepredict.repository.PredictResultRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class AdminPageController {
    private final CityRepository cityRepository;
    private final HouseRepository houseRepository;
    private final CrawlTaskRepository crawlTaskRepository;
    private final PredictResultRepository predictResultRepository;

    public AdminPageController(CityRepository cityRepository, HouseRepository houseRepository, CrawlTaskRepository crawlTaskRepository, PredictResultRepository predictResultRepository) {
        this.cityRepository = cityRepository;
        this.houseRepository = houseRepository;
        this.crawlTaskRepository = crawlTaskRepository;
        this.predictResultRepository = predictResultRepository;
    }

    @GetMapping("/admin/")
    public String admin(Model model) {
        model.addAttribute("cityCount", cityRepository.count());
        model.addAttribute("houseCount", houseRepository.count());
        model.addAttribute("cities", cityRepository.findAll());
        model.addAttribute("recentHouses", houseRepository.findTop20ByOrderByCreatedAtDescIdDesc());
        model.addAttribute("crawlTasks", crawlTaskRepository.findTop100ByOrderByCreatedAtDesc());
        model.addAttribute("recentPredictions", predictResultRepository.findByOrderByPredictTimeDesc(PageRequest.of(0, 10)));
        return "houses/admin";
    }
}
