"""
B.2 山东省各城市的房源分析
================================
功能：
1. 加载 B.1 清洗后的数据
2. 从城市维度对山东各城市房源进行对比分析：
   - 各城市房源数量分布
   - 各城市平均总价、单价对比
   - 各城市面积分布
   - 各城市房龄、装修、户型偏好
3. 可视化输出（柱状图、箱线图、热力图）
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

# 中文字体设置（先清缓存避免乱码）
import matplotlib.font_manager as fm
fm._load_fontmanager(try_read_cache=False)
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DIR

# 输出图表目录
FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def load_data() -> pd.DataFrame:
    """加载清洗后数据"""
    path = os.path.join(PROCESSED_DIR, "b1_cleaned_house_data.csv")
    if not os.path.exists(path):
        print(f"[警告] {path} 不存在，生成演示数据...")
        from part_b.b1_data_cleaning import _generate_demo_data, clean_data
        df = _generate_demo_data(500)
        df = clean_data(df)
        return df
    return pd.read_csv(path, encoding="utf-8-sig")


def plot_city_counts(df: pd.DataFrame):
    """各城市房源数量分布"""
    fig, ax = plt.subplots(figsize=(12, 6))
    city_counts = df["city"].value_counts()
    colors = sns.color_palette("viridis", len(city_counts))
    bars = ax.bar(city_counts.index, city_counts.values, color=colors, edgecolor="white")

    for bar, val in zip(bars, city_counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                str(val), ha="center", va="bottom", fontsize=10)

    ax.set_title("山东省各城市房源数量分布", fontsize=16, fontweight="bold")
    ax.set_xlabel("城市", fontsize=12)
    ax.set_ylabel("房源数量", fontsize=12)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b2_city_counts.png"), dpi=150)
    print(f"[√] 图表已保存: b2_city_counts.png")


def plot_city_price_comparison(df: pd.DataFrame):
    """各城市均价、总价对比（双轴柱状图+箱线图）"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    city_order = df.groupby("city")["unit_price"].mean().sort_values(ascending=False).index

    # 子图1：平均单价
    ax = axes[0]
    avg_price = df.groupby("city")["unit_price"].mean().loc[city_order]
    bars = ax.bar(avg_price.index, avg_price.values, color=sns.color_palette("Reds_r", len(avg_price)), edgecolor="white")
    for bar, val in zip(bars, avg_price.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f"{val:.0f}", ha="center", va="bottom", fontsize=8)
    ax.set_title("各城市平均单价 (元/㎡)", fontsize=14)
    ax.set_ylabel("元/㎡", fontsize=11)
    ax.tick_params(axis="x", rotation=30)

    # 子图2：平均总价
    ax = axes[1]
    avg_total = df.groupby("city")["total_price"].mean().loc[city_order]
    bars = ax.bar(avg_total.index, avg_total.values, color=sns.color_palette("Blues_r", len(avg_total)), edgecolor="white")
    for bar, val in zip(bars, avg_total.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{val:.0f}万", ha="center", va="bottom", fontsize=8)
    ax.set_title("各城市平均总价 (万元)", fontsize=14)
    ax.set_ylabel("万元", fontsize=11)
    ax.tick_params(axis="x", rotation=30)

    # 子图3：单价箱线图
    ax = axes[2]
    df_plot = df[df["city"].isin(city_order[:8])]  # 取前8个城市
    sns.boxplot(data=df_plot, x="city", y="unit_price", order=city_order[:8],
                palette="Spectral", ax=ax)
    ax.set_title("各城市单价分布 (箱线图)", fontsize=14)
    ax.set_ylabel("元/㎡", fontsize=11)
    ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b2_city_price_comparison.png"), dpi=150)
    print(f"[√] 图表已保存: b2_city_price_comparison.png")


def plot_city_area_distribution(df: pd.DataFrame):
    """各城市面积分布"""
    cities = df["city"].value_counts().index[:6]
    fig, ax = plt.subplots(figsize=(12, 6))

    for city in cities:
        city_data = df[df["city"] == city]["area"]
        ax.hist(city_data, bins=30, alpha=0.5, label=city, density=True)

    ax.set_title("各城市房源面积分布", fontsize=16, fontweight="bold")
    ax.set_xlabel("面积 (㎡)", fontsize=12)
    ax.set_ylabel("密度", fontsize=12)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b2_city_area_distribution.png"), dpi=150)
    print(f"[√] 图表已保存: b2_city_area_distribution.png")


def plot_city_heatmap(df: pd.DataFrame):
    """各城市特征热力图——涵盖价格、户型、建筑结构、房龄等"""
    agg_dict = {
        "平均单价": ("unit_price", "mean"),
        "平均总价": ("total_price", "mean"),
        "平均面积": ("area", "mean"),
        "房源数量": ("city", "count"),
    }
    city_agg = df.groupby("city").agg(**{k: v for k, v in agg_dict.items()}).round(1)

    fig, ax = plt.subplots(figsize=(12, 8))
    city_norm = (city_agg - city_agg.min()) / (city_agg.max() - city_agg.min())
    sns.heatmap(city_norm, annot=city_agg.values, fmt=".1f",
                cmap="YlOrRd", ax=ax, linewidths=0.5,
                annot_kws={"fontsize": 9})
    ax.set_title("山东省各城市房源特征对比 (数值为原始值)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b2_city_heatmap.png"), dpi=150)
    print(f"[OK] 图表已保存: b2_city_heatmap.png")


