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

## Swagger 接口文档

项目已接入 springdoc-openapi，启动 Spring Boot 后可以打开：

```text
http://127.0.0.1:8000/swagger-ui/index.html
```

也可以查看原始 OpenAPI JSON：

```text
http://127.0.0.1:8000/v3/api-docs
```

Swagger UI 里分了三组：

- `公开接口`：可以直接测试 `/api/houses/`、`/api/statistics/**`、`/api/predict/price/` 等 JSON 接口。
- `后台接口`：用于测试 `/api/admin/**`，需要先在浏览器登录 `/admin/`，否则会返回 401。
- `页面路由`：展示 `/`、`/houses/`、`/predict/`、`/admin/` 等 Thymeleaf 页面路由，主要方便查看项目完整请求入口。

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
- `service/*.java`：业务接口
- `service/impl/*.java`：业务实现
- `mapper/*.java`：MyBatis-Plus 持久层接口
- `resources/mapper/*.xml`：复杂 SQL 和统计查询
- `entity/*.java`：数据库表对象映射
- `templates/houses/*.html`：页面模板
- `static/houses/**`：CSS、JS、地图静态资源

## 预测功能说明

预测功能现在拆成两层：

- Spring Boot 继续提供页面和 `/api/predict/price/`。
- 独立 Python 服务负责机器学习模型预测。

Python 服务目录：

```text
web/python_predict_service/
```

训练模型：

```bash
cd web/python_predict_service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
MYSQL_USER=root MYSQL_PASSWORD=你的密码 python train_model.py
```

启动 Python 预测服务：

```bash
uvicorn app:app --host 127.0.0.1 --port 9000
```

启动 Spring Boot：

```bash
cd web
mvn spring-boot:run
```

Spring Boot 默认调用：

```text
http://127.0.0.1:9000/predict
```

如果要改 Python 服务地址：

```bash
PYTHON_PREDICT_URL=http://127.0.0.1:9000/predict mvn spring-boot:run
```

当 Python 服务不可用时，Spring Boot 会自动回退为规则估算：

```text
预测总价 = 区县/城市/整体平均单价 * 面积 / 10000
```
