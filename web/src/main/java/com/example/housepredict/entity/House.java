package com.example.housepredict.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(
        name = "houses_house",
        indexes = {
                @Index(name = "idx_house_city_district", columnList = "city_id,district_id"),
                @Index(name = "idx_house_price_area", columnList = "total_price,area")
        }
)
public class House extends BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 200)
    private String title;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "city_id")
    private City city;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "district_id")
    private District district;

    @Column(length = 100)
    private String community = "";

    @Column(name = "total_price", nullable = false, precision = 10, scale = 2)
    private BigDecimal totalPrice;

    @Column(name = "unit_price", nullable = false, precision = 10, scale = 2)
    private BigDecimal unitPrice;

    @Column(nullable = false, precision = 8, scale = 2)
    private BigDecimal area;

    @Column(name = "room_type", length = 50)
    private String roomType = "";

    @Column(length = 50)
    private String floor = "";

    @Column(length = 50)
    private String direction = "";

    @Column(length = 50)
    private String decoration = "";

    @Column(name = "build_year")
    private Integer buildYear;

    @Column(length = 255)
    private String address = "";

    @Column(precision = 10, scale = 6)
    private BigDecimal longitude;

    @Column(precision = 10, scale = 6)
    private BigDecimal latitude;

    @Column(columnDefinition = "TEXT")
    private String surrounding = "";

    @Column(name = "source_url", length = 500, unique = true)
    private String sourceUrl;

    @Column(name = "crawl_time")
    private LocalDateTime crawlTime;

    public Long getId() { return id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public City getCity() { return city; }
    public void setCity(City city) { this.city = city; }
    public District getDistrict() { return district; }
    public void setDistrict(District district) { this.district = district; }
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
