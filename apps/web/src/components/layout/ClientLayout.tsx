"use client";

import React, { useState, useEffect } from "react";
import { Header } from "./Header";
import { fetchHealth } from "@/lib/api";
import { DeepHealthResponse } from "@/lib/types";

export const ClientLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [health, setHealth] = useState<DeepHealthResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const loadHealth = async () => {
    setLoading(true);
    const data = await fetchHealth();
    setHealth(data);
    setLoading(false);
  };

  useEffect(() => {
    loadHealth();
    const timer = setInterval(loadHealth, 15000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
      <Header health={health} loading={loading} onRefresh={loadHealth} />
      <main className="flex-1 p-6 md:p-8 overflow-y-auto bg-[#090A0F]">
        {children}
      </main>
    </div>
  );
};
