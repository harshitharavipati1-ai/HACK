import './globals.css';
import React from 'react';

export const metadata = {
    title: 'Incident Response Memory Agent | SRE AI Dashboard',
    description: 'Long-term incident memory, semantic recall, evidence ranking, and continuous learning loop for SRE teams.',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="dark">
            <body className="bg-[#0b0f19] text-gray-100 min-h-screen antialiased">
                {children}
            </body>
        </html>
    );
}
