"use client";

import { useEffect, useState } from "react";
import { TrendingUp, Activity, AlertTriangle, ShieldCheck, Target } from "lucide-react";
import { motion } from "framer-motion";
import clsx from "clsx";

interface Thesis {
    decision: string;
    confidence: number;
    allocation_pct: number;
    reasoning: string;
    bull_case: string;
    bear_case: string;
}

export default function MarketStatus() {
    const [thesis, setThesis] = useState<Thesis | null>(null);

    useEffect(() => {
        const fetchThesis = async () => {
            try {
                const res = await fetch("http://127.0.0.1:8000/api/v1/latest/thesis");
                const data = await res.json();
                if (data && data.decision) {
                    setThesis(data);
                }
            } catch (e) {
                console.error("Failed to fetch thesis", e);
            }
        };

        fetchThesis();
        const interval = setInterval(fetchThesis, 5000); // Poll every 5s
        return () => clearInterval(interval);
    }, []);

    if (!thesis) {
        return (
            <div className="glass-panel p-6 animate-pulse">
                <div className="h-6 bg-white/5 rounded w-1/3 mb-4"></div>
                <div className="h-20 bg-white/5 rounded w-full"></div>
            </div>
        );
    }

    const isBuy = thesis.decision === "BUY";
    const isSell = thesis.decision === "SELL";

    return (
        <div className="glass-panel p-6 border-t-4 border-t-cyan-500 transition-all duration-300 hover:shadow-[0_0_40px_rgba(6,182,212,0.15)] group">
            <div className="flex flex-col md:flex-row justify-between items-start gap-6 mb-8">
                <div>
                    <h2 className="text-gray-500 text-[10px] uppercase tracking-[0.3em] font-bold mb-2">Live Market Directive</h2>
                    <div className="flex items-baseline gap-4">
                        <motion.div
                            animate={{
                                opacity: [0.8, 1, 0.8],
                                textShadow: isBuy ? "0 0 20px rgba(74,222,128,0.4)" : isSell ? "0 0 20px rgba(239,68,68,0.4)" : "none"
                            }}
                            transition={{ duration: 2, repeat: Infinity }}
                            className={clsx(
                                "text-5xl md:text-6xl font-black tracking-tighter italic",
                                isBuy ? "text-green-400" : isSell ? "text-red-500" : "text-gray-200"
                            )}
                        >
                            {thesis.decision}
                        </motion.div>
                        <div className="flex flex-col">
                            <span className="text-xl text-white/40 font-mono leading-none">
                                {(thesis.confidence * 100).toFixed(0)}%
                            </span>
                            <span className="text-[10px] text-white/20 uppercase tracking-widest font-bold">Confidence</span>
                        </div>
                    </div>
                </div>

                <div className="text-right bg-white/5 p-3 rounded-xl border border-white/5 min-w-[140px] transition-colors group-hover:bg-white/10">
                    <div className="text-gray-500 text-[10px] uppercase tracking-widest font-bold mb-1">Target Allocation</div>
                    <div className="text-3xl font-black text-cyan-400 tracking-tighter">
                        {thesis.allocation_pct}%
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full mt-2 overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${thesis.allocation_pct}%` }}
                            className="h-full bg-cyan-500"
                        />
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                <div className="p-4 bg-white/[0.03] rounded-xl border border-white/5 hover:bg-white/[0.05] transition-colors group/card">
                    <div className="flex items-center gap-2 text-green-400 text-xs font-black uppercase tracking-widest mb-3">
                        <TrendingUp size={14} className="group-hover/card:translate-y-[-2px] transition-transform" /> Bull Thesis
                    </div>
                    <p className="text-[13px] text-gray-400 leading-relaxed min-h-[60px]">
                        {thesis.bull_case?.replace(/\[.*?\]/g, "") || "Analyzing market momentum..."}
                    </p>
                </div>
                <div className="p-4 bg-white/[0.03] rounded-xl border border-white/5 hover:bg-white/[0.05] transition-colors group/card">
                    <div className="flex items-center gap-2 text-red-500 text-xs font-black uppercase tracking-widest mb-3">
                        <Activity size={14} className="group-hover/card:scale-110 transition-transform" /> Bear Thesis
                    </div>
                    <p className="text-[13px] text-gray-400 leading-relaxed min-h-[60px]">
                        {thesis.bear_case?.replace(/\[.*?\]/g, "") || "Scanning for structural risks..."}
                    </p>
                </div>
            </div>

            <div className="relative p-5 bg-black/40 rounded-xl border border-white/10 overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-yellow-500/50" />
                <h3 className="text-yellow-500 text-[10px] font-black uppercase tracking-[0.2em] mb-3 flex items-center gap-2">
                    <Target size={14} /> Cognitive Synthesis
                </h3>
                <p className="text-[14px] text-gray-200 leading-relaxed font-medium">
                    {thesis.reasoning}
                </p>
            </div>
        </div>
    );
}
