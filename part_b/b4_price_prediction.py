"""
B.4 构建房价预测模型
==========================
功能：
1. 加载 B.1 清洗后的数据
2. 特征工程：缺失值处理、One-Hot 编码、标准化、特征选择
3. 训练多个回归模型进行对比：
   - 线性回归 (Linear Regression)
   - 岭回归 (Ridge Regression)
   - 随机森林 (Random Forest)
   - XGBoost
   - 梯度提升 (Gradient Boosting)
4. 模型评估：R², MAE, RMSE, MAPE
5. 特征重要性分析
6. 保存最优模型

目标变量：unit_price（单价，元/㎡）或 total_price（总价，万元）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import pickle
import os
import sys
import io
import warnings
warnings.filterwarnings("ignore")

# 修复 Windows GBK 终端编码问题
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except (AttributeError, OSError):
        pass

# 机器学习库
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import (
    r2_score, mean_absolute_error, mean_squared_error,
    mean_absolute_percentage_error, explained_variance_score,
)
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("[提示] xgboost 未安装，跳过 XGBoost 模型")

import matplotlib.font_manager as fm
fm._load_fontmanager(try_read_cache=False)
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DIR

FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "figures")
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "models")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# 随机种子
RANDOM_STATE = 42


# ============================================================
#  数据加载与特征工程
# ============================================================
def load_data() -> pd.DataFrame:
    """加载清洗后数据"""
    path = os.path.join(PROCESSED_DIR, "b1_cleaned_house_data.csv")
    if not os.path.exists(path):
        from part_b.b1_data_cleaning import _generate_demo_data, clean_data
        df = _generate_demo_data(500)
        df = clean_data(df)
        return df
    return pd.read_csv(path, encoding="utf-8-sig")


def feature_engineering(df: pd.DataFrame, target: str = "unit_price") -> tuple:
    """
    特征工程：
    - 选择数值特征和分类特征
    - 返回 X, y, 以及特征列名
    """
    print(f"\n[1] 特征工程 (目标变量: {target})")

    # 定义特征
    numeric_features = ["area", "build_year", "longitude", "latitude"]
    categorical_features = [
        "layout", "orientation_clean", "floor_level", "decoration",
        "building_type", "has_elevator",
    ]

    # 只保留存在的列
    numeric_features = [c for c in numeric_features if c in df.columns]
    categorical_features = [c for c in categorical_features if c in df.columns]

    # 添加衍生特征（无 build_year，用其他方式）
    if "area" in df.columns:
        df["log_area"] = np.log1p(df["area"])
        numeric_features.append("log_area")

    # 目标变量
    if target not in df.columns:
        print(f"[×] 目标变量 {target} 不存在! 使用 total_price")
        target = "total_price"

    # 删除目标变量缺失的行
    df = df.dropna(subset=[target])
    y = df[target].values

    # 处理特征
    print(f"    数值特征 ({len(numeric_features)}): {numeric_features}")
    print(f"    分类特征 ({len(categorical_features)}): {categorical_features}")
    print(f"    有效样本: {len(df)}")

    return df, numeric_features, categorical_features, y


def build_preprocessor(numeric_features: list, categorical_features: list):
    """构建数据预处理器"""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
             categorical_features),
        ]
    )
    return preprocessor


# ============================================================
#  模型训练与评估
# ============================================================
def evaluate_model(model, X_train, X_test, y_train, y_test, model_name: str) -> dict:
    """评估模型并返回指标"""
    # 预测
    y_pred = model.predict(X_test)
    y_pred_train = model.predict(X_train)

    # 计算指标
    metrics = {
        "模型": model_name,
        "R2_训练集": r2_score(y_train, y_pred_train),
        "R2_测试集": r2_score(y_test, y_pred),
        "MAE": mean_absolute_error(y_test, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_test, y_pred)),
        "EVS": explained_variance_score(y_test, y_pred),
    }
    try:
        metrics["MAPE"] = mean_absolute_percentage_error(y_test, y_pred)
    except:
        metrics["MAPE"] = np.nan

    # 交叉验证
    try:
        cv_scores = cross_val_score(model, X_train, y_train, cv=5,
                                     scoring="r2", n_jobs=-1)
        metrics["CV_R2_Mean"] = cv_scores.mean()
        metrics["CV_R2_Std"] = cv_scores.std()
    except:
        metrics["CV_R2_Mean"] = np.nan
        metrics["CV_R2_Std"] = np.nan

    return metrics, y_pred


def train_models(df, numeric_features, categorical_features, y):
    """
    训练多个模型并对比

    模型清单：
    1. 线性回归
    2. Ridge 回归
    3. Lasso 回归
    4. 随机森林
    5. 梯度提升
    6. XGBoost
    """
    print("\n[2] 构建预处理器...")
    preprocessor = build_preprocessor(numeric_features, categorical_features)

    # 定义特征集
    feature_cols = numeric_features + categorical_features
    X = df[feature_cols].values
    feature_cols_reindexed = list(range(len(numeric_features))) + list(
        range(len(numeric_features), len(numeric_features) + len(categorical_features))
    )

    # 手动预处理
    X_processed = preprocessor.fit_transform(df[feature_cols])

    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=0.2, random_state=RANDOM_STATE
    )
    print(f"    训练集: {X_train.shape[0]} 条, 测试集: {X_test.shape[0]} 条")
    print(f"    特征维度: {X_train.shape[1]}")

    # ---- 定义模型 ----
    models = [
        ("线性回归", LinearRegression()),
        ("Ridge回归", Ridge(alpha=1.0)),
        ("Lasso回归", Lasso(alpha=0.1, max_iter=5000)),
        ("随机森林", RandomForestRegressor(
            n_estimators=200, max_depth=15, min_samples_split=5,
            min_samples_leaf=2, random_state=RANDOM_STATE, n_jobs=-1
        )),
        ("梯度提升", GradientBoostingRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            min_samples_split=5, random_state=RANDOM_STATE,
        )),
    ]

    if HAS_XGBOOST:
        models.append(("XGBoost", xgb.XGBRegressor(
            n_estimators=200, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, random_state=RANDOM_STATE,
            n_jobs=-1, verbosity=0,
        )))

    # ---- 训练与评估 ----
    print("\n[3] 训练模型...")
    results = []
    predictions = {}
    best_model = None
    best_r2 = -float("inf")

    for name, model in models:
        print(f"\n--- {name} ---")
        try:
            model.fit(X_train, y_train)
            metrics, y_pred = evaluate_model(model, X_train, X_test, y_train, y_test, name)
            results.append(metrics)
            predictions[name] = y_pred

            print(f"    R2(测试集): {metrics['R2_测试集']:.4f}")
            print(f"    MAE:        {metrics['MAE']:.2f}")
            print(f"    RMSE:       {metrics['RMSE']:.2f}")
            print(f"    CV_R2:      {metrics['CV_R2_Mean']:.4f} ± {metrics['CV_R2_Std']:.4f}")

            if metrics["R2_测试集"] > best_r2:
                best_r2 = metrics["R2_测试集"]
                best_model = (name, model, metrics)
        except Exception as e:
            print(f"    [×] 训练失败: {e}")

    # ---- 结果汇总 ----
    results_df = pd.DataFrame(results).set_index("模型").round(4)
    print("\n" + "=" * 70)
    print("模型对比结果")
    print("=" * 70)
    print(results_df.to_string())

    return results_df, best_model, predictions, y_test, preprocessor, X_train, X_test, y_train


# ============================================================
#  可视化
# ============================================================
def plot_model_comparison(results_df: pd.DataFrame):
    """模型对比柱状图"""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    metrics_plot = ["R2_测试集", "MAE", "RMSE"]
    titles = ["R2 (越高越好)", "MAE (越低越好)", "RMSE (越低越好)"]
    colors_list = [sns.color_palette("Greens_r", len(results_df)),
                   sns.color_palette("Reds_r", len(results_df)),
                   sns.color_palette("Oranges_r", len(results_df))]

    for ax, metric, title, colors in zip(axes, metrics_plot, titles, colors_list):
        if metric not in results_df.columns:
            continue
        vals = results_df[metric].sort_values()
        if "R2" in metric:
            vals = vals.sort_values(ascending=False)
        ax.barh(vals.index, vals.values, color=colors, edgecolor="white")
        for i, (idx, val) in enumerate(vals.items()):
            ax.text(val, i, f" {val:.4f}", va="center", fontsize=10)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.invert_yaxis()

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b4_model_comparison.png"), dpi=150)
    print(f"[√] 图表已保存: b4_model_comparison.png")


def plot_feature_importance(model, preprocessor, numeric_features, categorical_features, model_name: str):
    """特征重要性分析（仅对树模型有效）"""
    if not hasattr(model, "feature_importances_"):
        print(f"    {model_name} 不支持特征重要性")
        return

    importances = model.feature_importances_

    # 获取编码后特征名
    cat_encoder = preprocessor.named_transformers_["cat"]
    try:
        cat_names = cat_encoder.get_feature_names_out(categorical_features)
    except:
        cat_names = categorical_features

    all_names = list(numeric_features) + list(cat_names)
    # 对齐长度
    if len(all_names) != len(importances):
        all_names = [f"特征{i}" for i in range(len(importances))]

    # 排序取 TOP 20
    feat_imp = pd.DataFrame({"特征": all_names, "重要性": importances})
    feat_imp = feat_imp.sort_values("重要性", ascending=False).head(20)

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = sns.color_palette("viridis", len(feat_imp))
    ax.barh(range(len(feat_imp)), feat_imp["重要性"], color=colors, edgecolor="white")
    ax.set_yticks(range(len(feat_imp)))
    ax.set_yticklabels(feat_imp["特征"].values, fontsize=9)
    ax.set_xlabel("重要性", fontsize=12)
    ax.set_title(f"特征重要性 TOP20 — {model_name}", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b4_feature_importance.png"), dpi=150)
    print(f"[√] 图表已保存: b4_feature_importance.png")


def plot_predictions_vs_actual(y_test, predictions: dict, best_model_name: str):
    """预测值 vs 实际值散点图"""
    if best_model_name not in predictions:
        return

    y_pred = predictions[best_model_name]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # 散点图
    ax = axes[0]
    ax.scatter(y_test, y_pred, alpha=0.4, edgecolors="white", s=40)
    # y=x 参考线
    min_val = min(y_test.min(), y_pred.min())
    max_val = max(y_test.max(), y_pred.max())
    ax.plot([min_val, max_val], [min_val, max_val], "r--", linewidth=2, label="y=x (理想)")
    ax.set_xlabel("实际值", fontsize=12)
    ax.set_ylabel("预测值", fontsize=12)
    ax.set_title(f"{best_model_name}: 预测值 vs 实际值", fontsize=13)
    ax.legend()

    # 残差图
    ax = axes[1]
    residuals = y_test - y_pred
    ax.scatter(y_pred, residuals, alpha=0.4, edgecolors="white", s=40)
    ax.axhline(y=0, color="r", linestyle="--", linewidth=2)
    ax.set_xlabel("预测值", fontsize=12)
    ax.set_ylabel("残差", fontsize=12)
    ax.set_title("残差分布", fontsize=13)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b4_predictions_vs_actual.png"), dpi=150)
    print(f"[√] 图表已保存: b4_predictions_vs_actual.png")


# ============================================================
#  超参数调优（可选）
# ============================================================
def tune_random_forest(X_train, y_train, X_test, y_test):
    """对随机森林进行网格调优"""
    print("\n[可选] 随机森林超参数调优...")
    param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [10, 15, 20, None],
        "min_samples_split": [2, 5, 10],
    }

    rf = RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1)
    grid = GridSearchCV(rf, param_grid, cv=3, scoring="r2",
                         n_jobs=-1, verbose=1)
    grid.fit(X_train, y_train)

    print(f"    最优参数: {grid.best_params_}")
    print(f"    最优 CV R2: {grid.best_score_:.4f}")
    print(f"    测试集 R2: {grid.score(X_test, y_test):.4f}")

    return grid.best_estimator_


# ============================================================
#  模型保存
# ============================================================
def save_model(model, preprocessor, name: str, metrics: dict):
    """保存模型和预处理器"""
    model_path = os.path.join(MODEL_DIR, f"b4_{name}_model.pkl")
    preprocessor_path = os.path.join(MODEL_DIR, "b4_preprocessor.pkl")
    metrics_path = os.path.join(MODEL_DIR, "b4_model_metrics.json")

    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    with open(preprocessor_path, "wb") as f:
        pickle.dump(preprocessor, f)

    import json
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f"\n[√] 模型已保存:")
    print(f"    {model_path}")
    print(f"    {preprocessor_path}")
    print(f"    {metrics_path}")


# ============================================================
#  主流程
# ============================================================
def main():
    print("=" * 60)
    print("B.4 构建房价预测模型")
    print("=" * 60)

    # 加载数据
    df = load_data()
    print(f"[0] 数据加载完成: {df.shape[0]} 行")

    # 可选择目标变量
    target = "unit_price"  # 预测单价，也可改为 "total_price"
    if target not in df.columns:
        target = "total_price"

    # 特征工程
    df, numeric_features, categorical_features, y = feature_engineering(df, target=target)

    # 训练
    results_df, best_model_info, predictions, y_test, preprocessor, X_train, X_test, y_train = \
        train_models(df, numeric_features, categorical_features, y)

    if best_model_info is None:
        print("[×] 所有模型训练失败")
        return

    best_name, best_model, best_metrics = best_model_info
    print(f"\n最优模型: {best_name} (R2={best_metrics['R2_测试集']:.4f})")

    # 可视化
    print("\n[4] 生成可视化...")
    plot_model_comparison(results_df)
    plot_feature_importance(best_model, preprocessor, numeric_features, categorical_features, best_name)
    plot_predictions_vs_actual(y_test, predictions, best_name)

    # 超参数调优（对最优模型为随机森林时）
    if "随机森林" in best_name:
        print("\n[5] 超参数调优（可选）...")
        try:
            best_model = tune_random_forest(X_train, y_train, X_test, y_test)
        except:
            pass

    # 保存模型
    print("\n[6] 保存模型...")
    save_model(best_model, preprocessor, best_name.replace(" ", "_"), best_metrics)

    # 最终报告
    print("\n" + "=" * 60)
    print("B.4 最终报告")
    print("=" * 60)
    print(f"  最优模型:     {best_name}")
    print(f"  R2 (测试集):  {best_metrics['R2_测试集']:.4f}")
    print(f"  MAE:          {best_metrics['MAE']:.2f}")
    print(f"  RMSE:         {best_metrics['RMSE']:.2f}")
    if "MAPE" in best_metrics:
        print(f"  MAPE:         {best_metrics['MAPE']:.4f}")
    if "CV_R2_Mean" in best_metrics:
        print(f"  交叉验证R2:    {best_metrics['CV_R2_Mean']:.4f} ± {best_metrics['CV_R2_Std']:.4f}")
    print("=" * 60)

    print("\n[完成] B.4 房价预测模型构建结束。")


if __name__ == "__main__":
    main()
