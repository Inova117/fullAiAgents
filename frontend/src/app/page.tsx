'use client';

import { useState } from 'react';
import Link from 'next/link';
import { UserButton } from "@clerk/nextjs";
import JobForm from '@/components/JobForm';
import JobsTable from '@/components/JobsTable';

export default function Home() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const [processing, setProcessing] = useState(false);

  const handleJobStarted = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleProcessPending = async () => {
    try {
      setProcessing(true);
      // Dynamic import to avoid server-side issues with window.Clerk
      const { processPendingJobs } = await import('@/lib/api');
      const result = await processPendingJobs();
      if (result.processed > 0) {
        alert(`Started processing ${result.processed} job(s). They will appear as 'Processing' shortly.`);
        handleJobStarted();
      } else {
        alert('No pending jobs found to process.');
      }
    } catch (error) {
      console.error('Failed to process jobs:', error);
      alert('Failed to trigger job processing. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* ... existing logo code ... */}
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/25">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="flex items-center gap-8">
                <div>
                  <h1 className="text-2xl font-bold text-white">The Bridge</h1>
                  <p className="text-sm text-slate-400">Deterministic Lead Generation Engine</p>
                </div>
                <nav className="flex items-center gap-6 ml-4 border-l border-slate-700 pl-8">
                  <Link href="/" className="text-white font-medium hover:text-emerald-400 transition-colors">
                    Leads
                  </Link>
                  <Link href="/campaigns" className="text-slate-400 font-medium hover:text-emerald-400 transition-colors">
                    Campaigns
                  </Link>
                </nav>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-xl border border-slate-700">
                <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                <span className="text-sm text-slate-300">API Connected</span>
              </div>

              <button
                onClick={handleProcessPending}
                disabled={processing}
                className="hidden sm:flex items-center gap-2 px-4 py-2 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                title="Manually trigger processing for stuck jobs"
              >
                {processing ? (
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
                <span className="text-sm font-medium">Process Pending</span>
              </button>
              <UserButton afterSignOutUrl="/sign-in" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-slate-400">Pipeline Steps</p>
                <p className="text-xl font-bold text-white">4</p>
              </div>
            </div>
          </div>
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-slate-400">Data Sources</p>
                <p className="text-xl font-bold text-white">Google Maps</p>
              </div>
            </div>
          </div>
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
                <svg className="w-5 h-5 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-slate-400">Engine Type</p>
                <p className="text-xl font-bold text-white">Deterministic</p>
              </div>
            </div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Job Form */}
          <div className="lg:col-span-1">
            <JobForm onJobStarted={handleJobStarted} />
          </div>

          {/* Jobs Table */}
          <div className="lg:col-span-2">
            <JobsTable refreshTrigger={refreshTrigger} />
          </div>
        </div>

        {/* Pipeline Info */}
        <div className="mt-8 bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 border border-slate-700">
          <h3 className="text-lg font-bold text-white mb-4">Pipeline Architecture</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-3 p-4 bg-slate-800/50 rounded-xl">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm">1</div>
              <div>
                <p className="font-medium text-white">Search</p>
                <p className="text-xs text-slate-400">Google Maps API</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-slate-800/50 rounded-xl">
              <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold text-sm">2</div>
              <div>
                <p className="font-medium text-white">Enrich</p>
                <p className="text-xs text-slate-400">Website Scraping</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-slate-800/50 rounded-xl">
              <div className="w-8 h-8 rounded-lg bg-violet-500/20 flex items-center justify-center text-violet-400 font-bold text-sm">3</div>
              <div>
                <p className="font-medium text-white">Template</p>
                <p className="text-xs text-slate-400">Pain Point Map</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-slate-800/50 rounded-xl">
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400 font-bold text-sm">4</div>
              <div>
                <p className="font-medium text-white">Validate</p>
                <p className="text-xs text-slate-400">Pydantic Models</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-slate-500">
            The Bridge • Deterministic Lead Generation • No AI in Execution
          </p>
        </div>
      </footer>
    </div>
  );
}
