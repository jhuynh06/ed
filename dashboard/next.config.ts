import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = { poll: 1000, aggregateTimeout: 300 }
    }
    return config
  },
  async rewrites() {
    return [
      {
        source: '/api/sse',
        destination: 'http://localhost:8000/sse/events',
      },
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ]
  },
}

export default nextConfig
