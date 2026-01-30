'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Job, getJobs, createCampaign, CreateCampaignRequest } from '@/lib/api';

export default function CreateCampaignPage() {
    const router = useRouter();
    const [step, setStep] = useState(1);
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Form state
    const [selectedJobId, setSelectedJobId] = useState('');
    const [campaignName, setCampaignName] = useState('');
    const [dailyLimit, setDailyLimit] = useState(30);
    const [scheduleNow, setScheduleNow] = useState(true);

    useEffect(() => {
        loadCompletedJobs();
    }, []);

    async function loadCompletedJobs() {
        try {
            const response = await getJobs();
            const completed = response.jobs.filter((j) => j.status === 'completed');
            setJobs(completed);
        } catch (err) {
            setError('Failed to load jobs');
        } finally {
            setLoading(false);
        }
    }

    async function handleSubmit() {
        if (!selectedJobId || !campaignName) {
            setError('Please fill all required fields');
            return;
        }

        setSubmitting(true);
        setError(null);

        try {
            const request: CreateCampaignRequest = {
                job_id: selectedJobId,
                name: campaignName,
                daily_limit: dailyLimit,
                scheduled_at: scheduleNow ? null : undefined,
            };

            const response = await createCampaign(request);
            router.push(`/campaigns/${response.campaign_id}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create campaign');
        } finally {
            setSubmitting(false);
        }
    }

    const selectedJob = jobs.find((j) => j.id === selectedJobId);

    if (loading) {
        return (
            <div className="min-h-screen bg-black text-white p-8">
                <div className="max-w-4xl mx-auto">
                    <div className="animate-pulse">
                        <div className="h-8 bg-gray-800 rounded w-1/3 mb-8"></div>
                        <div className="h-64 bg-gray-900 rounded"></div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black text-white p-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <Link
                        href="/campaigns"
                        className="text-gray-400 hover:text-white mb-4 inline-flex items-center"
                    >
                        ← Back to Campaigns
                    </Link>
                    <h1 className="text-3xl font-bold text-white mt-4 mb-2">
                        Create Email Campaign
                    </h1>
                    <p className="text-gray-400">
                        Set up an automated email campaign from your generated leads
                    </p>
                </div>

                {/* Progress Steps */}
                <div className="flex items-center justify-between mb-8">
                    {[1, 2, 3].map((s) => (
                        <div key={s} className="flex-1">
                            <div className="flex items-center">
                                <div
                                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${step >= s
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-gray-800 text-gray-500'
                                        }`}
                                >
                                    {s}
                                </div>
                                {s < 3 && (
                                    <div
                                        className={`flex-1 h-1 mx-2 ${step > s ? 'bg-blue-600' : 'bg-gray-800'
                                            }`}
                                    ></div>
                                )}
                            </div>
                            <div className="text-xs text-gray-500 mt-2">
                                {s === 1 && 'Select Job'}
                                {s === 2 && 'Configure'}
                                {s === 3 && 'Review'}
                            </div>
                        </div>
                    ))}
                </div>

                {error && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-8">
                        <p className="text-red-400">{error}</p>
                    </div>
                )}

                {/* Step 1: Select Job */}
                {step === 1 && (
                    <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-8">
                        <h2 className="text-xl font-semibold text-white mb-4">
                            Select a completed job
                        </h2>
                        {jobs.length === 0 ? (
                            <div className="text-center py-12">
                                <p className="text-gray-400 mb-4">
                                    No completed jobs found. Generate leads first.
                                </p>
                                <Link
                                    href="/"
                                    className="inline-block px-6 py-3 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                                >
                                    Generate Leads
                                </Link>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {jobs.map((job) => (
                                    <label
                                        key={job.id}
                                        className={`block p-4 border rounded-lg cursor-pointer transition-all ${selectedJobId === job.id
                                                ? 'border-blue-500 bg-blue-500/10'
                                                : 'border-gray-700 hover:border-gray-600'
                                            }`}
                                    >
                                        <input
                                            type="radio"
                                            name="job"
                                            value={job.id}
                                            checked={selectedJobId === job.id}
                                            onChange={(e) => setSelectedJobId(e.target.value)}
                                            className="sr-only"
                                        />
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <div className="font-semibold text-white">
                                                    {job.niche} in {job.location}
                                                </div>
                                                <div className="text-sm text-gray-400">
                                                    {job.leads_count} leads
                                                </div>
                                            </div>
                                            {selectedJobId === job.id && (
                                                <svg
                                                    className="w-6 h-6 text-blue-500"
                                                    fill="none"
                                                    stroke="currentColor"
                                                    viewBox="0 0 24 24"
                                                >
                                                    <path
                                                        strokeLinecap="round"
                                                        strokeLinejoin="round"
                                                        strokeWidth={2}
                                                        d="M5 13l4 4L19 7"
                                                    />
                                                </svg>
                                            )}
                                        </div>
                                    </label>
                                ))}
                            </div>
                        )}
                        <div className="mt-8 flex justify-end">
                            <button
                                onClick={() => setStep(2)}
                                disabled={!selectedJobId}
                                className="px-8 py-3 bg-blue-600 rounded-lg font-medium hover:bg-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Next →
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 2: Configure */}
                {step === 2 && (
                    <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-8">
                        <h2 className="text-xl font-semibold text-white mb-6">
                            Configure Campaign
                        </h2>
                        <div className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">
                                    Campaign Name *
                                </label>
                                <input
                                    type="text"
                                    value={campaignName}
                                    onChange={(e) => setCampaignName(e.target.value)}
                                    placeholder="e.g., Portland Coffee Shops - Jan 2026"
                                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">
                                    Daily Send Limit
                                </label>
                                <input
                                    type="number"
                                    value={dailyLimit}
                                    onChange={(e) => setDailyLimit(parseInt(e.target.value))}
                                    min="1"
                                    max="200"
                                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                />
                                <p className="text-sm text-gray-500 mt-2">
                                    Maximum emails to send per day (recommended: 30-50)
                                </p>
                            </div>
                            <div>
                                <label className="flex items-center">
                                    <input
                                        type="checkbox"
                                        checked={scheduleNow}
                                        onChange={(e) => setScheduleNow(e.target.checked)}
                                        className="mr-3 w-5 h-5"
                                    />
                                    <span className="text-white">Start campaign immediately</span>
                                </label>
                            </div>
                        </div>
                        <div className="mt-8 flex justify-between">
                            <button
                                onClick={() => setStep(1)}
                                className="px-8 py-3 bg-gray-800 rounded-lg font-medium hover:bg-gray-700 transition-all"
                            >
                                ← Back
                            </button>
                            <button
                                onClick={() => setStep(3)}
                                disabled={!campaignName}
                                className="px-8 py-3 bg-blue-600 rounded-lg font-medium hover:bg-blue-700 transition-all disabled:opacity-50"
                            >
                                Next →
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 3: Review */}
                {step === 3 && selectedJob && (
                    <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-8">
                        <h2 className="text-xl font-semibold text-white mb-6">
                            Review & Create
                        </h2>
                        <div className="space-y-4 mb-8">
                            <div className="flex justify-between py-3 border-b border-gray-800">
                                <span className="text-gray-400">Campaign Name</span>
                                <span className="text-white font-semibold">{campaignName}</span>
                            </div>
                            <div className="flex justify-between py-3 border-b border-gray-800">
                                <span className="text-gray-400">Job</span>
                                <span className="text-white">
                                    {selectedJob.niche} in {selectedJob.location}
                                </span>
                            </div>
                            <div className="flex justify-between py-3 border-b border-gray-800">
                                <span className="text-gray-400">Total Leads</span>
                                <span className="text-white font-semibold">
                                    {selectedJob.leads_count}
                                </span>
                            </div>
                            <div className="flex justify-between py-3 border-b border-gray-800">
                                <span className="text-gray-400">Daily Limit</span>
                                <span className="text-white">{dailyLimit} emails/day</span>
                            </div>
                            <div className="flex justify-between py-3 border-b border-gray-800">
                                <span className="text-gray-400">Start Time</span>
                                <span className="text-white">
                                    {scheduleNow ? 'Immediately' : 'Scheduled'}
                                </span>
                            </div>
                            <div className="flex justify-between py-3">
                                <span className="text-gray-400">Estimated Duration</span>
                                <span className="text-white">
                                    ~{Math.ceil((selectedJob.leads_count || 0) / dailyLimit)} days
                                </span>
                            </div>
                        </div>
                        <div className="mt-8 flex justify-between">
                            <button
                                onClick={() => setStep(2)}
                                disabled={submitting}
                                className="px-8 py-3 bg-gray-800 rounded-lg font-medium hover:bg-gray-700 transition-all disabled:opacity-50"
                            >
                                ← Back
                            </button>
                            <button
                                onClick={handleSubmit}
                                disabled={submitting}
                                className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50"
                            >
                                {submitting ? 'Creating...' : 'Create Campaign 🚀'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
