'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
    Campaign,
    EmailLog,
    getCampaign,
    getCampaignEmails,
    pauseCampaign,
    startCampaign,
    formatRelativeTime,
} from '@/lib/api';
import CampaignMetrics from '@/components/CampaignMetrics';
import EmailLogTable from '@/components/EmailLogTable';
import StatusBadge from '@/components/StatusBadge';

export default function CampaignDetailPage() {
    const params = useParams();
    const router = useRouter();
    const campaignId = params.id as string;

    const [campaign, setCampaign] = useState<Campaign | null>(null);
    const [emails, setEmails] = useState<EmailLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        loadCampaign();
        loadEmails();
        // Poll every 5 seconds
        const interval = setInterval(() => {
            loadCampaign();
            loadEmails();
        }, 5000);
        return () => clearInterval(interval);
    }, [campaignId]);

    async function loadCampaign() {
        try {
            const data = await getCampaign(campaignId);
            setCampaign(data);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load campaign');
        } finally {
            setLoading(false);
        }
    }

    async function loadEmails() {
        try {
            const data = await getCampaignEmails(campaignId);
            setEmails(data.emails);
        } catch (err) {
            // Silently fail email loading
        }
    }

    async function handlePause() {
        if (!campaign) return;
        setActionLoading(true);
        try {
            await pauseCampaign(campaign.id);
            await loadCampaign();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to pause campaign');
        } finally {
            setActionLoading(false);
        }
    }

    async function handleStart() {
        if (!campaign) return;
        setActionLoading(true);
        try {
            await startCampaign(campaign.id);
            await loadCampaign();
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to start campaign');
        } finally {
            setActionLoading(false);
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-black text-white p-8">
                <div className="max-w-7xl mx-auto">
                    <div className="animate-pulse space-y-8">
                        <div className="h-8 bg-gray-800 rounded w-1/3"></div>
                        <div className="h-32 bg-gray-900 rounded"></div>
                        <div className="grid grid-cols-4 gap-4">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="h-24 bg-gray-900 rounded"></div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (error || !campaign) {
        return (
            <div className="min-h-screen bg-black text-white p-8">
                <div className="max-w-7xl mx-auto">
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-8 text-center">
                        <h2 className="text-2xl font-bold text-red-400 mb-2">Error</h2>
                        <p className="text-gray-400">{error || 'Campaign not found'}</p>
                        <Link
                            href="/campaigns"
                            className="inline-block mt-4 px-6 py-3 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
                        >
                            ← Back to Campaigns
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    const canStart = ['draft', 'scheduled', 'paused'].includes(campaign.status);
    const canPause = campaign.status === 'running';

    return (
        <div className="min-h-screen bg-black text-white p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <Link
                        href="/campaigns"
                        className="text-gray-400 hover:text-white mb-4 inline-flex items-center"
                    >
                        ← Back to Campaigns
                    </Link>
                    <div className="flex items-center justify-between mt-4">
                        <div>
                            <h1 className="text-3xl font-bold text-white mb-2">
                                {campaign.name}
                            </h1>
                            <p className="text-gray-400">
                                Created {formatRelativeTime(campaign.created_at)}
                            </p>
                        </div>
                        <div className="flex items-center gap-4">
                            <StatusBadge status={campaign.status} />
                            {canPause && (
                                <button
                                    onClick={handlePause}
                                    disabled={actionLoading}
                                    className="px-6 py-3 bg-yellow-600 rounded-lg font-medium hover:bg-yellow-700 transition-all disabled:opacity-50"
                                >
                                    {actionLoading ? 'Pausing...' : 'Pause'}
                                </button>
                            )}
                            {canStart && (
                                <button
                                    onClick={handleStart}
                                    disabled={actionLoading}
                                    className="px-6 py-3 bg-green-600 rounded-lg font-medium hover:bg-green-700 transition-all disabled:opacity-50"
                                >
                                    {actionLoading ? 'Starting...' : 'Start Campaign'}
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-6 mb-8">
                    <div className="flex items-center justify-between text-sm mb-2">
                        <span className="text-gray-400">Overall Progress</span>
                        <span className="text-white">
                            {campaign.emails_sent} / {campaign.total_leads} emails sent (
                            {((campaign.emails_sent / campaign.total_leads) * 100).toFixed(1)}%)
                        </span>
                    </div>
                    <div className="w-full bg-gray-800 rounded-full h-3">
                        <div
                            className="bg-gradient-to-r from-blue-600 to-purple-600 h-3 rounded-full transition-all"
                            style={{
                                width: `${(campaign.emails_sent / campaign.total_leads) * 100}%`,
                            }}
                        ></div>
                    </div>
                    <div className="mt-4 text-sm text-gray-400">
                        Daily limit: {campaign.daily_limit} emails/day
                        {campaign.last_sent_at && (
                            <span className="ml-4">
                                Last sent: {formatRelativeTime(campaign.last_sent_at)}
                            </span>
                        )}
                    </div>
                </div>

                {/* Metrics */}
                <div className="mb-8">
                    <h2 className="text-xl font-semibold text-white mb-4">Campaign Metrics</h2>
                    <CampaignMetrics campaign={campaign} />
                </div>

                {/* Email Logs */}
                <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-6">
                    <h2 className="text-xl font-semibold text-white mb-4">
                        Email Logs ({emails.length})
                    </h2>
                    <EmailLogTable emails={emails} />
                </div>
            </div>
        </div>
    );
}
