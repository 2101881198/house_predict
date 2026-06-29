function readJson(id) {
  const element = document.getElementById(id);
  if (!element) {
    return null;
  }
  try {
    return JSON.parse(element.textContent);
  } catch (error) {
    return null;
  }
}

function chartFor(id) {
  const element = document.getElementById(id);
  if (!element || typeof echarts === "undefined") {
    return null;
  }
  return echarts.init(element);
}

function formatCompactNumber(value) {
  const number = Number(value) || 0;
  const absValue = Math.abs(number);
  if (absValue >= 10000) {
    const compactValue = number / 10000;
    return `${Number.isInteger(compactValue) ? compactValue : compactValue.toFixed(1)}万`;
  }
  if (absValue >= 1000) {
    const compactValue = number / 1000;
    return `${Number.isInteger(compactValue) ? compactValue : compactValue.toFixed(1)}k`;
  }
  return number.toLocaleString("zh-CN");
}

function formatPercent(value, total) {
  if (!total) {
    return "0%";
  }
  return `${((Number(value) / total) * 100).toFixed(1)}%`;
}

function hiddenValueAxis() {
  return {
    type: "value",
    axisLabel: {show: false},
    axisLine: {show: false},
    axisTick: {show: false},
    splitLine: {lineStyle: {color: "#e6ebf2"}},
  };
}

function renderBarChart(id, labels, values, name, color) {
  const chart = chartFor(id);
  if (!chart) {
    return;
  }
  chart.setOption({
    tooltip: {trigger: "axis"},
    grid: {left: 56, right: 24, top: 36, bottom: 44},
    xAxis: {type: "category", data: labels},
    yAxis: {type: "value"},
    series: [{name, type: "bar", data: values, itemStyle: {color}}],
  });
}

function renderMultiLineChart(id, seriesRows, valueName) {
  const chart = chartFor(id);
  if (!chart) {
    return;
  }
  const dates = Array.from(
    new Set(seriesRows.flatMap((row) => (row.trend || []).map((item) => item.date))),
  ).sort();

  if (!dates.length) {
    renderEmptyChart(chart, "暂无价格趋势数据");
    return;
  }

  chart.setOption({
    tooltip: {trigger: "axis"},
    legend: {top: 0, type: "scroll"},
    grid: {left: 56, right: 24, top: 48, bottom: 44},
    xAxis: {type: "category", data: dates},
    yAxis: {type: "value", name: "万元"},
    series: seriesRows.map((row) => {
      const valuesByDate = new Map(
        (row.trend || []).map((item) => [item.date, item.avg_total_price]),
      );
      return {
        name: row.city,
        type: "line",
        smooth: true,
        connectNulls: false,
        data: dates.map((date) => valuesByDate.get(date) ?? null),
      };
    }),
  });
}

function renderHorizontalBarChart(id, labels, values, name, color) {
  const chart = chartFor(id);
  if (!chart) {
    return;
  }
  chart.setOption({
    tooltip: {
      trigger: "axis",
      axisPointer: {type: "shadow"},
      appendToBody: true,
      formatter: (params) => {
        const item = params[0] || {};
        return `${item.name}<br>${name}：${Number(item.value || 0).toLocaleString("zh-CN")}`;
      },
    },
    grid: {left: 128, right: 88, top: 28, bottom: 18},
    xAxis: hiddenValueAxis(),
    yAxis: {
      type: "category",
      data: labels,
      inverse: true,
      axisLabel: {width: 116, overflow: "truncate"},
    },
    series: [
      {
        name,
        type: "bar",
        data: values,
        itemStyle: {color},
        label: {show: true, position: "right", formatter: (params) => formatCompactNumber(params.value)},
      },
    ],
  });
}

