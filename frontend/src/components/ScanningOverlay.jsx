import React from 'react';

const ScanningOverlay = ({ isScanning }) => {
    if (!isScanning) return null;

    return (
        <div className="absolute inset-0 pointer-events-none z-20 overflow-hidden rounded-xl">
            {/* 1. Glassy dark overlay to focus attention */}
            <div className="absolute inset-0 bg-[#0B0C10]/20 backdrop-blur-[1px]"></div>

            {/* 2. Grid Pattern - mimicking Linear's subtle technical grids */}
            {/* We use a mask so the grid fades out at edges */}
            <div
                className="absolute inset-0 opacity-20"
                style={{
                    backgroundImage: `linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px), 
                                      linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px)`,
                    backgroundSize: '40px 40px',
                    maskImage: 'radial-gradient(circle at center, black 40%, transparent 100%)',
                    WebkitMaskImage: 'radial-gradient(circle at center, black 40%, transparent 100%)'
                }}
            ></div>

            {/* 3. The Scan Line (The "Light Beam") */}
            <div className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#5E6AD2] to-transparent shadow-[0_0_20px_2px_rgba(94,106,210,0.6)] animate-linear-scan">
                {/* Trailing fade gradient */}
                <div className="absolute bottom-full left-0 right-0 h-24 bg-gradient-to-t from-[#5E6AD2]/20 to-transparent"></div>
            </div>

            {/* 4. Focus Corners (Refined) */}
            <div className="absolute inset-4 opacity-50">
                <div className="absolute top-0 left-0 w-8 h-[1px] bg-gradient-to-r from-white/50 to-transparent"></div>
                <div className="absolute top-0 left-0 h-8 w-[1px] bg-gradient-to-b from-white/50 to-transparent"></div>

                <div className="absolute top-0 right-0 w-8 h-[1px] bg-gradient-to-l from-white/50 to-transparent"></div>
                <div className="absolute top-0 right-0 h-8 w-[1px] bg-gradient-to-b from-white/50 to-transparent"></div>

                <div className="absolute bottom-0 left-0 w-8 h-[1px] bg-gradient-to-r from-white/50 to-transparent"></div>
                <div className="absolute bottom-0 left-0 h-8 w-[1px] bg-gradient-to-t from-white/50 to-transparent"></div>

                <div className="absolute bottom-0 right-0 w-8 h-[1px] bg-gradient-to-l from-white/50 to-transparent"></div>
                <div className="absolute bottom-0 right-0 h-8 w-[1px] bg-gradient-to-t from-white/50 to-transparent"></div>
            </div>
        </div>
    );
};

export default ScanningOverlay;
