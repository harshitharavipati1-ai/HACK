'use client';

import React, { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import IncidentCard from '@/components/IncidentCard';
import BriefingCard from '@/components/BriefingCard';
import MemoryCard from '@/components/MemoryCard';
import TraceDrawer from '@/components/TraceDrawer';
import EvaluationPanel from '@/components/EvaluationPanel';
import IncidentDetailModal from '@/components/IncidentDetailModal';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    LineChart,
    Line
} from 'recharts';
import {
    ShieldAlert,
    Search,
    Filter,
    RefreshCw,
    Database,
    Plus,
    CheckCircle,
    Activity,
    Layers,
    Sparkles,
    BrainCircuit
} from 'lucide-react';

export default function Home() {
    const [activeTab, setActiveTab] = useState('triage');
    const [incidents, setIncidents] = useState<any[]>([]);
    const [memories, setMemories] = useState<any[]>([]);
    const [traces, setTraces] = useState<any[]>([]);
    const [analytics, setAnalytics] = useState<any>(null);

    const [selectedIncident, setSelectedIncident] = useState<any>(null);
    const [activeBriefing, setActiveBriefing] = useState<any>(null);
    const [modalIncidentId, setModalIncidentId] = useState<string | null>(null);

    const [memoryProvider, setMemoryProvider] = useState<string>('Local Demo Fallback');
    const [loading, setLoading] = useState(false);
    const [analyzingId, setAnalyzingId] = useState<string | null>(null);
    const [isSeeding, setIsSeeding] = useState(false);

    // Filters
    const [serviceFilter, setServiceFilter] = useState('ALL');
    const [severityFilter, setSeverityFilter] = useState('ALL');
    const [searchQuery, setSearchQuery] = useState('');

    // Fetch initial data
    const fetchData = async () => {
        setLoading(true);
        try {
            // 1. Fetch incidents
            let url = '/api/incidents?';
            if (serviceFilter !== 'ALL') url += `service=${serviceFilter}&`;
            if (severityFilter !== 'ALL') url += `severity=${severityFilter}&`;
            if (searchQuery) url += `search=${encodeURIComponent(searchQuery)}&`;

            const incRes = await fetch(url);
            const incData = await incRes.json();
            if (incData.success) {
                setIncidents(incData.data);
                if (incData.data.length > 0 && !selectedIncident) {
                    setSelectedIncident(incData.data[0]);
                }
            }

            // 2. Fetch memory stats & provider
            const memRes = await fetch('/api/memory/stats');
            const memData = await memRes.json();
            if (memData.success) {
                setMemoryProvider(memData.data.provider);
            }

            // 3. Fetch memories
            const listMemRes = await fetch('/api/memory/list');
            const listMemData = await listMemRes.json();
            if (listMemData.success) {
                setMemories(listMemData.data);
            }

            // 4. Fetch traces
            const traceRes = await fetch('/api/memory/traces');
            const traceData = await traceRes.json();
            if (traceData.success) {
                setTraces(traceData.data);
            }

            // 5. Fetch analytics
            const analRes = await fetch('/api/analytics/metrics');
            const analData = await analRes.json();
            if (analData.success) {
                setAnalytics(analData.data);
            }

        } catch (err) {
            console.error("Failed to fetch dashboard data:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [serviceFilter, severityFilter]);

    const handleSeed = async () => {
        setIsSeeding(true);
        try {
            const res = await fetch('/api/seed', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                alert("Database and Memory Bank successfully seeded with 25 historical incidents!");
                fetchData();
            }
        } catch (err) {
            alert("Failed to seed data");
        } finally {
            setIsSeeding(false);
        }
    };

    const handleAnalyze = async (incidentId: string) => {
        setAnalyzingId(incidentId);
        try {
            const res = await fetch(`/api/incidents/${incidentId}/analyze`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                setActiveBriefing(data.data);
                const found = incidents.find((i) => i.id === incidentId);
                if (found) setSelectedIncident(found);
            } else {
                alert(data.error?.message || "Failed to analyze incident");
            }
        } catch (err) {
            alert("Error analyzing incident");
        } finally {
            setAnalyzingId(null);
        }
    };

    const handleSubmitFeedback = async (incidentId: string, feedbackPayload: any) => {
        const res = await fetch(`/api/incidents/${incidentId}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(feedbackPayload),
        });
        const data = await res.json();
        if (!data.success) {
            throw new Error(data.error?.message || "Failed to submit feedback");
        }
        fetchData();
    };

    const handleRunEval = async () => {
        const res = await fetch('/api/eval/run', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            return data.data;
        }
        throw new Error(data.error?.message || "Failed to run evaluation");
    };

    const COLORS = ['#3b82f6', '#6366f1', '#f59e0b', '#ef4444', '#10b981', '#8b5cf6'];

    return (
        <div className="min-h-screen flex flex-col bg-[#0b0f19]">
            <Navbar
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                memoryProvider={memoryProvider}
                onReseed={handleSeed}
                isSeeding={isSeeding}
            />

            <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
                {/* TAB 1: TRIAGE & BRIEFING */}
                {activeTab === 'triage' && (
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                        {/* Left Column: Alerts List */}
                        <div className="lg:col-span-5 space-y-4">
                            <div className="flex items-center justify-between">
                                <h2 className="text-sm font-bold text-gray-200 flex items-center gap-2">
                                    <ShieldAlert className="w-4 h-4 text-rose-400" />
                                    INCOMING ALERTS & INCIDENTS ({incidents.length})
                                </h2>
                                <button
                                    onClick={fetchData}
                                    className="p-1.5 rounded-lg bg-gray-900 border border-gray-800 text-gray-400 hover:text-gray-200 transition"
                                >
                                    <RefreshCw className="w-3.5 h-3.5" />
                                </button>
                            </div>

                            {/* Filters */}
                            <div className="flex items-center gap-2">
                                <select
                                    value={serviceFilter}
                                    onChange={(e) => setServiceFilter(e.target.value)}
                                    className="bg-gray-900 border border-gray-800 text-xs rounded-lg px-2.5 py-1.5 text-gray-300 focus:outline-none"
                                >
                                    <option value="ALL">All Services</option>
                                    <option value="payment-api">payment-api</option>
                                    <option value="auth-service">auth-service</option>
                                    <option value="reporting-api">reporting-api</option>
                                    <option value="notification-service">notification-service</option>
                                    <option value="checkout-gateway">checkout-gateway</option>
                                </select>

                                <select
                                    value={severityFilter}
                                    onChange={(e) => setSeverityFilter(e.target.value)}
                                    className="bg-gray-900 border border-gray-800 text-xs rounded-lg px-2.5 py-1.5 text-gray-300 focus:outline-none"
                                >
                                    <option value="ALL">All Severities</option>
                                    <option value="CRITICAL">Critical</option>
                                    <option value="HIGH">High</option>
                                    <option value="MEDIUM">Medium</option>
                                </select>
                            </div>

                            {/* List */}
                            <div className="space-y-3 max-h-[750px] overflow-y-auto pr-1">
                                {incidents.map((inc) => (
                                    <IncidentCard
                                        key={inc.id}
                                        incident={inc}
                                        isSelected={selectedIncident?.id === inc.id}
                                        isAnalyzing={analyzingId === inc.id}
                                        onSelect={(i) => {
                                            setSelectedIncident(i);
                                            setActiveBriefing(null);
                                        }}
                                        onAnalyze={handleAnalyze}
                                    />
                                ))}
                            </div>
                        </div>

                        {/* Right Column: Active Briefing / Incident Detail */}
                        <div className="lg:col-span-7 space-y-6">
                            {activeBriefing ? (
                                <BriefingCard
                                    incidentId={selectedIncident?.id || ''}
                                    briefing={activeBriefing}
                                    onSubmitFeedback={handleSubmitFeedback}
                                />
                            ) : selectedIncident ? (
                                <div className="glass-panel rounded-2xl p-6 border border-gray-800 space-y-5">
                                    <div className="flex items-center justify-between pb-4 border-b border-gray-800">
                                        <div>
                                            <span className="font-mono text-xs text-indigo-400 font-bold">{selectedIncident.id}</span>
                                            <h2 className="text-base font-bold text-gray-100">{selectedIncident.title}</h2>
                                        </div>

                                        <button
                                            onClick={() => handleAnalyze(selectedIncident.id)}
                                            disabled={analyzingId === selectedIncident.id}
                                            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-lg shadow-indigo-500/20 transition"
                                        >
                                            <Sparkles className={`w-4 h-4 ${analyzingId === selectedIncident.id ? 'animate-spin' : ''}`} />
                                            <span>{analyzingId === selectedIncident.id ? 'Generating AI Briefing...' : 'Recall Memory & Brief'}</span>
                                        </button>
                                    </div>

                                    <div className="space-y-3 text-xs">
                                        <div>
                                            <span className="text-gray-400 font-semibold">Service:</span>{' '}
                                            <span className="text-gray-200 font-mono">{selectedIncident.service_name}</span>
                                        </div>

                                        <div>
                                            <span className="text-gray-400 font-semibold">Redacted Alert Signal:</span>
                                            <div className="p-3 rounded-lg bg-gray-950 border border-gray-900 font-mono text-amber-300 mt-1">
                                                {selectedIncident.alert}
                                            </div>
                                        </div>

                                        <div>
                                            <span className="text-gray-400 font-semibold">Redacted Log Snippet:</span>
                                            <div className="p-3 rounded-lg bg-gray-950 border border-gray-900 font-mono text-gray-300 mt-1 whitespace-pre-wrap">
                                                {selectedIncident.logs}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-900/30 text-xs text-indigo-300 flex items-center gap-3">
                                        <BrainCircuit className="w-5 h-5 shrink-0 text-indigo-400" />
                                        <span>Click <strong>"Recall Memory & Brief"</strong> to query past incident memory bank, rank evidence signals, and receive LLM root cause briefing with anti-pattern warnings.</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="glass-panel rounded-2xl p-12 text-center text-gray-400 space-y-2 border border-gray-800">
                                    <Activity className="w-8 h-8 text-gray-500 mx-auto animate-bounce" />
                                    <p className="text-xs">Select an incident from the left to view details and trigger memory recall.</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* TAB 2: INCIDENT HISTORY */}
                {activeTab === 'incidents' && (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-base font-bold text-gray-100 flex items-center gap-2">
                                    <Activity className="w-5 h-5 text-indigo-400" />
                                    Historical Incident Database ({incidents.length} Records)
                                </h2>
                                <p className="text-xs text-gray-400">
                                    All resolved and active incidents retaining resolution steps, root cause categories, and runbooks
                                </p>
                            </div>

                            <button
                                onClick={handleSeed}
                                disabled={isSeeding}
                                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 text-xs font-semibold hover:bg-indigo-600/30 transition"
                            >
                                <RefreshCw className={`w-3.5 h-3.5 ${isSeeding ? 'animate-spin' : ''}`} />
                                <span>Re-seed 25 Incidents</span>
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {incidents.map((inc) => (
                                <IncidentCard
                                    key={inc.id}
                                    incident={inc}
                                    onSelect={(selected) => setModalIncidentId(selected.id)}
                                    onAnalyze={handleAnalyze}
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* TAB 3: LONG-TERM MEMORY Explorer */}
                {activeTab === 'memory' && (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-base font-bold text-gray-100 flex items-center gap-2">
                                    <Database className="w-5 h-5 text-indigo-400" />
                                    Long-Term Memory Bank ({memories.length} Retained Memories)
                                </h2>
                                <p className="text-xs text-gray-400">
                                    Structured incident memories, feedback outcomes, and anti-pattern warnings stored in {memoryProvider}
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {memories.map((mem, idx) => (
                                <MemoryCard key={idx} memory={mem} />
                            ))}
                        </div>
                    </div>
                )}

                {/* TAB 4: MEMORY INSPECTOR */}
                {activeTab === 'inspector' && (
                    <TraceDrawer traces={traces} />
                )}

                {/* TAB 5: ANALYTICS & BENCHMARK */}
                {activeTab === 'analytics' && (
                    <div className="space-y-8">
                        {/* Live Evaluation Harness */}
                        <EvaluationPanel onRunEval={handleRunEval} />

                        {/* Real Data Charts */}
                        {analytics && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Chart 1: Root Cause Categories */}
                                <div className="glass-panel rounded-2xl p-6 border border-gray-800 space-y-4">
                                    <h3 className="text-sm font-bold text-gray-200">
                                        TOP ROOT CAUSE CATEGORIES
                                    </h3>
                                    <div className="h-64 w-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={analytics.root_cause_categories || []}>
                                                <XAxis dataKey="category" stroke="#9ca3af" fontSize={11} />
                                                <YAxis stroke="#9ca3af" fontSize={11} />
                                                <Tooltip contentStyle={{ background: '#111827', borderColor: '#374151' }} />
                                                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* Chart 2: MTTR Improvement */}
                                <div className="glass-panel rounded-2xl p-6 border border-gray-800 space-y-4">
                                    <h3 className="text-sm font-bold text-gray-200">
                                        MEAN TIME TO RESOLVE (MTTR) IMPROVEMENT
                                    </h3>
                                    <div className="p-4 rounded-xl bg-gray-900 border border-gray-800 flex items-center justify-around text-center">
                                        <div>
                                            <div className="text-xs text-gray-400">Baseline (No Memory)</div>
                                            <div className="text-2xl font-bold text-rose-400 font-mono">
                                                {analytics.mttr_improvement?.baseline_minutes || 48}m
                                            </div>
                                        </div>
                                        <div className="text-indigo-400 font-bold text-lg">→</div>
                                        <div>
                                            <div className="text-xs text-gray-400">Memory Assisted</div>
                                            <div className="text-2xl font-bold text-emerald-400 font-mono">
                                                {analytics.mttr_improvement?.memory_assisted_minutes || 14}m
                                            </div>
                                        </div>
                                    </div>
                                    <p className="text-xs text-gray-400 leading-relaxed text-center">
                                        Continuous incident memory recall reduces diagnosis time by up to <strong>70%</strong> by providing instant historical resolution steps.
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </main>

            <IncidentDetailModal
                incidentId={modalIncidentId}
                onClose={() => setModalIncidentId(null)}
                onResolveSuccess={fetchData}
            />
        </div>
    );
}
