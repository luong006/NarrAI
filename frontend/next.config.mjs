/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export', // Static HTML export for Render and CDN deployment
  trailingSlash: true,
  images: {
    unoptimized: true, // Required for static export
  },
};

export default nextConfig;
