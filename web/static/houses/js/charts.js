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

function renderDashboardCharts() {
  const overview = readJson("overview-data") || {};
  const priceBuckets = readJson("price-buckets-data") || [];

  const cityChart = chartFor("city-chart");
  if (cityChart) {
    const rows = overview.city_distribution || [];
    cityChart.setOption({
      tooltip: {trigger: "axis"},
      grid: {left: 48, right: 20, top: 24, bottom: 40},
      xAxis: {type: "category", data: rows.map((row) => row.name)},
      yAxis: {type: "value"},
      series: [
        {
          name: "房源数",
          type: "bar",
          data: rows.map((row) => row.count),
          itemStyle: {color: "#2563eb"},
        },
      ],
    });
  }

  const priceChart = chartFor("price-chart");
  if (priceChart) {
    priceChart.setOption({
      tooltip: {trigger: "item"},
      series: [
        {
          name: "总价区间",
          type: "pie",
          radius: ["44%", "72%"],
          data: priceBuckets.map((row) => ({name: row.label, value: row.count})),
        },
      ],
    });
  }
}

function renderProvinceCharts() {
  const stats = readJson("province-stats-data") || {};
  const rows = stats.cities || [];
  const chart = chartFor("province-chart");
  if (!chart) {
    return;
  }
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

function renderCityCharts() {
  const stats = readJson("city-stats-data") || {};
  const rows = stats.districts || [];
  const chart = chartFor("city-detail-chart");
  if (!chart) {
    return;
  }
  chart.setOption({
    tooltip: {trigger: "axis"},
    grid: {left: 56, right: 24, top: 28, bottom: 44},
    xAxis: {type: "category", data: rows.map((row) => row.name)},
    yAxis: {type: "value"},
    series: [
      {
        name: "平均单价",
        type: "bar",
        data: rows.map((row) => row.avg_unit_price),
        itemStyle: {color: "#d97706"},
      },
    ],
  });
}

window.addEventListener("resize", () => {
  document.querySelectorAll(".chart").forEach((element) => {
    const instance = typeof echarts !== "undefined" ? echarts.getInstanceByDom(element) : null;
    if (instance) {
      instance.resize();
    }
  });
});
