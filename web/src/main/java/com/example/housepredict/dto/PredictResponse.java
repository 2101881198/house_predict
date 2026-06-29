package com.example.housepredict.dto;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

public record PredictResponse(
        BigDecimal predictedPrice,
        BigDecimal predictedUnitPrice,
        String modelName,
        String note,
        List<Map<String, Object>> comparison
) {
}
