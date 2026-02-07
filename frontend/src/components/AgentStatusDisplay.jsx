import React, { useEffect, useState } from 'react';

const AgentStatusDisplay = ({ activeStep, error }) => {
    const steps = [
        { label: 'Vision Processing', detail: 'Detecting objects & OCR...' },
        { label: 'Discovery Layer', detail: 'Gathering market data...' },
        { label: 'Market Scout', detail: 'Searching alternatives...' },
        { label: 'Skeptic Verify', detail: 'Checking review authenticity...' },
        { label: 'Final Analysis', detail: 'Scoring & synthesizing...' },
    ];

    return (
        <div className="w-full h-full flex flex-col justify-center items-center py-12 px-6">
            <div className="w-full max-w-sm space-y-4">
                <h3 className="text-xl font-semibold text-white mb-6 text-center">Processing Request</h3>

                {steps.map((step, idx) => {
                    const isComplete = idx < activeStep;
                    const isCurrent = idx === activeStep;
                    const isPending = idx > activeStep;

                    return (
                        <div
                            key={idx}
                            className={`
                relative flex items-center gap-4 p-3 rounded-lg border transition-all duration-300
                ${isCurrent ? 'bg-white/10 border-indigo-500/50 scale-105 shadow-[0_0_15px_rgba(99,102,241,0.2)]' : ''}
                ${isComplete ? 'bg-white/5 border-green-500/30 opacity-70' : ''}
                ${isPending ? 'border-transparent opacity-30' : ''}
              `}
                        >
                            {/* Status Icon */}
                            <div className="flex-shrink-0">
                                {isComplete ? (
                                    <div className="w-6 h-6 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                                    </div>
                                ) : isCurrent ? (
                                    <div className="w-6 h-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>
                                ) : (
                                    <div className="w-6 h-6 rounded-full border border-white/10 bg-white/5"></div>
                                )}
                            </div>

                            {/* Text */}
                            <div className="flex-1 min-w-0">
                                <p className={`font-medium ${isCurrent ? 'text-white' : 'text-gray-400'} truncated`}>
                                    {step.label}
                                </p>
                                {isCurrent && (
                                    <p className="text-xs text-indigo-300 animate-pulse">{step.detail}</p>
                                )}
                            </div>

                            {/* Connecting Line (except last item) */}
                            {idx < steps.length - 1 && (
                                <div className={`
                  absolute left-[27px] top-10 w-0.5 h-6 
                  ${isComplete ? 'bg-green-500/30' : 'bg-white/5'}
                  -z-10
                `}></div>
                            )}
                        </div>
                    );
                })}

                {error && (
                    <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm text-center">
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AgentStatusDisplay;
