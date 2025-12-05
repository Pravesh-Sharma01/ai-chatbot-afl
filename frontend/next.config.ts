/// <reference types="node" />
import type { NextConfig } from "next";

const backendDomainFiber: string = process.env.BACKEND_DOMAIN_FIBER || "http://localhost:8002";
const backendDomainMotor: string = process.env.BACKEND_DOMAIN_MOTOR || "http://localhost:8003";
const backendDomainHR: string = process.env.BACKEND_DOMAIN_HR || "http://localhost:8000";
const backendDomainClaim: string = process.env.BACKEND_DOMAIN_CLAIM || "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/sales/motor/chat",
        destination: `${backendDomainMotor}/chat`,
      },
      {
        source: "/api/sales/fiber/chat",
        destination: `${backendDomainFiber}/chat`,
      },
      {
        source: "/api/hr/chat",
        destination: `${backendDomainHR}/chat`,
      },
      {
        source: "/api/jobs/latest",
        destination: `${backendDomainHR}/jobs/latest`,
      },
      {
        source: "/api/claim/chat",
        destination: `${backendDomainClaim}/chat`,
      },
    ];
  },

  output: "standalone",
};

export default nextConfig;
