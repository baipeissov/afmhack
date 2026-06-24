import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pin the workspace root to this project so Turbopack doesn't pick up a
  // stray lockfile in a parent directory.
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
