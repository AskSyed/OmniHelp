# OmniHelp Frontend

React-based chat interface for querying the OmniHelp RAG (Retrieval-Augmented Generation) system.

## Features

- 🎨 Modern, responsive chat interface
- 💬 Real-time query processing
- 📚 Source citations for answers
- 🔄 Loading states and error handling
- 📱 Mobile-friendly design

## Prerequisites

- Node.js 18+ and npm (or yarn/pnpm)
- Backend API running on `http://localhost:8000`

## Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create a `.env` file (optional):**
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```
   If not set, it defaults to `http://localhost:8000`

## Running the Application

1. **Start the development server:**
   ```bash
   npm run dev
   ```

2. **Open your browser:**
   Navigate to `http://localhost:3000`

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatMessage.jsx      # Message display component
│   │   ├── ChatMessage.css
│   │   ├── ChatInput.jsx         # Input form component
│   │   └── ChatInput.css
│   ├── services/
│   │   └── api.js                # API service layer
│   ├── App.jsx                   # Main app component
│   ├── App.css                   # App styles
│   ├── main.jsx                  # Entry point
│   └── index.css                 # Global styles
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

## Usage

1. Start the backend API server (see backend README)
2. Start the frontend development server
3. Open the chat interface in your browser
4. Type your product-related questions and get AI-powered answers

## API Integration

The frontend communicates with the backend API at `/api/v1/query` endpoint:

**Request:**
```json
{
  "query": "What laptops do you have?",
  "n_results": 5,
  "filters": null
}
```

**Response:**
```json
{
  "answer": "We have several laptops available...",
  "sources": ["source1", "source2"],
  "retrieved_chunks": [...],
  "metadata": {...}
}
```

## Customization

### Changing the API URL

Set the `VITE_API_BASE_URL` environment variable or modify `src/services/api.js`.

### Styling

Modify the CSS files in `src/` to customize the appearance:
- `src/App.css` - Main layout and chat container
- `src/components/ChatMessage.css` - Message styling
- `src/components/ChatInput.css` - Input form styling

## Troubleshooting

### CORS Errors

If you encounter CORS errors, ensure the backend has CORS properly configured to allow requests from `http://localhost:3000`.

### Connection Errors

- Verify the backend API is running on port 8000
- Check the `VITE_API_BASE_URL` environment variable
- Check browser console for detailed error messages

## Technologies Used

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **CSS3** - Styling

## License

Part of the OmniHelp project.
