import React, { useState } from 'react';

const BoundingBoxOverlay = ({ boundingBox, label, onHover, onClick, isSelected }) => {
    const [isHovered, setIsHovered] = useState(false);

    if (!boundingBox || boundingBox.length !== 4) return null;

    // Gemini returns [ymin, xmin, ymax, xmax] normalized to 0-1000
    const [ymin, xmin, ymax, xmax] = boundingBox;

    const top = (ymin / 1000) * 100;
    const left = (xmin / 1000) * 100;
    const height = ((ymax - ymin) / 1000) * 100;
    const width = ((xmax - xmin) / 1000) * 100;

    // Combine prop hover with local hover for style/behavior
    const active = isSelected || isHovered;

    const style = {
        position: 'absolute',
        top: `${top}%`,
        left: `${left}%`,
        width: `${width}%`,
        height: `${height}%`,
        // Subtle border by default, brighter when active
        border: active ? '2px solid #34d399' : '1px solid rgba(16, 185, 129, 0.4)',
        // Subtle background by default, more visible when active
        backgroundColor: active ? 'rgba(52, 211, 153, 0.15)' : 'rgba(16, 185, 129, 0.05)',
        cursor: 'pointer',
        zIndex: active ? 20 : 10,
        transition: 'all 0.2s ease-in-out',
        boxShadow: active ? '0 0 15px rgba(16,185,129,0.3)' : 'none',
    };

    return (
        <div
            className="bounding-box group"
            style={style}
            onMouseEnter={() => {
                setIsHovered(true);
                onHover && onHover(true);
            }}
            onMouseLeave={() => {
                setIsHovered(false);
                onHover && onHover(false);
            }}
            onClick={onClick}
        >
            {/* Label - Only visible on hover/select */}
            <div style={{
                position: 'absolute',
                top: '-24px', // Slightly closer
                left: '0',
                backgroundColor: active ? '#34d399' : 'rgba(16, 185, 129, 0.8)',
                color: 'black',
                padding: '2px 6px',
                fontSize: '11px',
                fontWeight: 'bold',
                borderRadius: '4px',
                whiteSpace: 'nowrap',
                maxWidth: '150px', // Limit width
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                opacity: active ? 1 : 0, // Hide by default
                transform: active ? 'translateY(0)' : 'translateY(5px)',
                transition: 'all 0.2s ease-in-out',
                pointerEvents: 'none' // Prevent label interfering with mouse events
            }}>
                {label || 'Detected Item'}
            </div>
        </div>
    );
};

export default BoundingBoxOverlay;
