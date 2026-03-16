(function () {

  let chart = null;
  let liveInterval = null;
  let paused = false;

  function getCanvas() {
    return document.getElementById("heatmapTrendChart");
  }

  function ensureChart() {

    if (chart) return chart;

    const canvas = getCanvas();
    if (!canvas) {
      console.warn("heatmapTrendChart canvas not found");
      return null;
    }

    if (!window.Chart) {
      console.error("Chart.js not loaded");
      return null;
    }

    const ctx = canvas.getContext("2d");

    chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "Max",
            data: [],
            borderColor: "#ef4444",
            backgroundColor: "rgba(239,68,68,0.15)",
            tension: 0.25
          },
          {
            label: "Avg",
            data: [],
            borderColor: "#2563eb",
            backgroundColor: "rgba(37,99,235,0.15)",
            tension: 0.25
          },
          {
            label: "Min",
            data: [],
            borderColor: "#22c55e",
            backgroundColor: "rgba(34,197,94,0.15)",
            tension: 0.25
          }
        ]
      },
      options: {
        responsive: true,
        animation: false,
        plugins: {
          legend: { display: true }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    });

    return chart;
  }

  function computeStats(matrix) {

    let max = 0;
    let min = Infinity;
    let sum = 0;
    let count = 0;

    for (let r = 0; r < matrix.length; r++) {

      const row = matrix[r] || [];

      for (let c = 0; c < row.length; c++) {

        const v = Number(row[c]) || 0;

        if (v > max) max = v;
        if (v < min) min = v;

        sum += v;
        count++;

      }
    }

    const avg = count ? sum / count : 0;

    if (min === Infinity) min = 0;

    return { max, avg, min };
  }

  function appendPoint(label, stats) {

    const c = ensureChart();
    if (!c) return;

    c.data.labels.push(label);

    c.data.datasets[0].data.push(stats.max);
    c.data.datasets[1].data.push(stats.avg);
    c.data.datasets[2].data.push(stats.min);

    const LIMIT = 60;

    if (c.data.labels.length > LIMIT) {

      c.data.labels.shift();
      c.data.datasets.forEach(ds => ds.data.shift());

    }

    c.update();
  }

  function showPastSnapshot(label, stats) {

    const c = ensureChart();
    if (!c) return;

    /* reset chart completely */

    c.data.labels = [label];

    c.data.datasets[0].data = [stats.max];
    c.data.datasets[1].data = [stats.avg];
    c.data.datasets[2].data = [stats.min];

    c.update();
  }

  async function tickLive() {

    if (paused) return;
    if (!window.LIVE_HEATMAP_CHART_URL) return;

    try {

      const resp = await fetch(window.LIVE_HEATMAP_CHART_URL);
      const payload = await resp.json();

      let stats;

      if (payload.matrix) {

        stats = computeStats(payload.matrix);

      } else {

        stats = {
          max: Number(payload.max ?? payload.max_value ?? 0),
          avg: Number(payload.avg ?? payload.avg_value ?? 0),
          min: Number(payload.min ?? payload.min_value ?? 0)
        };

      }

      const label = payload.timestamp
        ? new Date(payload.timestamp).toLocaleTimeString()
        : new Date().toLocaleTimeString();

      appendPoint(label, stats);

    } catch (err) {

      console.warn("Live chart error:", err);

    }

  }

  function startLive() {

    paused = false;

    if (liveInterval) clearInterval(liveInterval);

    tickLive();
    liveInterval = setInterval(tickLive, 2000);
  }

  function stopLive() {

    paused = true;

    if (liveInterval) {

      clearInterval(liveInterval);
      liveInterval = null;

    }

  }

  /*
  Called when user views a past day
  */

  window.renderPastTrendFromPastDayGridPayload = function(payload) {

    stopLive();

    if (!payload || !payload.matrix) {
      console.warn("Past payload missing matrix");
      return;
    }

    const stats = computeStats(payload.matrix);

    const label = payload.day || "Past Record";

    showPastSnapshot(label, stats);

  };

  window.pauseTrendChart = function () {
    stopLive();
  };

  window.resumeTrendChart = function () {
    startLive();
  };

  window.addEventListener("load", function () {

    ensureChart();
    startLive();

  });

})();