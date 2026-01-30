'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Campaign, getCampaigns, formatRelativeTime, formatPercentage } from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';

export default function CampaignsPage() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadCampaigns();
        // Poll every 10 seconds
        const interval = setInterval(loadCampaigns, 10000);
        return () => clearInterval(interval);
    }, []);

    async function loadCampaigns() {
        try {
            const response = await getCampaigns();
            setCampaigns(response.campaigns);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load campaigns');
        } finally {
            setLoading(false);
        }
    }

    const getStatusBadge = (status: Campaign['status']) => {
        return <StatusBadge status={status} />;
    };

    if (loading && campaigns.length === 0) {
        return (
            <div className="min-h-screen bg-black text-white p-8">
                <div className="max-w-7xl mx-auto">
                    <div className="animate-pulse">
                        <div className="h-8 bg-gray-800 rounded w-1/4 mb-8"></div>
                        <div className="space-y-4">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="h-24 bg-gray-900 rounded"></div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black text-white p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Email Campaigns</h1>
                        <p className="text-gray-400">
                            Automated email outreach to your generated leads
                        </p>
                    </div>
                    <Link
                        href="/campaigns/create"
                        className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all"
                    >
                        + Create Campaign
                    </Link>
                </div>

                {error && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-8">
                        <p className="text-red-400">{error}</p>
                    </div>
                )}

                {/* Campaigns List */}
                {campaigns.length === 0 ? (
                    <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-12 text-center">
                        <div className="text-6xl mb-4">📧</div>
                        <h3 className="text-xl font-semibold text-white mb-2">
                            No campaigns yet
                        </h3>
                        <p className="text-gray-400 mb-6">
                            Create your first email campaign to start reaching out to leads
                        </p>
                        <Link
                            href="/campaigns/create"
                            className="inline-block px-6 py-3 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Create Campaign
                        </Link>
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {campaigns.map((campaign) => (
                            <Link
                                key={campaign.id}
                                href={`/campaigns/${campaign.id}`}
                                className="block bg-gray-900/50 border border-gray-800 rounded-lg p-6 hover:border-gray-700 transition-all"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <h3 className="text-xl font-semibold text-white mb-1">
                                            {campaign.name}
                                        </h3>
                                        <p className="text-sm text-gray-500">
                                            Created {formatRelativeTime(campaign.created_at)}
                                        </p>
                                    </div>
                                    {getStatusBadge(campaign.status)}
                                </div>

                                {/* Progress Bar */}
                                <div className="mb-4">
                                    <div className="flex items-center justify-between text-sm mb-2">
                                        <span className="text-gray-400">Progress</span>
                                        <span className="text-white">
                                            {campaign.emails_sent} / {campaign.total_leads} sent
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-800 rounded-full h-2">
                                        <div
                                            className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all"
                                            style={{
                                                width: `${(campaign.emails_sent / campaign.total_leads) * 100}%`,
                                            }}
                                        ></div>
                                    </div>
                                </div>

                                {/* Metrics */}
                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <div className="text-xs text-gray-500 mb-1">Open Rate</div>
                                        <div className="text-lg font-semibold text-green-400">
                                            {formatPercentage(campaign.open_rate)}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500 mb-1">Click Rate</div>
                                        <div className="text-lg font-semibold text-purple-400">
                                            {formatPercentage(campaign.click_rate)}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500 mb-1">Replies</div>
                                        <div className="text-lg font-semibold text-orange-400">
                                            {campaign.replies}
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
