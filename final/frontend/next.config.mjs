/** @type {import('next').NextConfig} */
const nextConfig = {
  // On Vercel, deploy as native Next.js application. Locally or for Render, export static HTML.
  ...(process.env.VERCEL ? {} : { output: 'export' }),
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
