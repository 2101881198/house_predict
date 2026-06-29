(function () {
  const timeNode = document.getElementById("current-time");
  if (!timeNode) {
    return;
  }

  const formatter = new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

  function updateCurrentTime() {
    const now = new Date();
    timeNode.textContent = formatter.format(now);
    timeNode.dateTime = now.toISOString();
  }

  updateCurrentTime();
  window.setInterval(updateCurrentTime, 1000);
})();
