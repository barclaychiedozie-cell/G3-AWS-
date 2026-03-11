// heatmap_trend_chart.js
(function () {
  let chart = null;
  let liveIntervalId = null;
  let paused = false;

  // -------------------------
  // Helper: get chart canvas
  // -------------------------
  function getCanvas() {
    return document.getElementById("heatmapTrendChart");
  }

  // -------------------------
  // Initialize Chart.js
  // -------------------------
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
            tension: 0.25,
            fill: false,
            pointRadius: 0
          },
          {
            label: "Avg",
            data: [],
            borderColor: "#2563eb",
            backgroundColor: "rgba(37,99,235,0.12)",
            tension: 0.25,
            fill: false,
            pointRadius: 0
          },
          {
            label: "Min",
            data: [],
            borderColor: "#22c55e",
            backgroundColor: "rgba(34,197,94,0.12)",
            tension: 0.25,
            fill: false,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        animation: false,
        plugins: { legend: { display: true } },
        scales: {
          y: { beginAtZero: true, grid: { color: "rgba(148,163,184,.12)" } },
          x: { grid: { color: "rgba(148,163,184,.12)" } }
        }
      }
    });

    return chart;
  }

  // -------------------------
  // Compute Min/Avg/Max from cells
  // -------------------------
  function computeStatsFromCells(cells) {
    let min = Infinity, max = -Infinity, sum = 0, count = 0;
    (cells || []).forEach(c => {
      const v = Number(c.value) || 0;
      if (v < min) min = v;
      if (v > max) max = v;
      sum += v;
      count++;
    });
    return {
      min: min === Infinity ? 0 : min,
      max: max === -Infinity ? 0 : max,
      avg: count ? sum / count : 0
    };
  }

  // -------------------------
  // Render a series [{timestamp, min, avg, max}]
  // -------------------------
  function renderSeries(series) {
    const c = ensureChart();
    if (!c) return;

    c.data.labels = series.map(p => new Date(p.timestamp).toLocaleTimeString());
    c.data.datasets[0].data = series.map(p => p.max);
    c.data.datasets[1].data = series.map(p => p.avg);
    c.data.datasets[2].data = series.map(p => p.min);
    c.update();
  }

  // -------------------------
  // Append a live point
  // -------------------------
  function appendLivePoint(label, max, avg, min) {
    const c = ensureChart();
    if (!c) return;

    c.data.labels.push(label);
    c.data.datasets[0].data.push(max);
    c.data.datasets[1].data.push(avg);
    c.data.datasets[2].data.push(min);

    const MAX_POINTS = 60;
    if (c.data.labels.length > MAX_POINTS) {
      c.data.labels.shift();
      c.data.datasets.forEach(ds => ds.data.shift());
    }

    c.update();
  }

  // -------------------------
  // Live chart tick
  // -------------------------
  function tickLive() {
    if (paused || !window.LIVE_HEATMAP_CHART_URL) return;

    fetch(window.LIVE_HEATMAP_CHART_URL, { credentials: "same-origin" })
      .then(r => r.json())
      .then(payload => {
        let label = payload.timestamp ? new Date(payload.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        let maxVal = Number(payload.max ?? payload.max_value);
        let avgVal = Number(payload.avg ?? payload.avg_value);
        let minVal = Number(payload.min ?? payload.min_value);

        // Compute from cells/matrix if missing
        if (!isFinite(maxVal) || !isFinite(avgVal)) {
          let cells = payload.cells;
          if (!cells && payload.matrix) {
            cells = payload.matrix.flat().map(v => ({ value: v }));
          }
          const stats = computeStatsFromCells(cells || []);
          maxVal = stats.max;
          avgVal = stats.avg;
          minVal = stats.min;
        }

        appendLivePoint(label, maxVal, avgVal, minVal);
      })
      .catch(console.warn);
  }

  // -------------------------
  // Start/Stop live
  // -------------------------
  function startLive() {
    paused = false;
    if (liveIntervalId) clearInterval(liveIntervalId);
    tickLive();
    liveIntervalId = setInterval(tickLive, 2000);
  }

  function stopLive() {
    paused = true;
    if (liveIntervalId) {
      clearInterval(liveIntervalId);
      liveIntervalId = null;
    }
  }

  // -------------------------
  // Render past record
  // -------------------------
  window.renderPastTrendFromPastDayGridPayload = function (payload) {
    stopLive();

    let cells = payload.cells;
    if (!cells && payload.matrix) {
      cells = payload.matrix.flat().map(v => ({ value: v }));
    }

    const stats = computeStatsFromCells(cells || []);
    const label = payload.day || payload.timestamp || "Past";

    // Small series of 3 points so single-point is visible
    renderSeries([
      { timestamp: label + " 1", min: stats.min, avg: stats.avg, max: stats.max },
      { timestamp: label + " 2", min: stats.min, avg: stats.avg, max: stats.max },
      { timestamp: label + " 3", min: stats.min, avg: stats.avg, max: stats.max }
    ]);
  };

  // -------------------------
  // Public API
  // -------------------------
  window.pauseTrendChart = stopLive;
  window.resumeTrendChart = startLive;

  window.addEventListener("load", () => {
    ensureChart();
    startLive();
  });
})();