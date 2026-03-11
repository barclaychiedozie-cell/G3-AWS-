(function () {
  var heatmap;
  var liveIntervalId = null;
  var livePaused = false;

  // Used so "past view" can re-render on resize
  var lastRenderedData = null;

  function init() {
    var container = document.getElementById("heatmapContainer");
    if (!container) {
      console.warn("heatmapContainer not found");
      return false;
    }

    // Permanent/robust check: ensure Heatmap.js is actually the right library
    if (!window.h337 || typeof window.h337.create !== "function") {
      console.error("Heatmap.js not loaded correctly (window.h337.create missing).");
      container.innerHTML =
        '<div style="padding:12px; color:#b91c1c; background:#fee2e2; border-radius:8px;">' +
        "Heatmap library failed to load. Make sure heatmap.min.js is the real Heatmap.js build and is loaded before pressure_map.js." +
        "</div>";
      return false;
    }

    heatmap = window.h337.create({
      container: container,
      radius: 20,
      maxOpacity: 0.9,
      blur: 0.85,
    });

    return true;
  }

  // Normalize (supports cells coming as 1-based or 0-based indices)
  function normalizeCells(cells) {
    if (!cells || !cells.length) return [];

    var minR = Infinity,
      minC = Infinity;

    cells.forEach(function (p) {
      minR = Math.min(minR, Number(p.r));
      minC = Math.min(minC, Number(p.c));
    });

    var rOffset = minR === 1 ? 1 : 0;
    var cOffset = minC === 1 ? 1 : 0;

    return cells.map(function (p) {
      return {
        r: Number(p.r) - rOffset,
        c: Number(p.c) - cOffset,
        value: Number(p.value) || 0,
      };
    });
  }

  function gridToPoints(cells) {
    if (!cells || !cells.length) return [];

    var norm = normalizeCells(cells);

    var maxR = 0,
      maxC = 0;
    norm.forEach(function (p) {
      maxR = Math.max(maxR, p.r);
      maxC = Math.max(maxC, p.c);
    });

    var rows = maxR + 1,
      cols = maxC + 1;

    var container = document.getElementById("heatmapContainer");
    var w = container.offsetWidth,
      h = container.offsetHeight;

    if (!w || !h || !rows || !cols) return [];

    var cellW = w / cols,
      cellH = h / rows;

    return norm.map(function (p) {
      return {
        x: Math.floor((p.c + 0.5) * cellW),
        y: Math.floor((p.r + 0.5) * cellH),
        value: Number(p.value) || 0,
      };
    });
  }

  function applyRepositionSuggestion(data) {
    var sug = document.getElementById("reposition-suggestion");
    if (!sug) return;

    if (data && data.reposition && data.reposition.reason) {
      sug.style.display = "block";
      sug.textContent = data.reposition.reason;
    } else {
      sug.style.display = "none";
      sug.textContent = "";
    }
  }

  function render(data) {
    if (!heatmap) return;

    lastRenderedData = data || null;

    var pointsAll = gridToPoints((data && data.cells) || []);

    // Permanent fix for past matrices: drop zero-valued points
    var points = pointsAll.filter(function (p) {
      return Number(p.value) > 0;
    });

    var maxVal = points.reduce(function (m, p) {
      return Math.max(m, p.value);
    }, 0);

    if (!points.length) {
      heatmap.setData({ max: 1, min: 0, data: [] });
    } else {
      heatmap.setData({
        max: Math.max(100, Math.ceil(maxVal)),
        min: 0,
        data: points,
      });
    }

    var el = document.getElementById("last-update");
    if (el) {
      el.textContent =
        data && data.timestamp ? new Date(data.timestamp).toLocaleString() : "—";
    }

    applyRepositionSuggestion(data);
  }

  function tick() {
    if (livePaused) return;
    if (!window.LIVE_GRID_URL) return;

    fetch(window.LIVE_GRID_URL, { credentials: "same-origin" })
      .then((r) => r.json())
      .then(render)
      .catch(console.warn);
  }

  function startLive() {
    livePaused = false;
    tick();
    if (liveIntervalId) clearInterval(liveIntervalId);
    liveIntervalId = setInterval(tick, 2000);
  }

  function stopLive() {
    livePaused = true;
    if (liveIntervalId) {
      clearInterval(liveIntervalId);
      liveIntervalId = null;
    }
  }

  // Expose for Past Records UI
  window.renderHeatmapFromCells = function (cells, labelTimestamp) {
    stopLive();
    render({ cells: cells || [], timestamp: labelTimestamp || null });
  };

  window.pauseLiveHeatmap = function () {
    stopLive();
  };

  window.resumeLiveHeatmap = function () {
    startLive();
  };

  window.addEventListener("load", function () {
    if (init()) startLive();
  });

  window.addEventListener("resize", function () {
    if (lastRenderedData) render(lastRenderedData);
  });
})();