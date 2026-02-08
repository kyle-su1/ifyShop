
import { useState, useEffect } from 'react'
import ImageUploader from '../components/ImageUploader'
import LogoutButton from '../components/LogoutButton'
import { useAuth0 } from '@auth0/auth0-react'
import axios from 'axios';
import { chatAnalyze } from '../lib/api'
import ChatInterface from '../components/ChatInterface';
import ScanningOverlay from '../components/ScanningOverlay';
import AgentStatusDisplay from '../components/AgentStatusDisplay';
import BoundingBoxOverlay from '../components/BoundingBoxOverlay';

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
        setAnalyzedImage(base64); // Set the image for display
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
        const stepInterval = setInterval(() => {
            setAgentStep(prev => (prev < 4 ? prev + 1 : prev));
        }, 2500); // ~10s total for 4 steps

        try {
            const token = await getAccessTokenSilently();
            const result = await chatAnalyze(imageBase64, userQuery, chatMessages, token);

            clearInterval(stepInterval);
            setAgentStep(5); // Complete

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

            // Replace thinking with AI response
            setChatMessages([...newMessages, {
                role: 'assistant',
                content: result.chat_response || 'I found the item. Click the highlighted area for details.',
                boundingBox: result.targeted_bounding_box
            }]);

            // If full analysis available, update results
            if (result.analysis) {
                setAnalysisResult(prev => ({
                    ...prev,
                    ...result.analysis
                }));
            }

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

    if (isLoading) return <div className="text-white">Loading...</div>;

    return (
        <div className="min-h-screen bg-[#0B0C10] text-white font-sans selection:bg-purple-500/30 relative overflow-hidden">
            {/* Gradient for dashboard - simplified */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-[0%] right-[0%] w-[40%] h-[40%] rounded-full bg-purple-900/10 blur-[100px]" />
                <div className="absolute bottom-[0%] left-[0%] w-[40%] h-[40%] rounded-full bg-blue-900/10 blur-[100px]" />
            </div>
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none mix-blend-overlay"></div>


            <div className="relative w-full max-w-[95vw] mx-auto px-4 py-8 flex flex-col min-h-screen">
                {/* Header */}
                <header className="flex items-center justify-between mb-12">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded bg-gradient-to-tr from-indigo-500 to-purple-500" />
                        <span className="font-semibold text-sm tracking-wide text-white">CxC 2026 Dashboard</span>
                    </div>
                    <div className="flex items-center gap-4 bg-white/5 pr-2 pl-4 py-1.5 rounded-full border border-white/5 hover:border-white/10 transition-colors">
                        <span className="text-xs font-medium text-gray-400">Welcome, {user?.name}</span>
                        <LogoutButton />
                    </div>
                </header>

                {/* Main Interaction Area - 3 Column Layout */}
                <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch flex-1">

                    {/* Left Panel: Upload - Collapsible */}
                    <div className={`${isImageCollapsed ? 'lg:col-span-1' : 'lg:col-span-4'} glass-panel rounded-2xl p-1 transition-all duration-300 hover:border-white/20`}>
                        <div className="bg-[#121214] rounded-xl p-4 h-full flex flex-col">
                            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                                    {!isImageCollapsed && 'Input'}
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
                                            <div className="relative inline-block max-w-full max-h-[400px]">
                                                <img
                                                    src={imageBase64}
                                                    alt="Analyzed Item"
                                                    className="block max-w-full max-h-[400px] h-auto w-auto"
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
                                            {!isAnalyzing && (
                                                <button
                                                    onClick={() => { setImageBase64(null); setImageFile(null); setAnalysisResult(null); }}
                                                    className="absolute top-2 right-2 p-2 bg-black/60 hover:bg-black/80 text-white rounded-full backdrop-blur-sm transition-colors z-20"
                                                    title="Remove Image"
                                                >
                                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                                                </button>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Middle Panel: Chat */}
                    <div className={`${isImageCollapsed ? 'lg:col-span-4' : 'lg:col-span-3'} glass-panel rounded-2xl p-1 transition-all duration-300 hover:border-white/20`}>
                        <div className="bg-[#121214] rounded-xl p-4 h-full flex flex-col">
                            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                </svg>
                                Chat
                            </h3>
                            <div className="flex-1">
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
                    <div className={`${isImageCollapsed ? 'lg:col-span-7' : 'lg:col-span-5'} glass-panel rounded-2xl p-1 overflow-hidden`}>
                        <div className="bg-[#121214] rounded-xl p-6 h-full flex flex-col overflow-y-auto">
                            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                Agent Output
                            </h3>

                            {/* VISUAL RESULTS */}
                            {/* VISUAL RESULTS REMOVED (Moved to Left Panel) */}

                            {analysisResult ? (
                                <div className="animate-fade-in space-y-8">
                                    {/* --- MAIN PRODUCT CARD --- */}
                                    <div className="bg-white/5 rounded-2xl border border-white/10 overflow-hidden">
                                        <div className="p-6">
                                            <div className="flex items-center justify-between mb-4">
                                                <div className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide border ${analysisResult.outcome === 'highly_recommended'
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
                                                <span className="text-xs text-gray-400">Confidence: {analysisResult.confidence ? Math.round(analysisResult.confidence * 100) : 88}%</span>
                                            </div>

                                            <div className="flex flex-col gap-6">
                                                {/* Product Info Helper */}
                                                <div className="flex flex-col md:flex-row gap-6">
                                                    {/* Main Image */}
                                                    <div className="w-full md:w-1/3 aspect-square rounded-xl bg-black/40 border border-white/10 overflow-hidden relative group">
                                                        {analysisResult.active_product?.image_url || analyzedImage ? (
                                                            <img
                                                                src={analysisResult.active_product?.image_url || analyzedImage}
                                                                alt="Main Product"
                                                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                                            />
                                                        ) : (
                                                            <div className="w-full h-full flex items-center justify-center text-gray-500 text-xs">No Image</div>
                                                        )}

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

                                                    {/* Details Column */}
                                                    <div className="flex-1">
                                                        <h2 className="text-2xl font-bold text-white mb-2 leading-tight">
                                                            {analysisResult.identified_product || "Unknown Product"}
                                                        </h2>
                                                        <p className="text-gray-400 text-sm leading-relaxed mb-6 border-l-2 border-white/10 pl-4 py-1">
                                                            {analysisResult.summary || "No summary available."}
                                                        </p>

                                                        <div className="grid grid-cols-2 gap-4 mb-6">
                                                            <div className="bg-black/20 rounded-lg p-3">
                                                                <span className="text-[10px] uppercase text-gray-500 tracking-wider">Best Price</span>
                                                                <div className="flex items-baseline gap-1 mt-1">
                                                                    <span className="text-xl font-bold text-white">
                                                                        {analysisResult.active_product?.price_text || "Check Price"}
                                                                    </span>
                                                                </div>
                                                            </div>
                                                            <div className="bg-black/20 rounded-lg p-3">
                                                                <span className="text-[10px] uppercase text-gray-500 tracking-wider">Verdict</span>
                                                                <div className="mt-1">
                                                                    <span className="text-sm font-medium text-white block truncate">{analysisResult.price_analysis?.verdict || "N/A"}</span>
                                                                </div>
                                                            </div>
                                                        </div>

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
                                                <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>
                                                Top Alternatives
                                            </h3>

                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
                                                {analysisResult.alternatives.map((alt, idx) => (
                                                    <div key={idx} className="bg-white/5 border border-white/5 rounded-xl overflow-hidden hover:border-white/20 transition-all group flex flex-col h-full">
                                                        {/* Alt Image Header */}
                                                        <div className="h-40 bg-black/40 relative overflow-hidden flex-shrink-0">
                                                            {alt.image ? (
                                                                <img src={alt.image} alt={alt.name} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                                                            ) : (
                                                                <div className="w-full h-full flex items-center justify-center text-gray-700 bg-white/5">No Image</div>
                                                            )}
                                                            <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-md px-2 py-1 rounded text-xs font-mono text-white border border-white/10">
                                                                Score: {Math.round(alt.score || 0)}
                                                            </div>
                                                        </div>

                                                        <div className="p-4 flex flex-col flex-1">
                                                            <h4 className="font-semibold text-white mb-1 line-clamp-1" title={alt.name}>{alt.name}</h4>
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
                                                                        className="text-xs bg-white text-black px-3 py-1.5 rounded-md hover:bg-gray-200 transition-colors font-medium"
                                                                    >
                                                                        View Item
                                                                    </a>
                                                                ) : (
                                                                    <span className="text-xs text-gray-600 cursor-not-allowed">No Link</span>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
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
                                <AgentStatusDisplay activeStep={agentStep} />
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
        </div>
    )
}

export default DashboardPage
