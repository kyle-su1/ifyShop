import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Navigate, Link } from 'react-router-dom';
import Logo from '../components/Logo';

// Typewriter effect component
const TypewriterText = ({ texts, className }) => {
    const [currentTextIndex, setCurrentTextIndex] = useState(0);
    const [displayText, setDisplayText] = useState('');
    const [isDeleting, setIsDeleting] = useState(false);

    useEffect(() => {
        const currentFullText = texts[currentTextIndex];

        const timeout = setTimeout(() => {
            if (!isDeleting) {
                if (displayText.length < currentFullText.length) {
                    setDisplayText(currentFullText.slice(0, displayText.length + 1));
                } else {
                    setTimeout(() => setIsDeleting(true), 2000);
                }
            } else {
                if (displayText.length > 0) {
                    setDisplayText(displayText.slice(0, -1));
                } else {
                    setIsDeleting(false);
                    setCurrentTextIndex((prev) => (prev + 1) % texts.length);
                }
            }
        }, isDeleting ? 50 : 100);

        return () => clearTimeout(timeout);
    }, [displayText, isDeleting, currentTextIndex, texts]);

    return (
        <span className={className}>
            {displayText}
            <span className="animate-pulse">|</span>
        </span>
    );
};

const LandingPage = () => {
    const { isAuthenticated, isLoading, loginWithRedirect, logout } = useAuth0();
    const [windowsVisible, setWindowsVisible] = useState(false);

    useEffect(() => {
        // Trigger window animation after a delay
        const timer = setTimeout(() => setWindowsVisible(true), 800);
        return () => clearTimeout(timer);
    }, []);

    const navLinks = []; // Subpages removed

    return (
        <div className="min-h-screen bg-[#08090A] text-white font-sans selection:bg-emerald-500/30 relative overflow-hidden">

            {/* Atmospheric Background Glows */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                {/* Primary green glow - behind hero */}
                <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[800px] h-[600px] rounded-full bg-emerald-500/20 blur-[150px] animate-pulse-glow" />
                {/* Secondary purple glow - left */}
                <div className="absolute top-[40%] -left-[10%] w-[500px] h-[500px] rounded-full bg-violet-500/10 blur-[120px]" />
                {/* Tertiary purple glow - right bottom */}
                <div className="absolute bottom-[10%] right-[5%] w-[400px] h-[400px] rounded-full bg-violet-500/8 blur-[100px]" />
            </div>

            {/* Noise Texture Overlay */}
            <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.03] pointer-events-none" />

            <div className="relative w-full max-w-7xl mx-auto px-6">

                {/* ============================================
                    NAVIGATION BAR
                    ============================================ */}
                <nav className="sticky top-0 z-50 py-4">
                    <div className="glass-panel px-6 py-3 flex items-center justify-between">
                        {/* Logo + Brand */}
                        <Link to="/" className="flex items-center gap-3 group cursor-pointer">
                            <Logo className="w-8 h-8 transition-transform group-hover:scale-110" />
                            <span className="font-semibold text-lg tracking-tight text-white">ifyShop</span>
                        </Link>

                        {/* Center Links - REMOVED */}
                        <div className="hidden md:flex items-center gap-8">
                        </div>

                        {/* Right Actions */}
                        <div className="flex items-center gap-4">
                            {isAuthenticated ? (
                                <button
                                    onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                                    className="px-6 py-2.5 rounded-lg border-none cursor-pointer transition-all duration-200 font-medium text-white bg-gradient-to-br from-red-500 to-red-700 shadow-[0_0_20px_rgba(239,68,68,0.3)] hover:shadow-[0_0_30px_rgba(239,68,68,0.5)] hover:-translate-y-[1px] text-sm"
                                >
                                    Sign Out
                                </button>
                            ) : (
                                <>
                                    {/* Sign In Button */}
                                    <button
                                        onClick={() => loginWithRedirect()}
                                        className="btn-primary text-sm"
                                    >
                                        Sign In
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </nav>

                {/* ============================================
                    HERO SECTION
                    ============================================ */}
                <section className="pt-20 pb-8 text-center">
                    {/* Status Badge */}
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-emerald-400 mb-8 animate-fade-in-up">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                        </span>
                        Now in Beta • CxC2026
                    </div>

                    {/* Headline */}
                    <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-6 animate-fade-in-up delay-100">
                        <span className="text-white">Shop Smarter with</span>
                        <br />
                        <span className="gradient-text-green glow-text">
                            <TypewriterText
                                texts={['AI-Powered Insights', 'Visual Search', 'Smart Comparisons', 'Price Intelligence']}
                                className=""
                            />
                        </span>
                    </h1>

                    {/* Subtext */}
                    <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed mb-10 animate-fade-in-up delay-200">
                        Upload any product image. Get instant prices, reviews, and better alternatives.
                        Powered by intelligent agents that search the entire web for you.
                    </p>

                    {/* CTA Buttons */}
                    <div className="flex items-center justify-center gap-4 animate-fade-in-up delay-300">
                        {isAuthenticated ? (
                            <Link
                                to="/app"
                                className="btn-primary px-8 py-3 text-base group flex items-center gap-2"
                            >
                                <span>Go to Dashboard</span>
                                <svg className="w-5 h-5 ml-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                </svg>
                            </Link>
                        ) : (
                            <button
                                onClick={() => loginWithRedirect()}
                                className="btn-primary px-8 py-3 text-base"
                            >
                                Go to Dashboard
                            </button>
                        )}
                        {/* Secondary Link Removed */}
                    </div>
                </section>

                {/* ============================================
                    TILTED INTERFACE SHOWCASE
                    ============================================ */}
                <section className="py-16 relative">
                    <div className="flex items-center justify-center gap-4 md:gap-8 perspective-1000">
                        {/* Left Window */}
                        <div
                            className={`relative w-[280px] md:w-[400px] h-[200px] md:h-[280px] transition-all duration-1000 ease-out ${windowsVisible
                                ? 'opacity-100 translate-y-0'
                                : 'opacity-0 translate-y-20'
                                }`}
                            style={{
                                transform: windowsVisible
                                    ? 'perspective(1000px) rotateY(15deg) rotateX(5deg)'
                                    : 'perspective(1000px) rotateY(15deg) rotateX(5deg) translateY(40px)',
                                transformStyle: 'preserve-3d',
                                transitionDelay: '200ms'
                            }}
                        >
                            <div className="absolute inset-0 glass-card rounded-xl overflow-hidden">
                                {/* Window Chrome */}
                                <div className="h-8 bg-gradient-to-b from-white/10 to-transparent border-b border-white/10 flex items-center px-3 gap-1.5">
                                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
                                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
                                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
                                    <span className="ml-3 text-xs text-gray-500">ifyShop Dashboard</span>
                                </div>
                                {/* Placeholder Content */}
                                <div className="p-4 space-y-3">
                                    <div className="h-3 bg-white/10 rounded w-3/4" />
                                    <div className="h-3 bg-white/5 rounded w-1/2" />
                                    <div className="grid grid-cols-2 gap-2 mt-4">
                                        <div className="h-16 bg-emerald-500/10 rounded-lg border border-emerald-500/20 flex items-center justify-center">
                                            <span className="text-2xl">📷</span>
                                        </div>
                                        <div className="h-16 bg-white/5 rounded-lg border border-white/10 flex items-center justify-center">
                                            <span className="text-2xl">📊</span>
                                        </div>
                                    </div>
                                    <div className="h-20 bg-white/5 rounded-lg border border-white/10 mt-2 p-2">
                                        <div className="h-2 bg-emerald-500/30 rounded w-full" />
                                        <div className="h-2 bg-emerald-500/20 rounded w-3/4 mt-2" />
                                    </div>
                                </div>
                            </div>
                            {/* Glow Effect */}
                            <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500/20 to-transparent rounded-xl blur-xl -z-10" />
                        </div>

                        {/* Right Window */}
                        <div
                            className={`relative w-[280px] md:w-[400px] h-[200px] md:h-[280px] transition-all duration-1000 ease-out ${windowsVisible
                                ? 'opacity-100 translate-y-0'
                                : 'opacity-0 translate-y-20'
                                }`}
                            style={{
                                transform: windowsVisible
                                    ? 'perspective(1000px) rotateY(-15deg) rotateX(5deg)'
                                    : 'perspective(1000px) rotateY(-15deg) rotateX(5deg) translateY(40px)',
                                transformStyle: 'preserve-3d',
                                transitionDelay: '400ms'
                            }}
                        >
                            <div className="absolute inset-0 glass-card rounded-xl overflow-hidden">
                                {/* Window Chrome */}
                                <div className="h-8 bg-gradient-to-b from-white/10 to-transparent border-b border-white/10 flex items-center px-3 gap-1.5">
                                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
                                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
                                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
                                    <span className="ml-3 text-xs text-gray-500">Product Analysis</span>
                                </div>
                                {/* Placeholder Content - Results Style */}
                                <div className="p-4 space-y-3">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs rounded-full">Recommended</span>
                                    </div>
                                    <div className="h-3 bg-white/10 rounded w-full" />
                                    <div className="h-3 bg-white/5 rounded w-2/3" />
                                    <div className="flex items-center gap-2 mt-4">
                                        <div className="text-xl font-bold text-emerald-400">$42.99</div>
                                        <span className="text-xs text-gray-500 line-through">$59.99</span>
                                    </div>
                                    <div className="h-10 bg-emerald-500/10 rounded-lg border border-emerald-500/20 flex items-center justify-center text-emerald-400 text-sm">
                                        View Best Deal →
                                    </div>
                                </div>
                            </div>
                            {/* Glow Effect */}
                            <div className="absolute -inset-1 bg-gradient-to-l from-violet-500/20 to-transparent rounded-xl blur-xl -z-10" />
                        </div>
                    </div>

                    {/* Subtext below windows */}
                    <p className="text-center text-gray-500 text-sm mt-12 animate-fade-in-up delay-500">
                        See anything. Know everything. Buy smarter.
                    </p>
                </section>

                {/* ============================================
                    FEATURES GRID (Bento Box)
                    ============================================ */}
                <section id="features" className="py-20 relative">
                    {/* Background glow for features */}
                    <div className="absolute inset-0 pointer-events-none">
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-emerald-500/5 rounded-full blur-[100px]" />
                    </div>

                    <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">Why Choose ifyShop?</h2>
                    <p className="text-gray-400 text-center mb-12 max-w-xl mx-auto">Everything you need to make confident purchase decisions.</p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
                        {/* Feature 1: Price Intel */}
                        <div className="glass-card p-8 rounded-2xl flex flex-col h-[280px] group hover:border-emerald-500/30 transition-all duration-300 animate-fade-in-up">
                            <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:bg-emerald-500/20 transition-colors">
                                <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-semibold mb-3 text-white">Find the Lowest Price</h3>
                            <p className="text-gray-400 text-sm leading-relaxed">
                                Our agents search hundreds of retailers in real-time. We factor in shipping, taxes, and hidden fees so you see the true cost.
                            </p>
                        </div>

                        {/* Feature 2: Reviews - Spans 2 columns */}
                        <div className="glass-card p-8 rounded-2xl flex flex-col h-[280px] md:col-span-2 group hover:border-violet-500/30 transition-all duration-300 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
                            <div className="w-12 h-12 bg-violet-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:bg-violet-500/20 transition-colors">
                                <svg className="w-6 h-6 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-semibold mb-3 text-white">Verified Reviews Only</h3>
                            <p className="text-gray-400 text-sm leading-relaxed max-w-lg">
                                Fake reviews are everywhere. We analyze sentiment patterns, purchase verification, and reviewer history to surface only genuine feedback you can trust.
                            </p>
                            <div className="flex gap-2 mt-auto pt-4">
                                <span className="px-3 py-1 bg-violet-500/10 rounded-full text-xs text-violet-300 border border-violet-500/20">Sentiment Analysis</span>
                                <span className="px-3 py-1 bg-violet-500/10 rounded-full text-xs text-violet-300 border border-violet-500/20">Fake Detection</span>
                            </div>
                        </div>

                        {/* Feature 3: Visual Search - Spans 2 columns */}
                        <div className="glass-card p-8 rounded-2xl flex flex-col h-[280px] md:col-span-2 group hover:border-teal-500/30 transition-all duration-300 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
                            <div className="w-12 h-12 bg-teal-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:bg-teal-500/20 transition-colors">
                                <svg className="w-6 h-6 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-semibold mb-3 text-white">Visual Product Search</h3>
                            <p className="text-gray-400 text-sm leading-relaxed max-w-lg">
                                See something you like? Just snap a photo or upload an image. Our AI identifies products instantly—even from partial images or cluttered backgrounds.
                            </p>
                            <div className="mt-auto pt-4">
                                <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-gradient-to-r from-teal-500 to-emerald-400 w-[92%] rounded-full" />
                                </div>
                                <p className="text-xs text-gray-500 mt-2">92% recognition accuracy</p>
                            </div>
                        </div>

                        {/* Feature 4: Speed */}
                        <div className="glass-card p-8 rounded-2xl flex flex-col h-[280px] group hover:border-blue-500/30 transition-all duration-300 animate-fade-in-up" style={{ animationDelay: '300ms' }}>
                            <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:bg-blue-500/20 transition-colors">
                                <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-semibold mb-3 text-white">Results in Seconds</h3>
                            <p className="text-gray-400 text-sm leading-relaxed">
                                Multiple AI agents work in parallel. What would take you hours of research takes us seconds.
                            </p>
                        </div>
                    </div>
                </section>

                {/* ============================================
                    FINAL CTA
                    ============================================ */}
                <section className="py-20 text-center">
                    <div className="glass-card p-12 md:p-16 rounded-3xl max-w-4xl mx-auto animate-fade-in-up">
                        <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to Shop Smarter?</h2>
                        <p className="text-gray-400 mb-8 max-w-lg mx-auto">
                            Join thousands of smart shoppers who never overpay or get fooled by fake reviews again.
                        </p>
                        <button
                            onClick={() => loginWithRedirect()}
                            className="btn-primary px-10 py-4 text-lg"
                        >
                            Start Free — No Credit Card Required
                        </button>
                    </div>
                </section>

                {/* ============================================
                    FOOTER
                    ============================================ */}
                <footer className="border-t border-white/5 py-12">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="flex items-center gap-2">
                            <Logo className="w-6 h-6" />
                            <span className="font-medium text-white">ifyShop</span>
                        </div>
                        <div className="flex items-center gap-6 text-sm text-gray-400">
                            {navLinks.map((link) => (
                                <Link key={link.name} to={link.path} className="hover:text-white transition-colors">
                                    {link.name}
                                </Link>
                            ))}
                        </div>
                        <p className="text-gray-500 text-sm">
                            © 2026 ifyShop. Built for CxC Hackathon.
                        </p>
                    </div>
                </footer>
            </div>
        </div>
    );
};

export default LandingPage;
