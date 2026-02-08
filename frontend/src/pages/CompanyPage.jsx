import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import Logo from '../components/Logo';

const CompanyPage = () => {
    const { isAuthenticated, loginWithRedirect } = useAuth0();
    const team = [
        { name: "Ryan Qi", role: "Engineer", emoji: "⚡" },
        { name: "Tony Tan", role: "Engineer", emoji: "👨‍💻" },
        { name: "Kyle Su", role: "Engineer", emoji: "🧠" },
        { name: "Frank Zeng", role: "Engineer", emoji: "🎨" }
    ];

    const values = [
        {
            title: "User First",
            description: "Every feature we build starts with a real user problem. We obsess over making shopping easier, not just more technological."
        },
        {
            title: "Transparency",
            description: "We show you exactly how we find prices and analyze reviews. No black boxes, no hidden agendas."
        },
        {
            title: "Sustainability",
            description: "We highlight eco-friendly options and help you make purchases that last. Quality over quantity."
        }
    ];

    return (
        <div className="min-h-screen bg-[#08090A] text-white font-sans">
            {/* Background */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[40%] left-[20%] w-[400px] h-[400px] rounded-full bg-violet-500/10 blur-[120px]" />
                <div className="absolute bottom-[30%] right-[20%] w-[300px] h-[300px] rounded-full bg-emerald-500/10 blur-[100px]" />
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
                            <Link to="/product" className="relative text-sm text-gray-400 hover:text-white transition-colors duration-200 py-2 group">
                                Product
                                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-emerald-500 transition-all duration-300 group-hover:w-full" />
                            </Link>
                            <Link to="/company" className="relative text-sm text-emerald-400 font-medium py-2 group">
                                Company
                                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-emerald-500 transition-all duration-300" />
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
                    {/* Hero */}
                    <div className="text-center mb-20 animate-fade-in-up">
                        <h1 className="text-4xl md:text-6xl font-bold mb-6">
                            About <span className="gradient-text-green">ifyShop</span>
                        </h1>
                        <p className="text-xl text-gray-400 max-w-3xl mx-auto">
                            We're building the future of smart shopping. Founded at CxC 2026 Hackathon, ifyShop
                            uses multi-agent AI to help people shop smarter, save money, and make informed decisions.
                        </p>
                    </div>

                    {/* Mission */}
                    <div className="glass-card p-12 rounded-3xl text-center mb-20 animate-fade-in-up">
                        <h2 className="text-3xl font-bold mb-6">Our Mission</h2>
                        <p className="text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
                            "To eliminate buyer's remorse by giving everyone access to intelligent shopping assistance that was once only available to experts and insiders."
                        </p>
                    </div>

                    {/* Values */}
                    <div className="mb-20">
                        <h2 className="text-3xl font-bold text-center mb-12">What We Believe</h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                            {values.map((value, idx) => (
                                <div
                                    key={idx}
                                    className="glass-card p-8 rounded-2xl animate-fade-in-up"
                                    style={{ animationDelay: `${idx * 100}ms` }}
                                >
                                    <h3 className="text-xl font-semibold mb-4 text-emerald-400">{value.title}</h3>
                                    <p className="text-gray-400">{value.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Team */}
                    <div className="mb-20">
                        <h2 className="text-3xl font-bold text-center mb-12">The Team</h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                            {team.map((member, idx) => (
                                <div
                                    key={idx}
                                    className="glass-card p-6 rounded-2xl text-center animate-fade-in-up"
                                    style={{ animationDelay: `${idx * 100}ms` }}
                                >
                                    <div className="text-5xl mb-4">{member.emoji}</div>
                                    <h3 className="font-semibold mb-1">{member.name}</h3>
                                    <p className="text-sm text-gray-400">{member.role}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Contact */}
                    <div className="glass-card p-12 rounded-3xl text-center animate-fade-in-up">
                        <h2 className="text-3xl font-bold mb-6">Get in Touch</h2>
                        <p className="text-gray-400 mb-8 max-w-xl mx-auto">
                            Have questions, feedback, or partnership inquiries? We'd love to hear from you.
                        </p>
                        <div className="flex flex-wrap justify-center gap-4">
                            <a
                                href="mailto:team@ifyshop.com"
                                className="btn-primary px-6 py-3"
                            >
                                Email Us
                            </a>
                            <a
                                href="https://github.com/kyle-su1/CxC2026"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-6 py-3 bg-white/10 hover:bg-white/20 border border-white/10 rounded-lg transition-colors"
                            >
                                GitHub
                            </a>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <footer className="border-t border-white/5 py-12 text-center">
                    <p className="text-gray-500 text-sm">
                        © 2026 ifyShop. Built with ❤️ at CxC Hackathon.
                    </p>
                </footer>
            </div>
        </div>
    );
};

export default CompanyPage;
