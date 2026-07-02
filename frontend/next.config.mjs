/** @type {import('next').NextConfig} */
const apiInternalBaseUrl = (process.env.API_INTERNAL_BASE_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  ""
);

const nextConfig = {
  reactStrictMode: true,
  typedRoutes: true,
  async rewrites() {
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
