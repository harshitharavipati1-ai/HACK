'use client';

import React from 'react';
import { Database, AlertTriangle, ShieldCheck, Tag, Calendar, FileText } from 'lucide-react';

interface MemoryCardProps {
    memory: any;
}

export default function MemoryCard({ memory }: MemoryCardProps) {
    const isAntiPattern = memory.type === 'ANTI_PATTERN' || memory.memory_type === 'ANTI_PATTERN';
    const isFeedback = memory.type === 'FEEDBACK' || memory.memory_type === 'FEEDBACK';

    let typeBadge = 'bg-blue-500/10 border-blue-500/30 text-blue-400';
    let TypeIcon = Database;

    if (isAntiPattern) {
        typeBadge = 'bg-rose-500/10 border-rose-500/30 text-rose-400';
        TypeIcon = AlertTriangle;
    } else if (isFeedback) {
        typeBadge = 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
        TypeIcon = ShieldCheck;
    }

    const metadata = memory.metadata || {};

    return (
        <div className="glass-card rounded-xl p-5 space-y-3 border border-gray-800 hover:border-indigo-500/40 transition">
            {/* Header Row */}
            <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full border text-[11px] font-semibold flex items-center gap-1.5 ${typeBadge}`}>
                        <TypeIcon className="w-3.5 h-3.5" />
                        {memory.type || memory.memory_type || 'INCIDENT_MEMORY'}
                    </span>
                    <span className="font-mono text-xs text-gray-400">
                        ID: {memory.memory_id || memory.id || 'MEM-LOCAL'}
                    </span>
                </div>

                {metadata.service_name && (
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-gray-800 border border-gray-700 text-indigo-300">
                        {metadata.service_name}
                    </span>
                )}
            </div>

            {/* Memory Content Text */}
            <p className="text-xs text-gray-200 leading-relaxed font-mono bg-gray-950/70 p-3 rounded-lg border border-gray-900 whitespace-pre-wrap">
                {memory.content || memory.text}
            </p>

            {/* Metadata tags */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
                {metadata.outcome && (
                    <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950/50 border border-emerald-800/50 text-emerald-300 font-mono">
                        Outcome: {metadata.outcome}
                    </span>
                )}
                {metadata.resolution_time_minutes && (
                    <span className="px-2 py-0.5 rounded text-[10px] bg-indigo-950/50 border border-indigo-800/50 text-indigo-300 font-mono">
                        MTTR: {metadata.resolution_time_minutes}m
                    </span>
                )}
                {metadata.runbook_name && (
                    <span className="px-2 py-0.5 rounded text-[10px] bg-blue-950/50 border border-blue-800/50 text-blue-300 font-mono flex items-center gap-1">
                        <FileText className="w-3 h-3" />
                        {metadata.runbook_name}
                    </span>
                )}
            </div>
        </div>
    );
}
