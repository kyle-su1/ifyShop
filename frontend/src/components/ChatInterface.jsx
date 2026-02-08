import { useState, useRef, useEffect } from 'react';

// Simple markdown formatter for AI responses
const formatMessage = (content) => {
    if (!content) return null;

    // Split by line breaks first
    const lines = content.split('\n');

    return lines.map((line, lineIdx) => {
        // Handle bullet points
        if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
            const bulletContent = line.trim().substring(2);
            return (
                <div key={lineIdx} className="flex items-start gap-2 ml-2">
                    <span className="text-indigo-400 mt-0.5">•</span>
                    <span>{formatInlineStyles(bulletContent)}</span>
                </div>
            );
        }

        // Handle numbered lists
        const numberedMatch = line.trim().match(/^(\d+)\.\s+(.*)$/);
        if (numberedMatch) {
            return (
                <div key={lineIdx} className="flex items-start gap-2 ml-2">
                    <span className="text-indigo-400 font-medium min-w-[1rem]">{numberedMatch[1]}.</span>
                    <span>{formatInlineStyles(numberedMatch[2])}</span>
                </div>
            );
        }

        // Regular line
        if (line.trim() === '') {
            return <div key={lineIdx} className="h-2" />; // Empty line spacer
        }

        return <div key={lineIdx}>{formatInlineStyles(line)}</div>;
    });
};

// Format inline styles: **bold**, *italic*, `code`
const formatInlineStyles = (text) => {
    if (!text) return text;

    const parts = [];
    let remaining = text;
    let key = 0;

    while (remaining.length > 0) {
        // Check for **bold**
        const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
        // Check for *italic*
        const italicMatch = remaining.match(/\*([^*]+)\*/);
        // Check for `code`
        const codeMatch = remaining.match(/`([^`]+)`/);

        // Find the earliest match
        const matches = [
            { type: 'bold', match: boldMatch, pattern: /\*\*(.+?)\*\*/ },
            { type: 'italic', match: italicMatch, pattern: /\*([^*]+)\*/ },
            { type: 'code', match: codeMatch, pattern: /`([^`]+)`/ }
        ].filter(m => m.match).sort((a, b) => a.match.index - b.match.index);

        if (matches.length === 0) {
            parts.push(remaining);
            break;
        }

        const first = matches[0];
        const beforeMatch = remaining.substring(0, first.match.index);
        if (beforeMatch) {
            parts.push(beforeMatch);
        }

        const content = first.match[1];
        if (first.type === 'bold') {
            parts.push(<strong key={key++} className="font-semibold text-white">{content}</strong>);
        } else if (first.type === 'italic') {
            parts.push(<em key={key++} className="italic text-gray-300">{content}</em>);
        } else if (first.type === 'code') {
            parts.push(<code key={key++} className="px-1.5 py-0.5 bg-black/40 text-indigo-300 rounded text-xs font-mono">{content}</code>);
        }

        remaining = remaining.substring(first.match.index + first.match[0].length);
    }

    return parts.length > 0 ? parts : text;
};

const ChatInterface = ({
    imageBase64,
    onBoundingBoxUpdate,
    onAnalysisStart,
    onAnalysisComplete,
    isAnalyzing = false,
    disabled = false,
    messages = [],        // Controlled by parent
    setMessages = null    // Parent's setter function (optional)
}) => {
    // Use local state only if parent doesn't control it
    const [localMessages, setLocalMessages] = useState([]);
    const chatMessages = setMessages ? messages : localMessages;
    const setChatMessages = setMessages || setLocalMessages;

    const [inputValue, setInputValue] = useState('');
    const [isExpanded, setIsExpanded] = useState(true);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatMessages]);

    const handleSend = async () => {
        if (!inputValue.trim() || disabled || isAnalyzing) return;

        const userMessage = inputValue.trim();
        setInputValue('');

        // Notify parent to start analysis - parent handles message management
        if (onAnalysisStart) {
            onAnalysisStart(userMessage);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="w-full h-full flex flex-col">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3 border border-white/10 rounded-xl bg-[#0d0d0f]">
                {chatMessages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center">
                        <p className="text-gray-500 text-sm">
                            Ask about any item in the image
                        </p>
                        <p className="text-gray-600 text-xs mt-1">
                            e.g., "What is this phone?" or "Where can I buy this keyboard?"
                        </p>
                    </div>
                ) : (
                    chatMessages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[80%] px-3 py-2 rounded-xl text-sm ${msg.role === 'user'
                                    ? 'bg-indigo-600 text-white rounded-br-sm'
                                    : 'bg-white/10 text-gray-200 rounded-bl-sm'
                                    }`}
                            >
                                {msg.isThinking ? (
                                    <div className="flex items-center gap-1">
                                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                ) : msg.role === 'assistant' ? (
                                    formatMessage(msg.content)
                                ) : (
                                    msg.content
                                )}
                            </div>
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-white/5 p-3">
                <div className="flex items-center gap-2">
                    <input
                        ref={inputRef}
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder={disabled ? "Upload an image first..." : "Ask about any item..."}
                        disabled={disabled || isAnalyzing}
                        className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    />
                    <button
                        onClick={handleSend}
                        disabled={!inputValue.trim() || disabled || isAnalyzing}
                        className="p-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors"
                    >
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
};

// Export with ref forwarding for parent access to methods
export default ChatInterface;
