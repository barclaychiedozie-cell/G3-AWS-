(function () {
  var chart;

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
        animation: {
          duration: 250,
          easing: "easeOutQuad",
        },
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

  function selectedPatientId() {
    var selector = document.getElementById("comparisonPatientSelect");
    if (!selector) {
      return "";
    }
    return selector.value || "";
  }

  function selectedValue(id, fallback) {
    var el = document.getElementById(id);
    if (!el) return fallback;
    return el.value || fallback;
  }

  function selectedDate(id) {
    var el = document.getElementById(id);
    if (!el) return "";
    return el.value || "";
  }

  function updateChart(payload) {
    if (!chart) {
      initChart();
    }
    if (!chart) {
      return;
    }

    chart.data.labels = (payload.labels || []).map(function (iso) {
      var date = iso && iso.length === 10 ? new Date(iso + "T00:00:00") : new Date(iso);
      return date.toLocaleDateString();
    });

    chart.data.datasets = (payload.datasets || []).map(function (set, idx) {
      var color = set.color || (idx === 0 ? "#3b82f6" : "#22c55e");
      return {
        label: set.label,
        data: set.data,
        borderColor: color,
        backgroundColor: "transparent",
        tension: 0.25,
        pointRadius: 0,
        pointHoverRadius: 3,
        borderWidth: 2,
      };
    });

    chart.update();
  }

  function fetchComparison() {
    if (!window.CLINICIAN_COMPARISON_REPORT_URL) {
      return;
    }

    var patientId = selectedPatientId();
    var url = new URL(window.CLINICIAN_COMPARISON_REPORT_URL, window.location.origin);
    if (patientId) {
      url.searchParams.set("patient_id", patientId);
    }

    var source = selectedValue("comparisonSourceSelect", "live");
    var metric = selectedValue("comparisonMetricSelect", "avg");
    var startDate = selectedDate("comparisonStartDate");
    var endDate = selectedDate("comparisonEndDate");

    if (source) url.searchParams.set("source", source);
    if (metric) url.searchParams.set("metric", metric);
    if (startDate) url.searchParams.set("start_date", startDate);
    if (endDate) url.searchParams.set("end_date", endDate);

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

    var selector = document.getElementById("comparisonPatientSelect");
    if (selector) {
      selector.addEventListener("change", fetchComparison);
    }

    var sourceSelect = document.getElementById("comparisonSourceSelect");
    if (sourceSelect) {
      sourceSelect.addEventListener("change", fetchComparison);
    }

    var metricSelect = document.getElementById("comparisonMetricSelect");
    if (metricSelect) {
      metricSelect.addEventListener("change", fetchComparison);
    }

    var applyBtn = document.getElementById("comparisonApply");
    if (applyBtn) {
      applyBtn.addEventListener("click", fetchComparison);
    }

    var refresh = document.getElementById("refreshComparison");
    if (refresh) {
      refresh.addEventListener("click", fetchComparison);
    }
  });
})();
