package com.example.housepredict.service;

import com.example.housepredict.dto.PredictRequest;
import com.example.housepredict.dto.PredictResponse;
import com.example.housepredict.entity.PredictResult;
import com.example.housepredict.repository.HouseRepository;
import com.example.housepredict.repository.PredictResultRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class PredictionService {
    private static final BigDecimal DEFAULT_AREA = BigDecimal.valueOf(90);
    private static final BigDecimal DEFAULT_UNIT_PRICE = BigDecimal.valueOf(10000);

    private final HouseRepository houseRepository;
    private final PredictResultRepository predictResultRepository;
    private final ObjectMapper objectMapper;
    private final HttpClient httpClient;
    private final String pythonPredictUrl;

    public PredictionService(
            HouseRepository houseRepository,
            PredictResultRepository predictResultRepository,
            ObjectMapper objectMapper,
            @Value("${app.prediction.python-url}") String pythonPredictUrl) {
        this.houseRepository = houseRepository;
        this.predictResultRepository = predictResultRepository;
        this.objectMapper = objectMapper;
        this.pythonPredictUrl = pythonPredictUrl;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(2))
                .build();
    }

    public PredictResponse predict(PredictRequest request) {
        PredictResponse pythonResponse = callPythonService(request);
        if (pythonResponse != null) {
            PredictResponse response = withComparisonRows(request, pythonResponse);
            saveResult(request, response);
            return response;
        }

        PredictResponse response = rulePredict(request, "Python预测服务不可用，已回退为 Java 区域均价估算");
        saveResult(request, response);
        return response;
    }

    private PredictResponse callPythonService(PredictRequest request) {
        try {
            String body = objectMapper.writeValueAsString(request);
            HttpRequest httpRequest = HttpRequest.newBuilder()
                    .uri(URI.create(pythonPredictUrl))
                    .timeout(Duration.ofSeconds(8))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();
            HttpResponse<String> response = httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                return null;
            }
            return objectMapper.readValue(response.body(), PredictResponse.class);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            return null;
        } catch (IOException | IllegalArgumentException ex) {
            return null;
        }
    }

    private PredictResponse withComparisonRows(PredictRequest request, PredictResponse response) {
        BigDecimal area = normalizeArea(request.area());
        List<Map<String, Object>> comparison = new ArrayList<>();
        comparison.add(row("Python预测总价", response.predictedPrice()));
        if (response.comparison() != null) {
            for (Map<String, Object> row : response.comparison()) {
                Object label = row.get("label");
                if (!"预测总价".equals(label) && !"Python预测总价".equals(label)) {
                    comparison.add(row);
                }
            }
        }
        if (hasText(request.city()) && hasText(request.district())) {
            addAverageRow(comparison, "区域均价估算", houseRepository.avgUnitPriceByCityAndDistrictName(request.city(), request.district()), area);
        }
        if (hasText(request.city())) {
            addAverageRow(comparison, "城市均价估算", houseRepository.avgUnitPriceByCityName(request.city()), area);
        }
        addAverageRow(comparison, "整体均价估算", houseRepository.avgUnitPrice(), area);
        return new PredictResponse(
                response.predictedPrice(),
                response.predictedUnitPrice(),
                response.modelName(),
                response.note(),
                comparison
        );
    }

    private PredictResponse rulePredict(PredictRequest request, String note) {
        BigDecimal area = normalizeArea(request.area());
        BigDecimal unitPrice = averageUnitPrice(request.city(), request.district());
        BigDecimal predictedPrice = unitPrice.multiply(area).divide(BigDecimal.valueOf(10000), 2, RoundingMode.HALF_UP);
        BigDecimal predictedUnitPrice = unitPrice.setScale(2, RoundingMode.HALF_UP);

        return new PredictResponse(
                predictedPrice,
                predictedUnitPrice,
                "规则估算",
                note,
                comparisonRows(request.city(), request.district(), area, predictedPrice)
        );
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
