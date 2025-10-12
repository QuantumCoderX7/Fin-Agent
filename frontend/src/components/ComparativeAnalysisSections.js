import React from 'react';
import { BarChart2, ShieldAlert, PieChart, Boxes, Lightbulb, ArrowRight } from 'lucide-react';

const AnalysisSection = ({ title, icon: Icon, children, className = '' }) => (
  <div className={`mb-8 last:mb-0 ${className}`}>
    <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
      <Icon className="h-5 w-5 mr-2 text-primary-500" />
      {title}
    </h3>
    {children}
  </div>
);

const ComparativeAnalysisSections = ({ content }) => {
  // Split content into sections
  const sections = content.split(/(?=\*\*\d+\.)/).filter(Boolean);

  const renderSection = (section, index) => {
    // Extract title and content
    const titleMatch = section.match(/\*\*(\d+\.\s*[^*]+)\*\*/);
    const title = titleMatch ? titleMatch[1] : '';
    const sectionContent = section.replace(/\*\*\d+\.[^*]+\*\*/, '').trim();

    // Helper to format content with proper styling
    const formatContent = (text) => {
      return text.split('\n').map((line, i) => {
        const trimmedLine = line.trim();
        if (!trimmedLine) return null;

        // Format subsection headers (ending with ':')
        if (trimmedLine.endsWith(':')) {
          return (
            <h4 key={i} className="font-semibold text-gray-800 mt-4 mb-2">
              {trimmedLine}
            </h4>
          );
        }

        // Format stock groups (e.g., "High P/E (1 stock):")
        if (trimmedLine.match(/^(High|Medium|Low)\s+[^:]+:/)) {
          return (
            <div key={i} className="mb-2">
              <span className="font-medium text-gray-700">{trimmedLine}</span>
            </div>
          );
        }

        // Format stock listings with metrics
        if (trimmedLine.includes('(') && trimmedLine.includes(')') && /[A-Z]{2,}/.test(trimmedLine)) {
          return (
            <div key={i} className="flex items-center py-1">
              <div className="flex-1">
                {trimmedLine.split(/[()–]/).map((part, partIndex) => {
                  const trimmedPart = part.trim();
                  if (!trimmedPart) return null;
                  
                  // Format stock symbols
                  if (/^[A-Z]{2,}$/.test(trimmedPart)) {
                    return (
                      <span key={partIndex} className="font-semibold text-primary-600 mr-1">
                        {trimmedPart}
                      </span>
                    );
                  }
                  
                  // Format metrics (numbers with x, T, B, M)
                  if (/[\d.]+[xTBM]/.test(trimmedPart)) {
                    return (
                      <span key={partIndex} className="font-mono text-gray-900 mx-1">
                        {trimmedPart}
                      </span>
                    );
                  }
                  
                  // Regular text
                  return (
                    <span key={partIndex} className="text-gray-600">
                      {trimmedPart}
                    </span>
                  );
                })}
              </div>
            </div>
          );
        }

        // Format value groups
        if (trimmedLine.startsWith('Value Groups:')) {
          return (
            <div key={i} className="mt-4 mb-2">
              <h4 className="font-semibold text-gray-800">Value Groups:</h4>
            </div>
          );
        }

        if (/^(High|Medium|Low) P\/E:/.test(trimmedLine)) {
          const [category, stocks] = trimmedLine.split(':').map(s => s.trim());
          return (
            <div key={i} className="flex items-center py-1">
              <span className={`w-24 font-medium ${
                category.startsWith('High') ? 'text-red-600' :
                category.startsWith('Medium') ? 'text-yellow-600' :
                'text-green-600'
              }`}>
                {category}:
              </span>
              <span className="text-gray-700">{stocks || 'None'}</span>
            </div>
          );
        }

        // Format bullet points
        if (trimmedLine.startsWith('- ')) {
          return (
            <div key={i} className="flex items-start py-1">
              <ArrowRight className="h-4 w-4 mr-2 mt-1 text-primary-500 flex-shrink-0" />
              <div 
                className="flex-1 text-gray-700"
                dangerouslySetInnerHTML={{ __html: trimmedLine.replace('- ', '') }}
              />
            </div>
          );
        }

        // Regular paragraph with enhanced formatting
        return (
          <p key={i} className="mb-3 last:mb-0 text-gray-700">
            {trimmedLine.split(/([A-Z]{2,}|\$[\d.]+[TBM]|\d+\.\d+x)/).map((part, partIndex) => {
              if (/^[A-Z]{2,}$/.test(part)) {
                return <span key={partIndex} className="font-semibold text-primary-600">{part}</span>;
              }
              if (/^\$[\d.]+[TBM]$/.test(part)) {
                return <span key={partIndex} className="font-mono text-gray-900">{part}</span>;
              }
              if (/^\d+\.\d+x$/.test(part)) {
                return <span key={partIndex} className="font-mono text-gray-900">{part}</span>;
              }
              return part;
            })}
          </p>
        );
      }).filter(Boolean);
    };

    // Pick icon based on section content
    const getIcon = () => {
      if (title.includes('Valuation')) return BarChart2;
      if (title.includes('Risk')) return ShieldAlert;
      if (title.includes('Portfolio')) return PieChart;
      if (title.includes('Sector')) return Boxes;
      if (title.includes('Investment')) return Lightbulb;
      return BarChart2;
    };

    return (
      <AnalysisSection 
        key={index} 
        title={title}
        icon={getIcon()}
      >
        <div className="prose max-w-none text-gray-700">
          {formatContent(sectionContent)}
        </div>
      </AnalysisSection>
    );
  };

  // Special handling for Actionable Insight
  const actionableMatch = content.match(/\*\*Actionable Insight\*\*:([^]*$)/);
  const mainSections = sections.map((section, index) => renderSection(section, index));
  
  if (actionableMatch) {
    const actionableContent = actionableMatch[1].trim();
    mainSections.push(
      <div key="actionable" className="mt-8 pt-6 border-t border-gray-200">
        <div className="bg-primary-50 rounded-lg p-4">
          <h4 className="text-lg font-semibold text-primary-900 mb-2 flex items-center">
            <Lightbulb className="h-5 w-5 mr-2 text-primary-600" />
            Actionable Insight
          </h4>
          <div 
            className="text-primary-800"
            dangerouslySetInnerHTML={{ 
              __html: actionableContent.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            }}
          />
        </div>
      </div>
    );
  }

  return <div className="space-y-8">{mainSections}</div>;
};

export default ComparativeAnalysisSections;