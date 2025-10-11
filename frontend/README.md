# Financial AI Agents Frontend

A modern React frontend for the Financial AI Agents system, providing an intuitive interface for financial research, stock analysis, and RAG evaluation.

## Features

- **Dashboard**: Overview of system status and quick access to all services
- **Research Analysis**: Comprehensive financial research with real-time streaming
- **Stock Analysis**: Individual and comparative stock analysis with market data
- **RAG Evaluation**: Quality assessment of AI-generated responses
- **System Status**: Real-time monitoring of system health and performance
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Streaming**: Server-Sent Events for live analysis updates

## Technology Stack

- **React 18** - Modern React with hooks and functional components
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API requests
- **Lucide React** - Beautiful icons
- **React Markdown** - Markdown rendering for analysis results
- **Recharts** - Charts and data visualization

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Financial AI Agents backend running on `http://localhost:8000`

### Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**:
   ```bash
   npm start
   ```

3. **Open your browser**:
   Navigate to `http://localhost:3000`

### Environment Configuration

Create a `.env` file in the frontend directory to customize the API URL:

```bash
REACT_APP_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── Layout.js      # Main layout with navigation
│   │   ├── LoadingSpinner.js
│   │   ├── ProgressBar.js
│   │   └── StreamingOutput.js
│   ├── pages/            # Page components
│   │   ├── Dashboard.js   # Main dashboard
│   │   ├── Research.js    # Research analysis
│   │   ├── StockAnalysis.js
│   │   ├── RAGEvaluation.js
│   │   └── SystemStatus.js
│   ├── services/         # API services
│   │   └── api.js        # API client and endpoints
│   ├── App.js           # Main app component
│   ├── index.js         # Entry point
│   └── index.css        # Global styles
├── package.json
└── tailwind.config.js   # Tailwind configuration
```

## Key Features

### Dashboard
- System health overview
- Quick access to all services
- Real-time statistics
- Service status indicators

### Research Analysis
- Multi-source financial research
- Customizable parameters (sources, focus areas, time horizon)
- Real-time streaming analysis
- Suggested topics
- Downloadable results

### Stock Analysis
- Individual stock analysis
- Multi-stock comparison
- Technical and fundamental analysis
- Popular stock suggestions
- Real-time market data

### RAG Evaluation
- Quality assessment of AI responses
- Multiple evaluation criteria
- Batch processing support
- Detailed scoring and recommendations
- Context document management

### System Status
- Real-time system monitoring
- Service health checks
- Streaming statistics
- Configuration overview
- Stream management tools

## API Integration

The frontend integrates with the Financial AI Agents backend through:

- **REST API**: Standard HTTP requests for analysis and data retrieval
- **Server-Sent Events**: Real-time streaming for live analysis updates
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Progress Tracking**: Real-time progress updates during analysis

## Styling and UI

- **Tailwind CSS**: Utility-first CSS framework for rapid development
- **Responsive Design**: Mobile-first approach with responsive breakpoints
- **Component Library**: Reusable components with consistent styling
- **Dark Mode Ready**: Prepared for dark mode implementation
- **Accessibility**: ARIA labels and keyboard navigation support

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

### Code Style

- **ESLint**: Code linting with React rules
- **Prettier**: Code formatting (recommended)
- **Component Structure**: Functional components with hooks
- **State Management**: React hooks for local state

### Adding New Features

1. Create new components in `src/components/`
2. Add new pages in `src/pages/`
3. Update routing in `src/App.js`
4. Add API endpoints in `src/services/api.js`
5. Update navigation in `src/components/Layout.js`

## Deployment

### Production Build

```bash
npm run build
```

This creates a `build/` directory with optimized production files.

### Deployment Options

- **Static Hosting**: Deploy to Netlify, Vercel, or GitHub Pages
- **Docker**: Use the included Dockerfile for containerized deployment
- **Traditional Hosting**: Upload build files to any web server

### Environment Variables

Set these environment variables for production:

```bash
REACT_APP_API_URL=https://your-api-domain.com
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.