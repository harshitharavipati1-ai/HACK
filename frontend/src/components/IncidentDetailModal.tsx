'use client';

import React, { useState } from 'react';
import { X, CheckCircle, Clock, ShieldCheck, FileText, Tag, AlertTriangle, Layers, ThumbsUp, ThumbsDown } from 'lucide-react';
import ConfidenceBadge from './ConfidenceBadge';

interface IncidentDetailModalProps {
    incidentId: string | null;
    onClose: () => void;
    onResolveSuccess?: () => void;
}

export default function IncidentDetailModal({
    incidentId,
    onClose,
    onResolveSuccess
}: IncidentDetailModalProps) {
    const [incidentData, setIncidentData] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    // Resolve Form
    const [showResolveForm, setShowResolveForm] = useState(false);
    const [rootCause, setRootCause] = useState('');
    const [rootCauseCategory, setRootCauseCategory] = useState('database');
    const [resolutionSteps, setResolutionSteps] = useState('');
    const [outcome, setOutcome] = useState('SUCCESS');
    const [resolutionTime, setResolutionTime] = useState(15);
    const [runbookName, setRunbookName] = useState('');
    const [resolving, setResolving] = useState(false);

    React.useEffect(() => {
        if (!incidentId) return;
        setLoading(true);
        fetch(`/api/incidents/${incidentId}`)
            .then((res) => res.json())
            .then((data) => {
                if (data.success) {
                    setIncidentData(data.data);
                }
            })
            .catch((err) => console.error(err))
            .finally(() => setLoading(false));
    }, [incidentId]);

    if (!incidentId) return null;

    const handleResolveSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setResolving(true);
        try {
            const res = await fetch(`/api/incidents/${incidentId}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    root_cause: rootCause,
                    root_cause_category: rootCauseCategory,
                    resolution_steps: resolutionSteps,
                    outcome: outcome,
                    resolution_time_minutes: Number(resolutionTime),
                    runbook_name: runbookName || undefined,
                }),
            });
            const data = await res.json();
            if (data.success) {
                alert("Incident successfully resolved and saved to memory bank!");
                setShowResolveForm(false);
                if (onResolveSuccess) onResolveSuccess();
                onClose();
            } else {
                alert(data.error?.message || "Failed to resolve incident");
            }
        } catch (err: any) {
            alert("Error resolving incident");
        } finally {
            setResolving(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
            <div className="glass-panel w-full max-w-3xl rounded-2xl p-6 border border-gray-800 space-y-6 max-h-[90vh] overflow-y-auto relative shadow-2xl">
                {/* Close Button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 rounded-xl bg-gray-900 border border-gray-800 text-gray-400 hover:text-gray-100 transition"
                >
                    <X className="w-5 h-5" />
                </button>

                {loading ? (
                    <div className="p-12 text-center text-xs text-gray-400">Loading incident details...</div>
                ) : incidentData ? (
                    <div className="space-y-6">
                        {/* Header */}
                        <div className="space-y-2 pr-8">
                            <div className="flex items-center gap-2">
                                <span className="font-mono text-xs font-bold text-indigo-400">{incidentData.id}</span>
                                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-gray-800 border border-gray-700 text-indigo-300">
                                    {incidentData.service_name}
                                </span>
                                <span className={`px-2.5 py-0.5 rounded-full border text-[11px] font-medium ${incidentData.status === 'RESOLVED' ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800' : 'bg-rose-950/60 text-rose-300 border-rose-800'
                                    }`}>
                                    {incidentData.status}
                                </span>
                            </div>
                            <h2 className="text-lg font-bold text-gray-100">{incidentData.title}</h2>
                        </div>

                        {/* Alert & Log Snippet */}
                        <div className="space-y-3 text-xs">
                            <div>
                                <span className="text-gray-400 font-semibold">Alert Description:</span>
                                <div className="p-3 rounded-lg bg-gray-950 border border-gray-900 font-mono text-amber-300 mt-1">
                                    {incidentData.alert}
                                </div>
                            </div>

                            <div>
                                <span className="text-gray-400 font-semibold">Log Output:</span>
                                <div className="p-3 rounded-lg bg-gray-950 border border-gray-900 font-mono text-gray-300 mt-1 whitespace-pre-wrap">
                                    {incidentData.logs}
                                </div>
                            </div>
                        </div>

                        {/* Resolution Details if RESOLVED */}
                        {incidentData.status === 'RESOLVED' ? (
                            <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-900/40 space-y-3 text-xs">
                                <div className="flex items-center gap-2 font-bold text-emerald-400 text-sm">
                                    <CheckCircle className="w-4 h-4" />
                                    <span>RESOLUTION DETAILS</span>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-gray-300">
                                    <div>
                                        <span className="text-gray-400 font-semibold block">Root Cause:</span>
                                        <p className="font-mono text-emerald-200 mt-0.5">{incidentData.root_cause}</p>
                                    </div>
                                    <div>
                                        <span className="text-gray-400 font-semibold block">Category:</span>
                                        <p className="font-mono text-amber-300 mt-0.5">{incidentData.root_cause_category}</p>
                                    </div>
                                </div>

                                <div>
                                    <span className="text-gray-400 font-semibold block">Resolution Steps:</span>
                                    <p className="font-mono text-gray-200 bg-gray-950 p-2.5 rounded-lg border border-gray-900 mt-1 whitespace-pre-wrap">
                                        {incidentData.resolution_steps}
                                    </p>
                                </div>

                                <div className="flex items-center gap-4 text-[11px] text-gray-400 pt-1">
                                    <span>MTTR: <strong className="text-emerald-400">{incidentData.resolution_time_minutes} minutes</strong></span>
                                    {incidentData.runbook_name && (
                                        <span>Runbook: <strong className="text-blue-400 font-mono">{incidentData.runbook_name}</strong></span>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="pt-2">
                                {!showResolveForm ? (
                                    <button
                                        onClick={() => setShowResolveForm(true)}
                                        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition"
                                    >
                                        <CheckCircle className="w-4 h-4" />
                                        <span>Resolve Incident & Retain Memory</span>
                                    </button>
                                ) : (
                                    <form onSubmit={handleResolveSubmit} className="p-4 rounded-xl bg-gray-900 border border-gray-800 space-y-3">
                                        <h3 className="text-xs font-bold text-emerald-400">RESOLVE INCIDENT FORM</h3>

                                        <div>
                                            <label className="block text-xs text-gray-400 mb-1">Root Cause Description:</label>
                                            <input
                                                required
                                                type="text"
                                                value={rootCause}
                                                onChange={(e) => setRootCause(e.target.value)}
                                                placeholder="e.g. QueuePool limit reached due to unclosed DB connections"
                                                className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                                            />
                                        </div>

                                        <div className="grid grid-cols-2 gap-3">
                                            <div>
                                                <label className="block text-xs text-gray-400 mb-1">Root Cause Category:</label>
                                                <select
                                                    value={rootCauseCategory}
                                                    onChange={(e) => setRootCauseCategory(e.target.value)}
                                                    className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2 text-xs text-gray-200"
                                                >
                                                    <option value="connection_pool_exhaustion">connection_pool_exhaustion</option>
                                                    <option value="redis_memory_oom">redis_memory_oom</option>
                                                    <option value="oauth_key_rotation">oauth_key_rotation</option>
                                                    <option value="kafka_consumer_lag">kafka_consumer_lag</option>
                                                    <option value="slow_query_lock">slow_query_lock</option>
                                                    <option value="infrastructure">infrastructure</option>
                                                    <option value="config_drift">config_drift</option>
                                                </select>
                                            </div>

                                            <div>
                                                <label className="block text-xs text-gray-400 mb-1">MTTR (Minutes):</label>
                                                <input
                                                    type="number"
                                                    value={resolutionTime}
                                                    onChange={(e) => setResolutionTime(Number(e.target.value))}
                                                    className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2 text-xs text-gray-200"
                                                />
                                            </div>
                                        </div>

                                        <div>
                                            <label className="block text-xs text-gray-400 mb-1">Resolution Steps:</label>
                                            <textarea
                                                required
                                                value={resolutionSteps}
                                                onChange={(e) => setResolutionSteps(e.target.value)}
                                                rows={3}
                                                placeholder="Detail exact commands or PRs executed to resolve this issue..."
                                                className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                                            />
                                        </div>

                                        <div className="flex items-center gap-2 pt-2">
                                            <button
                                                type="submit"
                                                disabled={resolving}
                                                className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition"
                                            >
                                                {resolving ? 'Saving Resolution to Memory...' : 'Submit Resolution'}
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setShowResolveForm(false)}
                                                className="px-4 py-2 rounded-lg bg-gray-800 text-gray-400 text-xs hover:text-gray-200"
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </form>
                                )}
                            </div>
                        )}

                        {/* Engineer Feedback Loop Records */}
                        {incidentData.feedbacks && incidentData.feedbacks.length > 0 && (
                            <div className="space-y-2 pt-2 border-t border-gray-800">
                                <span className="text-xs font-semibold text-gray-300">ENGINEER FEEDBACK HISTORY ({incidentData.feedbacks.length})</span>
                                <div className="space-y-2">
                                    {incidentData.feedbacks.map((fb: any) => (
                                        <div key={fb.id} className="p-3 rounded-lg bg-gray-950 border border-gray-900 text-xs space-y-1">
                                            <div className="flex items-center justify-between">
                                                <span className={`font-semibold ${fb.feedback_type === 'WORKED' ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                    {fb.feedback_type === 'WORKED' ? '👍 WORKED' : '👎 DID NOT WORK'}
                                                </span>
                                                <span className="text-[10px] text-gray-400">{new Date(fb.created_at).toLocaleString()}</span>
                                            </div>
                                            <p className="text-gray-300"><strong className="text-gray-400">Action:</strong> {fb.recommendation}</p>
                                            {fb.actual_fix && (
                                                <p className="text-rose-300"><strong className="text-rose-400">Actual Fix:</strong> {fb.actual_fix}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : null}
            </div>
        </div>
    );
}
