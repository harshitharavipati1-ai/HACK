'use client';

import React from 'react';
import { BrainCircuit, Clock, Cpu, Filter, Layers, Zap } from 'lucide-react';

interface TraceDrawerProps {
    traces: any[];
}

export default function TraceDrawer({ traces }: TraceDrawerProps) {
    if (!traces || traces.length === 0) {
        return (
            <div className="glass-panel rounded-2xl p-12 text-center space-y-3 border border-gray-800">
                <BrainCircuit className="w-10 h-10 text-gray-400 mx-auto animate-pulse" />
                <h3 className="text-sm font-semibold text-gray-300">No Memory Recall Traces Logged Yet</h3>
                <p className="text-xs text-gray-400 max-w-md mx-auto">
                    Trigger an incident investigation from the Triage tab to log real-time memory recall queries, candidate scoring, and latency metrics.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-base font-bold text-gray-100 flex items-center gap-2">
                        <BrainCircuit className="w-5 h-5 text-indigo-400" />
                        Memory Recall Traces & Signal Ranking Inspector
                    </h2>
                    <p className="text-xs text-gray-400">
                        Transparent execution telemetry for vector similarity recall, candidate re-ranking, and evidence scoring
                    </p>
                </div>
                <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold">
                    {traces.length} Recall Traces Logged
                </span>
            </div>

            <div className="space-y-4">
                {traces.map((trace: any) => {
                    let results = [];
                    try {
                        results = typeof trace.results_json === 'string' ? JSON.parse(trace.results_json) : trace.results_json;
                    } catch (e) {
                        results = [];
                    }

                    return (
                        <div key={trace.id} className="glass-panel rounded-xl p-5 border border-gray-800 space-y-4">
                            {/* Header Info */}
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-3 border-b border-gray-800">
                                <div className="flex items-center gap-3">
                                    <span className="font-mono text-xs font-bold text-indigo-400">
                                        Incident: {trace.incident_id}
                                    </span>
                                    <span className="flex items-center gap-1 text-xs text-gray-400">
                                        <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                                        Provider: <strong className="text-emerald-300">{trace.provider}</strong>
                                    </span>
                                    <span className="flex items-center gap-1 text-xs text-gray-400">
                                        <Clock className="w-3.5 h-3.5 text-amber-400" />
                                        Latency: <strong className="text-amber-300">{trace.latency_ms}ms</strong>
                                    </span>
                                </div>
                                <span className="text-[11px] text-gray-400">
                                    {new Date(trace.created_at).toLocaleString()}
                                </span>
                            </div>

                            {/* Recall Query */}
                            <div className="space-y-1">
                                <div className="text-[11px] font-semibold text-gray-400 flex items-center gap-1">
                                    <Filter className="w-3 h-3 text-indigo-400" />
                                    RECALL QUERY STRING
                                </div>
                                <div className="p-2.5 rounded-lg bg-gray-950 border border-gray-900 text-xs font-mono text-gray-300">
                                    {trace.query_text}
                                </div>
                            </div>

                            {/* Candidate Results & Ranking Breakdown */}
                            <div className="space-y-2">
                                <div className="text-[11px] font-semibold text-gray-400 flex items-center gap-1">
                                    <Layers className="w-3 h-3 text-emerald-400" />
                                    RECALLED MEMORY CANDIDATES ({results.length})
                                </div>

                                <div className="grid grid-cols-1 gap-2">
                                    {results.map((item: any, idx: number) => (
                                        <div key={idx} className="p-3 rounded-lg bg-gray-900/60 border border-gray-800/80 text-xs space-y-1">
                                            <div className="flex items-center justify-between">
                                                <span className="font-semibold text-gray-200">
                                                    #{idx + 1} {item.title || item.incident_id || 'Memory Item'}
                                                </span>
                                                {item.final_score !== undefined && (
                                                    <span className="px-2 py-0.5 rounded bg-indigo-500/20 border border-indigo-500/40 font-mono text-indigo-300 font-bold">
                                                        Score: {(item.final_score * 100).toFixed(1)}%
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-gray-400 font-mono text-[11px] line-clamp-2">
                                                {item.content || item.narrative || item.root_cause}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
