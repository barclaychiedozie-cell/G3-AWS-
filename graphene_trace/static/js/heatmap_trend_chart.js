(function () {
  let chart;

  function init() {
    const el = document.getElementById("heatmapTrendChart");
    if (!el) {
      console.warn("heatmapTrendChart canvas not found");
      return;
    }

    if (typeof Chart === "undefined") {
      console.error("Chart.js not loaded (Chart is undefined). Check the CDN script tag.");
      return;
    }

    const ctx = el.getContext("2d");
    chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "Max (mmHg)",
            data: [],
            borderColor: "#ef4444",
            backgroundColor: "rgba(239,68,68,0.10)",
            tension: 0.25,
            fill: true,
            pointRadius: 0,
          },
          {
            label: "Avg (mmHg)",
            data: [],
            borderColor: "#3b82f6",
            backgroundColor: "rgba(59,130,246,0.10)",
            tension: 0.25,
            fill: false,
            pointRadius: 0,
          },
        ],
      },
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#e5e7eb" } },
        },
        scales: {
          x: {
            ticks: { maxTicksLimit: 8, color: "#94a3b8" },
            grid: { color: "rgba(148,163,184,.12)" },
          },
          y: {
            beginAtZero: true,
            ticks: { color: "#94a3b8" },
            grid: { color: "rgba(148,163,184,.12)" },
          },
        },
      },
    });

    console.log("Heatmap trend chart initialized");
  }

  function update(series) {
    if (!chart) init();
    if (!chart) return;

    const labels = series.map((p) => new Date(p.timestamp).toLocaleTimeString());
    chart.data.labels = labels;
    chart.data.datasets[0].data = series.map((p) => p.max);
    chart.data.datasets[1].data = series.map((p) => p.avg);
    chart.update();
  }

  function tick() {
    if (!window.LIVE_HEATMAP_CHART_URL) {
      console.warn("LIVE_HEATMAP_CHART_URL is not set");
      return;
    }

    fetch(window.LIVE_HEATMAP_CHART_URL, { credentials: "same-origin" })
      .then((r) => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then((j) => update(j.data || []))
      .catch((e) => console.warn("heatmap chart fetch failed", e));
  }

  window.addEventListener("load", function () {
    init();
    tick();
    setInterval(tick, 2000);
  });
})();