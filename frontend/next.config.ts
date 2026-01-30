import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://*.clerk.com https://*.clerk.dev https://*.clerk.services https://challenges.cloudflare.com",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: https: blob:",
              "font-src 'self' data:",
              "connect-src 'self' https://*.clerk.com https://*.clerk.dev https://*.clerk.services https://*.onrender.com",
              "frame-src 'self' https://*.clerk.com https://*.clerk.dev",
            ].join('; '),
          },
        ],
      },
    ];
  },
};

export default nextConfig;