# ============================================================
#  新增：户型分布、建筑结构、产权、抵押、挂牌分析
# ============================================================
def plot_city_layout_distribution(df: pd.DataFrame):
    """各城市户型分布"""
    if "layout" not in df.columns:
        return
    cities = df["city"].value_counts().index[:4]
    top_layouts = df["layout"].value_counts().head(6).index

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    for ax, city in zip(axes.flat, cities):
        city_df = df[df["city"] == city]
        layout_counts = city_df["layout"].value_counts()
        # 只取 top layouts
        plot_data = layout_counts[layout_counts.index.isin(top_layouts)]
        colors = sns.color_palette("Set2", len(plot_data))
        wedges, texts, autotexts = ax.pie(
            plot_data.values, labels=plot_data.index, autopct="%1.1f%%",
            colors=colors, pctdistance=0.85
        )
        ax.set_title(f"{city} 户型分布", fontsize=13, fontweight="bold")

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b2_layout_distribution.png"), dpi=150)
    print(f"[OK] 图表已保存: b2_layout_distribution.png")


def plot_building_structure_analysis(df: pd.DataFrame):
    """各城市建筑结构分布 + 建筑结构与单价关系"""
    if "building_structure" not in df.columns:
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 子图1：各城市建筑结构占比（堆叠柱状图）
    ax = axes[0]
    cities = df["city"].value_counts().index[:6]
    structs = df["building_structure"].value_counts().index
    cross_tab = pd.crosstab(df["city"], df["building_structure"])
    cross_tab = cross_tab.loc[cross_tab.index.isin(cities), cross_tab.columns.isin(structs)]
    cross_tab_pct = cross_tab.div(cross_tab.sum(axis=1), axis=0)
    cross_tab_pct.plot(kind="bar", stacked=True, ax=ax, colormap="Set3")
    ax.set_title("各城市建筑结构占比", fontsize=13, fontweight="bold")
    ax.set_ylabel("占比", fontsize=11)
    ax.legend(title="建筑结构", fontsize=8, title_fontsize=9)
    ax.tick_params(axis="x", rotation=30)

    # 子图2：建筑结构 vs 单价
    ax = axes[1]
    struct_order = df.groupby("building_structure")["unit_price"].mean().sort_values(ascending=False).index
    sns.boxplot(data=df, x="building_structure", y="unit_price",
                order=struct_order, palette="Set3", ax=ax, legend=False)
    ax.set_title("建筑结构 vs 单价", fontsize=13, fontweight="bold")
    ax.set_ylabel("单价 (元/㎡)", fontsize=11)
    ax.tick_params(axis="x", rotation=20)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b2_building_structure.png"), dpi=150)
    print(f"[OK] 图表已保存: b2_building_structure.png")


