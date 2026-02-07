import { useState } from 'react'
import ImageUploader from './components/ImageUploader'
import './App.css'

function App() {
  const [imageFile, setImageFile] = useState(null)
  const [imageBase64, setImageBase64] = useState(null)

  const [analysisResult, setAnalysisResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState(null)

  const handleImageSelected = (file, base64) => {
    setImageFile(file)
    setImageBase64(base64)
    setAnalysisResult(null)
    setError(null)
    // No longer auto-start analysis
  }

  const analyzeImage = async () => {
    if (!imageBase64) return;

    setAnalysisResult(null)
    setError(null)
    setIsAnalyzing(true)

    console.log("Sending Base64:", imageBase64 ? imageBase64.substring(0, 100) + "..." : "Empty");

    try {
      const response = await fetch('http://localhost:3001/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ imageBase64 }),
      });

      const data = await response.json();
      if (response.ok) {
        setAnalysisResult(data);
      } else {
        console.error("Analysis failed:", data);
        const errorMessage = data.details || data.error || 'Unknown error occurred';
        setError(errorMessage);
      }
    } catch (error) {
      console.error("Error analyzing image:", error);
      setError("Could not connect to backend server. Make sure the backend is running on port 3001.");
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-4 md:p-8">
      <div className="w-full h-full">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
              AI Vision Uploader
            </h1>
            <p className="text-gray-400 mt-2 text-lg">
              Upload an image to process with Google Cloud Vision or OpenAI Vision.
            </p>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-180px)]">
          <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-6 border border-white/20 shadow-2xl flex flex-col">
            <h2 className="text-2xl font-semibold mb-4 text-white/90">Input Image</h2>
            <div className="flex-1 flex flex-col">
              <ImageUploader
                onImageSelected={handleImageSelected}
                overlays={analysisResult?.objects}
              />
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-lg rounded-3xl p-6 border border-white/10 shadow-xl flex flex-col h-full max-h-[calc(100vh-180px)]">
            <h2 className="text-2xl font-semibold mb-4 text-white/90">Processing Results</h2>
            {isAnalyzing ? (
              <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p>Analyzing image with Cloud Vision...</p>
              </div>
            ) : error ? (
              <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
                <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-red-400 mb-2">Analysis Failed</h3>
                <p className="text-gray-300 mb-6 max-w-md">{error}</p>
                <button
                  onClick={analyzeImage}
                  className="px-6 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors border border-white/10"
                >
                  Try Again
                </button>
              </div>
            ) : analysisResult ? (
              <div className="flex-1 space-y-6 overflow-y-auto pr-2 custom-scrollbar">
                <div className="p-4 bg-black/30 rounded-xl border border-white/10">
                  <h3 className="text-xl font-semibold mb-3 text-blue-300">Objects Detected ({analysisResult.objects ? analysisResult.objects.length : 0})</h3>
                  <div className="space-y-2">
                    {analysisResult.objects && analysisResult.objects.map((obj, idx) => (
                      <div key={idx} className="flex items-center justify-between text-sm bg-white/5 p-2 rounded border border-white/5">
                        <span className="font-medium text-gray-200">{obj.name}</span>
                        <span className="text-gray-400">{(obj.score * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                    {(!analysisResult.objects || analysisResult.objects.length === 0) && (
                      <p className="text-gray-500 italic">No objects detected.</p>
                    )}
                  </div>
                </div>

                <div className="p-4 bg-black/30 rounded-xl border border-white/10">
                  <h3 className="text-xl font-semibold mb-3 text-purple-300">Labels</h3>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.labels && analysisResult.labels.map((label, idx) => (
                      <span key={idx} className="bg-purple-500/20 text-purple-200 px-3 py-1 rounded-full text-xs border border-purple-500/30">
                        {label.description} ({(label.score * 100).toFixed(0)}%)
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-4 bg-black/30 rounded-xl border border-white/10">
                  <h3 className="text-xl font-semibold mb-2 text-green-300">Raw Data</h3>
                  <details>
                    <summary className="cursor-pointer text-gray-400 hover:text-white text-sm">View JSON</summary>
                    <pre className="mt-2 text-xs text-green-400 bg-black/50 p-2 rounded overflow-x-auto">
                      {JSON.stringify(analysisResult, null, 2)}
                    </pre>
                  </details>
                </div>
              </div>
            ) : imageFile ? (
              <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                <p className="mb-4 text-center">Image loaded.</p>
                <button
                  onClick={analyzeImage}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium shadow-lg shadow-blue-500/30"
                >
                  Analyze Image
                </button>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <p>Upload an image to start analysis.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
