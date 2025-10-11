import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Copy, Download, Pause, Play } from 'lucide-react';
import ProgressBar from './ProgressBar';

const StreamingOutput = ({ 
  isStreaming, 
  content, 
  progress, 
  error, 
  onStop,
  title = "Analysis Results"
}) => {
  const [isPaused, setIsPaused] = useState(false);
  const [copiedContent, setCopiedContent] = useState(false);
  const contentRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (autoScroll && contentRef.current && isStreaming) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [content, autoScroll, isStreaming]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedContent(true);
      setTimeout(() => setCopiedContent(false), 2000);
    } catch (err) {
      console.error('Failed to copy content:', err);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, '-')}-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleScroll = () => {
    if (contentRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = contentRef.current;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
      setAutoScroll(isAtBottom);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="flex items-center space-x-2">
          {isStreaming && onStop && (
            <button
              onClick={() => {
                setIsPaused(!isPaused);
                if (onStop) onStop();
              }}
              className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
              title={isPaused ? "Resume" : "Pause"}
            >
              {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
            </button>
          )}
          {content && (
            <>
              <button
                onClick={handleCopy}
                className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
                title="Copy to clipboard"
              >
                <Copy className="h-4 w-4" />
              </button>
              <button
                onClick={handleDownload}
                className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
                title="Download as file"
              >
                <Download className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {progress && (
        <div className="mb-4">
          <ProgressBar 
            progress={progress.percentage} 
            text={progress.message}
            showPercentage={true}
          />
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="mb-4 p-4 bg-danger-50 border border-danger-200 rounded-lg">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-danger-800">
                Error occurred
              </h3>
              <div className="mt-2 text-sm text-danger-700">
                <p>{error.message || error}</p>
                {error.suggestions && (
                  <ul className="mt-2 list-disc list-inside">
                    {error.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content display */}
      <div 
        ref={contentRef}
        onScroll={handleScroll}
        className="max-h-96 overflow-y-auto border border-gray-200 rounded-lg p-4 bg-gray-50"
      >
        {content ? (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        ) : (
          <div className="text-gray-500 text-center py-8">
            {isStreaming ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-primary-600"></div>
                <span>Waiting for response...</span>
              </div>
            ) : (
              "No content available"
            )}
          </div>
        )}
      </div>

      {/* Status indicators */}
      <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center space-x-4">
          {isStreaming && (
            <div className="flex items-center space-x-1">
              <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
              <span>Streaming...</span>
            </div>
          )}
          {copiedContent && (
            <span className="text-green-600">Copied to clipboard!</span>
          )}
        </div>
        
        {content && (
          <div className="text-xs">
            {content.length} characters
          </div>
        )}
      </div>

      {/* Auto-scroll indicator */}
      {isStreaming && !autoScroll && (
        <div className="mt-2">
          <button
            onClick={() => {
              setAutoScroll(true);
              if (contentRef.current) {
                contentRef.current.scrollTop = contentRef.current.scrollHeight;
              }
            }}
            className="text-xs text-primary-600 hover:text-primary-700 underline"
          >
            Scroll to bottom to resume auto-scroll
          </button>
        </div>
      )}
    </div>
  );
};

export default StreamingOutput;