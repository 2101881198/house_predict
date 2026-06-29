# Python 预测服务

这是独立于 Spring Boot 的房价预测服务。Spring Boot 的 `/api/predict/price/` 会优先调用这里的 `/predict`。

## 安装

```bash
cd web/python_predict_service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 训练模型

训练脚本会从 MySQL 的 `houses_house`、`houses_city`、`houses_district` 表读取数据。

```bash
MYSQL_USER=root MYSQL_PASSWORD=你的密码 python train_model.py
```

默认模型输出：

```text
web/python_predict_service/models/price_model.joblib
```

## 启动预测服务

```bash
uvicorn app:app --host 127.0.0.1 --port 9000
```

如果 Windows/conda 环境里 `uvicorn` 启动后没有任何输出，使用内置 HTTP 服务：

```bash
python server.py
```

健康检查：

```bash
curl http://127.0.0.1:9000/health
```

预测接口：

```bash
curl -X POST http://127.0.0.1:9000/predict \
  -H "Content-Type: application/json" \
  -d '{"city":"济南","district":"历下区","area":90,"room_type":"两室一厅","floor":"中楼层","direction":"南北","decoration":"精装","build_year":2015}'
```
