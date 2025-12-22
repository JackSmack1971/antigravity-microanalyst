"use client";

import AgentChat from "@/components/AgentChat";
import MarketStatus from "@/components/MarketStatus";
import { useI18n } from "@/hooks/useI18n";

export default function Home() {
  const { t } = useI18n();
  return (
    <main className="h-screen w-screen cyber-grid bg-[#0a0b14] p-4 md:p-6 overflow-hidden flex flex-col gap-6">
      <header className="flex items-center justify-between shrink-0">
        <h1 className="text-3xl md:text-4xl font-black italic tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500 neon-text">
          {t("Dashboard.Title")} <span className="text-white text-lg not-italic font-normal opacity-50 ml-2">{t("Dashboard.Subtitle")}</span>
        </h1>
        <div className="flex gap-2 text-xs font-mono opacity-50">
          <span className="text-green-400">● {t("Common.SystemOnline")}</span>
          <span className="text-blue-400">● {t("Common.NeuralLinkActive")}</span>
        </div>
      </header>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        {/* Left Column: Data & Thesis */}
        <div className="lg:col-span-7 flex flex-col gap-6 min-h-0">
          <MarketStatus />

          {/* Placeholder for future Chart/Depth Visuals */}
          <div className="flex-1 glass-panel p-6 flex flex-col items-center justify-center text-white/20 border-t-4 border-t-purple-500">
            <div className="text-6xl font-black opacity-10">{t("Dashboard.PlaceholderChartTitle")}</div>
            <p className="mt-2 text-sm font-mono">{t("Dashboard.PlaceholderChartText")}</p>
          </div>
        </div>

        {/* Right Column: Agent Debate */}
        <div className="lg:col-span-5 min-h-0">
          <AgentChat />
        </div>
      </div>
    </main>
  );
}
