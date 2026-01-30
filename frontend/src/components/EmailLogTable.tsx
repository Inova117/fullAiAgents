'use client';

import { EmailLog, formatRelativeTime } from '@/lib/api';

interface EmailLogTableProps {
    emails: EmailLog[];
}

export default function EmailLogTable({ emails }: EmailLogTableProps) {
    if (emails.length === 0) {
        return (
            <div className="text-center py-12 text-gray-500">
                No emails sent yet
            </div>
        );
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-left">
                <thead className="border-b border-gray-800">
                    <tr>
                        <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">
                            Lead
                        </th>
                        <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">
                            Email
                        </th>
                        <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">
                            Sent
                        </th>
                        <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">
                            Opened
                        </th>
                        <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">
                            Clicked
                        </th>
                        <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase">
                            Status
                        </th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                    {emails.map((email) => (
                        <tr key={email.id} className="hover:bg-gray-900/50">
                            <td className="px-4 py-3 text-sm text-white">
                                {email.lead_name}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-400">
                                {email.lead_email}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-400">
                                {formatRelativeTime(email.sent_at)}
                            </td>
                            <td className="px-4 py-3">
                                {email.opened_at ? (
                                    <span className="flex items-center text-green-400">
                                        <svg
                                            className="w-4 h-4 mr-1"
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
                                        {formatRelativeTime(email.opened_at)}
                                    </span>
                                ) : (
                                    <span className="text-gray-600">—</span>
                                )}
                            </td>
                            <td className="px-4 py-3">
                                {email.clicked_at ? (
                                    <span className="flex items-center text-purple-400">
                                        <svg
                                            className="w-4 h-4 mr-1"
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
                                        {formatRelativeTime(email.clicked_at)}
                                    </span>
                                ) : (
                                    <span className="text-gray-600">—</span>
                                )}
                            </td>
                            <td className="px-4 py-3">
                                {email.error ? (
                                    <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-red-500/10 text-red-400 border border-red-500/20">
                                        Error
                                    </span>
                                ) : email.bounce ? (
                                    <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
                                        Bounced
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-green-500/10 text-green-400 border border-green-500/20">
                                        Delivered
                                    </span>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
