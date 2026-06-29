package com.example.housepredict.service;

import com.example.housepredict.dto.PredictRequest;
import com.example.housepredict.dto.PredictResponse;
import com.example.housepredict.entity.PredictResult;
import com.example.housepredict.repository.HouseRepository;
import com.example.housepredict.repository.PredictResultRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class PredictionService {
    private static final BigDecimal DEFAULT_AREA = BigDecimal.valueOf(90);
    private static final BigDecimal DEFAULT_UNIT_PRICE = BigDecimal.valueOf(10000);

    private final HouseRepository houseRepository;
    private final PredictResultRepository predictResultRepository;
    private final ObjectMapper objectMapper;

    public PredictionService(HouseRepository houseRepository, PredictResultRepository predictResultRepository, ObjectMapper objectMapper) {
        this.houseRepository = houseRepository;
        this.predictResultRepository = predictResultRepository;
        this.objectMapper = objectMapper;
    }

    public PredictResponse predict(PredictRequest request) {
        BigDecimal area = normalizeArea(request.area());
        BigDecimal unitPrice = averageUnitPrice(request.city(), request.district());
        BigDecimal predictedPrice = unitPrice.multiply(area).divide(BigDecimal.valueOf(10000), 2, RoundingMode.HALF_UP);
        BigDecimal predictedUnitPrice = unitPrice.setScale(2, RoundingMode.HALF_UP);

        PredictResponse response = new PredictResponse(
                predictedPrice,
                predictedUnitPrice,
                "规则估算",
                "当前 Spring Boot 版本使用区域均价估算；如需机器学习模型，可后续接入 JPMML、Tribuo 或独立 Python 推理服务。",
                comparisonRows(request.city(), request.district(), area, predictedPrice)
        );
        saveResult(request, response);
        return response;
    }

    private void saveResult(PredictRequest request, PredictResponse response) {
        PredictResult result = new PredictResult();
        try {
            result.setInputFeatures(objectMapper.writeValueAsString(request));
        } catch (JsonProcessingException ex) {
            result.setInputFeatures("{}");
        }
        result.setPredictedPrice(response.predictedPrice());
        result.setPredictedUnitPrice(response.predictedUnitPrice());
        result.setModelName(response.modelName());
        predictResultRepository.save(result);
    }

    private BigDecimal averageUnitPrice(String city, String district) {
        BigDecimal value = null;
        if (hasText(city) && hasText(district)) {
            value = houseRepository.avgUnitPriceByCityAndDistrictName(city, district);
        }
        if (value == null && hasText(city)) {
            value = houseRepository.avgUnitPriceByCityName(city);
        }
        if (value == null) {
            value = houseRepository.avgUnitPrice();
        }
        return value == null || value.compareTo(BigDecimal.ZERO) <= 0 ? DEFAULT_UNIT_PRICE : value;
    }

    private List<Map<String, Object>> comparisonRows(String city, String district, BigDecimal area, BigDecimal predictedPrice) {
        List<Map<String, Object>> rows = new ArrayList<>();
        rows.add(row("预测总价", predictedPrice));
        if (hasText(city) && hasText(district)) {
            addAverageRow(rows, "区域均价估算", houseRepository.avgUnitPriceByCityAndDistrictName(city, district), area);
        }
        if (hasText(city)) {
            addAverageRow(rows, "城市均价估算", houseRepository.avgUnitPriceByCityName(city), area);
        }
        addAverageRow(rows, "整体均价估算", houseRepository.avgUnitPrice(), area);
        return rows;
    }

    private void addAverageRow(List<Map<String, Object>> rows, String label, BigDecimal unitPrice, BigDecimal area) {
        if (unitPrice != null && unitPrice.compareTo(BigDecimal.ZERO) > 0) {
            rows.add(row(label, unitPrice.multiply(area).divide(BigDecimal.valueOf(10000), 2, RoundingMode.HALF_UP)));
        }
    }

    private Map<String, Object> row(String label, BigDecimal value) {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("label", label);
        data.put("value", value);
        return data;
    }

    private BigDecimal normalizeArea(BigDecimal area) {
        if (area == null || area.compareTo(BigDecimal.TEN) < 0 || area.compareTo(BigDecimal.valueOf(1000)) > 0) {
            return DEFAULT_AREA;
        }
        return area;
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}
