async function loadPastDays() {
  const limit = document.getElementById("pastDaysLimit").value;
  const status = document.getElementById("pastDaysStatus");
  const sel = document.getElementById("pastDaySelect");

  status.textContent = "Loading...";
  sel.innerHTML = "";

  const url = `${window.PAST_DAYS_URL}?limit=${encodeURIComponent(limit)}`;
  const resp = await fetch(url, { headers: { Accept: "application/json" } });

  if (!resp.ok) {
    status.textContent = `Error (${resp.status}) loading past days`;
    return;
  }

  const payload = await resp.json();
  const data = payload.data || [];

  if (data.length === 0) {
    status.textContent = "No past daily records found.";
    return;
  }

  for (const item of data) {
    const opt = document.createElement("option");
    opt.value = item.day;
    opt.textContent = `${item.day} (saved @ ${item.timestamp})`;
    sel.appendChild(opt);
  }

  status.textContent = `Loaded ${data.length} day(s).`;
}

function matrixToCells(matrix) {
  const cells = [];
  const m = matrix || [];
  for (let r = 0; r < m.length; r++) {
    const row = m[r] || [];
    for (let c = 0; c < row.length; c++) {
      cells.push({ r: r + 1, c: c + 1, value: Number(row[c]) || 0 });
    }
  }
  return cells;
}

function setViewMode(mode, label) {
  const heatmapTitle = document.getElementById("heatmapTitle");
  const heatmapSubtitle = document.getElementById("heatmapSubtitle");
  const trendTitle = document.getElementById("trendTitle");
  const trendSubtitle = document.getElementById("trendSubtitle");

  const backBtn = document.getElementById("backToLive");
  const backBtnTop = document.getElementById("backToLiveTop");

  if (mode === "past") {
    if (heatmapTitle) heatmapTitle.textContent = "Past Pressure Heatmap";
    if (heatmapSubtitle) heatmapSubtitle.textContent = `Viewing past record: ${label || ""}`;

    if (trendTitle) trendTitle.textContent = "Heatmap Trend (Past Snapshot)";
    if (trendSubtitle) trendSubtitle.textContent = "Max/avg computed from the selected day's matrix.";

    if (backBtn) backBtn.style.display = "inline-block";
    if (backBtnTop) backBtnTop.style.display = "inline-block";
  } else {
    if (heatmapTitle) heatmapTitle.textContent = "Live Pressure Heatmap";
    if (heatmapSubtitle) heatmapSubtitle.textContent = "Red = higher pressure. Updates automatically.";

    if (trendTitle) trendTitle.textContent = "Heatmap Trend (Real Time)";
    if (trendSubtitle) trendSubtitle.textContent = "Max and average pressure derived from the heatmap grid.";

    if (backBtn) backBtn.style.display = "none";
    if (backBtnTop) backBtnTop.style.display = "none";
  }
}

async function viewPastDay() {
  const day = document.getElementById("pastDaySelect").value;
  const status = document.getElementById("pastDaysStatus");

  if (!day) {
    status.textContent = "Select a day first.";
    return;
  }

  status.textContent = `Loading ${day}...`;

  const url = `${window.PAST_DAY_GRID_URL}?day=${encodeURIComponent(day)}&max_rows=60&max_cols=60`;
  const resp = await fetch(url, { headers: { Accept: "application/json" } });

  if (!resp.ok) {
    status.textContent = `Error (${resp.status}) loading past day`;
    return;
  }

  const payload = await resp.json();
  const cells = payload.cells || (payload.matrix ? matrixToCells(payload.matrix) : []);
  if (window.renderHeatmapFromCells) {
    window.renderHeatmapFromCells(cells, payload.timestamp || payload.day);
  }
  if (window.renderPastTrendFromPastDayGridPayload) {
    window.renderPastTrendFromPastDayGridPayload(payload);
  } else if (window.pauseTrendChart) {
    window.pauseTrendChart();
  }

  setViewMode("past", payload.day || day);
  status.textContent = `Viewing past record for ${payload.day || day}.`;
}

function backToLive() {
  const status = document.getElementById("pastDaysStatus");

  if (window.resumeLiveHeatmap) window.resumeLiveHeatmap();
  if (window.resumeTrendChart) window.resumeTrendChart();

  setViewMode("live");
  status.textContent = "Back to Live heatmap.";
}

document.addEventListener("DOMContentLoaded", function() {
  document.getElementById("loadPastDays").addEventListener("click", loadPastDays);
  document.getElementById("viewPastDay").addEventListener("click", viewPastDay);
  document.getElementById("backToLive").addEventListener("click", backToLive);
  document.getElementById("backToLiveTop").addEventListener("click", backToLive);
});