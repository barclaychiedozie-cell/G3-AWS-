(function () {
  var chart;
  var colors = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#a855f7"];

  function initChart() {
    var canvas = document.getElementById("clinicianComparisonChart");
    if (!canvas || typeof Chart === "undefined") {
      return;
    }

    chart = new Chart(canvas.getContext("2d"), {
      type: "line",
      data: {
        labels: [],
        datasets: [],
      },
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        spanGaps: true,
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
  }

  function selectedPatientIds() {
    var checks = document.querySelectorAll(".patient-checkbox:checked");
    var ids = [];
    checks.forEach(function (el) {
      ids.push(el.value);
    });
    return ids;
  }

  function updateChart(payload) {
    if (!chart) {
      initChart();
    }
    if (!chart) {
      return;
    }

    chart.data.labels = (payload.labels || []).map(function (iso) {
      return new Date(iso).toLocaleString();
    });

    chart.data.datasets = (payload.datasets || []).map(function (set, idx) {
      var color = colors[idx % colors.length];
      return {
        label: set.label,
        data: set.data,
        borderColor: color,
        backgroundColor: "transparent",
        tension: 0.25,
        pointRadius: 0,
      };
    });

    chart.update();
  }

  function fetchComparison() {
    if (!window.CLINICIAN_COMPARISON_REPORT_URL) {
      return;
    }

    var ids = selectedPatientIds();
    var url = new URL(window.CLINICIAN_COMPARISON_REPORT_URL, window.location.origin);
    ids.forEach(function (id) {
      url.searchParams.append("patient_ids", id);
    });

    fetch(url.toString(), { credentials: "same-origin" })
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then(updateChart)
      .catch(function (err) {
        console.warn("comparison report fetch failed", err);
      });
  }

  window.addEventListener("load", function () {
    initChart();
    fetchComparison();

    var selector = document.getElementById("patientSelector");
    if (selector) {
      selector.addEventListener("change", fetchComparison);
    }

    var refresh = document.getElementById("refreshComparison");
    if (refresh) {
      refresh.addEventListener("click", fetchComparison);
    }
  });
})();
