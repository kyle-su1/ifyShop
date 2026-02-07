import React from 'react';
import LoginButton from '../components/LoginButton';
import { useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';

const LandingPage = () => {
    const { isAuthenticated, isLoading } = useAuth0();

    // If already logged in, redirect to dashboard automatically
    if (!isLoading && isAuthenticated) {
        return <Navigate to="/app" />;
    }

    return (
        <div className="min-h-screen bg-[#0B0C10] text-white font-sans selection:bg-purple-500/30 relative overflow-hidden">
            {/* Animated Gradient Background */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-purple-500/20 blur-[120px] animate-[pulse_8s_ease-in-out_infinite]" />
                <div className="absolute top-[20%] -right-[10%] w-[40%] h-[60%] rounded-full bg-indigo-500/10 blur-[120px] animate-[pulse_10s_ease-in-out_infinite_reverse]" />
                <div className="absolute bottom-[0%] left-[20%] w-[60%] h-[40%] rounded-full bg-blue-500/10 blur-[100px] animate-[pulse_12s_ease-in-out_infinite]" />
            </div>

            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none mix-blend-overlay"></div>

            <div className="relative w-full max-w-7xl mx-auto px-6 py-12 flex flex-col">
                {/* Header */}
                <header className="flex items-center justify-between mb-24 anim-fade-in">
                    <div className="flex items-center gap-2 group cursor-pointer">
                        <div className="w-6 h-6 rounded bg-gradient-to-tr from-indigo-500 to-purple-500 group-hover:shadow-[0_0_15px_rgba(99,102,241,0.5)] transition-all duration-300" />
                        <span className="font-semibold text-sm tracking-wide text-gray-300 group-hover:text-white transition-colors">CxC 2026</span>
                    </div>
                    <div>
                        <LoginButton />
                    </div>
                </header>

                {/* Hero Section */}
                <div className="flex flex-col items-center text-center max-w-4xl mx-auto mb-32">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-purple-300 mb-8 animate-fade-in-up">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
                        </span>
                        Agentic Workflow Engine v1.0
                    </div>

                    <h1 className="text-5xl md:text-8xl font-bold tracking-tight text-white mb-8 leading-tight">
                        Shop Smarter with <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 glow-text">
                            AI Agent Intelligence
                        </span>
                    </h1>

                    <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed mb-12">
                        Upload any product image. Our autonomous agents verify details, compare prices across the web, and analyze sentiment to give you the perfect recommendation.
                    </p>

                    <div className="flex items-center gap-4">
                        <LoginButton />
                        <a href="#features" className="px-6 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors">
                            Learn more ↓
                        </a>
                    </div>
                </div>

                {/* Features Grid (Bento Box) */}
                <div id="features" className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-32">
                    {/* Feature 1: Cost */}
                    <div className="glass-panel p-8 rounded-3xl flex flex-col justify-between h-[300px] group hover:border-green-500/30 transition-all">
                        <div>
                            <div className="w-12 h-12 bg-green-500/10 rounded-2xl flex items-center justify-center mb-6 text-green-400 group-hover:scale-110 transition-transform">
                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            </div>
                            <h3 className="text-2xl font-semibold mb-2 text-white">Cost Optimization</h3>
                            <p className="text-gray-400">Our agents scour the web to find the absolute best price, factoring in shipping and hidden fees.</p>
                        </div>
                    </div>

                    {/* Feature 2: Quality */}
                    <div className="glass-panel p-8 rounded-3xl flex flex-col justify-between h-[300px] group hover:border-purple-500/30 transition-all md:col-span-2">
                        <div>
                            <div className="w-12 h-12 bg-purple-500/10 rounded-2xl flex items-center justify-center mb-6 text-purple-400 group-hover:scale-110 transition-transform">
                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            </div>
                            <h3 className="text-2xl font-semibold mb-2 text-white">Quality Assurance</h3>
                            <p className="text-gray-400 max-w-lg">Don't get scammed by cheap knockoffs. We analyze thousands of reviews and verify seller reputation to ensure you buy for life, not just for now.</p>
                        </div>
                        <div className="flex gap-2 mt-4">
                            <span className="px-3 py-1 bg-purple-500/10 rounded-full text-xs text-purple-300 border border-purple-500/20">Sentiment Analysis</span>
                            <span className="px-3 py-1 bg-purple-500/10 rounded-full text-xs text-purple-300 border border-purple-500/20">Detect Fakes</span>
                        </div>
                    </div>

                    {/* Feature 3: Sustainability */}
                    <div className="glass-panel p-8 rounded-3xl flex flex-col justify-between h-[300px] group hover:border-teal-500/30 transition-all md:col-span-2">
                        <div>
                            <div className="w-12 h-12 bg-teal-500/10 rounded-2xl flex items-center justify-center mb-6 text-teal-400 group-hover:scale-110 transition-transform">
                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            </div>
                            <h3 className="text-2xl font-semibold mb-2 text-white">Sustainability Impact</h3>
                            <p className="text-gray-400 max-w-lg">Make choices that matter. We highlight eco-friendly products and carbon-neutral shipping options automatically.</p>
                        </div>
                        <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
                            <div className="h-full bg-teal-500 w-3/4"></div>
                        </div>
                    </div>

                    {/* Feature 4: Speed */}
                    <div className="glass-panel p-8 rounded-3xl flex flex-col justify-between h-[300px] group hover:border-blue-500/30 transition-all">
                        <div>
                            <div className="w-12 h-12 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 text-blue-400 group-hover:scale-110 transition-transform">
                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                            </div>
                            <h3 className="text-2xl font-semibold mb-2 text-white">Agent Speed</h3>
                            <p className="text-gray-400">Parallel processing means you get results in seconds, not ours.</p>
                        </div>
                    </div>
                </div>

                <footer className="border-t border-white/5 pt-12 text-center pb-12">
                    <p className="text-gray-500">© 2026 Shopping Suggester. Built for CxC Hackathon.</p>
                </footer>

            </div>
        </div>
    );
};

export default LandingPage;
