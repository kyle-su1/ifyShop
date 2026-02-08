import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import ImageUploader from '../components/ImageUploader'
import LogoutButton from '../components/LogoutButton'
import { useAuth0 } from '@auth0/auth0-react'
import axios from 'axios';
import { chatAnalyze, chatFollowup } from '../lib/api'
import ChatInterface from '../components/ChatInterface';
import ScanningOverlay from '../components/ScanningOverlay';
import AgentStatusDisplay from '../components/AgentStatusDisplay';
import BoundingBoxOverlay from '../components/BoundingBoxOverlay';
import Logo from '../components/Logo';
import PreferencesModal from '../components/PreferencesModal';

const SafeImage = ({ src, alt, className, fallback }) => {
    const [error, setError] = useState(false);
    useEffect(() => setError(false), [src]);

    if (!src || error) {
        return fallback || (
            <div className="w-full h-full flex flex-col items-center justify-center text-gray-500 bg-white/5 gap-2">
                <svg className="w-8 h-8 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="text-xs">No Preview</span>
            </div>
        );
    }
    return <img src={src} alt={alt} className={className} onError={() => setError(true)} referrerPolicy="no-referrer" />;
};

const ProductModal = ({ product, onClose }) => {
    if (!product) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in" onClick={onClose}>
            <div className="bg-[#121214] border border-white/10 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto relative shadow-2xl" onClick={e => e.stopPropagation()}>
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 rounded-full bg-black/40 hover:bg-white/10 text-gray-400 hover:text-white transition-colors z-10"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
                    <div className="relative aspect-square md:aspect-auto md:h-full bg-black/40">
                        <SafeImage
                            src={product.image || product.thumbnail || product.image_url}
                            alt={product.name}
                            className="w-full h-full object-contain"
                        />
                    </div>

                    <div className="p-8 flex flex-col h-full bg-[#18181b]">
                        <h2 className="text-2xl font-bold text-white mb-2">{product.name}</h2>
                        <div className="flex items-center gap-2 mb-6">
                            <span className="text-xl font-bold text-emerald-400">{product.price_text || "Price N/A"}</span>
                            {product.eco_score !== undefined && (
                                <span className="bg-green-900/40 px-2 py-1 rounded text-xs font-mono text-green-300 border border-green-500/30">
                                    🌱 {Math.round((product.eco_score || 0.5) * 100)}% Eco Score
                                </span>
                            )}
                        </div>

                        {product.eco_notes && (
                            <div className="mb-6 bg-green-900/10 border border-green-500/10 rounded-lg p-3">
                                <h4 className="text-xs font-bold text-green-400 uppercase mb-1 flex items-center gap-1">
                                    <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span> Eco Analysis
                                </h4>
                                <p className="text-xs text-gray-300 leading-relaxed">
                                    {product.eco_notes}
                                </p>
                            </div>
                        )}

                        <div className="prose prose-invert prose-sm mb-8 flex-1 overflow-y-auto">
                            <h3 className="text-gray-400 uppercase text-xs font-bold tracking-wider mb-2">Analysis</h3>
                            <p className="text-gray-300 leading-relaxed">{product.reason || product.description || "No detailed description available."}</p>

                            <div className="mt-4 grid grid-cols-2 gap-3">
                                {/* Price Score */}
                                <div className="bg-white/5 p-3 rounded-lg border border-white/5">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-[10px] text-gray-500 uppercase tracking-wider flex items-center gap-1">💰 Price</span>
                                        <span className="text-xs font-mono text-white">{Math.round(product.score_breakdown?.price || 0)}/100</span>
                                    </div>
                                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full transition-all duration-500" style={{ width: `${product.score_breakdown?.price || 0}%` }} />
                                    </div>
                                </div>
                                {/* Quality Score */}
                                <div className="bg-white/5 p-3 rounded-lg border border-white/5">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-[10px] text-gray-500 uppercase tracking-wider flex items-center gap-1">⭐ Quality</span>
                                        <span className="text-xs font-mono text-white">{Math.round(product.score_breakdown?.quality || 0)}/100</span>
                                    </div>
                                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-amber-400 to-orange-500 rounded-full transition-all duration-500" style={{ width: `${product.score_breakdown?.quality || 0}%` }} />
                                    </div>
                                </div>
                                {/* Trust Score */}
                                <div className="bg-white/5 p-3 rounded-lg border border-white/5">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-[10px] text-gray-500 uppercase tracking-wider flex items-center gap-1">🛡️ Trust</span>
                                        <span className="text-xs font-mono text-white">{Math.round(product.score_breakdown?.trust || 0)}/100</span>
                                    </div>
                                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full transition-all duration-500" style={{ width: `${product.score_breakdown?.trust || 0}%` }} />
                                    </div>
                                </div>
                                {/* Eco Score */}
                                <div className="bg-white/5 p-3 rounded-lg border border-white/5">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-[10px] text-gray-500 uppercase tracking-wider flex items-center gap-1">🌱 Eco</span>
                                        <span className="text-xs font-mono text-white">{Math.round(product.score_breakdown?.eco || 0)}/100</span>
                                    </div>
                                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-emerald-400 to-green-500 rounded-full transition-all duration-500" style={{ width: `${product.score_breakdown?.eco || 0}%` }} />
                                    </div>
                                </div>
                            </div>

                            {/* Overall Match Score */}
                            <div className="mt-4 bg-gradient-to-r from-purple-500/10 to-indigo-500/10 p-3 rounded-lg border border-purple-500/20">
                                <div className="flex items-center justify-between">
                                    <span className="text-xs text-purple-300 uppercase tracking-wider font-medium">Overall Match</span>
                                    <span className="text-lg font-mono font-bold text-white">{Math.round(product.score || 0)}/100</span>
                                </div>
                            </div>
                        </div>

                        <div className="mt-auto pt-6 border-t border-white/10">
                            {product.link ? (
                                <a
                                    href={product.link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn-primary w-full flex items-center justify-center gap-2 py-3"
                                    onClick={(e) => e.stopPropagation()}
                                >
                                    <span>View on Store</span>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                                </a>
                            ) : (
                                <button disabled className="w-full py-3 bg-white/5 text-gray-500 font-semibold rounded-lg cursor-not-allowed">
                                    Link Unavailable
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const AlternativeCard = ({ alt, onSelect }) => {
    return (
        <div
            onClick={() => onSelect(alt)}
            className="bg-white/5 border border-white/5 rounded-xl overflow-hidden hover:border-emerald-500/50 hover:shadow-lg hover:shadow-emerald-900/20 transition-all cursor-pointer group flex flex-col h-full active:scale-[0.98] duration-200"
        >
            {/* Alt Image Header */}
            <div className="h-40 bg-black/40 relative overflow-hidden flex-shrink-0">
                <SafeImage
                    src={alt.image || alt.thumbnail || alt.image_url}
                    alt={alt.name}
                    className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity duration-300"
                />
                <div className="absolute top-2 right-2 flex gap-1">
                    <span className="bg-black/60 backdrop-blur-md px-2 py-1 rounded text-xs font-mono text-white border border-white/10">
                        Score: {Math.round(alt.score || 0)}
                    </span>
                    {alt.eco_score !== undefined && (
                        <span className="bg-green-900/60 backdrop-blur-md px-2 py-1 rounded text-xs font-mono text-green-300 border border-green-500/30 cursor-help" title={alt.eco_notes || "Environmental Friendliness"}>
                            🌱 {Math.round((alt.eco_score || 0.5) * 100)}%
                        </span>
                    )}
                </div>
            </div>

            <div className="p-4 flex flex-col flex-1">
                <h4 className="font-semibold text-white mb-1 line-clamp-1 group-hover:text-emerald-400 transition-colors" title={alt.name}>{alt.name}</h4>
                <p className="text-xs text-gray-400 mb-3 line-clamp-2">{alt.reason}</p>

                <div className="mt-auto pt-3 border-t border-white/5 flex items-center justify-between">
                    <div className="text-sm font-medium text-white">
                        {alt.price_text || "Price N/A"}
                    </div>
                    {alt.link ? (
                        <a
                            href={alt.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs bg-white text-black px-3 py-1.5 rounded-md hover:bg-emerald-400 hover:text-black transition-colors font-medium z-10 relative"
                            onClick={(e) => e.stopPropagation()}
                        >
                            View Item
                        </a>
                    ) : (
                        <span className="text-xs text-gray-600 cursor-not-allowed">No Link</span>
                    )}
                </div>
            </div>
        </div>
    );
};

const DashboardPage = () => {
    const { user, getAccessTokenSilently, isLoading, logout, isAuthenticated } = useAuth0()
    const [imageFile, setImageFile] = useState(null)
    const [imageBase64, setImageBase64] = useState(null)
    const [analysisResult, setAnalysisResult] = useState(null)
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [analyzedImage, setAnalyzedImage] = useState(null);
    const [backendReady, setBackendReady] = useState(false);
    const [isChatAnalyzing, setIsChatAnalyzing] = useState(false);
    const [chatMessages, setChatMessages] = useState([]);
    const [agentStep, setAgentStep] = useState(0);
    const [isImageCollapsed, setIsImageCollapsed] = useState(false);
    // Follow-up conversation state
    const [threadId, setThreadId] = useState(null);
    const [sessionState, setSessionState] = useState(null);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [isRefining, setIsRefining] = useState(false); // Visual loop state
    const [isPreferencesOpen, setIsPreferencesOpen] = useState(false); // Preferences modal

    // Poll backend health
    useEffect(() => {
        const checkHealth = async () => {
            try {
                // Simple health check call
                await axios.get(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/health`);
                setBackendReady(true);
            } catch (e) {
                setBackendReady(false);
            }
        };

        checkHealth();
        const interval = setInterval(checkHealth, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleImageSelected = (file, base64) => {
        setImageFile(file)
        setImageBase64(base64)
        setAnalysisResult(null)
        setAnalyzedImage(base64);
        // Reset conversation state for new image
        setThreadId(null);
        setSessionState(null);
        setChatMessages([]);
        setSelectedProduct(null);
    }

    // Handle chat-based targeted analysis
    const handleChatAnalyze = async (userQuery) => {
        if (!imageBase64 || !userQuery.trim()) return;

        setIsChatAnalyzing(true);
        setIsAnalyzing(true);  // Trigger right-panel loading UI
        setAgentStep(0);       // Start agent progress animation
        setAnalysisResult(null); // Clear old results while loading

        // Add user message to chat history
        const newMessages = [...chatMessages, { role: 'user', content: userQuery }];
        setChatMessages(newMessages);

        // Add thinking placeholder
        setChatMessages([...newMessages, { role: 'assistant', content: null, isThinking: true }]);

        // Animate agent steps (simulated progress)
        let seconds = 0;
        const stepInterval = setInterval(() => {
            seconds++;
            if (seconds === 2) setAgentStep(1);
            if (seconds === 5) setAgentStep(2);
            if (seconds === 9) setAgentStep(3);

            // Loop Trigger (>14s means Veto likely)
            if (seconds === 14) {
                setIsRefining(true);
                setAgentStep(2);
            }
            if (seconds === 20) setAgentStep(3);
        }, 1000);

        try {
            const token = await getAccessTokenSilently();
            let result;

            // Use follow-up endpoint if we have prior analysis state
            if (threadId && sessionState) {
                console.log('[DashboardPage] Using chat-followup endpoint');
                result = await chatFollowup(userQuery, threadId, sessionState, chatMessages, token);

                // If follow-up returned updated analysis, merge it
                if (result.analysis) {
                    setAnalysisResult(prev => ({
                        ...prev,
                        ...result.analysis
                    }));
                    // Update session state with new analysis data
                    setSessionState(prev => ({
                        ...prev,
                        analysis_object: result.analysis
                    }));
                }
            } else {
                // First analysis - use full pipeline
                console.log('[DashboardPage] Using chat-analyze endpoint (initial)');
                result = await chatAnalyze(imageBase64, userQuery, chatMessages, token);

                // Store thread_id and session_state for follow-ups
                if (result.thread_id) {
                    setThreadId(result.thread_id);
                }
                if (result.session_state) {
                    setSessionState(result.session_state);
                }

                // Update bounding boxes if targeted object found
                if (result.targeted_bounding_box) {
                    setAnalysisResult(prev => ({
                        ...prev,
                        active_product: {
                            ...(prev?.active_product || {}),
                            detected_objects: [{
                                name: result.targeted_object_name || 'Target',
                                bounding_box: result.targeted_bounding_box,
                                confidence: result.confidence || 0.9,
                                lens_status: 'identified'
                            }]
                        }
                    }));
                }

                // If full analysis available, update results
                if (result.analysis) {
                    setAnalysisResult(prev => ({
                        ...prev,
                        ...result.analysis
                    }));
                }
            }

            clearInterval(stepInterval);
            setIsRefining(false);
            setAgentStep(5); // Complete

            // Replace thinking with AI response
            setChatMessages([...newMessages, {
                role: 'assistant',
                content: result.chat_response || 'Analysis complete.',
                boundingBox: result.targeted_bounding_box
            }]);

        } catch (error) {
            clearInterval(stepInterval);
            console.error("Chat analyze failed:", error);
            setChatMessages([...newMessages, {
                role: 'assistant',
                content: 'Sorry, I encountered an error analyzing your request. Please try again.'
            }]);
        } finally {
            setIsChatAnalyzing(false);
            setIsAnalyzing(false);
        }
    };

    if (isLoading) return (
        <div className="min-h-screen flex items-center justify-center bg-[#08090A] text-white">
            <div className="flex items-center gap-3">
                <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                <span className="text-gray-400">Loading...</span>
            </div>
        </div>
    );

    return (
        <div className="h-screen bg-[#08090A] text-white font-sans selection:bg-emerald-500/30 relative overflow-hidden">
            {/* Gradient for dashboard - green theme */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-[0%] right-[0%] w-[40%] h-[40%] rounded-full bg-emerald-900/15 blur-[100px]" />
                <div className="absolute bottom-[0%] left-[0%] w-[40%] h-[40%] rounded-full bg-violet-900/10 blur-[100px]" />
            </div>
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.03] pointer-events-none"></div>

            <div className="relative w-full max-w-[98vw] mx-auto px-6 py-6 flex flex-col h-full">
                {/* Header */}
                <header className="flex items-center justify-between mb-4 animate-fade-in-up flex-shrink-0">
                    <Link to="/" className="flex items-center gap-3 group cursor-pointer" title="Return to landing page">
                        <Logo className="w-8 h-8 transition-all duration-300 group-hover:scale-110 group-hover:rotate-[360deg]" />
                        <div className="flex flex-col">
                            <span className="font-bold text-lg tracking-tight text-white group-hover:text-emerald-400 transition-colors">ifyShop</span>
                            <span className="text-[10px] text-gray-500 font-medium tracking-wide opacity-0 group-hover:opacity-100 transition-opacity">← Back to home</span>
                        </div>
                    </Link>
                    <div className="flex items-center gap-4 glass-panel px-5 py-2.5">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-xs font-medium text-gray-300">Welcome, <span className="text-white">{user?.name}</span></span>
                        </div>
                        <LogoutButton />
                    </div>
                </header>

                {/* Main Interaction Area - 3 Column Layout */}
                <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch flex-1 min-h-0">

                    {/* Left Panel: Upload - Collapsible */}
                    <div className={`${isImageCollapsed ? 'lg:col-span-1' : 'lg:col-span-4'} glass-panel rounded-2xl p-1 transition-all duration-500 hover:border-emerald-500/20 animate-fade-in-up overflow-hidden`} style={{ animationDelay: '100ms' }}>
                        <div className="bg-[#121214] rounded-xl p-4 h-full flex flex-col">
                            <h3 className="text-sm font-semibold text-blue-400/80 uppercase tracking-wider mb-3 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                                    {!isImageCollapsed && 'Product Image'}
                                </div>
                                {imageBase64 && (
                                    <button
                                        onClick={() => setIsImageCollapsed(!isImageCollapsed)}
                                        className="p-1 hover:bg-white/10 rounded transition-colors"
                                        title={isImageCollapsed ? 'Expand image' : 'Collapse image'}
                                    >
                                        <svg className={`w-4 h-4 transition-transform ${isImageCollapsed ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                                        </svg>
                                    </button>
                                )}
                            </h3>

                            {isImageCollapsed ? (
                                <div className="flex-1 flex items-center justify-center">
                                    <div className="relative w-16 h-16 rounded-lg overflow-hidden border border-white/10">
                                        <img src={imageBase64} alt="Thumbnail" className="w-full h-full object-cover" />
                                    </div>
                                </div>
                            ) : (
                                <div className="flex-1 flex flex-col relative">
                                    {!imageBase64 ? (
                                        <ImageUploader
                                            onImageSelected={handleImageSelected}
                                            overlays={analysisResult?.objects}
                                        />
                                    ) : (
                                        <div className="relative rounded-xl overflow-hidden border border-white/10 group flex-1 bg-black/40 flex items-center justify-center">
                                            {/* Image wrapper for proper bounding box positioning */}
                                            <div className="relative inline-block max-w-full max-h-[60vh]">
                                                <img
                                                    src={imageBase64}
                                                    alt="Analyzed Item"
                                                    className="block max-w-full max-h-[60vh] h-auto w-auto"
                                                />

                                                {/* CHATBOT BOUNDING BOX - positioned relative to the image */}
                                                {analysisResult?.active_product?.detected_objects?.map((obj, idx) => (
                                                    <BoundingBoxOverlay
                                                        key={idx}
                                                        boundingBox={obj?.bounding_box}
                                                        label={obj?.name || 'Target'}
                                                    />
                                                ))}
                                            </div>

                                            {/* SCANNING OVERLAY */}
                                            <ScanningOverlay isScanning={isAnalyzing} />

                                            {/* Change Image Button */}
                                            <button
                                                onClick={() => { setImageBase64(null); setImageFile(null); setAnalysisResult(null); }}
                                                disabled={isAnalyzing}
                                                className={`absolute top-2 right-2 p-2 rounded-full backdrop-blur-sm transition-colors z-20 ${isAnalyzing
                                                    ? 'bg-black/40 text-gray-500 cursor-not-allowed'
                                                    : 'bg-black/60 hover:bg-black/80 text-white'
                                                    }`}
                                                title="Remove Image"
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Middle Panel: Chat */}
                    <div className={`${isImageCollapsed ? 'lg:col-span-4' : 'lg:col-span-3'} glass-panel rounded-2xl p-1 transition-all duration-500 hover:border-emerald-500/20 animate-fade-in-up overflow-hidden`} style={{ animationDelay: '200ms' }}>
                        <div className="bg-[#121214] rounded-xl p-4 h-full flex flex-col min-h-0">
                            <h3 className="text-sm font-semibold text-emerald-400/80 uppercase tracking-wider mb-3 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                    </svg>
                                    AI Assistant
                                </div>
                                <button
                                    onClick={() => setIsPreferencesOpen(true)}
                                    className="p-1.5 rounded-md hover:bg-white/10 text-gray-400 hover:text-emerald-400 transition-colors"
                                    title="Preferences"
                                >
                                    <svg className="w-4 h-4 rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                                    </svg>
                                </button>
                            </h3>
                            <div className="flex-1 min-h-0">
                                <ChatInterface
                                    imageBase64={imageBase64}
                                    onAnalysisStart={handleChatAnalyze}
                                    isAnalyzing={isChatAnalyzing}
                                    disabled={!backendReady || !imageBase64}
                                    messages={chatMessages}
                                    setMessages={setChatMessages}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Right Panel: Results */}
                    <div className={`${isImageCollapsed ? 'lg:col-span-7' : 'lg:col-span-5'} glass-panel rounded-2xl p-1 overflow-hidden transition-all duration-500 hover:border-violet-500/20 animate-fade-in-up`} style={{ animationDelay: '300ms' }}>
                        <div className="bg-[#121214] rounded-xl p-6 h-full flex flex-col overflow-y-auto">
                            <h3 className="text-sm font-semibold text-violet-400/80 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                Analysis Results
                            </h3>

                            {/* VISUAL RESULTS */}
                            {/* VISUAL RESULTS REMOVED (Moved to Left Panel) */}

                            {/* --- DEEP SEARCH NOTIFICATION --- */}
                            {analysisResult && analysisResult.was_refined && (
                                <div className="mb-6 bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4 flex items-center gap-4 animate-fade-in relative overflow-hidden group">
                                    {/* Background glow */}
                                    <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                                    <div className="bg-indigo-500/20 p-2 rounded-lg text-indigo-400 shrink-0 flex items-center justify-center">
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                        </svg>
                                    </div>
                                    <div>
                                        <h4 className="text-sm font-bold text-indigo-300 uppercase tracking-wide flex items-center gap-2">
                                            Deep Search Activated
                                            <span className="text-[10px] bg-indigo-500/20 px-1.5 py-0.5 rounded text-indigo-300 border border-indigo-500/20">Auto-Refined</span>
                                        </h4>
                                        <p className="text-sm text-gray-400 mt-1 leading-relaxed">
                                            {analysisResult.refinement_context || analysisResult.refinement_reason || "Initial results didn't meet our quality standards, so we performed an extra search cycle to find better options."}
                                        </p>
                                    </div>
                                </div>
                            )}

                            {analysisResult ? (
                                <div className="animate-fade-in space-y-8">
                                    {/* --- MAIN PRODUCT CARD --- */}
                                    <div className="bg-white/5 rounded-2xl border border-white/10 overflow-hidden">
                                        <div className="p-6">
                                            {/* 1. Header Row - Full Width */}
                                            <div className="flex items-start justify-between gap-4 mb-6">
                                                <h2 className="text-2xl font-bold text-white leading-tight">
                                                    {analysisResult.identified_product || "Unknown Product"}
                                                </h2>
                                                <div className="flex flex-col items-end gap-1 shrink-0">
                                                    <div className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide border whitespace-nowrap ${analysisResult.outcome === 'highly_recommended'
                                                        ? 'bg-green-500/10 border-green-500/20 text-green-400'
                                                        : analysisResult.outcome === 'recommended'
                                                            ? 'bg-blue-500/10 border-blue-500/20 text-blue-400'
                                                            : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                                                        }`}>
                                                        {analysisResult.outcome === 'highly_recommended'
                                                            ? 'HIGHLY RECOMMENDED'
                                                            : analysisResult.outcome === 'recommended'
                                                                ? 'RECOMMENDED'
                                                                : 'CONSIDER ALTERNATIVES'}
                                                    </div>
                                                    <span className="text-xs text-gray-500">Confidence: {analysisResult.confidence ? Math.round(analysisResult.confidence * 100) : 88}%</span>
                                                </div>
                                            </div>

                                            <div className="flex flex-col md:flex-row gap-8">

                                                {/* LEFT COLUMN - Visual Anchor (Image) + Key Stats */}
                                                <div className="w-full md:w-1/3 flex flex-col gap-6">
                                                    {/* Image */}
                                                    <div className="aspect-[4/5] rounded-xl bg-black/40 border border-white/10 overflow-hidden relative group w-full">
                                                        <SafeImage
                                                            src={analysisResult.active_product?.image_url || analyzedImage}
                                                            alt="Main Product"
                                                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                                        />

                                                        {analysisResult.active_product?.purchase_link && (
                                                            <a
                                                                href={analysisResult.active_product.purchase_link}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="absolute bottom-3 right-3 p-2 bg-white text-black rounded-full shadow-lg hover:scale-110 transition-transform opacity-0 group-hover:opacity-100"
                                                                title="View Store Page"
                                                            >
                                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                                                            </a>
                                                        )}
                                                    </div>

                                                    {/* Key Stats - Vertical Stack */}
                                                    <div className="flex flex-col gap-3">
                                                        <div className="bg-black/20 rounded-lg p-3">
                                                            <span className="text-[10px] uppercase text-gray-500 tracking-wider w-full block text-left">Best Price</span>
                                                            <div className="flex items-baseline gap-1 mt-1">
                                                                <span className="text-xl font-bold text-white truncate block w-full text-left">
                                                                    {analysisResult.active_product?.price_text || "Check Price"}
                                                                </span>
                                                            </div>
                                                        </div>
                                                        <div className="bg-black/20 rounded-lg p-3">
                                                            <span className="text-[10px] uppercase text-gray-500 tracking-wider w-full block text-left">Verdict</span>
                                                            <div className="mt-1">
                                                                <span className="text-sm font-medium text-white block truncate text-left">{analysisResult.price_analysis?.verdict || "N/A"}</span>
                                                            </div>
                                                        </div>
                                                        <div className="bg-green-900/20 rounded-lg p-3 border border-green-500/10 group relative">
                                                            <span className="text-[10px] uppercase text-green-400 tracking-wider flex items-center gap-1 w-full text-left">🌱 Eco Score</span>
                                                            <div className="mt-1">
                                                                <span className="text-xl font-bold text-green-300 block text-left">
                                                                    {analysisResult.active_product?.eco_score !== undefined
                                                                        ? `${Math.round(analysisResult.active_product.eco_score * 100)}%`
                                                                        : "N/A"}
                                                                </span>
                                                            </div>
                                                            {/* Tooltip for Eco Notes */}
                                                            {analysisResult.active_product?.eco_notes && (
                                                                <div className="absolute bottom-full left-0 mb-2 w-64 p-2 bg-black/90 border border-green-500/30 rounded text-xs text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
                                                                    {analysisResult.active_product.eco_notes}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* RIGHT COLUMN - Information Stack */}
                                                <div className="flex-1 flex flex-col min-w-0">

                                                    {/* Summary Section */}
                                                    <p className="text-gray-400 text-sm leading-relaxed mb-8 border-l-2 border-white/10 pl-4 py-1">
                                                        {analysisResult.summary || "No summary available."}
                                                    </p>

                                                    {/* Eco Analysis Section */}
                                                    {analysisResult.active_product?.eco_notes && (
                                                        <div className="mb-8 bg-green-900/10 border border-green-500/10 rounded-lg p-4">
                                                            <h4 className="text-xs font-bold text-green-400 uppercase mb-2">Eco Analysis</h4>
                                                            <p className="text-xs text-gray-400 leading-relaxed">
                                                                {analysisResult.active_product.eco_notes}
                                                            </p>
                                                        </div>
                                                    )}

                                                    {/* Buy Now Button (Bottom aligned) */}
                                                    <div className="mt-auto pt-2">
                                                        {analysisResult.active_product?.purchase_link ? (
                                                            <a
                                                                href={analysisResult.active_product.purchase_link}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="flex items-center justify-center w-full py-3 bg-white text-black font-semibold text-sm rounded-lg hover:bg-gray-200 transition-colors gap-2"
                                                            >
                                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"></path></svg>
                                                                Buy Now
                                                            </a>
                                                        ) : (
                                                            <button disabled className="block w-full py-3 bg-white/10 text-gray-500 font-semibold text-sm rounded-lg cursor-not-allowed">
                                                                Link Unavailable
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* --- ALTERNATIVES SECTION --- */}
                                    {analysisResult.alternatives && analysisResult.alternatives.length > 0 && (
                                        <div>
                                            <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                                                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>
                                                Top Alternatives
                                            </h3>

                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
                                                {analysisResult.alternatives.map((alt, idx) => (
                                                    <AlternativeCard
                                                        key={idx}
                                                        alt={alt}
                                                        onSelect={setSelectedProduct}
                                                    />
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* JSON Data Toggle */}
                                    <div className="pt-4 border-t border-white/5">
                                        <details className="group">
                                            <summary className="cursor-pointer text-xs text-gray-600 hover:text-gray-400 transition-colors list-none flex items-center gap-2">
                                                <span className="group-open:rotate-90 transition-transform">▸</span>
                                                View Raw Analysis Data
                                            </summary>
                                            <pre className="mt-3 text-[10px] text-gray-500 bg-black/50 p-4 rounded-lg overflow-x-auto font-mono">
                                                {JSON.stringify(analysisResult, null, 2)}
                                            </pre>
                                        </details>
                                    </div>
                                </div>
                            ) : isChatAnalyzing ? (
                                <AgentStatusDisplay activeStep={agentStep} isRefining={isRefining} />
                            ) : (
                                <div className="flex-1 flex flex-col items-center justify-center text-center space-y-4 py-12">
                                    <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-2 group-hover:bg-white/10 transition-colors">
                                        <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                                    </div>
                                    <div className="max-w-xs mx-auto">
                                        <p className="text-gray-400 text-sm">Results will appear here after analysis.</p>
                                        <p className="text-gray-600 text-xs mt-2">The agent will break down the image into actionable data points.</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
            {selectedProduct && (
                <ProductModal
                    product={selectedProduct}
                    onClose={() => setSelectedProduct(null)}
                />
            )}
            <PreferencesModal
                isOpen={isPreferencesOpen}
                onClose={() => setIsPreferencesOpen(false)}
            />
        </div>
    )
}

export default DashboardPage
