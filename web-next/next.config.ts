import type { NextConfig } from "next";

// Vercel natively builds and deploys Next.js. `standalone` is only needed
// when we package the app into our own Docker/Node runtime.
const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
