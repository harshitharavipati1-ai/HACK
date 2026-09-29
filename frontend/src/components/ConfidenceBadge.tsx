'use client';

import React from 'react';
import { ShieldCheck, ShieldAlert, ShieldX, HelpCircle } from 'lucide-react';

interface ConfidenceBadgeProps {
    score: number;
    level: string;
    reasoning?: string;
}

export default function ConfidenceBadge({ score, level, reasoning }: ConfidenceBadgeProps) {
    let color = 'bg-gray-500/10 border-gray-500/20 text-gray-400';
    let Icon = HelpCircle;

    if (level === 'HIGH') {
        color = 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
        Icon = ShieldCheck;
    } else if (level === 'MEDIUM') {
        color = 'bg-amber-500/10 border-amber-500/30 text-amber-400';
        Icon = ShieldAlert;
    } else if (level === 'LOW' || level === 'INSUFFICIENT') {
        color = 'bg-rose-500/10 border-rose-500/30 text-rose-400';
        Icon = ShieldX;
    }

    const percentage = Math.round(score * 100);

    return (
        <div className="flex flex-col gap-1">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-semibold ${color}`}>
                <Icon className="w-4 h-4" />
                <span>Confidence: {percentage}% ({level})</span>
            </div>
            {reasoning && (
                <p className="text-[11px] text-gray-400 italic leading-relaxed">
                    {reasoning}
                </p>
            )}
        </div>
    );
}
