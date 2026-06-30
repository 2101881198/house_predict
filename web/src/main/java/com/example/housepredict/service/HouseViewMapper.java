package com.example.housepredict.service;

import com.example.housepredict.entity.House;
import java.util.Map;

public interface HouseViewMapper {
    Map<String, Object> toMap(House house);
}
