import { useMemo } from "react";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip
} from "chart.js";
import { Bar } from "react-chartjs-2";
import { buildHourChartData, hourChartOptions } from "../utils/charts";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function HourChart({ statsHora, label = "Delitos por hora" }) {
  const chartData = useMemo(() => buildHourChartData(statsHora, label), [label, statsHora]);

  return (
    <div className="chart-wrap" role="img" aria-label={label}>
      <Bar data={chartData} options={hourChartOptions} />
    </div>
  );
}
