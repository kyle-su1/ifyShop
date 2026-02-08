import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import Logo from '../components/Logo';

const ProductPage = () => {
    const { isAuthenticated, loginWithRedirect } = useAuth0();
    const features = [
        {
            title: "Visual Recognition",
            description: "Upload any product image and our AI identifies items instantly. From groceries to electronics, we recognize millions of products.",
            visual: "🔍"
        },
        {
            title: "Smart Price Hunting",
            description: "Our agents search across hundreds of retailers in real-time to find you the absolute best price, including hidden deals and coupons.",
            visual: "💰"
        },
        {
            title: "Review Analysis",
            description: "We analyze thousands of reviews to separate genuine feedback from fake ones. Know exactly what you're buying before you buy.",
            visual: "⭐"
        },
        {
            title: "Alternative Discovery",
            description: "Found something you like? We'll show you similar products that might be better, cheaper, or more sustainable.",
            visual: "🔄"
        }
    ];

    const steps = [
        { step: "01", title: "Upload", description: "Take a photo or upload an image of any product" },
        { step: "02", title: "Analyze", description: "Our AI agents process and identify what you're looking for" },
        { step: "03", title: "Discover", description: "Get prices, reviews, and alternatives in seconds" },
        { step: "04", title: "Decide", description: "Make informed purchases with confidence" }
    ];

    return (
        <div className="min-h-screen bg-[#08090A] text-white font-sans">
            {/* Background */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[30%] right-[10%] w-[500px] h-[500px] rounded-full bg-violet-500/10 blur-[120px]" />
                <div className="absolute bottom-[20%] left-[10%] w-[400px] h-[400px] rounded-full bg-emerald-500/10 blur-[100px]" />
            </div>

            {/* Navigation */}
            <div className="relative w-full max-w-7xl mx-auto px-6">
                <nav className="sticky top-0 z-50 py-4">
                    <div className="glass-panel px-6 py-3 flex items-center justify-between">
                        <Link to="/" className="flex items-center gap-3 group cursor-pointer">
                            <Logo className="w-8 h-8 transition-all duration-300 group-hover:scale-110 group-hover:rotate-[360deg]" />
                            <span className="font-semibold text-lg tracking-tight">ifyShop</span>
                        </Link>

                        <div className="hidden md:flex items-center gap-8">
                            <Link to="/demo" className="relative text-sm text-gray-400 hover:text-white transition-colors duration-200 py-2 group">
                                Demo
                                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-emerald-500 transition-all duration-300 group-hover:w-full" />
                            </Link>
                            <Link to="/solutions" className="relative text-sm text-gray-400 hover:text-white transition-colors duration-200 py-2 group">
                                Solutions
                                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-emerald-500 transition-all duration-300 group-hover:w-full" />
                            </Link>
                            <Link to="/product" className="relative text-sm text-emerald-400 font-medium py-2 group">
                                Product
                                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-emerald-500 transition-all duration-300" />
                            </Link>
                            <Link to="/company" className="relative text-sm text-gray-400 hover:text-white transition-colors duration-200 py-2 group">
                                Company
                                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-emerald-500 transition-all duration-300 group-hover:w-full" />
                            </Link>
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

                {/* Hero */}
                <div className="relative py-20">
                    <div className="text-center mb-20 animate-fade-in-up">
                        <h1 className="text-4xl md:text-6xl font-bold mb-6">
                            How <span className="gradient-text-green">ifyShop</span> Works
                        </h1>
                        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                            Powered by multi-agent AI that thinks like a team of expert shoppers working just for you.
                        </p>
                    </div>

                    {/* How it Works Steps */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-24">
                        {steps.map((item, idx) => (
                            <div
                                key={idx}
                                className="text-center animate-fade-in-up"
                                style={{ animationDelay: `${idx * 100}ms` }}
                            >
                                <div className="text-5xl font-bold text-emerald-500/20 mb-4">{item.step}</div>
                                <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                                <p className="text-sm text-gray-400">{item.description}</p>
                            </div>
                        ))}
                    </div>

                    {/* Features Grid */}
                    <div className="mb-20">
                        <h2 className="text-3xl font-bold text-center mb-12">Core Features</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {features.map((feature, idx) => (
                                <div
                                    key={idx}
                                    className="glass-card p-8 rounded-2xl hover:border-emerald-500/30 transition-all duration-300 flex gap-6 animate-fade-in-up"
                                    style={{ animationDelay: `${idx * 100}ms` }}
                                >
                                    <div className="text-4xl">{feature.visual}</div>
                                    <div>
                                        <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                                        <p className="text-gray-400">{feature.description}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Agent Architecture */}
                    <div className="glass-card p-12 rounded-3xl text-center animate-fade-in-up">
                        <h2 className="text-3xl font-bold mb-6">Multi-Agent Architecture</h2>
                        <p className="text-gray-400 max-w-2xl mx-auto mb-10">
                            Unlike simple chatbots, ifyShop uses specialized AI agents that work together:
                        </p>
                        <div className="flex flex-wrap justify-center gap-4">
                            {['Vision Agent', 'Discovery Agent', 'Market Scout', 'Review Analyst', 'Price Optimizer'].map((agent, idx) => (
                                <div
                                    key={idx}
                                    className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-sm text-emerald-300"
                                >
                                    {agent}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* CTA */}
                    <div className="text-center mt-20">
                        <Link to="/app" className="btn-primary px-8 py-3 text-base inline-block">
                            Try It Now
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProductPage;
