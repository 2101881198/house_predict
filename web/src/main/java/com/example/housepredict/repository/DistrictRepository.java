package com.example.housepredict.repository;

import com.example.housepredict.entity.City;
import com.example.housepredict.entity.District;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DistrictRepository extends JpaRepository<District, Long> {
    List<District> findByCityOrderByName(City city);
    Optional<District> findByCityAndName(City city, String name);
}
