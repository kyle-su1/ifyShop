
import { useState, useEffect } from 'react'
import ImageUploader from '../components/ImageUploader'
import LogoutButton from '../components/LogoutButton'
import { useAuth0 } from '@auth0/auth0-react'
import { analyzeImage } from '../lib/api'
import BoundingBoxOverlay from '../components/BoundingBoxOverlay';
import ScanningOverlay from '../components/ScanningOverlay';
import AgentStatusDisplay from '../components/AgentStatusDisplay';

const DashboardPage = () => {
    const { user, getAccessTokenSilently, isLoading, logout, isAuthenticated } = useAuth0()
    const [imageFile, setImageFile] = useState(null)
    const [imageBase64, setImageBase64] = useState(null)
    const [analysisResult, setAnalysisResult] = useState(null)
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [activeProductHover, setActiveProductHover] = useState(false);
    const [analyzedImage, setAnalyzedImage] = useState(null);
    const [loading, setLoading] = useState(false);
    const [showAlternatives, setShowAlternatives] = useState(false);
    const [selectedObject, setSelectedObject] = useState(null);
    const [agentStep, setAgentStep] = useState(0);

    // Initialize selectedObject when analysis results load
    useEffect(() => {
        if (analysisResult?.active_product?.detected_objects?.length > 0) {
            setSelectedObject(analysisResult.active_product.detected_objects[0]);
        } else if (analysisResult?.active_product) {
            // Fallback to active_product itself
            setSelectedObject(analysisResult.active_product);
        }
    }, [analysisResult]);


    const handleImageSelected = (file, base64) => {
        setImageFile(file)
        setImageBase64(base64)
        setAnalysisResult(null)
        setAnalyzedImage(base64); // Set the image for display
    }

    const handleAnalyze = async () => {
        if (!imageFile) return;
        setIsAnalyzing(true);
        setAgentStep(0);
        setAnalysisResult(null);

        // Simulate agent steps progress
        // Ideally this would be driven by WebSocket events
        const stepInterval = setInterval(() => {
            setAgentStep(prev => (prev < 4 ? prev + 1 : prev));
        }, 1200);

        try {
            const token = await getAccessTokenSilently();
            const result = await analyzeImage(imageFile, token);

            clearInterval(stepInterval);
            setAgentStep(5); // Mark as complete

            // Small delay to show completion state before revealing results
            setTimeout(() => {
                setAnalysisResult(result);
                setIsAnalyzing(false);
            }, 600);

        } catch (error) {
            clearInterval(stepInterval);
            console.error("Analysis failed:", error);
            const errorMessage = error.response?.data?.detail || error.message || "Unknown error";
            alert(`Failed to analyze image: ${errorMessage} `);
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


            <div className="relative w-full max-w-7xl mx-auto px-6 py-8 flex flex-col min-h-screen">
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

                {/* Main Interaction Area */}
                <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-6 items-start flex-1">

                    {/* Left Panel: Upload */}
                    <div className="lg:col-span-5 glass-panel rounded-2xl p-1 transition-all duration-300 hover:border-white/20 h-full max-h-[700px]">
                        <div className="bg-[#121214] rounded-xl p-6 h-full flex flex-col">
                            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                                Input Source
                            </h3>

                            <div className="flex-1 flex flex-col">
                                <ImageUploader
                                    onImageSelected={handleImageSelected}
                                    overlays={analysisResult?.objects}
                                />

                                {imageFile && (
                                    <button
                                        onClick={handleAnalyze}
                                        disabled={isAnalyzing}
                                        className="mt-6 w-full py-3 px-4 btn-primary rounded-lg font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
                                    >
                                        {isAnalyzing ? (
                                            <>
                                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                Processing...
                                            </>
                                        ) : (
                                            <>
                                                Start Agent Workflow
                                                <svg className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                                            </>
                                        )}
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Right Panel: Results */}
                    <div className="lg:col-span-7 glass-panel rounded-2xl p-1 h-full max-h-[700px] overflow-hidden">
                        <div className="bg-[#121214] rounded-xl p-6 h-full flex flex-col overflow-y-auto">
                            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                Agent Output
                            </h3>

                            {/* VISUAL RESULTS */}
                            {analyzedImage && (
                                <div className="mb-6 relative rounded-xl overflow-hidden border border-white/10 group flex-shrink-0">
                                    <img
                                        src={analyzedImage}
                                        alt="Analyzed Item"
                                        className="w-full h-auto object-cover max-h-[400px]"
                                    />

                                    {/* SCANNING OVERLAY */}
                                    <ScanningOverlay isScanning={isAnalyzing} />

                                    {/* MULTI-OBJECT BOUNDING BOX OVERLAY */}
                                    {analysisResult?.active_product && (
                                        <>
                                            {/* 1. If we have a list of detected objects, render all of them */}
                                            {analysisResult.active_product.detected_objects && analysisResult.active_product.detected_objects.length > 0 ? (
                                                analysisResult.active_product.detected_objects.map((obj, idx) => (
                                                    <BoundingBoxOverlay
                                                        key={idx}
                                                        boundingBox={obj.bounding_box}
                                                        label={`${obj.name} (${Math.round((obj.confidence || 0) * 100)}%)`}
                                                        isSelected={selectedObject?.name === obj.name}
                                                        onClick={() => setSelectedObject(obj)}
                                                        onHover={(isHovering) => {
                                                            if (isHovering) setActiveProductHover(true);
                                                            else setActiveProductHover(false);
                                                        }}
                                                    />
                                                ))
                                            ) : (
                                                /* 2. Fallback to single box */
                                                analysisResult.active_product.bounding_box && (
                                                    <BoundingBoxOverlay
                                                        boundingBox={analysisResult.active_product.bounding_box}
                                                        label={analysisResult.active_product.name}
                                                        onHover={setActiveProductHover}
                                                    />
                                                )
                                            )}
                                        </>
                                    )}
                                </div>
                            )}

                            {analysisResult ? (
                                <div className="animate-fade-in space-y-6">
                                    {/* Status Banner */}
                                    <div className={`flex items-center gap-3 p-3 rounded-lg border ${analysisResult.outcome === 'highly_recommended' ? 'bg-green-500/10 border-green-500/20' : 'bg-blue-500/10 border-blue-500/20'} `}>
                                        <div className={`w-2 h-2 rounded-full shadow-[0_0_10px_currentColor] ${analysisResult.outcome === 'highly_recommended' ? 'bg-green-500 text-green-500' : 'bg-blue-500 text-blue-500'} `}></div>
                                        <span className={`text-sm font-medium ${analysisResult.outcome === 'highly_recommended' ? 'text-green-400' : 'text-blue-400'} `}>
                                            {analysisResult.outcome === 'highly_recommended' ? 'Highly Recommended' : 'Consider Alternatives'}
                                        </span>
                                    </div>

                                    {/* Main Product Identity */}
                                    <div>
                                        <h4 className="text-lg font-semibold text-white mb-1">
                                            {selectedObject?.name || analysisResult.identified_product || "Unknown Product"}
                                            {selectedObject?.confidence && (
                                                <span className="ml-2 text-sm font-normal text-cyan-400">({Math.round(selectedObject.confidence * 100)}% confidence)</span>
                                            )}
                                        </h4>
                                        <p className="text-gray-400 text-sm leading-relaxed">{analysisResult.summary}</p>
                                    </div>

                                    {/* Key Metrics Grid */}
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                                            <span className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Community Trust</span>
                                            <div className="flex items-end gap-2">
                                                <span className="text-2xl font-bold text-white">{(analysisResult.community_sentiment?.trust_score || 0).toFixed(1)}</span>
                                                <span className="text-xs text-gray-500 mb-1">/ 10</span>
                                            </div>
                                        </div>
                                        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                                            <span className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Price Score</span>
                                            <div className="flex items-end gap-2">
                                                <span className="text-2xl font-bold text-white">{(analysisResult.price_analysis?.price_score || 0).toFixed(1)}</span>
                                                <span className="text-xs text-gray-500 mb-1">/ 1.0</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Action Buttons */}
                                    <div className="flex gap-3 pt-2">
                                        <button
                                            onClick={() => setShowAlternatives(!showAlternatives)}
                                            className="flex-1 py-2 px-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 group"
                                        >
                                            {showAlternatives ? (
                                                <>
                                                    <span>Hide Alternatives</span>
                                                    <svg className="w-4 h-4 rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                                                </>
                                            ) : (
                                                <>
                                                    <span>View Alternatives (Node 2b)</span>
                                                    <svg className="w-4 h-4 group-hover:translate-y-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                                                </>
                                            )}
                                        </button>
                                    </div>

                                    {/* Alternatives List (Hidden by default) */}
                                    {showAlternatives && analysisResult.alternatives && analysisResult.alternatives.length > 0 && (
                                        <div className="animate-fade-in pt-4 border-t border-white/5 mt-4">
                                            <span className="text-xs text-gray-500 uppercase tracking-widest block mb-3">Comparison</span>
                                            <div className="space-y-3">
                                                {analysisResult.alternatives.map((alt, idx) => (
                                                    <div key={idx} className="p-3 bg-white/5 rounded-lg border border-white/10 hover:border-white/20 transition-colors">
                                                        <div className="flex justify-between items-start mb-2">
                                                            <span className="font-medium text-white">{alt.name}</span>
                                                            <span className={`text-xs px-2 py-0.5 rounded ${alt.score > 30 ? 'bg-green-500/20 text-green-300' : 'bg-gray-700 text-gray-300'} `}>
                                                                Score: {alt.score?.toFixed(1)}
                                                            </span>
                                                        </div>
                                                        <p className="text-xs text-gray-400">{alt.reason}</p>
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
                            ) : isAnalyzing ? (
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
