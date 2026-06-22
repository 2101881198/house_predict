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

function renderDashboardCharts() {
  const overview = readJson("overview-data") || {};
  const priceBuckets = readJson("price-buckets-data") || [];
  const cityRows = overview.city_distribution || [];

  renderBarChart(
    "city-chart",
    cityRows.map((row) => row.name),
    cityRows.map((row) => row.count),
    "房源数",
    "#2563eb",
  );
  renderPieChart("price-chart", priceBuckets, "总价区间", "label", "count");

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

  renderPieChart("province-price-chart", priceBuckets, "总价区间", "label", "count");
  renderBarChart(
    "province-area-chart",
    areaBuckets.map((row) => row.label),
    areaBuckets.map((row) => row.count),
    "面积区间",
    "#d97706",
  );
  renderPieChart("province-room-chart", roomTypes, "户型结构", "room_type", "count");
}

function renderCityCharts() {
  const stats = readJson("city-stats-data") || {};
  const rows = stats.districts || [];
  const priceBuckets = readJson("city-price-buckets-data") || [];
  const areaBuckets = readJson("city-area-buckets-data") || [];
  const roomTypes = readJson("city-room-types-data") || [];

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

  renderPieChart("city-price-chart", priceBuckets, "总价区间", "label", "count");
  renderBarChart(
    "city-area-chart",
    areaBuckets.map((row) => row.label),
    areaBuckets.map((row) => row.count),
    "面积区间",
    "#d97706",
  );
  renderPieChart("city-room-chart", roomTypes, "户型结构", "room_type", "count");
}

window.addEventListener("resize", () => {
  document.querySelectorAll(".chart").forEach((element) => {
    const instance = typeof echarts !== "undefined" ? echarts.getInstanceByDom(element) : null;
    if (instance) {
      instance.resize();
    }
  });
});
