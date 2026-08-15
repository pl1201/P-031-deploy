import type { NextConfig } from "next";

// Vercel natively builds and deploys Next.js. `standalone` is only needed
// when we package the app into our own Docker/Node runtime.
const nextConfig: NextConfig = {
  output: "standalone",
  // Chỉ báo dev-tools (nút "N" góc dưới-trái) trùng vị trí khối "Tài khoản" trong sidebar —
  // đổi sang góc dưới-phải. Chỉ ảnh hưởng `next dev`, không xuất hiện ở bản production.
  devIndicators: {
    position: "bottom-right",
  },
};

export default nextConfig;
