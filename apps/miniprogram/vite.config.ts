import { defineConfig } from "vite";
import uni from "@dcloudio/vite-plugin-uni";

const createUniPlugin =
  typeof uni === "function"
    ? uni
    : (uni as { default: typeof uni }).default;

export default defineConfig({
  plugins: [createUniPlugin()],
  server: {
    host: "0.0.0.0",
    port: 5173,
  },
});
