import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  // Pin the workspace root to this project so Turbopack doesn't pick up a
  // stray lockfile in a parent directory.
  turbopack: {
    root: __dirname,
  },
  // Separate build dir lets a second `next dev` instance (e.g. port 3001)
  // run alongside the main one without fighting over the shared .next lock.
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default withNextIntl(nextConfig);
