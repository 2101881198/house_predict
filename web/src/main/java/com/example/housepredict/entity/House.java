package com.example.housepredict.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@TableName("houses_house")
public class House extends BaseEntity {
    @TableId(type = IdType.AUTO)
    private Long id;

    private String title;

    @TableField("city_id")
    private Long cityId;

    @TableField("district_id")
    private Long districtId;

    @TableField(exist = false)
    private City city;

    @TableField(exist = false)
    private District district;

    private String community = "";

    @TableField("total_price")
    private BigDecimal totalPrice;

    @TableField("unit_price")
    private BigDecimal unitPrice;

    private BigDecimal area;

    @TableField("room_type")
    private String roomType = "";

    private String floor = "";

    private String direction = "";

    private String decoration = "";

    @TableField("build_year")
    private Integer buildYear;

    private String address = "";

    private BigDecimal longitude;

    private BigDecimal latitude;

    private String surrounding = "";

    @TableField("source_url")
    private String sourceUrl;

    @TableField("crawl_time")
    private LocalDateTime crawlTime;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public Long getCityId() { return cityId; }
    public void setCityId(Long cityId) { this.cityId = cityId; }
    public Long getDistrictId() { return districtId; }
    public void setDistrictId(Long districtId) { this.districtId = districtId; }
    public City getCity() { return city; }
    public void setCity(City city) {
        this.city = city;
        this.cityId = city == null ? null : city.getId();
    }
    public District getDistrict() { return district; }
    public void setDistrict(District district) {
        this.district = district;
        this.districtId = district == null ? null : district.getId();
    }
    public String getCommunity() { return community; }
    public void setCommunity(String community) { this.community = community; }
    public BigDecimal getTotalPrice() { return totalPrice; }
    public void setTotalPrice(BigDecimal totalPrice) { this.totalPrice = totalPrice; }
    public BigDecimal getUnitPrice() { return unitPrice; }
    public void setUnitPrice(BigDecimal unitPrice) { this.unitPrice = unitPrice; }
    public BigDecimal getArea() { return area; }
    public void setArea(BigDecimal area) { this.area = area; }
    public String getRoomType() { return roomType; }
    public void setRoomType(String roomType) { this.roomType = roomType; }
    public String getFloor() { return floor; }
    public void setFloor(String floor) { this.floor = floor; }
    public String getDirection() { return direction; }
    public void setDirection(String direction) { this.direction = direction; }
    public String getDecoration() { return decoration; }
    public void setDecoration(String decoration) { this.decoration = decoration; }
    public Integer getBuildYear() { return buildYear; }
    public void setBuildYear(Integer buildYear) { this.buildYear = buildYear; }
    public String getAddress() { return address; }
    public void setAddress(String address) { this.address = address; }
    public BigDecimal getLongitude() { return longitude; }
    public void setLongitude(BigDecimal longitude) { this.longitude = longitude; }
    public BigDecimal getLatitude() { return latitude; }
    public void setLatitude(BigDecimal latitude) { this.latitude = latitude; }
    public String getSurrounding() { return surrounding; }
    public void setSurrounding(String surrounding) { this.surrounding = surrounding; }
    public String getSourceUrl() { return sourceUrl; }
    public void setSourceUrl(String sourceUrl) { this.sourceUrl = sourceUrl; }
    public LocalDateTime getCrawlTime() { return crawlTime; }
    public void setCrawlTime(LocalDateTime crawlTime) { this.crawlTime = crawlTime; }
}
