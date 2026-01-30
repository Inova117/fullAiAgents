'use client';

import { Campaign, formatPercentage } from '@/lib/api';

interface CampaignMetricsProps {
    campaign: Campaign;
}

export default function CampaignMetrics({ campaign }: CampaignMetricsProps) {
    const stats = [
        {
            name: 'Total Sent',
            value: campaign.emails_sent,
            total: campaign.total_leads,
            color: 'blue',
        },
        {
            name: 'Open Rate',
            value: formatPercentage(campaign.open_rate),
            subtitle: `${campaign.opens} opens`,
            color: 'green',
        },
        {
            name: 'Click Rate',
            value: formatPercentage(campaign.click_rate),
            subtitle: `${campaign.clicks} clicks`,
            color: 'purple',
        },
        {
            name: 'Reply Rate',
            value: formatPercentage(campaign.reply_rate),
            subtitle: `${campaign.replies} replies`,
            color: 'orange',
        },
    ];

    const getColorClasses = (color: string) => {
        const colors: Record<string, { bg: string; text: string; border: string }> = {
            blue: {
                bg: 'bg-blue-500/10',
                text: 'text-blue-400',
                border: 'border-blue-500/20',
            },
            green: {
                bg: 'bg-green-500/10',
                text: 'text-green-400',
                border: 'border-green-500/20',
            },
            purple: {
                bg: 'bg-purple-500/10',
                text: 'text-purple-400',
                border: 'border-purple-500/20',
            },
            orange: {
                bg: 'bg-orange-500/10',
                text: 'text-orange-400',
                border: 'border-orange-500/20',
            },
        };
        return colors[color] || colors.blue;
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((stat) => {
                const colors = getColorClasses(stat.color);
                return (
                    <div
                        key={stat.name}
                        className={`${colors.bg} ${colors.border} border rounded-lg p-6`}
                    >
                        <div className="text-sm text-gray-400 mb-1">{stat.name}</div>
                        <div className={`text-3xl font-bold ${colors.text}`}>
                            {stat.value}
                            {stat.total && (
                                <span className="text-xl text-gray-500">/{stat.total}</span>
                            )}
                        </div>
                        {stat.subtitle && (
                            <div className="text-sm text-gray-500 mt-1">{stat.subtitle}</div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
