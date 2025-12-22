"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Terminal, Bot, Zap, Brain, Shield } from "lucide-react";
import clsx from "clsx";

interface LogMessage {
    id: number;
    text: string;
    source: "Whale" | "Institution" | "Retail" | "Facilitator" | "System" | "Risk";
    timestamp: string;
}

export default function AgentChat() {
    const [logs, setLogs] = useState<LogMessage[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // SSE Connection
        const eventSource = new EventSource("http://127.0.0.1:8000/api/v1/stream/logs");

        eventSource.onmessage = (event) => {
            const text = event.data;

            // Heuristic parsing to determine source
            let source: LogMessage["source"] = "System";
            if (text.includes("[WHALE")) source = "Whale";
            else if (text.includes("[INSTITUTION")) source = "Institution";
            else if (text.includes("[RETAIL")) source = "Retail";
            else if (text.includes("Facilitator")) source = "Facilitator";
            else if (text.includes("Risk Manager")) source = "Risk";

            const newLog: LogMessage = {
                id: Date.now(),
                text: text,
                source: source,
                timestamp: new Date().toLocaleTimeString(),
            };

            setLogs((prev) => [...prev.slice(-50), newLog]); // Keep last 50
        };

        return () => {
            eventSource.close();
        };
    }, []);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    const getSourceStyle = (source: LogMessage["source"]) => {
        switch (source) {
            case "Whale": return "text-fuchsia-400 border-fuchsia-500/20 bg-fuchsia-950/20";
            case "Institution": return "text-blue-400 border-blue-500/20 bg-blue-950/20";
            case "Retail": return "text-emerald-400 border-emerald-500/20 bg-emerald-950/20";
            case "Facilitator": return "text-yellow-100 border-yellow-500/20 bg-yellow-900/30";
            case "Risk": return "text-red-400 border-red-500/20 bg-red-950/20";
            default: return "text-gray-400 border-gray-700/30";
        }
    };

    const getIcon = (source: LogMessage["source"]) => {
        switch (source) {
            case "Whale": return <Bot className="w-4 h-4" />;
            case "Institution": return <Brain className="w-4 h-4" />;
            case "Retail": return <Zap className="w-4 h-4" />;
            case "Facilitator": return <Terminal className="w-4 h-4" />;
            case "Risk": return <Shield className="w-4 h-4" />;
            default: return <Terminal className="w-4 h-4" />;
        }
    };

    return (
        <div className="glass-panel h-full flex flex-col p-4 transition-all duration-300 hover:border-white/20 hover:shadow-2xl">
            <header className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
                <h2 className="text-xl font-bold flex items-center gap-2 text-white italic tracking-tight uppercase">
                    <Terminal className="text-cyan-400" aria-hidden="true" /> Swarm Debate Protocol
                </h2>
                <span className="text-[10px] font-mono opacity-40 uppercase tracking-[0.2em] hidden md:block">Live Stream</span>
            </header>

            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin focus-visible:outline-none"
                tabIndex={0}
                aria-label="Agent conversation logs"
            >
                <AnimatePresence initial={false}>
                    {logs.map((log) => (
                        <motion.div
                            key={log.id}
                            initial={{ opacity: 0, x: -10, scale: 0.98 }}
                            animate={{ opacity: 1, x: 0, scale: 1 }}
                            className={clsx(
                                "p-3 rounded-lg border text-[13px] font-mono flex gap-3 transition-colors duration-200",
                                getSourceStyle(log.source)
                            )}
                        >
                            <div className="mt-0.5 opacity-80 shrink-0" aria-hidden="true">
                                {getIcon(log.source)}
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="opacity-40 text-[10px] font-bold tracking-widest block uppercase">
                                    {log.timestamp} • {log.source}
                                </span>
                                <div className="leading-relaxed">
                                    {log.text}
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {logs.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full gap-4 text-cyan-400/30">
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                        >
                            <Brain size={40} />
                        </motion.div>
                        <div className="text-sm font-mono animate-pulse uppercase tracking-widest">
                            Syncing Neural Swarm...
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