def plot_property_ownership_analysis(df: pd.DataFrame):
    """产权所属 & 抵押信息分析"""
    if "property_ownership" not in df.columns:
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # 产权所属分布
    ax = axes[0]
    ownership_counts = df["property_ownership"].value_counts()
    colors = sns.color_palette("Pastel1", len(ownership_counts))
    ax.pie(ownership_counts.values, labels=ownership_counts.index,
           autopct="%1.1f%%", colors=colors, pctdistance=0.85)
    ax.set_title("产权所属分布", fontsize=13, fontweight="bold")

    # 抵押信息分布
    ax = axes[1]
    if "mortgage_info" in df.columns:
        mortgage_counts = df["mortgage_info"].value_counts()
        colors = sns.color_palette("Pastel2", len(mortgage_counts))
        ax.pie(mortgage_counts.values, labels=mortgage_counts.index,
               autopct="%1.1f%%", colors=colors, pctdistance=0.85)
    ax.set_title("抵押信息分布", fontsize=13, fontweight="bold")

    # 产权所属 vs 单价
    ax = axes[2]
    if "property_ownership" in df.columns:
        own_order = df.groupby("property_ownership")["unit_price"].mean().sort_values(ascending=False).index
        sns.barplot(data=df, x="property_ownership", y="unit_price",
                    order=own_order, palette="Set2", ax=ax, legend=False)
        ax.set_title("产权所属 vs 平均单价", fontsize=13, fontweight="bold")
        ax.set_ylabel("单价 (元/㎡)", fontsize=11)
        ax.tick_params(axis="x", rotation=15)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b2_property_mortgage.png"), dpi=150)
    print(f"[OK] 图表已保存: b2_property_mortgage.png")


def plot_listing_time_analysis(df: pd.DataFrame):
    """挂牌时间分析"""
    if "listing_time" not in df.columns:
        return

    # 尝试解析为 datetime
    try:
        listing_dt = pd.to_datetime(df["listing_time"], errors="coerce")
    except:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 按月统计挂牌量
    ax = axes[0]
    monthly = listing_dt.dt.to_period("M").value_counts().sort_index()
    monthly.index = monthly.index.astype(str)
    ax.plot(range(len(monthly)), monthly.values, "o-", color="steelblue", markersize=6)
    ax.set_xticks(range(0, len(monthly), max(1, len(monthly)//6)))
    ax.set_xticklabels(monthly.index[::max(1, len(monthly)//6)], rotation=30, fontsize=8)
    ax.set_title("各月挂牌房源数量", fontsize=13, fontweight="bold")
    ax.set_ylabel("房源数", fontsize=11)

    # 挂牌天数分布
    ax = axes[1]
    if "deed_year" in df.columns:
        deed_counts = df["deed_year"].value_counts()
        colors = sns.color_palette("coolwarm", len(deed_counts))
        ax.bar(deed_counts.index, deed_counts.values, color=colors, edgecolor="white")
        ax.set_title("房本年限分布", fontsize=13, fontweight="bold")
        ax.set_ylabel("房源数", fontsize=11)
        ax.tick_params(axis="x", rotation=15)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "b2_listing_time.png"), dpi=150)
    print(f"[OK] 图表已保存: b2_listing_time.png")


def print_city_statistics(df: pd.DataFrame):
    """打印城市维度的统计表格——涵盖全部分析维度"""
    print("\n" + "=" * 70)
    print("山东省各城市房源统计（价格、户型、建筑结构、产权、抵押、挂牌）")
    print("=" * 70)

    agg_specs = {
        "房源数": ("city", "count"),
        "均价_元每平": ("unit_price", lambda x: f"{x.mean():.0f}"),
        "总价中位数_万": ("total_price", lambda x: f"{x.median():.1f}"),
        "面积中位数_平": ("area", lambda x: f"{x.median():.1f}"),
        # "平均房龄_年": 无 build_year 数据，跳过
    }

    # 动态加入可用字段
    for col, label in [
        ("layout", "主要户型"),
        ("building_structure", "主流建筑结构"),
        ("property_ownership", "主流产权所属"),
        ("mortgage_info", "主流抵押情况"),
    ]:
        if col in df.columns:
            agg_specs[label] = (col, lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "未知")

    stats = df.groupby("city").agg(**{k: v for k, v in agg_specs.items()}).sort_values("房源数", ascending=False)
    print(stats.to_string())


def main():
    print("=" * 60)
    print("B.2 山东省各城市的房源分析")
    print("=" * 60)

    df = load_data()
    print(f"[1] 加载数据: {df.shape[0]} 行, {len(df['city'].unique())} 个城市")

    print("\n[2] 生成可视化图表...")
    plot_city_counts(df)
    plot_city_price_comparison(df)
    plot_city_area_distribution(df)
    plot_city_heatmap(df)
    # 新增分析维度
    plot_city_layout_distribution(df)
    plot_building_structure_analysis(df)
    plot_property_ownership_analysis(df)
    plot_listing_time_analysis(df)

    print("\n[3] 统计表格...")
    print_city_statistics(df)

    print(f"\n[完成] B.2 分析结束。图表保存在: {FIG_DIR}")


if __name__ == "__main__":
    main()
