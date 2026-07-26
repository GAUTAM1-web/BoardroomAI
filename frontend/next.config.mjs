/** @type {import('next').NextConfig} */
const isProduction = process.env.NODE_ENV === "production";
const configuredApiBaseUrl =
  process.env.API_INTERNAL_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  (isProduction ? "" : "http://localhost:8000");
const apiInternalBaseUrl = configuredApiBaseUrl.replace(/\/+$/, "");

const nextConfig = {
  reactStrictMode: true,
  typedRoutes: true,
  output: "standalone",
  async rewrites() {
    if (!apiInternalBaseUrl) {
      return [];
    }
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiInternalBaseUrl}/api/v1/:path*`
      },
      {
        source: "/health",
        destination: `${apiInternalBaseUrl}/health`
      }
    ];
  }
};

export default nextConfig;
