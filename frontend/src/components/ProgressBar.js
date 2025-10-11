import React from 'react';

const ProgressBar = ({ progress, text, showPercentage = true }) => {
  const percentage = Math.min(Math.max(progress || 0, 0), 100);

  return (
    <div className="w-full">
      {text && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">{text}</span>
          {showPercentage && (
            <span className="text-sm text-gray-500">{Math.round(percentage)}%</span>
          )}
        </div>
      )}
      <div className="progress-bar">
        <div 
          className="progress-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;