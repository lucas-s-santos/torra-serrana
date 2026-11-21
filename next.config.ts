import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  turbopack: { root: __dirname }, // há um package-lock.json solto em C:\projetos
};

export default nextConfig;
