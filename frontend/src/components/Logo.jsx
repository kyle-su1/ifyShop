import React from 'react';

const Logo = ({ className = "w-8 h-8" }) => {
    return (
        <svg
            viewBox="0 0 100 100"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className={className}
        >
            {/* Shopping Bag Body - Filled */}
            <path
                d="M20 35 L25 85 C25 88 27 90 30 90 L70 90 C73 90 75 88 75 85 L80 35 L20 35 Z"
                fill="url(#bagGradient)"
            />
            {/* Bag Handle */}
            <path
                d="M35 35 L35 25 C35 17 42 10 50 10 C58 10 65 17 65 25 L65 35"
                stroke="#10B981"
                strokeWidth="5"
                fill="none"
                strokeLinecap="round"
            />
            {/* Shine/Highlight */}
            <path
                d="M30 45 L35 80"
                stroke="rgba(255,255,255,0.3)"
                strokeWidth="3"
                strokeLinecap="round"
            />
            <defs>
                <linearGradient id="bagGradient" x1="20" y1="35" x2="80" y2="90" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stopColor="#34D399" />
                    <stop offset="100%" stopColor="#10B981" />
                </linearGradient>
            </defs>
        </svg>
    );
};

export default Logo;
