import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalizedId = id.replaceAll("\\", "/");

          if (!normalizedId.includes("node_modules")) {
            return undefined;
          }

          if (
            normalizedId.includes("/node_modules/react/") ||
            normalizedId.includes("/node_modules/react-dom/") ||
            normalizedId.includes("/node_modules/scheduler/")
          ) {
            return "react-vendor";
          }

          if (
            normalizedId.includes("/node_modules/leaflet/") ||
            normalizedId.includes("/node_modules/react-leaflet/") ||
            normalizedId.includes("/node_modules/leaflet.heat/")
          ) {
            return "maps-vendor";
          }

          if (
            normalizedId.includes("/node_modules/chart.js/") ||
            normalizedId.includes("/node_modules/react-chartjs-2/")
          ) {
            return "charts-vendor";
          }

          return undefined;
        }
      }
    }
  },
  server: {
    port: 5173,
    host: "0.0.0.0"
  }
});
