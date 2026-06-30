package com.example.housepredict.service;

import java.math.BigDecimal;

public interface AdminHouseService {
    String createHouse(
            String title,
            String city,
            String district,
            BigDecimal totalPrice,
            BigDecimal area,
            String roomType,
            String floor,
            String direction,
            String decoration,
            Integer buildYear,
            String address);

    void deleteHouse(Long houseId);
}
