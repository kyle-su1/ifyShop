import { useState, useRef, useEffect } from 'react'

const ImageUploader = ({ onImageSelected, initialImage, overlays = [] }) => {
    const [preview, setPreview] = useState(initialImage || null)
    const [isDragging, setIsDragging] = useState(false)
    const fileInputRef = useRef(null)

    useEffect(() => {
        if (initialImage) {
            setPreview(initialImage)
        }
    }, [initialImage])

    const handleFile = (file) => {
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader()
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    // Convert to JPEG using Canvas
                    const canvas = document.createElement('canvas');
                    canvas.width = img.width;
                    canvas.height = img.height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);

                    // Get JPEG Base64
                    const jpegBase64 = canvas.toDataURL('image/jpeg', 0.9);

                    setPreview(jpegBase64)
                    if (onImageSelected) {
                        // Pass original file for name/metadata, but NEW base64 for processing
                        onImageSelected(file, jpegBase64)
                    }
                };
                img.src = e.target.result;
            }
            reader.readAsDataURL(file)
        }
    }

    // ... (handlers remain the same) ...
    const handleDrop = (e) => {
        e.preventDefault()
        setIsDragging(false)
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0])
        }
    }

    const handleDragOver = (e) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = (e) => {
        e.preventDefault()
        setIsDragging(false)
    }

    const handleClick = () => {
        fileInputRef.current.click()
    }

    const handleInputChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0])
        }
    }

    return (
        <div className="w-full h-full">
            <div
                onClick={handleClick}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`
          relative group cursor-pointer 
          border-2 border-dashed rounded-2xl p-4
          transition-all duration-300 ease-in-out
          flex flex-col items-center justify-center
          h-full min-h-[400px] w-full overflow-hidden
          ${isDragging
                        ? 'border-blue-500 bg-blue-500/10 scale-[1.01]'
                        : 'border-gray-600 hover:border-blue-400 hover:bg-white/5'
                    }
        `}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleInputChange}
                    className="hidden"
                    accept="image/*"
                />

                {preview ? (
                    <div className="relative w-full h-full flex items-center justify-center">
                        {/* Image Container with relative positioning for overlays */}
                        <div className="relative max-h-full max-w-full">
                            <img
                                src={preview}
                                alt="Preview"
                                className="max-h-full max-w-full w-auto h-auto rounded-lg shadow-xl object-contain"
                                style={{ maxHeight: 'calc(100vh - 250px)' }}
                            />

                            {/* Bounding Box Overlays */}
                            {overlays && overlays.map((obj, idx) => {
                                const vertices = obj.boundingPoly?.normalizedVertices;
                                if (!vertices || vertices.length < 4) return null;

                                // Simple box from top-left and bottom-right (assuming rect)
                                // Or polygon using clip-path? Box is safer for generic rects.
                                // Google Vision usually returns 4 points.
                                // Let's find min/max x/y to be safe.
                                const xs = vertices.map(v => v.x || 0);
                                const ys = vertices.map(v => v.y || 0);
                                const minX = Math.min(...xs) * 100;
                                const maxX = Math.max(...xs) * 100;
                                const minY = Math.min(...ys) * 100;
                                const maxY = Math.max(...ys) * 100;
                                const width = maxX - minX;
                                const height = maxY - minY;

                                return (
                                    <div
                                        key={idx}
                                        className="absolute border-2 border-green-400 bg-green-400/20 hover:bg-green-400/40 transition-colors z-10"
                                        style={{
                                            left: `${minX}%`,
                                            top: `${minY}%`,
                                            width: `${width}%`,
                                            height: `${height}%`,
                                        }}
                                        title={`${obj.name} (${(obj.score * 100).toFixed(1)}%)`}
                                    >
                                        <span className="absolute -top-6 left-0 bg-green-500 text-black text-xs font-bold px-1 rounded shadow-md whitespace-nowrap">
                                            {obj.name}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>

                        <div className={`absolute inset-0 bg-black/60 transition-opacity flex items-center justify-center rounded-lg ${overlays.length > 0 ? 'opacity-0 hover:opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
                            <p className="text-white font-medium">Click or Drop to Replace</p>
                        </div>
                    </div>
                ) : (
                    <div className="text-center">
                        <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-700/50 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                            <svg className="w-10 h-10 text-gray-400 group-hover:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <p className="text-xl font-medium text-gray-200 mb-2">
                            Drop your image here
                        </p>
                        <p className="text-sm text-gray-400">
                            or click to browse from your computer
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
}

export default ImageUploader
