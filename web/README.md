# Spring Boot Web 版说明

这个目录已经从 Django 改写为 Spring Boot 项目，保留了原来的主要 URL：

- `/`
- `/province/`
- `/cities/{cityId}/`
- `/houses/`
- `/houses/{houseId}/`
- `/predict/`
- `/api/houses/`
- `/api/houses/{houseId}/`
- `/api/statistics/overview/`
- `/api/statistics/province/`
- `/api/statistics/city/?city_id=1`
- `/api/predict/price/`
- `/api/admin/crawl-tasks/`

## 运行方式

当前电脑没有 Java 环境，所以本次没有在本机编译运行。换到有 Java 17 和 Maven 的机器后：

```bash
cd web
mvn spring-boot:run
```

默认端口仍然是 `8000`：

```text
http://127.0.0.1:8000/
```

## 数据库配置

配置在 `src/main/resources/application.yml`，支持环境变量：

```text
MYSQL_HOST
MYSQL_PORT
MYSQL_DATABASE
MYSQL_USER
MYSQL_PASSWORD
```

默认数据库名是 `house_predict`。

## 演示数据

如果要启动时自动插入少量演示数据：

```bash
SEED_DEMO_DATA=true mvn spring-boot:run
```

也可以调用接口创建演示爬取任务并导入演示数据：

```bash
curl -X POST "http://127.0.0.1:8000/api/admin/crawl-tasks/" \
  -H "Content-Type: application/json" \
  -d '{"target_city":"济南","page_count":1}'
```

## 和 Django 版本的对应关系

Spring Boot 版本里，请求入口直接写在 Controller 注解上：

```java
@GetMapping("/api/houses/")
public ApiResponse<Map<String, Object>> houses(...) {
    ...
}
```

对应关系：

- `controller/PageController.java`：返回 Thymeleaf 页面
- `controller/HouseApiController.java`：返回 JSON API
- `service/*.java`：业务逻辑
- `repository/*.java`：数据库访问
- `entity/*.java`：数据库表映射
- `templates/houses/*.html`：页面模板
- `static/houses/**`：CSS、JS、地图静态资源

## 预测功能说明

原 Django 版本使用 Python/scikit-learn 训练 `joblib` 模型。Spring Boot 版本目前改为规则估算：

```text
预测总价 = 区县/城市/整体平均单价 * 面积 / 10000
```

如果后续要恢复机器学习预测，建议有两种方式：

1. Java 后端调用一个 Python 推理服务。
2. 将模型导出为 Java 可加载格式，例如 PMML，再用 JPMML 读取。
