# 智慧房源探索平台

这是一个智慧房源探索平台课程项目，覆盖房源数据存储、统计分析、价格预测和可视化展示等功能。

当前 `web` 目录已经改写为 Spring Boot + MySQL 项目。原来的 Django 路由表方式已改为 Spring Boot 常见的 Controller 注解方式，例如：

```java
@GetMapping("/api/houses/")
public ApiResponse<Map<String, Object>> houses(...) {
    ...
}
```

## Web 项目结构

```text
web/
  pom.xml
  src/main/java/com/example/housepredict/
    controller/     页面和 API 请求入口
    service/        业务逻辑
    repository/     JPA 数据访问
    entity/         数据库表映射
    dto/            请求和响应对象
  src/main/resources/
    application.yml
    templates/      Thymeleaf 页面
    static/         CSS、JS、地图静态资源
```

## 环境要求

- Java 17
- Maven
- MySQL

当前电脑没有 Java/Maven 环境，所以本次改写没有在本机编译运行。

## 运行

```bash
cd web
mvn spring-boot:run
```

默认访问地址：

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## 数据库配置

配置文件：

```text
web/src/main/resources/application.yml
```

支持这些环境变量：

```text
MYSQL_HOST
MYSQL_PORT
MYSQL_DATABASE
MYSQL_USER
MYSQL_PASSWORD
```

默认数据库名是 `house_predict`。JPA 表名尽量沿用原 Django 项目的默认表名，例如 `houses_house`、`houses_city`、`houses_district`，方便复用已有 MySQL 数据。

## 演示数据

启动时自动插入少量演示数据：

```bash
SEED_DEMO_DATA=true mvn spring-boot:run
```

或启动后调用演示爬取任务接口：

```bash
curl -X POST "http://127.0.0.1:8000/api/admin/crawl-tasks/" \
  -H "Content-Type: application/json" \
  -d '{"target_city":"济南","page_count":1}'
```

## 页面入口

- 首页看板：`/`
- 省级分析：`/province/`
- 城市分析：`/cities/{城市ID}/`
- 房源列表：`/houses/`
- 房源详情：`/houses/{房源ID}/`
- 价格预测：`/predict/`

## 常用 API

- 房源列表：`/api/houses/`
- 房源详情：`/api/houses/{房源ID}/`
- 总览统计：`/api/statistics/overview/`
- 省级统计：`/api/statistics/province/`
- 城市统计：`/api/statistics/city/?city_id=1`
- 价格预测：`/api/predict/price/`
- 爬取任务管理：`/api/admin/crawl-tasks/`

## 预测功能说明

原 Django 版本使用 Python/scikit-learn 的 `joblib` 模型。Spring Boot 版本目前改为规则估算：

```text
预测总价 = 区县/城市/整体平均单价 * 面积 / 10000
```

后续如果需要机器学习预测，建议让 Spring Boot 调用独立 Python 推理服务，或者把模型导出为 PMML 后在 Java 中加载。
