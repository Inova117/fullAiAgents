interface StatusBadgeProps {
    status: string; // Allow flexible status strings
}

export default function StatusBadge({ status }: StatusBadgeProps) {
    const statusKey = status.toLowerCase();

    const styles: Record<string, string> = {
        // Job Statuses
        pending: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
        processing: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        completed: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
        failed: 'bg-red-500/20 text-red-400 border-red-500/30',

        // Campaign Statuses
        draft: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
        scheduled: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
        running: 'bg-green-500/20 text-green-400 border-green-500/30 animate-pulse',
        paused: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    };

    const icons: Record<string, React.ReactNode> = {
        // Job Statuses
        pending: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
        processing: (
            <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
        ),
        completed: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
        ),
        failed: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
        ),

        // Campaign Statuses (Reuse or add new)
        draft: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
        ),
        scheduled: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
        ),
        running: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
        ),
        paused: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
    };

    const labels: Record<string, string> = {
        pending: 'Pending',
        processing: 'Processing',
        completed: 'Completed',
        failed: 'Failed',
        draft: 'Draft',
        scheduled: 'Scheduled',
        running: 'Running',
        paused: 'Paused',
    };

    // Default fallbacks
    const safeStyle = styles[statusKey] || 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    const safeIcon = icons[statusKey];
    const safeLabel = labels[statusKey] || status;

    return (
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${safeStyle}`}>
            {safeIcon}
            {safeLabel}
        </span>
    );
}
