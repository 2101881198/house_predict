package com.example.housepredict.service;

import com.example.housepredict.entity.City;
import com.example.housepredict.entity.CrawlTask;
import com.example.housepredict.entity.District;
import com.example.housepredict.entity.House;
import com.example.housepredict.entity.PredictResult;
import java.util.List;

public interface LookupService {
    List<City> findAllCities();

    long cityCount();

    long houseCount();

    List<District> findDistrictsByCity(City city);

    List<String> findRoomTypes();

    List<String> findFloors();

    List<String> findDirections();

    List<String> findDecorations();

    List<House> recentHouses(int limit);

    List<CrawlTask> recentCrawlTasks();

    List<PredictResult> recentPredictions(int limit);
}
