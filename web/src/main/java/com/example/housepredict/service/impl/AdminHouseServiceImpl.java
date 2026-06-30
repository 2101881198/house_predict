package com.example.housepredict.service.impl;

import com.example.housepredict.entity.City;
import com.example.housepredict.entity.District;
import com.example.housepredict.entity.House;
import com.example.housepredict.mapper.CityMapper;
import com.example.housepredict.mapper.DistrictMapper;
import com.example.housepredict.mapper.HouseMapper;
import com.example.housepredict.service.AdminHouseService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.NoSuchElementException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AdminHouseServiceImpl implements AdminHouseService {
    private final CityMapper cityMapper;
    private final DistrictMapper districtMapper;
    private final HouseMapper houseMapper;

    public AdminHouseServiceImpl(CityMapper cityMapper, DistrictMapper districtMapper, HouseMapper houseMapper) {
        this.cityMapper = cityMapper;
        this.districtMapper = districtMapper;
        this.houseMapper = houseMapper;
    }

    @Override
    @Transactional
    public String createHouse(
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
            String address) {
        if (title.isBlank() || city.isBlank() || district.isBlank()) {
            throw new IllegalArgumentException("标题、城市和区县不能为空");
        }
        if (totalPrice.compareTo(BigDecimal.ZERO) <= 0 || area.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("总价和面积必须大于 0");
        }

        City cityEntity = findOrCreateCity(city.trim());
        District districtEntity = findOrCreateDistrict(cityEntity, district.trim());

        House house = new House();
        house.setTitle(title.trim());
        house.setCity(cityEntity);
        house.setDistrict(districtEntity);
        house.setTotalPrice(totalPrice);
        house.setArea(area);
        house.setUnitPrice(totalPrice.multiply(BigDecimal.valueOf(10000)).divide(area, 2, RoundingMode.HALF_UP));
        house.setRoomType(roomType.trim());
        house.setFloor(floor.trim());
        house.setDirection(direction.trim());
        house.setDecoration(decoration.trim());
        house.setBuildYear(buildYear);
        house.setAddress(address.isBlank() ? cityEntity.getName() + " " + districtEntity.getName() + " " + title.trim() : address.trim());
        house.setCrawlTime(LocalDateTime.now());
        houseMapper.insert(house);
        return house.getTitle();
    }

    @Override
    @Transactional
    public void deleteHouse(Long houseId) {
        if (houseMapper.selectById(houseId) == null) {
            throw new NoSuchElementException("房源不存在，无法删除");
        }
        houseMapper.deleteById(houseId);
    }

    private City findOrCreateCity(String name) {
        City city = cityMapper.selectByName(name);
        if (city != null) {
            return city;
        }
        City created = new City();
        created.setName(name);
        created.setProvince("山东省");
        cityMapper.insert(created);
        return created;
    }

    private District findOrCreateDistrict(City city, String name) {
        District district = districtMapper.selectByCityIdAndName(city.getId(), name);
        if (district != null) {
            district.setCity(city);
            return district;
        }
        District created = new District();
        created.setCity(city);
        created.setName(name);
        districtMapper.insert(created);
        return created;
    }
}
