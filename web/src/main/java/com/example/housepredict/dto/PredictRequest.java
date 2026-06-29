package com.example.housepredict.dto;

import java.math.BigDecimal;

public record PredictRequest(
        String city,
        String district,
        BigDecimal area,
        String roomType,
        String floor,
        String direction,
        String decoration,
        Integer buildYear
) {
}
