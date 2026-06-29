package com.example.housepredict.service;

import com.example.housepredict.entity.House;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class HouseMapper {
    public Map<String, Object> toMap(House house) {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("id", house.getId());
        data.put("title", house.getTitle());
        data.put("city", house.getCity().getName());
        data.put("district", house.getDistrict().getName());
        data.put("community", house.getCommunity());
        data.put("total_price", house.getTotalPrice());
        data.put("unit_price", house.getUnitPrice());
        data.put("area", house.getArea());
        data.put("room_type", house.getRoomType());
        data.put("floor", house.getFloor());
        data.put("direction", house.getDirection());
        data.put("decoration", house.getDecoration());
        data.put("build_year", house.getBuildYear());
        data.put("address", house.getAddress());
        data.put("longitude", house.getLongitude());
        data.put("latitude", house.getLatitude());
        data.put("surrounding", house.getSurrounding());
        data.put("crawl_time", house.getCrawlTime());
        return data;
    }
}
