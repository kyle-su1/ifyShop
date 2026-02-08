import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import Logo from '../components/Logo';

const SolutionsPage = () => {
    const { isAuthenticated, loginWithRedirect } = useAuth0();
    const solutions = [
        {
            title: "For Shoppers",
            description: "Find the best products at the best prices without hours of research.",
            features: [
                "AI-powered product discovery",
                "Real-time price comparison across retailers",
                "Authenticity verification for reviews",
                "Personalized recommendations"
            ],
            icon: (
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
            )
        },
        {
            title: "For Researchers",
            description: "Analyze product trends and market data with intelligent agents.",
            features: [
                "Batch image analysis",
                "Market trend identification",
                "Competitive pricing insights",
                "Export data to any format"
            ],
            icon: (
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
            )
        },
        {
            title: "For Businesses",
            description: "Integrate AI shopping intelligence into your own applications.",
            features: [
                "REST API access",
                "Webhook notifications",
                "Custom model training",
                "White-label solutions"
            ],
            icon: (
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
            )
        }
    ];

    return (
        <div className="min-h-screen bg-[#08090A] text-white font-sans">
            {/* Background */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[20%] left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-emerald-500/10 blur-[120px]" />
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
                            <Link to="/solutions" className="relative text-sm text-emerald-400 font-medium py-2 group">
                                Solutions
                                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-emerald-500 transition-all duration-300" />
                            </Link>
                            <Link to="/product" className="relative text-sm text-gray-400 hover:text-white transition-colors duration-200 py-2 group">
                                Product
                                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-emerald-500 transition-all duration-300 group-hover:w-full" />
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

                {/* Content */}
                <div className="relative py-20">
                    <div className="text-center mb-16 animate-fade-in-up">
                        <h1 className="text-4xl md:text-6xl font-bold mb-6">
                            Solutions for <span className="gradient-text-green">Everyone</span>
                        </h1>
                        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                            Whether you're a savvy shopper or a data-driven business, ifyShop adapts to your needs.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {solutions.map((solution, idx) => (
                            <div
                                key={idx}
                                className="glass-card p-8 rounded-2xl hover:border-emerald-500/30 transition-all duration-300 animate-fade-in-up"
                                style={{ animationDelay: `${idx * 100}ms` }}
                            >
                                <div className="w-14 h-14 bg-emerald-500/10 rounded-xl flex items-center justify-center text-emerald-400 mb-6">
                                    {solution.icon}
                                </div>
                                <h3 className="text-2xl font-semibold mb-3">{solution.title}</h3>
                                <p className="text-gray-400 mb-6">{solution.description}</p>
                                <ul className="space-y-3">
                                    {solution.features.map((feature, fIdx) => (
                                        <li key={fIdx} className="flex items-center gap-2 text-sm text-gray-300">
                                            <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                                            </svg>
                                            {feature}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>

                    {/* CTA */}
                    <div className="text-center mt-20 animate-fade-in-up" style={{ animationDelay: '400ms' }}>
                        <Link to="/app" className="btn-primary px-8 py-3 text-base inline-block">
                            Get Started Free
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SolutionsPage;
