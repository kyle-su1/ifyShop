import { useState } from 'react'
import ImageUploader from '../components/ImageUploader'
import LogoutButton from '../components/LogoutButton'
import { useAuth0 } from '@auth0/auth0-react'
import { analyzeImage } from '../lib/api'

const DashboardPage = () => {
    const { user, getAccessTokenSilently, isLoading } = useAuth0()
    const [imageFile, setImageFile] = useState(null)
    const [imageBase64, setImageBase64] = useState(null)
    const [analysisResult, setAnalysisResult] = useState(null)
    const [isAnalyzing, setIsAnalyzing] = useState(false)

    const handleImageSelected = (file, base64) => {
        setImageFile(file)
        setImageBase64(base64)
        setAnalysisResult(null)
    }

    const handleAnalyze = async () => {
        if (!imageFile) return;
        setIsAnalyzing(true);
        try {
            const token = await getAccessTokenSilently();
            const result = await analyzeImage(imageFile, token);
            setAnalysisResult(result);
        } catch (error) {
            console.error("Analysis failed:", error);
            alert("Failed to analyze image. Ensure you are logged in.");
        } finally {
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
                                <ImageUploader onImageSelected={handleImageSelected} />

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

                            {analysisResult ? (
                                <div className="animate-fade-in space-y-6">
                                    {/* Status Banner */}
                                    <div className="flex items-center gap-3 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                                        <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
                                        <span className="text-sm text-green-400 font-medium">Analysis Complete</span>
                                    </div>

                                    {/* Main Content */}
                                    <div className="space-y-4">
                                        <div>
                                            <span className="text-xs text-gray-500 uppercase tracking-widest">Identified Item</span>
                                            <h2 className="text-2xl font-semibold text-white mt-1">{analysisResult.item_name}</h2>
                                        </div>

                                        <div className="p-4 bg-white/5 rounded-lg border border-white/5">
                                            <p className="text-gray-300 leading-relaxed text-sm">{analysisResult.description}</p>
                                        </div>

                                        <div>
                                            <span className="text-xs text-gray-500 uppercase tracking-widest block mb-2">Detected Signals</span>
                                            <div className="flex flex-wrap gap-2">
                                                {analysisResult.detected_keywords?.map((kw, i) => (
                                                    <span key={i} className="px-2.5 py-1 bg-white/5 border border-white/10 rounded text-xs text-gray-400 hover:text-white hover:border-white/20 transition-all cursor-default">
                                                        {kw}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    {/* JSON Data Toggle */}
                                    <div className="pt-4 border-t border-white/5">
                                        <details className="group">
                                            <summary className="cursor-pointer text-xs text-gray-600 hover:text-gray-400 transition-colors list-none flex items-center gap-2">
                                                <span className="group-open:rotate-90 transition-transform">▸</span>
                                                View Raw Agent Data
                                            </summary>
                                            <pre className="mt-3 text-[10px] text-gray-500 bg-black/50 p-4 rounded-lg overflow-x-auto font-mono">
                                                {JSON.stringify(analysisResult, null, 2)}
                                            </pre>
                                        </details>
                                    </div>
                                </div>
                            ) : isAnalyzing ? (
                                <div className="flex-1 flex flex-col items-center justify-center text-center space-y-4">
                                    <div className="relative">
                                        <div className="w-16 h-16 rounded-full border-2 border-dashed border-white/20 animate-[spin_10s_linear_infinite]"></div>
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <div className="w-8 h-8 rounded-full bg-indigo-500/20 animate-pulse"></div>
                                        </div>
                                    </div>
                                    <div>
                                        <p className="text-white font-medium">Analyzing Visual Data</p>
                                        <p className="text-sm text-gray-500 mt-1">Extracting features and identifying products...</p>
                                    </div>
                                </div>
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
