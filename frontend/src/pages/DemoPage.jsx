import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import Logo from '../components/Logo';

const DemoPage = () => {
    const { isAuthenticated, loginWithRedirect } = useAuth0();
    const [demoStep, setDemoStep] = useState(0);

    const navLinks = [
        { name: 'Demo', path: '/demo' },
        { name: 'Solutions', path: '/solutions' },
        { name: 'Product', path: '/product' },
        { name: 'Company', path: '/company' }
    ];

    const runDemo = () => {
        setDemoStep(1); // Scanning
        setTimeout(() => {
            setDemoStep(2); // Results
        }, 1500);
    };

    const resetDemo = () => {
        setDemoStep(0);
    };

    return (
        <div className="min-h-screen bg-[#08090A] text-white font-sans">
            {/* Simple Background Gradient */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[-20%] left-1/2 -translate-x-1/2 w-[800px] h-[600px] rounded-full bg-emerald-500/10 blur-[120px]" />
            </div>

            <div className="relative w-full max-w-7xl mx-auto px-6">
                {/* Navigation */}
                <nav className="sticky top-0 z-50 py-4">
                    <div className="glass-panel px-6 py-3 flex items-center justify-between">
                        <Link to="/" className="flex items-center gap-3 group cursor-pointer">
                            <Logo className="w-8 h-8 transition-all duration-300 group-hover:scale-110 group-hover:rotate-[360deg]" />
                            <span className="font-semibold text-lg tracking-tight text-white">ifyShop</span>
                        </Link>

                        <div className="hidden md:flex items-center gap-8">
                            {navLinks.map((link) => (
                                <Link
                                    key={link.name}
                                    to={link.path}
                                    className={`relative text-sm font-medium transition-colors duration-200 py-2 group ${link.path === '/demo' ? 'text-emerald-400' : 'text-gray-400 hover:text-white'}`}
                                >
                                    {link.name}
                                    <span className={`absolute bottom-0 left-0 h-0.5 bg-emerald-500 transition-all duration-300 ${link.path === '/demo' ? 'w-full' : 'w-0 group-hover:w-full'}`} />
                                </Link>
                            ))}
                        </div>

                        <div className="flex items-center gap-4">
                            {isAuthenticated ? (
                                <Link
                                    to="/app"
                                    className="btn-primary text-sm group flex items-center gap-2 px-6 py-2"
                                >
                                    <span>Dashboard</span>
                                    <svg className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                    </svg>
                                </Link>
                            ) : (
                                <>
                                    <button
                                        onClick={() => loginWithRedirect()}
                                        className="text-sm text-gray-300 hover:text-white transition-colors"
                                    >
                                        Sign In
                                    </button>
                                    <button
                                        onClick={() => loginWithRedirect()}
                                        className="btn-primary text-sm px-6 py-2"
                                    >
                                        Try Demo
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </nav>

                {/* Hero / Instruction */}
                <div className="py-16 text-center">
                    <h1 className="text-4xl md:text-5xl font-bold mb-6">See <span className="text-emerald-400">ifyShop</span> in Action</h1>
                    <p className="text-gray-400 max-w-2xl mx-auto mb-12 text-lg">
                        A simple demonstration of how our AI agents identifying products and finding prices.
                    </p>

                    {/* Interactive Demo Container */}
                    <div className="glass-card max-w-4xl mx-auto rounded-2xl overflow-hidden border border-white/10 bg-[#0B0C0E]">
                        {/* Demo Window Header */}
                        <div className="h-10 bg-white/5 border-b border-white/10 flex items-center px-4 gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-500/50" />
                            <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                            <div className="w-3 h-3 rounded-full bg-green-500/50" />
                            <div className="ml-4 px-3 py-1 bg-black/20 rounded text-xs text-gray-400 font-mono">
                                demo_session.js
                            </div>
                        </div>

                        {/* Demo Content */}
                        <div className="p-8 md:p-12 min-h-[400px] flex items-center justify-center">
                            {demoStep === 0 && (
                                <div className="text-center animate-fade-in">
                                    <div className="w-24 h-24 bg-white/5 rounded-2xl border-2 border-dashed border-white/20 flex items-center justify-center mx-auto mb-6">
                                        <svg className="w-10 h-10 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                        </svg>
                                    </div>
                                    <h3 className="text-xl font-semibold mb-2">Select a Product</h3>
                                    <p className="text-gray-400 mb-8">Upload an image to start the analysis.</p>
                                    <button
                                        onClick={runDemo}
                                        className="btn-primary px-8 py-3 text-base"
                                    >
                                        Upload Demo Image
                                    </button>
                                </div>
                            )}

                            {demoStep === 1 && (
                                <div className="text-center w-full max-w-md animate-fade-in">
                                    <div className="mb-8 relative w-32 h-32 mx-auto">
                                        {/* Simple spinner */}
                                        <div className="absolute inset-0 rounded-full border-4 border-white/10"></div>
                                        <div className="absolute inset-0 rounded-full border-4 border-emerald-500 border-t-transparent animate-spin"></div>
                                        <div className="absolute inset-0 flex items-center justify-center font-bold text-2xl">🤖</div>
                                    </div>
                                    <h3 className="text-xl font-semibold mb-2">AI Agents Working...</h3>
                                    <div className="space-y-2 text-sm text-gray-400 mt-6 font-mono text-left bg-black/30 p-4 rounded-lg">
                                        <div className="flex items-center gap-2">
                                            <span className="text-emerald-400">✓</span> Vision Agent: Identifying object...
                                        </div>
                                        <div className="flex items-center gap-2 animate-pulse">
                                            <span className="text-blue-400">➜</span> Market Scout: Searching 500+ stores...
                                        </div>
                                    </div>
                                </div>
                            )}

                            {demoStep === 2 && (
                                <div className="w-full animate-fade-in text-left grid md:grid-cols-2 gap-8">
                                    {/* Left: Product Image */}
                                    <div className="bg-white/5 rounded-xl border border-white/10 p-6 flex flex-col items-center justify-center">
                                        <div className="text-6xl mb-4">🎧</div>
                                        <div className="font-semibold">Sony WH-1000XM5</div>
                                        <div className="text-xs px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded mt-2">Match Confidence: 99.8%</div>
                                    </div>

                                    {/* Right: Results */}
                                    <div className="space-y-4">
                                        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                                            <div className="text-sm text-emerald-400 mb-1">Best Price Found</div>
                                            <div className="text-3xl font-bold">$298.00</div>
                                            <div className="text-xs text-gray-400">via Amazon (Saved $50)</div>
                                        </div>

                                        <div className="space-y-2">
                                            <div className="flex justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                                                <span>Best Buy</span>
                                                <span className="text-gray-300">$348.00</span>
                                            </div>
                                            <div className="flex justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                                                <span>Walmart</span>
                                                <span className="text-gray-300">$329.99</span>
                                            </div>
                                        </div>

                                        <button
                                            onClick={resetDemo}
                                            className="w-full btn-primary py-3 mt-4"
                                        >
                                            Try Another Product
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <footer className="border-t border-white/5 py-12 flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="flex items-center gap-2">
                        <Logo className="w-6 h-6" />
                        <span className="font-medium">ifyShop</span>
                    </div>
                    <p className="text-gray-500 text-sm">© 2026 ifyShop. Simple Demo.</p>
                </footer>
            </div>
        </div>
    );
};

export default DemoPage;
