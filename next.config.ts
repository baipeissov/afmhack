import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  // Pin the workspace root to this project so Turbopack doesn't pick up a
  // stray lockfile in a parent directory.
  turbopack: {
    root: __dirname,
  },
};

export default withNextIntl(nextConfig);