function renderDistributionBarChart(id, rows, name, labelKey, valueKey, color) {
  const chart = chartFor(id);
  if (!chart) {
    return;
  }
  const visibleRows = rows
    .map((row) => ({
      label: row[labelKey] || "未知",
      value: Number(row[valueKey]) || 0,
    }))
    .filter((row) => row.value > 0);
  const total = visibleRows.reduce((sum, row) => sum + row.value, 0);

  if (!total) {
    renderEmptyChart(chart, "暂无分布数据");
    return;
  }

  chart.setOption({
    tooltip: {
      trigger: "axis",
      axisPointer: {type: "shadow"},
      appendToBody: true,
      formatter: (params) => {
        const item = params[0] || {};
        const value = Number(item.value || 0);
        return [
          item.name,
          `${name}：${value.toLocaleString("zh-CN")} 套`,
          `占比：${formatPercent(value, total)}`,
        ].join("<br>");
      },
    },
    grid: {left: 112, right: 126, top: 28, bottom: 18},
    xAxis: hiddenValueAxis(),
    yAxis: {
      type: "category",
      data: visibleRows.map((row) => row.label),
      inverse: true,
      axisLabel: {width: 104, overflow: "truncate"},
    },
    series: [
      {
        name,
        type: "bar",
        data: visibleRows.map((row) => row.value),
        itemStyle: {color},
        label: {
          show: true,
          position: "right",
          formatter: (params) => `${formatCompactNumber(params.value)}套  ${formatPercent(params.value, total)}`,
        },
      },
    ],
  });
}

function topRowsWithOther(rows, labelKey, valueKey, limit = 8) {
  const normalizedRows = rows
    .map((row) => ({
      label: row[labelKey] || "未知",
      value: Number(row[valueKey]) || 0,
    }))
    .filter((row) => row.value > 0)
    .sort((left, right) => right.value - left.value);
  const visibleRows = normalizedRows.slice(0, limit);
  const otherValue = normalizedRows
    .slice(limit)
    .reduce((total, row) => total + row.value, 0);

  if (otherValue > 0) {
    visibleRows.push({label: "其他", value: otherValue});
  }

  return visibleRows;
}

function renderTopHorizontalChart(id, rows, name, labelKey, valueKey, color, limit = 8) {
  const visibleRows = topRowsWithOther(rows, labelKey, valueKey, limit);

  renderHorizontalBarChart(
    id,
    visibleRows.map((row) => row.label),
    visibleRows.map((row) => row.value),
    name,
    color,
  );
}

function renderPieChart(id, rows, name, labelKey, valueKey) {
  const chart = chartFor(id);
  if (!chart) {
    return;
  }
  chart.setOption({
    tooltip: {trigger: "item"},
    series: [
      {
        name,
        type: "pie",
        radius: ["42%", "72%"],
        data: rows.map((row) => ({name: row[labelKey], value: row[valueKey]})),
      },
    ],
  });
}

function normalizeCityMapName(name) {
  if (!name) {
    return "";
  }
  return name.endsWith("市") ? name : `${name}市`;
}

function renderEmptyChart(chart, message) {
  chart.setOption({
    title: {
      text: message,
      left: "center",
      top: "middle",
      textStyle: {fontSize: 15, color: "#687386", fontWeight: 500},
    },
  });
}

function renderProvinceMap() {
  const chart = chartFor("province-map-chart");
  if (!chart) {
    return;
  }
  const stats = readJson("province-stats-data") || {};
  const meta = readJson("teacher-map-meta") || {};
  const rows = stats.cities || [];
  const maxCount = Math.max(1, ...rows.map((row) => row.count || 0));
  const data = rows.map((row) => ({
    name: normalizeCityMapName(row.city),
    city: row.city,
    value: row.count,
    avg_total_price: row.avg_total_price,
    avg_unit_price: row.avg_unit_price,
  }));

  chart.setOption({
    tooltip: {
      trigger: "item",
      formatter: (params) => {
        const row = params.data || {};
        if (!row.city) {
          return `${params.name}<br>暂无房源数据`;
        }
        return [
          row.city,
          `房源数：${row.value}`,
          `平均总价：${row.avg_total_price} 万元`,
          `平均单价：${row.avg_unit_price} 元/㎡`,
        ].join("<br>");
      },
    },
    visualMap: {
      min: 0,
      max: maxCount,
      left: 12,
      bottom: 12,
      calculable: true,
      inRange: {color: ["#dbeafe", "#60a5fa", "#1d4ed8"]},
    },
    series: [
      {
        name: "房源数",
        type: "map",
        map: meta.province_map_name || "shandong",
        roam: true,
        label: {show: true, color: "#172033"},
        emphasis: {label: {show: true}},
        data,
      },
    ],
  });
}

