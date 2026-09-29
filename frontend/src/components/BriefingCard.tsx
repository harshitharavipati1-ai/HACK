'use client';

import React, { useState } from 'react';
import {
    CheckCircle2,
    AlertTriangle,
    History,
    Lightbulb,
    ThumbsUp,
    ThumbsDown,
    Send,
    FileText,
    Shield,
    Layers,
    Sparkles
} from 'lucide-react';
import ConfidenceBadge from './ConfidenceBadge';

interface BriefingCardProps {
    incidentId: string;
    briefing: any;
    onSubmitFeedback: (incidentId: string, feedback: any) => Promise<void>;
}

export default function BriefingCard({ incidentId, briefing, onSubmitFeedback }: BriefingCardProps) {
    const [feedbackType, setFeedbackType] = useState<'WORKED' | 'DID_NOT_WORK' | null>(null);
    const [feedbackText, setFeedbackText] = useState('');
    const [actualFix, setActualFix] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
    const [activeRecommendation, setActiveRecommendation] = useState<string>('');

    const handleFeedback = async (type: 'WORKED' | 'DID_NOT_WORK') => {
        setFeedbackType(type);
        if (!activeRecommendation && briefing.recommended_actions?.length > 0) {
            setActiveRecommendation(briefing.recommended_actions[0]);
        }
    };

    const submitFeedbackForm = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!feedbackType) return;
        if (feedbackType === 'DID_NOT_WORK' && !actualFix.trim()) {
            alert("Please specify 'What actually fixed it?' when marking DID_NOT_WORK.");
            return;
        }

        setSubmitting(true);
        try {
            await onSubmitFeedback(incidentId, {
                recommendation: activeRecommendation || briefing.recommended_actions?.[0] || "General Recommendation",
                feedback_type: feedbackType,
                feedback_text: feedbackText,
                actual_fix: actualFix
            });
            setFeedbackSubmitted(true);
        } catch (err: any) {
            alert(err.message || "Failed to submit feedback");
        } finally {
            setSubmitting(false);
        }
    };

    if (!briefing) return null;

    return (
        <div className="glass-panel rounded-2xl p-6 border border-indigo-500/20 space-y-6 shadow-2xl relative overflow-hidden">
            {/* Glow highlight header */}
            <div className="absolute -top-24 -right-24 w-60 h-60 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

            {/* Header Title */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gray-800">
                <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 text-indigo-300">
                        <Sparkles className="w-5 h-5 animate-pulse" />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-gray-100 flex items-center gap-2">
                            AI Incident Briefing & Recall Analysis
                        </h2>
                        <p className="text-xs text-gray-400">
                            Generated from long-term memory patterns and historical incident resolutions
                        </p>
                    </div>
                </div>

                {/* Confidence Meter */}
                <ConfidenceBadge
                    score={briefing.confidence_score}
                    level={briefing.confidence_level}
                    reasoning={briefing.confidence_reasoning}
                />
            </div>

            {/* Likely Root Cause */}
            <div className="p-4 rounded-xl bg-gray-900/80 border border-gray-800 space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400">
                    <Lightbulb className="w-4 h-4" />
                    <span>LIKELY ROOT CAUSE</span>
                </div>
                <p className="text-sm font-medium text-gray-200 leading-relaxed">
                    {briefing.likely_root_cause}
                </p>
            </div>

            {/* Grid Section: Recommendations & Warnings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Recommended Actions */}
                <div className="space-y-3">
                    <h3 className="text-xs font-semibold text-emerald-400 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>RECOMMENDED RESOLUTION ACTIONS</span>
                    </h3>
                    <ul className="space-y-2">
                        {briefing.recommended_actions?.map((action: string, idx: number) => (
                            <li
                                key={idx}
                                onClick={() => setActiveRecommendation(action)}
                                className={`p-3 rounded-xl border text-xs leading-relaxed transition cursor-pointer ${activeRecommendation === action
                                    ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
                                    : 'bg-gray-900/60 border-gray-800 text-gray-300 hover:border-gray-700'
                                    }`}
                            >
                                <div className="flex items-start gap-2">
                                    <span className="font-mono text-emerald-400 font-bold">{idx + 1}.</span>
                                    <span>{action}</span>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Anti-Pattern Warnings */}
                <div className="space-y-3">
                    <h3 className="text-xs font-semibold text-rose-400 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        <span>ANTI-PATTERN WARNINGS (PAST FAILURES)</span>
                    </h3>
                    {briefing.anti_pattern_warnings?.length > 0 ? (
                        <ul className="space-y-2">
                            {briefing.anti_pattern_warnings.map((warning: string, idx: number) => (
                                <li key={idx} className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 leading-relaxed">
                                    ⚠️ {warning}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <div className="p-3 rounded-xl bg-gray-900/40 border border-gray-800 text-xs text-gray-400 italic">
                            No known anti-patterns recorded for this failure signature yet.
                        </div>
                    )}
                </div>
            </div>

            {/* Shared Patterns & Runbook */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                {briefing.shared_patterns?.length > 0 && (
                    <div className="p-3 rounded-xl bg-indigo-950/30 border border-indigo-900/40 text-xs text-indigo-300 space-y-1">
                        <div className="flex items-center gap-1.5 font-semibold text-indigo-400">
                            <Layers className="w-3.5 h-3.5" />
                            <span>SHARED HISTORICAL PATTERNS</span>
                        </div>
                        <ul className="list-disc list-inside space-y-1 text-gray-300">
                            {briefing.shared_patterns.map((p: string, i: number) => (
                                <li key={i}>{p}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {briefing.runbook_recommendation && (
                    <div className="p-3 rounded-xl bg-blue-950/30 border border-blue-900/40 text-xs text-blue-300 space-y-1">
                        <div className="flex items-center gap-1.5 font-semibold text-blue-400">
                            <FileText className="w-3.5 h-3.5" />
                            <span>RECOMMENDED RUNBOOK</span>
                        </div>
                        <p className="font-mono text-blue-200">{briefing.runbook_recommendation}</p>
                    </div>
                )}
            </div>

            {/* Historical Evidence Citations */}
            {briefing.historical_evidence_used?.length > 0 && (
                <div className="pt-2 border-t border-gray-800/80">
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                        <History className="w-3.5 h-3.5 text-gray-400" />
                        <span>Historical Evidence Cited:</span>
                        <div className="flex flex-wrap gap-1.5">
                            {briefing.historical_evidence_used.map((id: string, idx: number) => (
                                <span key={idx} className="px-2 py-0.5 rounded bg-gray-800 text-gray-300 font-mono text-[11px]">
                                    {id}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Safety Note Disclaimer */}
            <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/10 text-[11px] text-amber-400/90 flex items-center gap-2">
                <Shield className="w-4 h-4 shrink-0" />
                <span>{briefing.risk_note || "Recommendations only — human SRE engineer approves and executes all infrastructure actions."}</span>
            </div>

            {/* Continuous Learning Loop - Feedback Section */}
            <div className="pt-4 border-t border-gray-800 space-y-4">
                <div className="flex items-center justify-between">
                    <div className="text-xs font-semibold text-gray-300 flex items-center gap-2">
                        <span>ENGINEER FEEDBACK LOOP</span>
                        <span className="text-[10px] text-gray-400 font-normal">(Updates memory weights & anti-patterns)</span>
                    </div>

                    {!feedbackSubmitted && (
                        <div className="flex items-center gap-2">
                            <button
                                type="button"
                                onClick={() => handleFeedback('WORKED')}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${feedbackType === 'WORKED'
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20'
                                    }`}
                            >
                                <ThumbsUp className="w-3.5 h-3.5" />
                                <span>Worked</span>
                            </button>

                            <button
                                type="button"
                                onClick={() => handleFeedback('DID_NOT_WORK')}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${feedbackType === 'DID_NOT_WORK'
                                    ? 'bg-rose-600 text-white'
                                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/30 hover:bg-rose-500/20'
                                    }`}
                            >
                                <ThumbsDown className="w-3.5 h-3.5" />
                                <span>Did Not Work</span>
                            </button>
                        </div>
                    )}
                </div>

                {/* Feedback Input Form */}
                {feedbackType && !feedbackSubmitted && (
                    <form onSubmit={submitFeedbackForm} className="p-4 rounded-xl bg-gray-900 border border-gray-800 space-y-3">
                        <div className="text-xs font-semibold text-gray-300">
                            Selected Action: <span className="text-indigo-400">{activeRecommendation || briefing.recommended_actions?.[0]}</span>
                        </div>

                        <div>
                            <label className="block text-xs text-gray-400 mb-1">Feedback Comments (Optional):</label>
                            <textarea
                                value={feedbackText}
                                onChange={(e) => setFeedbackText(e.target.value)}
                                placeholder="What happened when you executed this action?"
                                rows={2}
                                className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                            />
                        </div>

                        {feedbackType === 'DID_NOT_WORK' && (
                            <div>
                                <label className="block text-xs text-rose-400 font-semibold mb-1">
                                    What actually fixed it? * (Required for Anti-Pattern Learning)
                                </label>
                                <textarea
                                    required
                                    value={actualFix}
                                    onChange={(e) => setActualFix(e.target.value)}
                                    placeholder="Detail the actual resolution steps that resolved the issue..."
                                    rows={2}
                                    className="w-full bg-gray-950 border border-rose-900/50 rounded-lg p-2.5 text-xs text-gray-200 focus:outline-none focus:border-rose-500"
                                />
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={submitting}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition"
                        >
                            <Send className="w-3.5 h-3.5" />
                            <span>{submitting ? 'Submitting to Memory...' : 'Submit Feedback to Agent Memory'}</span>
                        </button>
                    </form>
                )}

                {feedbackSubmitted && (
                    <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 shrink-0" />
                        <span>Thank you! Feedback recorded and saved to long-term memory bank. Agent confidence weights updated.</span>
                    </div>
                )}
            </div>
        </div>
    );
}
