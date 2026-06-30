package com.example.housepredict.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.housepredict.entity.City;
import com.example.housepredict.entity.CrawlTask;
import com.example.housepredict.entity.District;
import com.example.housepredict.entity.House;
import com.example.housepredict.entity.PredictResult;
import com.example.housepredict.mapper.CityMapper;
import com.example.housepredict.mapper.CrawlTaskMapper;
import com.example.housepredict.mapper.DistrictMapper;
import com.example.housepredict.mapper.HouseMapper;
import com.example.housepredict.mapper.PredictResultMapper;
import com.example.housepredict.service.LookupService;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class LookupServiceImpl implements LookupService {
    private final CityMapper cityMapper;
    private final DistrictMapper districtMapper;
    private final HouseMapper houseMapper;
    private final CrawlTaskMapper crawlTaskMapper;
    private final PredictResultMapper predictResultMapper;

    public LookupServiceImpl(CityMapper cityMapper, DistrictMapper districtMapper, HouseMapper houseMapper, CrawlTaskMapper crawlTaskMapper, PredictResultMapper predictResultMapper) {
        this.cityMapper = cityMapper;
        this.districtMapper = districtMapper;
        this.houseMapper = houseMapper;
        this.crawlTaskMapper = crawlTaskMapper;
        this.predictResultMapper = predictResultMapper;
    }

    @Override
    public List<City> findAllCities() {
        return cityMapper.selectList(new LambdaQueryWrapper<City>().orderByAsc(City::getName));
    }

    @Override
    public long cityCount() {
        return cityMapper.selectCount(null);
    }

    @Override
    public long houseCount() {
        return houseMapper.selectCount(null);
    }

    @Override
    public List<District> findDistrictsByCity(City city) {
        return districtMapper.selectByCityIdOrderByName(city.getId());
    }

    @Override
    public List<String> findRoomTypes() {
        return houseMapper.findRoomTypes();
    }

    @Override
    public List<String> findFloors() {
        return houseMapper.findFloors();
    }

    @Override
    public List<String> findDirections() {
        return houseMapper.findDirections();
    }

    @Override
    public List<String> findDecorations() {
        return houseMapper.findDecorations();
    }

    @Override
    public List<House> recentHouses(int limit) {
        return houseMapper.selectRecentWithCityAndDistrict(limit);
    }

    @Override
    public List<CrawlTask> recentCrawlTasks() {
        return crawlTaskMapper.selectRecent100();
    }

    @Override
    public List<PredictResult> recentPredictions(int limit) {
        return predictResultMapper.selectRecent(limit);
    }
}
