import React from 'react';

const AgentStatusDisplay = ({ activeStep, error, isRefining }) => {
    const steps = [
        {
            label: 'Vision Processing',
            detail: 'Detecting objects & OCR...',
            icon: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
        },
        {
            label: 'Discovery Layer',
            detail: 'Gathering market data...',
            icon: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
        },
        {
            label: 'Market Scout',
            detail: isRefining ? 'Re-scanning market for better options...' : 'Searching alternatives...',
            icon: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
        },
        {
            label: 'Skeptic Verify',
            detail: 'Checking review authenticity...',
            icon: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        },
        {
            label: 'Final Analysis',
            detail: 'Scoring & synthesizing...',
            icon: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
        },
    ];

    return (
        <div className="w-full h-full flex flex-col justify-center items-center py-8 px-6 animate-fade-in">
            <div className="w-full max-w-md">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-500/10 rounded-2xl mb-4 relative">
                        {isRefining && (
                            <div className="absolute -top-1 -right-1 w-4 h-4 bg-amber-500 rounded-full animate-ping" />
                        )}
                        <div className={`w-8 h-8 border-3 ${isRefining ? 'border-amber-500' : 'border-emerald-500'} border-t-transparent rounded-full animate-spin`} />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">
                        {isRefining ? 'Deep Search Activated' : 'Analyzing Your Product'}
                    </h3>
                    <p className="text-sm text-gray-500">
                        {isRefining ? 'Skeptic Agent detected low quality results. Looping...' : '"If I shop, I use ifyShop"'}
                    </p>
                </div>

                {/* Steps */}
                <div className="space-y-3">
                    {steps.map((step, idx) => {
                        const isComplete = idx < activeStep;
                        const isCurrent = idx === activeStep;
                        const isPending = idx > activeStep;

                        // Special styling for refining state (amber/orange theme)
                        const activeColor = isRefining && isCurrent ? 'text-amber-400' : 'text-emerald-400';
                        // Explicit classes for Tailwind JIT
                        const activeBg = isRefining && isCurrent ? 'bg-amber-500/10' : 'bg-emerald-500/10';
                        const activeBorder = isRefining && isCurrent ? 'border-amber-500/30' : 'border-emerald-500/30';
                        const activePulse = isRefining && isCurrent ? 'bg-amber-500' : 'bg-emerald-500';
                        const activeGradient = isRefining && isCurrent ? 'from-amber-500/10 shadow-amber-500/10' : 'from-emerald-500/10 shadow-emerald-500/10';

                        return (
                            <div
                                key={idx}
                                className={`
                                    relative flex items-center gap-4 p-4 rounded-xl border transition-all duration-500 animate-fade-in-up
                                    ${isCurrent ? `bg-gradient-to-r ${activeGradient} to-transparent ${activeBorder} scale-[1.02] shadow-lg` : ''}
                                    ${isComplete ? 'bg-white/5 border-emerald-500/20' : ''}
                                    ${isPending ? 'border-white/5 opacity-40' : ''}
                                `}
                                style={{ animationDelay: `${idx * 100}ms` }}
                            >
                                {/* Status Icon */}
                                <div className="flex-shrink-0">
                                    {isComplete ? (
                                        <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center animate-scale-in">
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7"></path>
                                            </svg>
                                        </div>
                                    ) : isCurrent ? (
                                        <div className={`w-10 h-10 rounded-xl ${activeBg} ${activeBorder} flex items-center justify-center`}>
                                            <div className={`w-5 h-5 border-2 ${isRefining ? 'border-amber-500' : 'border-emerald-500'} border-t-transparent rounded-full animate-spin`}></div>
                                        </div>
                                    ) : (
                                        <div className="w-10 h-10 rounded-xl border border-white/10 bg-white/5 flex items-center justify-center text-lg text-emerald-400/80">
                                            {step.icon}
                                        </div>
                                    )}
                                </div>

                                {/* Text */}
                                <div className="flex-1 min-w-0">
                                    <p className={`font-semibold transition-colors ${isCurrent ? 'text-white' : isComplete ? 'text-gray-400' : 'text-gray-500'}`}>
                                        {step.label}
                                    </p>
                                    {isCurrent && (
                                        <p className={`text-xs ${activeColor} mt-0.5 animate-pulse`}>{step.detail}</p>
                                    )}
                                    {isComplete && (
                                        <p className="text-xs text-emerald-600 mt-0.5">Complete</p>
                                    )}
                                </div>

                                {/* Progress indicator for current */}
                                {isCurrent && (
                                    <div className={`w-2 h-2 rounded-full ${activePulse} animate-pulse`} />
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Progress bar */}
                <div className="mt-8">
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                        <span>Progress</span>
                        <span>{Math.round((activeStep / steps.length) * 100)}%</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <div
                            className={`h-full bg-gradient-to-r ${isRefining ? 'from-amber-600 to-amber-400' : 'from-emerald-600 to-emerald-400'} rounded-full transition-all duration-700 ease-out`}
                            style={{ width: `${(activeStep / steps.length) * 100}%` }}
                        />
                    </div>
                </div>

                {error && (
                    <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm text-center animate-fade-in-up">
                        <div className="flex items-center justify-center gap-2">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {error}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AgentStatusDisplay;
