import { defineConfig } from "vite";

// Aurelius is served under /aurelius. The built dist/ is mounted at that path by
// the host's static server as a coordinated deploy step — a relative base path,
// no internal hostnames or absolute node paths in the build config.
export default defineConfig({
  base: "/aurelius/",
  build: {
    target: "es2022",
  },
});
