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
        <div className="glass-panel p-6 border-t-4 border-t-cyan-500">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h2 className="text-gray-400 text-sm uppercase tracking-wider mb-1">Current Directive</h2>
                    <div className="flex items-center gap-3">
                        <motion.div
                            animate={{ scale: [1, 1.1, 1] }}
                            transition={{ duration: 2, repeat: Infinity }}
                            className={clsx(
                                "text-4xl font-black tracking-tighter",
                                isBuy ? "text-green-400 drop-shadow-[0_0_10px_rgba(74,222,128,0.5)]" :
                                    isSell ? "text-red-500 drop-shadow-[0_0_10px_rgba(239,68,68,0.5)]" : "text-gray-200"
                            )}
                        >
                            {thesis.decision}
                        </motion.div>
                        <span className="text-2xl text-white/50 font-light">
                            {(thesis.confidence * 100).toFixed(0)}% Conf.
                        </span>
                    </div>
                </div>

                <div className="text-right">
                    <div className="text-gray-400 text-xs uppercase mb-1">Start Allocation</div>
                    <div className="text-2xl font-mono text-cyan-400">
                        {thesis.allocation_pct}%
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="p-3 bg-white/5 rounded-lg border border-white/5">
                    <div className="flex items-center gap-2 text-green-400 text-sm font-bold mb-1">
                        <TrendingUp size={14} /> Bull Case
                    </div>
                    <p className="text-xs text-gray-300 leading-relaxed max-h-20 overflow-y-auto">
                        {thesis.bull_case?.replace(/\[.*?\]/g, "") || "Analyzing..."}
                    </p>
                </div>
                <div className="p-3 bg-white/5 rounded-lg border border-white/5">
                    <div className="flex items-center gap-2 text-red-400 text-sm font-bold mb-1">
                        <Activity size={14} /> Bear Case
                    </div>
                    <p className="text-xs text-gray-300 leading-relaxed max-h-20 overflow-y-auto">
                        {thesis.bear_case?.replace(/\[.*?\]/g, "") || "Analyzing..."}
                    </p>
                </div>
            </div>

            <div className="p-4 bg-black/40 rounded-lg border-l-2 border-l-yellow-500">
                <h3 className="text-yellow-500 text-xs font-bold uppercase mb-2 flex items-center gap-2">
                    <Target size={14} /> Synthesis & Reasoning
                </h3>
                <p className="text-sm text-gray-200 leading-relaxed">
                    {thesis.reasoning}
                </p>
            </div>
        </div>
    );
}
