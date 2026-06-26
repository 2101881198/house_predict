"""
B.1 房源信息数据清洗
========================
功能：
1. 加载 A.4 爬取的原始房源数据
2. 数据探索：缺失值、异常值、分布概览
3. 数据清洗：解析数值、处理缺失、剔除异常、编码分类
4. 特征衍生：log变换、楼层编码、朝向编码
5. 输出清洗后数据供 B.2/B.3/B.4 使用
"""

import pandas as pd
import numpy as np
import re
import os
import sys
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except:
        pass

from config import RAW_DIR, PROCESSED_DIR


# ============================================================
#  数据加载
# ============================================================
def load_raw_data(filepath: str = None) -> pd.DataFrame:
    """加载原始 CSV 数据，自动处理编码问题"""
    if filepath is None:
        filepath = os.path.join(RAW_DIR, "a4_house_details.csv")
        if not os.path.exists(filepath):
            filepath = os.path.join(RAW_DIR, "a1_house_details.csv")

    if not os.path.exists(filepath):
        print(f"[FAIL] 数据文件不存在: {filepath}")
        sys.exit(1)

    for enc in ["utf-8-sig", "gb18030", "latin1"]:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            print(f"[1] 编码={enc}, 形状={df.shape}")
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue

    raise Exception("无法读取 CSV 文件（所有编码均失败）")


# ============================================================
#  数据探索
# ============================================================
def explore_data(df: pd.DataFrame):
    print("\n" + "=" * 60)
    print("数据探索")
    print("=" * 60)
    print(f"形状: {df.shape}")
    print(f"\n--- 列名 ---")
    for i, c in enumerate(df.columns, 1):
        nulls = df[c].isna().sum()
        pct = nulls / len(df) * 100 if len(df) > 0 else 0
        print(f"  {i:2d}. {c:25s}  dtype={str(df[c].dtype):10s}  缺失={nulls:6d} ({pct:.1f}%)")

    print(f"\n--- 城市分布 ---")
    if "city" in df.columns:
        for city, cnt in df["city"].value_counts().items():
            print(f"  {city}: {cnt}")


# ============================================================
#  工具函数
# ============================================================
def extract_num(val) -> float:
    """从字符串提取数值"""
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    match = re.search(r'[\d.]+', str(val))
    return float(match.group()) if match else np.nan


def clean_floor(val) -> str:
    """统一楼层：低/中/高"""
    if pd.isna(val):
        return "未知"
    s = str(val)
    if "低" in s:
        return "低楼层"
    elif "中" in s:
        return "中楼层"
    elif "高" in s:
        return "高楼层"
    return "未知"


def clean_orient(val) -> str:
    """统一朝向：南/南北/东西/..."""
    if pd.isna(val):
        return "未知"
    s = str(val).strip()
    has_s = "南" in s
    has_n = "北" in s
    has_e = "东" in s
    has_w = "西" in s
    if has_s and has_n:
        return "南北"
    if has_s:
        return "南"
    if has_n:
        return "北"
    if has_e and has_w:
        return "东西"
    if has_e:
        return "东"
    if has_w:
        return "西"
    return "其他"


def clean_text(val, max_len=500) -> str:
    """清洗文本字段"""
    if pd.isna(val):
        return ""
    s = str(val)
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()[:max_len]