async function renderCityMap() {
  const chart = chartFor("city-map-chart");
  if (!chart) {
    return;
  }
  const stats = readJson("city-stats-data") || {};
  const meta = readJson("teacher-map-meta") || {};
  const rows = stats.districts || [];
  if (!meta.city_map_file) {
    renderEmptyChart(chart, "暂无该城市地图资料");
    return;
  }

  try {
    const response = await fetch(`${meta.city_map_base_url}${meta.city_map_file}`);
    if (!response.ok) {
      throw new Error(`Map request failed: ${response.status}`);
    }
    const geoJson = await response.json();
    const mapName = `teacher-${meta.city_name}`;
    echarts.registerMap(mapName, geoJson);
    const maxCount = Math.max(1, ...rows.map((row) => row.count || 0));
    chart.setOption({
      tooltip: {
        trigger: "item",
        formatter: (params) => {
          const row = params.data || {};
          if (!row.name) {
            return `${params.name}<br>暂无房源数据`;
          }
          return [
            row.name,
            `房源数：${row.value}`,
            `平均总价：${row.avg_total_price} 万元`,
            `平均单价：${row.avg_unit_price} 元/㎡`,
          ].join("<br>");
        },
      },
      visualMap: {
        min: 0,
        max: maxCount,
        left: 12,
        bottom: 12,
        calculable: true,
        inRange: {color: ["#ecfdf5", "#34d399", "#047857"]},
      },
      series: [
        {
          name: "区县房源数",
          type: "map",
          map: mapName,
          roam: true,
          label: {show: true, color: "#172033"},
          emphasis: {label: {show: true}},
          data: rows.map((row) => ({
            name: row.name,
            value: row.count,
            avg_total_price: row.avg_total_price,
            avg_unit_price: row.avg_unit_price,
          })),
        },
      ],
    });
  } catch (error) {
    renderEmptyChart(chart, "地图资料加载失败");
  }
}

function renderDashboardCharts() {
  const overview = readJson("overview-data") || {};
  const priceBuckets = readJson("price-buckets-data") || [];
  const areaBuckets = readJson("area-buckets-data") || [];
  const roomTypes = readJson("room-types-data") || [];
  const decorations = readJson("decoration-data") || [];
  const cityRows = overview.city_distribution || [];
  const districtRows = overview.hot_districts || [];
  const cityPriceRows = overview.city_price_rankings || [];
  const cityTrendRows = overview.city_price_trends || [];

  renderBarChart(
    "city-chart",
    cityRows.map((row) => row.name),
    cityRows.map((row) => row.count),
    "房源数",
    "#2563eb",
  );
  renderDistributionBarChart("price-chart", priceBuckets, "房源数量", "label", "count", "#2563eb");

  renderBarChart(
    "area-chart",
    areaBuckets.map((row) => row.label),
    areaBuckets.map((row) => row.count),
    "面积区间",
    "#d97706",
  );
  renderTopHorizontalChart("room-chart", roomTypes, "户型结构", "room_type", "count", "#059669");
  renderBarChart(
    "decoration-chart",
    decorations.map((row) => row.decoration),
    decorations.map((row) => row.count),
    "装修情况",
    "#7c3aed",
  );
  renderHorizontalBarChart(
    "district-chart",
    districtRows.map((row) => `${row.city} ${row.district}`),
    districtRows.map((row) => row.count),
    "房源数量",
    "#0891b2",
  );
  renderBarChart(
    "city-price-chart",
    cityPriceRows.map((row) => row.city),
    cityPriceRows.map((row) => row.avg_unit_price),
    "平均单价",
    "#dc2626",
  );
  renderMultiLineChart("city-comparison-trend-chart", cityTrendRows, "平均总价");

  const trendChart = chartFor("trend-chart");
  if (trendChart) {
    const rows = overview.trend || [];
    trendChart.setOption({
      tooltip: {trigger: "axis"},
      grid: {left: 56, right: 24, top: 36, bottom: 44},
      xAxis: {type: "category", data: rows.map((row) => row.date)},
      yAxis: {type: "value", name: "万元"},
      series: [
        {
          name: "平均总价",
          type: "line",
          smooth: true,
          data: rows.map((row) => row.avg_total_price),
          itemStyle: {color: "#059669"},
        },
      ],
    });
  }

  const mapChart = chartFor("map-chart");
  if (mapChart) {
    const rows = overview.map_points || [];
    mapChart.setOption({
      tooltip: {
        trigger: "item",
        formatter: (params) => {
          const data = params.data || {};
          return `${data.name}<br>${data.city} ${data.district}<br>${data.value[2]} 万元`;
        },
      },
      grid: {left: 64, right: 24, top: 36, bottom: 44},
      xAxis: {type: "value", name: "经度", scale: true},
      yAxis: {type: "value", name: "纬度", scale: true},
      series: [
        {
          name: "房源坐标",
          type: "scatter",
          symbolSize: 10,
          data: rows.map((row) => ({
            name: row.title,
            city: row.city,
            district: row.district,
            value: [row.longitude, row.latitude, row.total_price],
          })),
          itemStyle: {color: "#d97706"},
        },
      ],
    });
  }
}

