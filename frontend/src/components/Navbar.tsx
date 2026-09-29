'use client';

import React from 'react';
import {
    ShieldAlert,
    BrainCircuit,
    Database,
    Activity,
    BarChart3,
    RefreshCw,
    Cpu
} from 'lucide-react';

interface NavbarProps {
    activeTab: string;
    setActiveTab: (tab: string) => void;
    memoryProvider: string;
    onReseed: () => void;
    isSeeding: boolean;
}

export default function Navbar({
    activeTab,
    setActiveTab,
    memoryProvider,
    onReseed,
    isSeeding,
}: NavbarProps) {
    const navItems = [
        { id: 'triage', label: 'Alert Triage & Briefing', icon: ShieldAlert },
        { id: 'incidents', label: 'Incident History', icon: Activity },
        { id: 'memory', label: 'Long-Term Memory', icon: Database },
        { id: 'inspector', label: 'Memory Inspector', icon: BrainCircuit },
        { id: 'analytics', label: 'Analytics & Benchmark', icon: BarChart3 },
    ];

    return (
        <header className="sticky top-0 z-50 glass-panel border-b border-gray-800 px-6 py-3.5">
            <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                {/* Logo & Brand */}
                <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
                        <BrainCircuit className="w-6 h-6 animate-pulse" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <h1 className="text-lg font-bold bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
                                Incident Response Memory Agent
                            </h1>
                            <span className="px-2 py-0.5 text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 rounded-full">
                                v1.0.0
                            </span>
                        </div>
                        <p className="text-xs text-gray-400">
                            SRE Incident Recall, Evidence Ranking & Continuous Learning Loop
                        </p>
                    </div>
                </div>

                {/* Navigation Tabs */}
                <nav className="flex items-center gap-1 bg-gray-900/60 p-1 rounded-xl border border-gray-800">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = activeTab === item.id;
                        return (
                            <button
                                key={item.id}
                                onClick={() => setActiveTab(item.id)}
                                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${isActive
                                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-indigo-500/20'
                                        : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60'
                                    }`}
                            >
                                <Icon className="w-3.5 h-3.5" />
                                <span>{item.label}</span>
                            </button>
                        );
                    })}
                </nav>

                {/* Status Badge & Actions */}
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-900 border border-gray-800 text-xs">
                        <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-gray-400">Memory:</span>
                        <span className="font-semibold text-emerald-400">{memoryProvider}</span>
                    </div>

                    <button
                        onClick={onReseed}
                        disabled={isSeeding}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-600/30 text-xs font-medium transition"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${isSeeding ? 'animate-spin' : ''}`} />
                        <span>{isSeeding ? 'Seeding...' : 'Seed Data'}</span>
                    </button>
                </div>
            </div>
        </header>
    );
}
