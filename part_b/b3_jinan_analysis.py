"""
B.3 济南市房源分析
=======================
功能：
1. 从清洗数据中筛选济南市房源
2. 济南各区房源分布与均价
3. 济南房源价格影响因素分析：
   - 面积-价格关系
   - 房龄-价格关系
   - 朝向/装修/楼层对价格的影响
   - 热门小区 TOP N
4. 济南房价空间分布（如经纬度散点图）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import os
import sys
import io

# 修复 Windows GBK 终端编码问题
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except (AttributeError, OSError):
        pass

import matplotlib.font_manager as fm
fm._load_fontmanager(try_read_cache=False)
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DIR

FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def load_data() -> pd.DataFrame:
    """加载数据，筛选济南市"""
    path = os.path.join(PROCESSED_DIR, "b1_cleaned_house_data.csv")
    if not os.path.exists(path):
        from part_b.b1_data_cleaning import _generate_demo_data, clean_data
        df = _generate_demo_data(500)
        df = clean_data(df)
    else:
        df = pd.read_csv(path, encoding="utf-8-sig")

    jn = df[df["city"] == "济南"].copy()
    if len(jn) == 0:
        print("[警告] 数据中无济南房源，使用全部数据模拟")
        jn = df.copy()
        jn["city"] = "济南"
    print(f"[1] 济南市房源: {len(jn)} 条")
    return jn


# ============================================================
#  济南各区分析
# ============================================================
def analyze_jinan_districts(df: pd.DataFrame):
    """济南各行政区房源分析"""
    print("\n" + "=" * 50)
    print("济南各区房源统计")
    print("=" * 50)

    if "district" not in df.columns:
        print("无 district 字段")
        return

    stats = df.groupby("district").agg(
        房源数=("district", "count"),
        平均单价=("unit_price", "mean"),
        中位总价=("total_price", "median"),
        平均面积=("area", "mean"),
        # 平均房龄: 无 build_year 数据
    ).round(1).sort_values("房源数", ascending=False)

    print(stats.to_string())

    # 可视化
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    district_order = stats.index
    colors = sns.color_palette("coolwarm", len(district_order))
    ax.bar(district_order, stats["房源数"], color=colors, edgecolor="white")
    for i, (idx, row) in enumerate(stats.iterrows()):
        ax.text(i, row["房源数"] + 1, str(int(row["房源数"])), ha="center", fontsize=9)
    ax.set_title("济南各区房源数量", fontsize=14)
    ax.tick_params(axis="x", rotation=30)

    ax = axes[1]
    ax.bar(district_order, stats["平均单价"], color=colors, edgecolor="white")
    for i, (idx, row) in enumerate(stats.iterrows()):
        ax.text(i, row["平均单价"] + 50, f"{row['平均单价']:.0f}", ha="center", fontsize=8)
    ax.set_title("济南各区平均单价 (元/㎡)", fontsize=14)
    ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b3_jinan_districts.png"), dpi=150)
    print("[√] 图表已保存: b3_jinan_districts.png")


# ============================================================
#  价格影响因素分析
# ============================================================
def analyze_price_factors(df: pd.DataFrame):
    """分析各因素对房价的影响"""
    print("\n" + "=" * 50)
    print("价格影响因素分析")
    print("=" * 50)

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # 1. 面积 vs 总价
    ax = axes[0, 0]
    sns.scatterplot(data=df, x="area", y="total_price", alpha=0.6,
                    hue="floor_level" if "floor_level" in df.columns else None, ax=ax)
    # 趋势线
    from numpy.polynomial.polynomial import polyfit
    x = df["area"].dropna()
    y = df["total_price"].loc[x.index]
    if len(x) > 1:
        b, m = polyfit(x, y, 1)
        ax.plot(x, b + m * x, "r--", linewidth=2, label="趋势线")
    ax.set_xlabel("面积 (㎡)", fontsize=11)
    ax.set_ylabel("总价 (万元)", fontsize=11)
    ax.set_title("面积 vs 总价", fontsize=13)
    ax.legend(fontsize=8)

    # 2. 面积 vs 单价
    ax = axes[0, 1]
    sns.scatterplot(data=df, x="area", y="unit_price", alpha=0.5, ax=ax)
    x = df["area"].dropna()
    y = df["unit_price"].loc[x.index]
    if len(x) > 1:
        b, m = polyfit(x, y, 1)
        ax.plot(x, b + m * x, "r--", linewidth=2)
    ax.set_xlabel("面积 (㎡)", fontsize=11)
    ax.set_ylabel("单价 (元/㎡)", fontsize=11)
    ax.set_title("面积 vs 单价", fontsize=13)

    # 3. 朝向 vs 单价
    ax = axes[0, 2]
    orient_col = "orientation_clean" if "orientation_clean" in df.columns else "orientation"
    if orient_col in df.columns:
        orient_order = df.groupby(orient_col)["unit_price"].mean().sort_values(ascending=False).index
        sns.boxplot(data=df, x=orient_col, y="unit_price", order=orient_order, ax=ax, palette="Set2")
        ax.set_title("朝向 vs 单价", fontsize=13)
        ax.tick_params(axis="x", rotation=20)

    # 4. 装修 vs 单价
    ax = axes[1, 0]
    if "decoration" in df.columns:
        decor_order = df.groupby("decoration")["unit_price"].mean().sort_values(ascending=False).index
        sns.boxplot(data=df, x="decoration", y="unit_price", order=decor_order, ax=ax, palette="Set2")
        ax.set_title("装修 vs 单价", fontsize=13)
        ax.tick_params(axis="x", rotation=20)

    # 5. 楼层 vs 单价
    ax = axes[1, 1]
    floor_col = "floor_level" if "floor_level" in df.columns else "floor"
    if floor_col in df.columns:
        sns.violinplot(data=df, x=floor_col, y="unit_price", ax=ax, palette="Set3")
        ax.set_title("楼层 vs 单价", fontsize=13)

    # 6. 户型热门排行
    ax = axes[1, 2]
    if "layout" in df.columns:
        layout_counts = df["layout"].value_counts().head(10)
        ax.barh(range(len(layout_counts)), layout_counts.values,
                color=sns.color_palette("viridis", len(layout_counts)))
        ax.set_yticks(range(len(layout_counts)))
        ax.set_yticklabels(layout_counts.index)
        ax.set_title("济南热门户型 TOP10", fontsize=13)
        ax.set_xlabel("房源数量", fontsize=11)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b3_jinan_price_factors.png"), dpi=150)
    print("[√] 图表已保存: b3_jinan_price_factors.png")


# ============================================================
#  热门小区分析
# ============================================================
def analyze_communities(df: pd.DataFrame):
    """热门小区 TOP N"""
    print("\n" + "=" * 50)
    print("济南热门小区 TOP 20")
    print("=" * 50)

    if "community" not in df.columns:
        return

    comm_stats = df.groupby("community").agg(
        房源数=("community", "count"),
        平均单价=("unit_price", "mean"),
        平均总价=("total_price", "mean"),
    ).round(1).sort_values("房源数", ascending=False)

    print(comm_stats.head(20).to_string())

    # 可视化 TOP 15
    top15 = comm_stats.head(15)

    fig, ax = plt.subplots(figsize=(10, 8))
    y_pos = range(len(top15))
    ax.barh(y_pos, top15["房源数"], color=sns.color_palette("magma", len(top15)))
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{name} ({price:.0f}元/㎡)" for name, price in zip(top15.index, top15["平均单价"])],
                       fontsize=9)
    ax.set_xlabel("房源数量", fontsize=12)
    ax.set_title("济南热门小区 TOP15 (标注均价)", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b3_jinan_communities.png"), dpi=150)
    print("[√] 图表已保存: b3_jinan_communities.png")


# ============================================================
#  空间分布分析
# ============================================================
def analyze_spatial(df: pd.DataFrame):
    """济南房源空间分布散点图（经纬度）"""
    if "longitude" not in df.columns or "latitude" not in df.columns:
        return
    if df["longitude"].isna().all() or df["latitude"].isna().all():
        return

    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(
        df["longitude"], df["latitude"],
        c=df["unit_price"], cmap="YlOrRd",
        s=df["area"] / 5, alpha=0.6, edgecolors="white", linewidth=0.3
    )
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("单价 (元/㎡)", fontsize=11)

    ax.set_xlabel("经度", fontsize=12)
    ax.set_ylabel("纬度", fontsize=12)
    ax.set_title("济南房源空间分布 (颜色=单价, 大小=面积)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b3_jinan_spatial.png"), dpi=150)
    print("[OK] 图表已保存: b3_jinan_spatial.png")


# ============================================================
#  B.3 新增分析维度：建筑结构、产权所属、抵押信息、挂牌时间
# ============================================================
def analyze_building_structure_jn(df: pd.DataFrame):
    """济南建筑结构分析"""
    if "building_structure" not in df.columns:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 建筑结构占比
    ax = axes[0]
    struct_counts = df["building_structure"].value_counts()
    colors = sns.color_palette("Set3", len(struct_counts))
    ax.pie(struct_counts.values, labels=struct_counts.index,
           autopct="%1.1f%%", colors=colors, pctdistance=0.85)
    ax.set_title("济南建筑结构分布", fontsize=13, fontweight="bold")

    # 建筑结构 vs 单价
    ax = axes[1]
    struct_order = df.groupby("building_structure")["unit_price"].mean().sort_values(ascending=False).index
    sns.barplot(data=df, x="building_structure", y="unit_price",
                order=struct_order, palette="Set3", ax=ax, legend=False)
    for i, val in enumerate(struct_order):
        mean_v = df[df["building_structure"] == val]["unit_price"].mean()
        ax.text(i, mean_v + 50, f"{mean_v:.0f}", ha="center", fontsize=9)
    ax.set_title("济南建筑结构 vs 平均单价", fontsize=13, fontweight="bold")
    ax.set_ylabel("单价 (元/㎡)", fontsize=11)
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=20)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b3_jinan_building_structure.png"), dpi=150)
    print("[OK] 图表已保存: b3_jinan_building_structure.png")


def analyze_ownership_mortgage_jn(df: pd.DataFrame):
    """济南产权所属和抵押信息分析"""
    if "property_ownership" not in df.columns and "mortgage_info" not in df.columns:
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # 产权所属 vs 均价
    ax = axes[0]
    if "property_ownership" in df.columns:
        own_order = df.groupby("property_ownership")["unit_price"].mean().sort_values(ascending=False).index
        sns.barplot(data=df, x="property_ownership", y="unit_price",
                    order=own_order, palette="Set2", ax=ax, legend=False)
        for i, val in enumerate(own_order):
            mean_v = df[df["property_ownership"] == val]["unit_price"].mean()
            ax.text(i, mean_v + 50, f"{mean_v:.0f}", ha="center", fontsize=9)
        ax.set_title("产权所属 vs 平均单价", fontsize=13, fontweight="bold")
        ax.set_ylabel("单价 (元/㎡)", fontsize=11)
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=15)

    # 抵押信息 vs 均价
    ax = axes[1]
    if "mortgage_info" in df.columns:
        mort_order = df.groupby("mortgage_info")["unit_price"].mean().sort_values(ascending=False).index
        sns.barplot(data=df, x="mortgage_info", y="unit_price",
                    order=mort_order, palette="Set2", ax=ax, legend=False)
        for i, val in enumerate(mort_order):
            mean_v = df[df["mortgage_info"] == val]["unit_price"].mean()
            ax.text(i, mean_v + 50, f"{mean_v:.0f}", ha="center", fontsize=9)
        ax.set_title("抵押信息 vs 平均单价", fontsize=13, fontweight="bold")
        ax.set_ylabel("单价 (元/㎡)", fontsize=11)
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=15)

    # 交易权属分布
    ax = axes[2]
    if "transaction_ownership" in df.columns:
        tx_counts = df["transaction_ownership"].value_counts()
        colors = sns.color_palette("Pastel1", len(tx_counts))
        ax.pie(tx_counts.values, labels=tx_counts.index,
               autopct="%1.1f%%", colors=colors, pctdistance=0.85)
        ax.set_title("交易权属分布", fontsize=13, fontweight="bold")

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b3_jinan_ownership_mortgage.png"), dpi=150)
    print("[OK] 图表已保存: b3_jinan_ownership_mortgage.png")


def analyze_listing_time_jn(df: pd.DataFrame):
    """济南挂牌时间分析"""
    if "listing_time" not in df.columns:
        return

    try:
        listing_dt = pd.to_datetime(df["listing_time"], errors="coerce")
    except:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 按月挂牌量趋势
    ax = axes[0]
    monthly = listing_dt.dt.to_period("M").value_counts().sort_index()
    monthly.index = monthly.index.astype(str)
    ax.fill_between(range(len(monthly)), monthly.values, alpha=0.3, color="steelblue")
    ax.plot(range(len(monthly)), monthly.values, "o-", color="steelblue", markersize=8)
    ax.set_xticks(range(0, len(monthly), max(1, len(monthly)//6)))
    ax.set_xticklabels(monthly.index[::max(1, len(monthly)//6)], rotation=30, fontsize=8)
    ax.set_title("济南各月挂牌房源数量", fontsize=13, fontweight="bold")
    ax.set_ylabel("房源数", fontsize=11)

    # 房本年限 vs 单价
    ax = axes[1]
    if "deed_year" in df.columns:
        deed_order = ["不满两年", "满两年", "满五年"]
        existing = [d for d in deed_order if d in df["deed_year"].values]
        if existing:
            sns.boxplot(data=df, x="deed_year", y="unit_price", order=existing,
                        palette="coolwarm", ax=ax, legend=False)
        ax.set_title("房本年限 vs 单价", fontsize=13, fontweight="bold")
        ax.set_ylabel("单价 (元/㎡)", fontsize=11)
        ax.set_xlabel("")

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b3_jinan_listing_time.png"), dpi=150)
    print("[OK] 图表已保存: b3_jinan_listing_time.png")


def print_jn_summary(df: pd.DataFrame):
    """打印济南市分析摘要"""
    print("\n" + "=" * 60)
    print("济南市房源分析摘要")
    print("=" * 60)

    print(f"  房源总数: {len(df)}")
    print(f"  平均单价: {df['unit_price'].mean():.0f} 元/㎡")
    print(f"  中位总价: {df['total_price'].median():.1f} 万元")
    print(f"  平均面积: {df['area'].mean():.1f} ㎡")
    # 平均房龄: 无 build_year 数据

    if "layout" in df.columns:
        print(f"  主要户型: {df['layout'].mode().iloc[0] if len(df['layout'].mode()) > 0 else 'N/A'}")
    if "orientation_clean" in df.columns:
        print(f"  主要朝向: {df['orientation_clean'].mode().iloc[0] if len(df['orientation_clean'].mode()) > 0 else 'N/A'}")
    if "building_structure" in df.columns:
        print(f"  主流建筑结构: {df['building_structure'].mode().iloc[0] if len(df['building_structure'].mode()) > 0 else 'N/A'}")
    if "property_ownership" in df.columns:
        print(f"  主流产权所属: {df['property_ownership'].mode().iloc[0] if len(df['property_ownership'].mode()) > 0 else 'N/A'}")
    if "mortgage_info" in df.columns:
        print(f"  主流抵押情况: {df['mortgage_info'].mode().iloc[0] if len(df['mortgage_info'].mode()) > 0 else 'N/A'}")
    if "decoration" in df.columns:
        print(f"  主流装修: {df['decoration'].mode().iloc[0] if len(df['decoration'].mode()) > 0 else 'N/A'}")
    print("=" * 60)


def main():
    print("=" * 60)
    print("B.3 济南市房源分析")
    print("=" * 60)

    df = load_data()

    analyze_jinan_districts(df)
    analyze_price_factors(df)
    analyze_communities(df)
    analyze_spatial(df)
    # 新增分析维度
    analyze_building_structure_jn(df)
    analyze_ownership_mortgage_jn(df)
    analyze_listing_time_jn(df)
    print_jn_summary(df)

    print(f"\n[完成] B.3 济南市分析结束。")


if __name__ == "__main__":
    main()
