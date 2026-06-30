package com.example.housepredict.dto;

import java.math.BigDecimal;

public class HouseQuery {
    private final String city;
    private final String district;
    private final String roomType;
    private final String decoration;
    private final BigDecimal minPrice;
    private final BigDecimal maxPrice;
    private final BigDecimal minArea;
    private final BigDecimal maxArea;
    private final String sort;
    private final int page;
    private final int pageSize;

    public HouseQuery(
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
            int pageSize) {
        this.city = city;
        this.district = district;
        this.roomType = roomType;
        this.decoration = decoration;
        this.minPrice = minPrice;
        this.maxPrice = maxPrice;
        this.minArea = minArea;
        this.maxArea = maxArea;
        this.sort = sort;
        this.page = page;
        this.pageSize = pageSize;
    }

    public String getCity() { return city; }
    public String getDistrict() { return district; }
    public String getRoomType() { return roomType; }
    public String getDecoration() { return decoration; }
    public BigDecimal getMinPrice() { return minPrice; }
    public BigDecimal getMaxPrice() { return maxPrice; }
    public BigDecimal getMinArea() { return minArea; }
    public BigDecimal getMaxArea() { return maxArea; }
    public String getSort() { return sort; }
    public int getPage() { return page; }
    public int getPageSize() { return pageSize; }

    public String sort() {
        return sort;
    }

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
