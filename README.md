# Omni-Help

**Intelligent Customer Support Platform with Adaptive Multi-Source Routing**

Omni-Help is an intelligent customer support platform that revolutionizes traditional RAG (Retrieval-Augmented Generation) systems through adaptive multi-source routing. Unlike conventional single-pipeline RAG solutions that fail when queries require data from different sources, Omni-Help employs a sophisticated Router Agent that intelligently classifies user intent and dispatches queries to the optimal data source.

## 🏗️ Architecture

The system consists of two main data pipelines:

### A. Unstructured Path (Product Manuals)
- **Vector Database (ChromaDB)**: Stores and retrieves product manuals, policies, and documentation
- **RAG Agent**: Processes queries using Retrieval-Augmented Generation from vector embeddings
- **Use Cases**: Product manuals, FAQs, policy documents, how-to guides

### B. Structured Path (Order Management)
- **SQLite Database**: Stores transactional data about orders, customers, and products
- **SQL Agent**: Converts natural language queries to SQL and retrieves structured data
- **Use Cases**: Order tracking, order history, customer information, transactional queries

### C. Router Agent
- **Intelligent Routing**: Classifies user intent and routes to the appropriate data source
- **Multi-Source Support**: Seamlessly handles queries that may require multiple data sources

## 🛠️ Tech Stack

### Backend
- **Python 3.11+**: Latest Python features
- **FastAPI**: Modern, fast web framework for building APIs
- **LangGraph**: Agent orchestration and workflow management
- **LangChain**: LLM integration and RAG capabilities
- **ChromaDB**: Vector database for embeddings
- **SQLite**: Lightweight relational database
- **OpenAI**: LLM and embeddings (GPT-4, text-embedding-3-small)

### Frontend
- **Angular 18**: Modern frontend framework
- **TypeScript**: Type-safe development
- **SCSS**: Styling with modern CSS features

## 📁 Project Structure

```
OmniHelp/
├── backend/
│   ├── app/
│   │   ├── agents/              # LangGraph agents
│   │   │   ├── router_agent.py  # Intent classification & routing
│   │   │   ├── rag_agent.py     # Vector DB RAG agent
│   │   │   ├── sql_agent.py     # SQL query agent
│   │   │   └── orchestrator.py # Main orchestration
│   │   ├── api/                 # FastAPI routes
│   │   │   └── v1/
│   │   │       ├── chat.py      # Chat endpoints
│   │   │       ├── documents.py # Document management
│   │   │       └── orders.py    # Order management
│   │   ├── core/                # Core configuration
│   │   │   └── config.py        # Settings management
│   │   ├── db/                  # Database modules
│   │   │   ├── sqlite.py        # SQLite utilities
│   │   │   └── chroma.py        # ChromaDB utilities
│   │   ├── models/              # Data models
│   │   │   └── order.py         # Order & customer models
│   │   ├── services/            # Business logic
│   │   │   ├── document_service.py
│   │   │   └── order_service.py
│   │   └── utils/               # Utilities
│   │       └── logger.py        # Logging configuration
│   ├── main.py                  # FastAPI application entry
│   ├── requirements.txt         # Python dependencies
│   └── .env.example            # Environment variables template
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   ├── chat/                    # Chat interface
│   │   │   │   ├── document-upload/          # Document upload UI
│   │   │   │   └── order-management/         # Order management UI
│   │   │   ├── services/
│   │   │   │   └── api.service.ts           # API service
│   │   │   ├── app.component.ts             # Root component
│   │   │   └── app.routes.ts                # Routing configuration
│   │   ├── environments/
│   │   │   └── environment.ts               # Environment config
│   │   ├── styles.scss                      # Global styles
│   │   └── main.ts                          # Application entry
│   ├── package.json                         # Node dependencies
│   └── angular.json                         # Angular configuration
│
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ and npm
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. **Create data directories:**
   ```bash
   mkdir -p data logs
   ```

6. **Run the backend server:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`
   API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm start
   ```
   
   The application will be available at `http://localhost:4200`

## 📖 Usage

### 1. Upload Documents

- Navigate to the **Documents** tab in the UI
- Upload PDF files (e.g., product manuals)
- Documents are automatically processed, chunked, and indexed in ChromaDB

### 2. Create Orders

- Navigate to the **Orders** tab
- Create orders with customer information, products, and order details
- Orders are stored in SQLite database

### 3. Chat with Omni-Help

- Navigate to the **Chat** tab
- Ask questions about:
  - **Product manuals**: "How do I reset my laptop?"
  - **Order tracking**: "What's the status of order ORD-12345?"
  - **General questions**: Any other customer support queries

The Router Agent automatically classifies your intent and routes to the appropriate data source.

## 🔄 How It Works

1. **User Query**: User submits a question through the chat interface
2. **Router Agent**: Classifies intent (policy_document, order_tracking, or general)
3. **Routing Decision**:
   - `policy_document` → **RAG Agent** (ChromaDB vector search)
   - `order_tracking` → **SQL Agent** (SQLite database query)
   - `general` → **General LLM** (Direct OpenAI response)
4. **Response Generation**: Selected agent processes query and returns answer
5. **User Response**: Formatted answer displayed to user

## 🧪 API Endpoints

### Chat
- `POST /api/v1/chat/query` - Submit a chat query

### Documents
- `POST /api/v1/documents/upload` - Upload a PDF document
- `GET /api/v1/documents/list` - List all documents
- `DELETE /api/v1/documents/{document_id}` - Delete a document

### Orders
- `POST /api/v1/orders/` - Create a new order
- `GET /api/v1/orders/{order_id}` - Get order by ID
- `GET /api/v1/orders/customer/{customer_id}` - Get customer orders
- `POST /api/v1/orders/customers` - Create a customer
- `GET /api/v1/orders/customers/{customer_id}` - Get customer by ID

## 🔧 Configuration

Key configuration options in `backend/.env`:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: LLM model (default: gpt-4o-mini)
- `OPENAI_EMBEDDING_MODEL`: Embedding model (default: text-embedding-3-small)
- `SQLITE_DB_PATH`: Path to SQLite database
- `CHROMA_DB_PATH`: Path to ChromaDB storage
- `CORS_ORIGINS`: Allowed CORS origins

## 📝 Sample Data

For testing, you can use Dell laptop product manuals:
- Download: https://dl.dell.com/content/manual34122770-latitude-3480-owner-s-manual.pdf?language=en-us
- Upload through the Documents interface

## 🧪 Development

### Running Tests

```bash
cd backend
pytest
```

### Code Structure

- **Agents**: LangGraph workflows for different query types
- **Services**: Business logic and data processing
- **API**: FastAPI route handlers
- **Models**: Pydantic models for data validation
- **DB**: Database initialization and utilities

## 🚧 Future Enhancements

- [ ] Multi-source query support (combining vector DB + SQL)
- [ ] Conversation history and context management
- [ ] Advanced intent classification with confidence scoring
- [ ] Support for additional file formats (DOCX, TXT, etc.)
- [ ] User authentication and authorization
- [ ] Analytics and query performance monitoring
- [ ] Custom embedding model support
- [ ] Multi-language support

## 📄 License

This project is part of an AI engineering demonstration.

## 🤝 Contributing

This is a demonstration project. For production use, consider:
- Adding comprehensive error handling
- Implementing rate limiting
- Adding authentication/authorization
- Setting up proper logging and monitoring
- Adding unit and integration tests
- Implementing caching strategies

---

**Built with ❤️ using LangGraph, FastAPI, ChromaDB, SQLite, and Angular**
