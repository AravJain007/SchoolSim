import React from 'react';
import { Outlet } from 'react-router-dom';

export default function Layout() {
    return (
        <div className="min-h-screen bg-neutral-50 text-neutral-900 font-sans antialiased">
            <header className="sticky top-0 z-50 w-full border-b border-neutral-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
                <div className="container mx-auto flex h-14 items-center px-4">
                    <div className="mr-4 hidden md:flex">
                        <a className="mr-6 flex items-center space-x-2" href="/">
                            <span className="hidden font-bold sm:inline-block">
                                Sims Teacher
                            </span>
                        </a>
                    </div>
                </div>
            </header>
            <main className="container mx-auto px-4 py-8">
                <Outlet />
            </main>
        </div>
    );
}
