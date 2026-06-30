package com.example.housepredict.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springdoc.core.models.GroupedOpenApi;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {
    @Bean
    public OpenAPI housePredictOpenApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("智慧房源探索平台 API")
                        .version("1.0")
                        .description("用于课程作业调试的 Spring Boot 接口文档。"));
    }

    @Bean
    public GroupedOpenApi publicApi() {
        return GroupedOpenApi.builder()
                .group("公开接口")
                .pathsToMatch("/api/houses/**", "/api/statistics/**", "/api/predict/**")
                .build();
    }

    @Bean
    public GroupedOpenApi adminApi() {
        return GroupedOpenApi.builder()
                .group("后台接口")
                .pathsToMatch("/api/admin/**")
                .build();
    }
}
