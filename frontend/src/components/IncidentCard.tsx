'use client';

import React from 'react';
import {
    AlertOctagon,
    AlertTriangle,
    Info,
    CheckCircle,
    Search,
    Clock,
    Terminal,
    ShieldCheck
} from 'lucide-react';

interface IncidentCardProps {
    incident: any;
    onAnalyze?: (incidentId: string) => void;
    onSelect?: (incident: any) => void;
    isAnalyzing?: boolean;
    isSelected?: boolean;
}

export default function IncidentCard({
    incident,
    onAnalyze,
    onSelect,
    isAnalyzing,
    isSelected,
}: IncidentCardProps) {
    let severityBg = 'bg-gray-800 text-gray-300 border-gray-700';
    let SeverityIcon = Info;

    if (incident.severity === 'CRITICAL') {
        severityBg = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
        SeverityIcon = AlertOctagon;
    } else if (incident.severity === 'HIGH') {
        severityBg = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
        SeverityIcon = AlertTriangle;
    } else if (incident.severity === 'MEDIUM') {
        severityBg = 'bg-blue-500/10 text-blue-400 border-blue-500/30';
    }

    let statusBg = 'bg-gray-800 text-gray-300';
    if (incident.status === 'OPEN') statusBg = 'bg-rose-950/60 text-rose-300 border-rose-800/60';
    if (incident.status === 'INVESTIGATING') statusBg = 'bg-amber-950/60 text-amber-300 border-amber-800/60';
    if (incident.status === 'RESOLVED') statusBg = 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60';

    return (
        <div
            className={`glass-card rounded-xl p-5 space-y-3 transition duration-200 cursor-pointer ${isSelected ? 'border-indigo-500/60 ring-2 ring-indigo-500/20 bg-gray-900/90' : ''
                }`}
            onClick={() => onSelect && onSelect(incident)}
        >
            {/* Header Row */}
            <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-gray-400">{incident.id}</span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-gray-800 border border-gray-700 text-indigo-300">
                        {incident.service_name}
                    </span>
                    {incident.memory_assisted && (
                        <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                            <ShieldCheck className="w-3 h-3" />
                            Memory Assisted
                        </span>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded-full border text-[11px] font-semibold flex items-center gap-1 ${severityBg}`}>
                        <SeverityIcon className="w-3 h-3" />
                        {incident.severity}
                    </span>
                    <span className={`px-2.5 py-0.5 rounded-full border text-[11px] font-medium ${statusBg}`}>
                        {incident.status}
                    </span>
                </div>
            </div>

            {/* Incident Title */}
            <h3 className="text-sm font-semibold text-gray-100 line-clamp-1">
                {incident.title}
            </h3>

            {/* Alert & Logs snippet */}
            <div className="p-3 rounded-lg bg-gray-950 border border-gray-900 text-xs font-mono space-y-1 overflow-hidden">
                <p className="text-gray-300 line-clamp-1">
                    <span className="text-amber-400 font-bold">Alert:</span> {incident.alert}
                </p>
                {incident.logs && (
                    <p className="text-gray-400 line-clamp-2 text-[11px]">
                        <span className="text-indigo-400 font-bold">Logs:</span> {incident.logs}
                    </p>
                )}
            </div>

            {/* Footer Meta & Actions */}
            <div className="flex items-center justify-between pt-1">
                <div className="flex items-center gap-3 text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {new Date(incident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    {incident.resolution_time_minutes && (
                        <span className="text-emerald-400 font-medium">
                            MTTR: {incident.resolution_time_minutes}m
                        </span>
                    )}
                </div>

                {onAnalyze && (
                    <button
                        type="button"
                        onClick={(e) => {
                            e.stopPropagation();
                            onAnalyze(incident.id);
                        }}
                        disabled={isAnalyzing}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition"
                    >
                        <Search className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
                        <span>{isAnalyzing ? 'Analyzing...' : 'Investigate & Brief'}</span>
                    </button>
                )}
            </div>
        </div>
    );
}
