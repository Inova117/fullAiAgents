'use client';

import { useState } from 'react';
import { startJob, StartJobRequest } from '@/lib/api';

interface JobFormProps {
    onJobStarted: () => void;
}

export default function JobForm({ onJobStarted }: JobFormProps) {
    const [niche, setNiche] = useState('');
    const [location, setLocation] = useState('');
    const [mode, setMode] = useState<'local' | 'people' | 'b2b'>('local');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            const request: StartJobRequest = {
                niche: niche.trim(),
                location: location.trim(),
                max_results: 50,
                mode: mode,
            };

            await startJob(request);

            // Clear form
            setNiche('');
            setLocation('');

            // Notify parent
            onJobStarted();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start job');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 shadow-2xl border border-slate-700">
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
                <div>
                    <h2 className="text-xl font-bold text-white">New Lead Search</h2>
                    <p className="text-sm text-slate-400">Find businesses in any niche and location</p>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                    <label htmlFor="niche" className="block text-sm font-medium text-slate-300 mb-2">
                        Business Niche
                    </label>
                    <input
                        type="text"
                        id="niche"
                        value={niche}
                        onChange={(e) => setNiche(e.target.value)}
                        placeholder="e.g., gyms, restaurants, dental clinics"
                        required
                        className="w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    />
                </div>

                <div>
                    <label htmlFor="location" className="block text-sm font-medium text-slate-300 mb-2">
                        Location
                    </label>
                    <input
                        type="text"
                        id="location"
                        value={location}
                        onChange={(e) => setLocation(e.target.value)}
                        placeholder="e.g., Madrid, Spain"
                        required
                        className="w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    />
                </div>

                <div>
                    <label htmlFor="mode" className="block text-sm font-medium text-slate-300 mb-2">
                        Search Strategy
                    </label>
                    <select
                        id="mode"
                        value={mode}
                        onChange={(e) => setMode(e.target.value as any)}
                        className="w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                    >
                        <option value="local">📍 Local Business (Maps + Instagram)</option>
                        <option value="people">👔 Professionals / Founders (LinkedIn)</option>
                        <option value="b2b">🏢 B2B Companies (Web Search)</option>
                    </select>
                </div>

                {error && (
                    <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400 text-sm">
                        {error}
                    </div>
                )}

                <button
                    type="submit"
                    disabled={isLoading || !niche.trim() || !location.trim()}
                    className="w-full py-4 px-6 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-emerald-500/25 disabled:shadow-none disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    {isLoading ? (
                        <>
                            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            <span>Starting Job...</span>
                        </>
                    ) : (
                        <>
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            <span>Start Lead Generation</span>
                        </>
                    )}
                </button>
            </form>
        </div>
    );
}
