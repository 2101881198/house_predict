package com.example.housepredict.service;

import java.util.List;
import java.util.Map;

public interface AnalysisService {
    Map<String, Object> overview();

    Map<String, Object> provinceStats();

    Map<String, Object> cityStats(Long cityId);

    List<Map<String, Object>> priceBuckets(Long cityId);

    List<Map<String, Object>> areaBuckets(Long cityId);

    List<Map<String, Object>> roomTypeDistribution(Long cityId);

    List<Map<String, Object>> decorationDistribution(Long cityId);
}
