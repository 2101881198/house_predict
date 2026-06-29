package com.example.housepredict.dto;

import java.math.BigDecimal;

public record HouseQuery(
        String city,
        String district,
        String roomType,
        String decoration,
        BigDecimal minPrice,
        BigDecimal maxPrice,
        BigDecimal minArea,
        BigDecimal maxArea,
        String sort,
        int page,
        int pageSize
) {
    public int safePage() {
        return Math.max(page, 1);
    }

    public int safePageSize(int max) {
        if (pageSize < 1) {
            return 10;
        }
        return Math.min(pageSize, max);
    }
}
