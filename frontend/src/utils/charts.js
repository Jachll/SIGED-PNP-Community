const HOUR_LABELS = Array.from({ length: 24 }, (_, index) => `${String(index).padStart(2, "0")}:00`);
const CHART_AXIS_COLOR = "#9db4c3";
const CHART_GRID_COLOR = "rgba(157, 180, 195, 0.18)";

export function buildHoraDataset(data = []) {
  const totals = Array(24).fill(0);

  data.forEach((item) => {
    if (item.hora >= 0 && item.hora <= 23) {
      totals[item.hora] = item.total;
    }
  });

  return totals;
}

export function buildHourChartData(statsHora = [], label = "Delitos por hora") {
  return {
    labels: HOUR_LABELS,
    datasets: [
      {
        label,
        data: buildHoraDataset(statsHora),
        backgroundColor: "rgba(21, 125, 165, 0.78)",
        borderColor: "rgba(87, 190, 220, 0.9)",
        borderRadius: 5,
        borderSkipped: false,
        borderWidth: 1,
        barPercentage: 0.7,
        categoryPercentage: 0.82
      }
    ]
  };
}

export const hourChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      grid: { color: CHART_GRID_COLOR },
      ticks: {
        autoSkip: true,
        color: CHART_AXIS_COLOR,
        font: { size: 11 },
        maxRotation: 45,
        maxTicksLimit: 12,
        minRotation: 45
      }
    },
    y: {
      beginAtZero: true,
      grid: { color: CHART_GRID_COLOR },
      ticks: {
        color: CHART_AXIS_COLOR,
        font: { size: 11 },
        precision: 0
      }
    }
  },
  plugins: {
    legend: {
      align: "start",
      labels: {
        boxHeight: 8,
        boxWidth: 22,
        color: CHART_AXIS_COLOR,
        font: { size: 11, weight: "600" }
      }
    }
  }
};
