package com.example.housepredict;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@MapperScan("com.example.housepredict.mapper")
@SpringBootApplication
public class HousePredictApplication {
    public static void main(String[] args) {
        SpringApplication.run(HousePredictApplication.class, args);
    }
}
