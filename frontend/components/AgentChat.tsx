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
            case "Whale": return "text-fuchsia-400 border-fuchsia-500/20 bg-fuchsia-950/30";
            case "Institution": return "text-blue-400 border-blue-500/20 bg-blue-950/30";
            case "Retail": return "text-emerald-400 border-emerald-500/20 bg-emerald-950/30";
            case "Facilitator": return "text-yellow-400 border-yellow-500/20 bg-yellow-950/30";
            case "Risk": return "text-red-400 border-red-500/20 bg-red-950/30";
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
        <div className="glass-panel h-full flex flex-col p-4">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-white">
                <Terminal className="text-cyan-400" /> Swarm Debate Protocol
            </h2>

            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin"
            >
                <AnimatePresence initial={false}>
                    {logs.map((log) => (
                        <motion.div
                            key={log.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className={clsx(
                                "p-3 rounded-lg border text-sm font-mono flex gap-3",
                                getSourceStyle(log.source)
                            )}
                        >
                            <div className="mt-0.5 opacity-70">{getIcon(log.source)}</div>
                            <div>
                                <span className="opacity-50 text-xs block mb-1">{log.timestamp} • {log.source.toUpperCase()}</span>
                                {log.text}
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {logs.length === 0 && (
                    <div className="text-center text-gray-600 mt-20 animate-pulse">
                        Connecting to Swarm Neural Link...
                    </div>
                )}
            </div>
        </div>
    );
}
