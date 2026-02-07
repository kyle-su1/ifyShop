import { useState } from 'react'

/**
 * ProductCard Component
 * 
 * Shows a product with three possible states:
 * - 'loading': Shimmer effect, non-interactive, shows basic info
 * - 'ready': Fully loaded, clickable, shows all details
 * - 'selected': Currently selected product
 */

// Placeholder product icons based on category
const CATEGORY_ICONS = {
    electronics: '🎧',
    furniture: '🪑',
    clothing: '👕',
    shoes: '👟',
    accessories: '⌚',
    home: '🏠',
    sports: '⚽',
    beauty: '💄',
    food: '🍕',
    default: '📦'
}

const getCategoryIcon = (category) => {
    if (!category) return CATEGORY_ICONS.default
    const lowerCategory = category.toLowerCase()
    for (const [key, icon] of Object.entries(CATEGORY_ICONS)) {
        if (lowerCategory.includes(key)) return icon
    }
    return CATEGORY_ICONS.default
}

export default function ProductCard({
    product,
    status = 'loading', // 'loading' | 'ready' | 'selected'
    index = 0,
    onClick,
    isMainProduct = false
}) {
    const [imageError, setImageError] = useState(false)

    const isLoading = status === 'loading'
    const isReady = status === 'ready' || status === 'selected'
    const isSelected = status === 'selected'

    // Animation delay based on index for staggered appearance
    const animationDelay = `${index * 100}ms`

    return (
        <div
            onClick={isReady && onClick ? onClick : undefined}
            style={{ animationDelay }}
            className={`
                relative overflow-hidden rounded-xl border transition-all duration-300
                animate-fade-slide-in
                ${isMainProduct
                    ? 'p-4 bg-gradient-to-br from-purple-500/10 to-indigo-500/10 border-purple-500/30'
                    : 'p-3 bg-white/5 border-white/10'
                }
                ${isLoading
                    ? 'cursor-default opacity-80'
                    : 'cursor-pointer hover:border-white/30 hover:bg-white/10 hover:scale-[1.02] hover:shadow-lg hover:shadow-purple-500/10'
                }
                ${isSelected
                    ? 'ring-2 ring-cyan-400 border-cyan-400/50 bg-cyan-500/10'
                    : ''
                }
            `}
        >
            {/* Loading shimmer overlay */}
            {isLoading && (
                <div className="absolute inset-0 shimmer-overlay" />
            )}

            <div className="flex items-center gap-3">
                {/* Product Icon/Image */}
                <div className={`
                    relative flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center text-2xl
                    ${isMainProduct ? 'bg-purple-500/20' : 'bg-white/10'}
                    ${isLoading ? 'animate-pulse' : ''}
                `}>
                    {product.imageUrl && !imageError ? (
                        <img
                            src={product.imageUrl}
                            alt={product.name}
                            onError={() => setImageError(true)}
                            className={`w-full h-full object-cover rounded-lg ${isLoading ? 'opacity-50' : ''}`}
                        />
                    ) : (
                        <span className={isLoading ? 'opacity-50' : ''}>
                            {getCategoryIcon(product.category)}
                        </span>
                    )}

                    {/* Loading spinner on icon */}
                    {isLoading && (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-6 h-6 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
                        </div>
                    )}
                </div>

                {/* Product Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <h4 className={`
                            font-medium truncate
                            ${isMainProduct ? 'text-white' : 'text-gray-200'}
                            ${isLoading ? 'text-gray-400' : ''}
                        `}>
                            {product.name}
                        </h4>
                        {isMainProduct && (
                            <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide bg-purple-500/30 text-purple-300 rounded">
                                Main
                            </span>
                        )}
                    </div>

                    {/* Loading state: show shimmer placeholders */}
                    {isLoading ? (
                        <div className="mt-1 space-y-1">
                            <div className="h-3 w-24 bg-white/10 rounded animate-pulse" />
                            <div className="h-3 w-16 bg-white/5 rounded animate-pulse" />
                        </div>
                    ) : (
                        <div className="mt-1">
                            {product.price && (
                                <span className="text-sm font-semibold text-green-400">
                                    ${product.price.toFixed(2)}
                                </span>
                            )}
                            {product.source && (
                                <span className="text-xs text-gray-500 ml-2">
                                    via {product.source}
                                </span>
                            )}
                            {product.matchScore && (
                                <div className="flex items-center gap-1 mt-1">
                                    <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-cyan-400 to-purple-400 rounded-full transition-all duration-500"
                                            style={{ width: `${product.matchScore}%` }}
                                        />
                                    </div>
                                    <span className="text-[10px] text-gray-400">{product.matchScore}%</span>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Status indicator */}
                <div className="flex-shrink-0">
                    {isLoading ? (
                        <div className="flex items-center gap-1.5 text-xs text-gray-500">
                            <div className="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse" />
                            <span>Loading...</span>
                        </div>
                    ) : (
                        <svg
                            className={`w-5 h-5 transition-transform ${isSelected ? 'text-cyan-400' : 'text-gray-600 group-hover:translate-x-0.5'}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                    )}
                </div>
            </div>

            {/* Disabled interaction overlay */}
            {isLoading && (
                <div className="absolute inset-0 cursor-not-allowed" title="Still loading product data..." />
            )}
        </div>
    )
}