# ============================================================
#  数据清洗
# ============================================================
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 60)
    print("数据清洗")
    print("=" * 60)

    df = df.copy()
    initial = len(df)

    # ---- 1. 解析数值 ----
    print("\n[1] 解析数值字段...")
    df["total_price_num"] = df["total_price"].apply(extract_num)   # 总价（万）
    df["unit_price_num"] = df["unit_price"].apply(extract_num)    # 单价（元/㎡）
    df["area_num"] = df["area"].apply(extract_num)                # 面积（㎡）
    df["lon_num"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["lat_num"] = pd.to_numeric(df["latitude"], errors="coerce")

    for col in ["total_price_num", "unit_price_num", "area_num"]:
        n = df[col].notna().sum()
        print(f"    {col}: {n} 有效值")

    # ---- 2. 清理分类 ----
    print("\n[2] 清理分类字段...")
    df["floor_level"] = df["floor"].apply(clean_floor)
    df["orientation_clean"] = df["orientation"].apply(clean_orient)

    # ---- 3. 缺失值处理 ----
    print("\n[3] 处理缺失值...")
    # 数值：中位数
    for col in ["total_price_num", "unit_price_num", "area_num"]:
        if col in df.columns:
            med = df[col].median()
            b = df[col].isna().sum()
            if b > 0:
                df[col].fillna(med, inplace=True)
                print(f"    {col}: 填充 {b} 个 (中位数={med:.1f})")

    # 分类：众数
    cat_cols = ["layout", "layout_structure", "floor_level", "orientation_clean",
                 "building_structure", "building_type", "decoration",
                 "elevator_ratio", "heating", "has_elevator",
                 "transaction_ownership", "property_ownership", "mortgage_info", "usage"]
    for col in cat_cols:
        if col in df.columns:
            mode_vals = df[col].mode()
            if len(mode_vals) > 0:
                b = df[col].isna().sum()
                if b > 0:
                    df[col].fillna(mode_vals[0], inplace=True)
                    print(f"    {col}: 填充 {b} 个 (众数={mode_vals[0][:30]})")

    # 城市：用 district 推测
    if "city" in df.columns:
        df["city"] = df["city"].fillna("未知")

    # ---- 4. 异常值 ----
    print("\n[4] 剔除异常值...")
    df = df[(df["total_price_num"] >= 5) & (df["total_price_num"] <= 5000)]
    df = df[(df["unit_price_num"] >= 1000) & (df["unit_price_num"] <= 150000)]
    df = df[(df["area_num"] >= 20) & (df["area_num"] <= 500)]
    print(f"    剔除前: {initial}, 剔除后: {len(df)} (移除 {initial - len(df)} 行)")

    # ---- 5. 特征衍生 ----
    print("\n[5] 特征衍生...")
    df["log_total_price"] = np.log1p(df["total_price_num"])
    df["log_unit_price"] = np.log1p(df["unit_price_num"])
    df["log_area"] = np.log1p(df["area_num"])
    df["calc_unit_price"] = df["total_price_num"] * 10000 / df["area_num"].clip(lower=1)
    df["calc_unit_price"] = df["calc_unit_price"].clip(1000, 150000)

    # 楼层编码
    floor_map = {"低楼层": 0, "中楼层": 1, "高楼层": 2, "未知": 1}
    df["floor_code"] = df["floor_level"].map(floor_map).fillna(1).astype(int)

    # 朝向编码
    orient_map = {"南": 4, "南北": 5, "东南": 3, "西南": 3, "东西": 2, "东": 2, "西": 1, "北": 1, "其他": 2, "未知": 2}
    df["orient_code"] = df["orientation_clean"].map(orient_map).fillna(2).astype(int)

    # ---- 6. 兼容别名（让 B.2/B.3/B.4 直接用） ----
    print("\n[6] 添加列别名...")
    col_aliases = {
        "unit_price_num": "unit_price",
        "total_price_num": "total_price",
        "area_num": "area",
        "lon_num": "longitude_num",
        "lat_num": "latitude_num",
    }
    for src, dst in col_aliases.items():
        if src in df.columns:
            df[dst] = df[src]

    print(f"    清洗后: {len(df)} 行, {len(df.columns)} 列")

    return df


# ============================================================
#  保存
# ============================================================
def save_cleaned_data(df: pd.DataFrame):
    path = os.path.join(PROCESSED_DIR, "b1_cleaned_house_data.csv")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"\n[OK] 清洗后数据已保存: {path}")
    print(f"     共 {len(df)} 行, {len(df.columns)} 列")


def main():
    print("=" * 60)
    print("B.1 房源信息数据清洗")
    print("=" * 60)

    df = load_raw_data()
    explore_data(df)
    df_clean = clean_data(df)
    save_cleaned_data(df_clean)
    print("\n[完成] B.1 数据清洗结束。")


if __name__ == "__main__":
    main()