function renderProvinceCharts() {
  const stats = readJson("province-stats-data") || {};
  const rows = stats.cities || [];
  const priceBuckets = readJson("province-price-buckets-data") || [];
  const areaBuckets = readJson("province-area-buckets-data") || [];
  const roomTypes = readJson("province-room-types-data") || [];

  renderProvinceMap();

  const chart = chartFor("province-chart");
  if (chart) {
    chart.setOption({
      tooltip: {trigger: "axis"},
      legend: {top: 0},
      grid: {left: 56, right: 24, top: 48, bottom: 44},
      xAxis: {type: "category", data: rows.map((row) => row.city)},
      yAxis: [
        {type: "value", name: "房源数"},
        {type: "value", name: "单价"},
      ],
      series: [
        {
          name: "房源数",
          type: "bar",
          data: rows.map((row) => row.count),
          itemStyle: {color: "#2563eb"},
        },
        {
          name: "平均单价",
          type: "line",
          yAxisIndex: 1,
          data: rows.map((row) => row.avg_unit_price),
          itemStyle: {color: "#059669"},
        },
      ],
    });
  }

  renderDistributionBarChart("province-price-chart", priceBuckets, "房源数量", "label", "count", "#2563eb");
  renderBarChart(
    "province-area-chart",
    areaBuckets.map((row) => row.label),
    areaBuckets.map((row) => row.count),
    "面积区间",
    "#d97706",
  );
  renderTopHorizontalChart("province-room-chart", roomTypes, "户型结构", "room_type", "count", "#059669");
}

function renderCityCharts() {
  const stats = readJson("city-stats-data") || {};
  const rows = stats.districts || [];
  const priceBuckets = readJson("city-price-buckets-data") || [];
  const areaBuckets = readJson("city-area-buckets-data") || [];
  const roomTypes = readJson("city-room-types-data") || [];
  const decorations = readJson("city-decoration-data") || [];

  renderCityMap();

  const chart = chartFor("city-detail-chart");
  if (chart) {
    chart.setOption({
      tooltip: {trigger: "axis"},
      legend: {top: 0},
      grid: {left: 56, right: 24, top: 48, bottom: 44},
      xAxis: {type: "category", data: rows.map((row) => row.name)},
      yAxis: [
        {type: "value", name: "房源数"},
        {type: "value", name: "单价"},
      ],
      series: [
        {
          name: "房源数",
          type: "bar",
          data: rows.map((row) => row.count),
          itemStyle: {color: "#2563eb"},
        },
        {
          name: "平均单价",
          type: "line",
          yAxisIndex: 1,
          data: rows.map((row) => row.avg_unit_price),
          itemStyle: {color: "#059669"},
        },
      ],
    });
  }

  renderDistributionBarChart("city-price-chart", priceBuckets, "房源数量", "label", "count", "#2563eb");
  renderBarChart(
    "city-area-chart",
    areaBuckets.map((row) => row.label),
    areaBuckets.map((row) => row.count),
    "面积区间",
    "#d97706",
  );
  renderTopHorizontalChart("city-room-chart", roomTypes, "户型结构", "room_type", "count", "#059669");
  renderBarChart(
    "city-decoration-chart",
    decorations.map((row) => row.decoration),
    decorations.map((row) => row.count),
    "装修情况",
    "#7c3aed",
  );
  renderMultiLineChart(
    "city-trend-chart",
    [{city: stats.city?.name || "当前城市", trend: stats.trend || []}],
    "平均总价",
  );
}

window.addEventListener("resize", () => {
  document.querySelectorAll(".chart").forEach((element) => {
    const instance = typeof echarts !== "undefined" ? echarts.getInstanceByDom(element) : null;
    if (instance) {
      instance.resize();
    }
  });
});
