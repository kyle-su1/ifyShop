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
                    <span className="text-emerald-400 mt-0.5">•</span>
                    <span>{formatInlineStyles(bulletContent)}</span>
                </div>
            );
        }

        // Handle numbered lists
        const numberedMatch = line.trim().match(/^(\d+)\.\s+(.*)$/);
        if (numberedMatch) {
            return (
                <div key={lineIdx} className="flex items-start gap-2 ml-2">
                    <span className="text-emerald-400 font-medium min-w-[1rem]">{numberedMatch[1]}.</span>
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
            parts.push(<code key={key++} className="px-1.5 py-0.5 bg-black/40 text-emerald-300 rounded text-xs font-mono">{content}</code>);
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
        <div className="w-full h-full flex flex-col min-h-0">
            {/* Messages Area - scrollable */}
            <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-3 border border-white/10 rounded-xl bg-[#0d0d0f]">
                {chatMessages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center animate-fade-in">
                        <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                        </div>
                        <p className="text-gray-400 text-sm font-medium">
                            Ask about any item in the image
                        </p>
                        <p className="text-gray-600 text-xs mt-2 max-w-[200px]">
                            e.g., "What is this phone?" or "Find the best price for this"
                        </p>
                    </div>
                ) : (
                    chatMessages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
                            style={{ animationDelay: `${idx * 50}ms` }}
                        >
                            <div
                                className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${msg.role === 'user'
                                    ? 'bg-gradient-to-br from-emerald-600 to-emerald-700 text-white rounded-br-md shadow-lg shadow-emerald-500/10'
                                    : 'bg-white/5 border border-white/10 text-gray-200 rounded-bl-md'
                                    }`}
                            >
                                {msg.isThinking ? (
                                    <div className="flex items-center gap-1.5 py-1">
                                        <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
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
                        className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    />
                    <button
                        onClick={handleSend}
                        disabled={!inputValue.trim() || disabled || isAnalyzing}
                        className="p-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors"
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
