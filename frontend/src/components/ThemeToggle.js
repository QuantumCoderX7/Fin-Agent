import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const ThemeToggle = () => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`
        p-2 rounded-full transition-colors duration-200
        ${isDark 
          ? 'bg-gray-900 text-yellow-400 hover:bg-gray-800 hover:text-yellow-300' 
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }
        focus:outline-none focus:ring-2 focus:ring-offset-2 dark:ring-offset-black focus:ring-primary-500
      `}
      aria-label="Toggle theme"
    >
      {isDark ? (
        <Sun className="h-5 w-5" />
      ) : (
        <Moon className="h-5 w-5" />
      )}
    </button>
  );
};

export default ThemeToggle;