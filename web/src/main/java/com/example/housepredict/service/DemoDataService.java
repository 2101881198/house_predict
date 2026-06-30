package com.example.housepredict.service;

import com.example.housepredict.entity.CrawlTask;

public interface DemoDataService {
    int seedDemoData();

    CrawlTask runDemoCrawler(String city, String district, int pages);
}
