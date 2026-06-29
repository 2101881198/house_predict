package com.example.housepredict.config;

import com.example.housepredict.service.DemoDataService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class DemoDataLoader implements CommandLineRunner {
    private final DemoDataService demoDataService;
    private final boolean seedDemoData;

    public DemoDataLoader(DemoDataService demoDataService, @Value("${app.seed-demo-data:false}") boolean seedDemoData) {
        this.demoDataService = demoDataService;
        this.seedDemoData = seedDemoData;
    }

    @Override
    public void run(String... args) {
        if (seedDemoData) {
            demoDataService.seedDemoData();
        }
    }
}
