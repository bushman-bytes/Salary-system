# AI Agent Architecture Overview

## Executive Summary

The AI agent is a **RAG (Retrieval Augmented Generation)** system that uses LangChain to generate intelligent summaries and reports. It does NOT use multi-sub-agents, tools, or function calling. The architecture is linear: **Database → RAG → LLM → Response**. Response times may be slow due to sequential processing and no caching.

---

## 1. Data Collection for RAG (Knowledge Base Building)

### Process Flow

```
Database (PostgreSQL) → DocumentLoader → Documents → Embeddings → Vector Store (ChromaDB)
```

### How Data is Collected

The **`DocumentLoader`** (`app/ai_agent/document_loader.py`) extracts data from the database in three ways:

1. **Employee Summaries** (`load_employee_summaries`)
   - Queries all employees from the database
   - For each employee, fetches:
     - Related advances (all advance requests)
     - Related bills (all bills)
     - Attendance data (off_days)
   - Calculates statistics:
     - Total advances, total advance amount
     - Pending/approved/denied counts
     - Total bills and bill amounts
   - Creates text documents with this information

2. **Financial Patterns** (`load_financial_patterns`)
   - Loads last 12 months of advances and bills
   - Groups by month
   - Calculates monthly patterns (totals, trends)
   - Creates monthly summary documents

3. **Advance Patterns** (`load_advance_patterns`)
   - Analyzes all advances by status
   - Groups by common reasons
   - Creates pattern documents

### Document Structure

Each document contains:
- **`page_content`**: Text representation of the data
- **`metadata`**: 
  - `type`: "employee_summary", "financial_pattern", "advance_pattern", etc.
  - `employee_id`, `employee_name`, `role` (for employee docs)
  - `month` (for financial patterns)
  - `created_at` timestamp

### Running the Build Script

```bash
python scripts/build_knowledge_base.py
```

This script:
1. Connects to the database
2. Uses `KnowledgeBaseBuilder` to load documents
3. Adds domain knowledge (static documents about system operations)
4. Generates embeddings and stores in ChromaDB

---

## 2. Vector Database Updates

### Storage Technology

- **Vector Store**: ChromaDB (local or cloud)
- **Embedding Models**:
  - OpenAI: `text-embedding-ada-002` (1536 dimensions)
  - Hugging Face: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)

### Collections

Different collections are used based on the AI provider:
- **OpenAI**: Collection name `salary_queries`
- **Hugging Face**: Collection name `salary_queries_hugFace`

This is because embedding dimensions differ between providers.

### Update Mechanism

**Currently, there is NO automatic update mechanism.** The knowledge base must be manually rebuilt:

1. When new data is added to the database
2. When switching AI providers (different embeddings)
3. Periodically to refresh patterns

**The system does NOT automatically sync database changes to the vector store.**

### Manual Update Process

```python
from app.ai_agent.knowledge_base_builder import KnowledgeBaseBuilder
from app.models.schema import get_session, get_engine
from app.config.config import DATABASE_URL

engine = get_engine(DATABASE_URL)
session = get_session(engine)
builder = KnowledgeBaseBuilder(session)

# Refresh knowledge base
result = builder.refresh_knowledge_base()
```

---

## 3. Prompt System

### Prompt Templates

Located in `app/ai_agent/prompt_templates.py`, there are three main templates:

1. **Employee Summary Template**
   - System prompt: Defines role as AI assistant for salary management
   - Context injection: Retrieved RAG context + employee data
   - Output format: Structured JSON with sections (overview, advance_requests_summary, bills_summary, etc.)

2. **Financial Report Template**
   - Includes historical patterns from RAG
   - Current financial data
   - Output format: Structured JSON (summary, advances_analysis, bills_analysis, trends, anomalies, etc.)

3. **General Query Template**
   - For ad-hoc queries
   - Includes retrieved context and query data

### Prompt Construction Flow

```
User Query → QueryProcessor (fetches DB data) → RAG Engine (retrieves context) 
→ Prompt Template (combines everything) → LLM
```

**Example Prompt Structure:**
```
System: You are an AI assistant for a salary management system...

Context from knowledge base:
[Retrieved relevant documents from vector store]

Employee Data:
{JSON with actual database results}

Query Parameters:
- Employee: John Doe
- Time Period: 2024-01-01 to 2024-12-31

Generate a summary that includes:
1. Overview...
2. Advance requests...
...
```

### No Few-Shot Examples

The prompts do NOT include few-shot examples. They rely on:
- RAG context for examples
- Domain knowledge documents
- Structured output schemas (Pydantic models)

---

## 4. Tools & Function Calling

### ❌ NO Tools Are Used

The AI agent does NOT implement:
- Function calling
- Tool use capabilities
- External API tools
- Database query tools (LLM doesn't query DB directly)

### Database Interaction Pattern

Instead, the system uses a **pre-query pattern**:

1. **QueryProcessor** (`app/ai_agent/query_processor.py`) queries the database **before** calling the LLM
2. Results are formatted as JSON strings
3. This JSON is injected into the prompt
4. LLM generates text based on the provided data

**The LLM never directly queries the database. All data is fetched programmatically and provided in prompts.**

---

## 5. LLM-Database Interaction

### Architecture: Separated Concerns

```
┌─────────────────────────────────────────┐
│  User Request                           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  QueryProcessor                         │
│  - Fetches data from PostgreSQL         │
│  - Formats as JSON                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  RAG Engine                             │
│  - Retrieves context from ChromaDB      │
│  - Formats context string               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Prompt Builder                         │
│  - Combines: context + data + query     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  LLM (OpenAI/Hugging Face)              │
│  - Generates response                   │
└─────────────────────────────────────────┘
```

### Query Processing

The **QueryProcessor** provides two main methods:

1. **`get_employee_data()`**
   - Queries employee, advances, bills, attendance
   - Filters by employee_id or name
   - Optional date range filtering
   - Returns structured dictionary

2. **`get_financial_data()`**
   - Aggregates advances and bills
   - Optional date range and employee filtering
   - Calculates statistics (totals, approval rates)

### Why This Design?

- **Security**: LLM doesn't have direct DB access
- **Control**: All queries are predefined and validated
- **Performance**: Can optimize queries independently
- **Reliability**: No risk of LLM generating invalid SQL

---

## 6. Multi-Sub-Agents

### ❌ NO Multi-Agent System

The system does NOT use:
- Multiple specialized agents
- Agent orchestration
- Agent-to-agent communication
- Hierarchical agent structures

### Single Agent Architecture

There is **one main AI agent** (`AIAgent` class) that:
- Coordinates all components
- Uses different chains for different tasks
- But operates as a single unified system

### Chains (Not Agents)

The system uses **LangChain chains** (not agents):

1. **RAGChain**: Query → Context → LLM → Response
2. **StructuredOutputChain**: For JSON output parsing
3. **MultiStepChain**: For multi-step reasoning (sequential, not parallel)

These are **chains**, not **agents**—they don't make autonomous decisions or use tools.

---

## 7. Performance Issues: Why It's Slow

### Current Bottlenecks

1. **Sequential Processing**
   ```
   DB Query → RAG Retrieval → Embedding → LLM Call
   ```
   Each step waits for the previous one to complete.

2. **No Caching**
   - No caching of LLM responses
   - No caching of RAG retrievals
   - Every query re-fetches everything

3. **Embedding Generation**
   - If using local Hugging Face embeddings, each query may generate embeddings on-the-fly
   - OpenAI embeddings are faster (API calls) but still add latency

4. **Multiple LLM Calls**
   - Structured output chains may retry parsing (up to 3 attempts)
   - If structured output fails, falls back to regular chain (2 LLM calls)

5. **Vector Search**
   - ChromaDB similarity search
   - Multiple query expansions (if hybrid search enabled)
   - Context formatting

6. **No Parallel Processing**
   - DB queries and RAG retrieval could be parallel
   - Currently sequential

### Estimated Latency Breakdown

For a typical employee summary:
- Database query: ~100-500ms
- RAG retrieval + formatting: ~200-800ms
- LLM call: ~2-10 seconds (depends on provider/model)
- **Total: ~3-12 seconds**

### Optimization Opportunities

1. **Add caching layer** (Redis) for common queries
2. **Parallel processing**: Run DB query and RAG retrieval simultaneously
3. **Streaming responses**: Stream LLM output as it generates
4. **Pre-compute embeddings**: Cache query embeddings
5. **Reduce context size**: Limit retrieved documents
6. **Use smaller/faster models** for simple queries

---

## 8. Visualizations

### ❌ NO Visualization Generation

The system does NOT generate:
- Charts
- Graphs
- Visual reports
- Plotly/Matplotlib outputs
- HTML visualizations

### Current Output

The AI agent returns:
- **Text summaries** (structured or unstructured)
- **JSON data** (raw database results)
- **No visual elements**

### Where Visuals Would Be Added

If you want to add visualizations, you would need to:

1. **Generate charts in the frontend**
   - Use JavaScript libraries (Chart.js, D3.js)
   - Parse JSON data from API
   - Render charts client-side

2. **Add visualization generation in Python**
   - Use Matplotlib/Plotly to generate charts
   - Save as images or HTML
   - Include in report response

3. **Use LLM to generate visualization code**
   - Have LLM output Chart.js/Plotly code
   - Execute in frontend
   - **This is NOT currently implemented**

### Recommended Approach

Since the system already returns structured JSON with financial data, the best approach is:
- **Frontend visualization**: Parse JSON, render charts client-side
- **Backend visualization**: Generate chart images in `ReportGenerator` using Plotly/Matplotlib
- **LLM-guided visualization**: Have LLM suggest chart types based on data

---

## 9. Complete Query Flow

### Example: Employee Summary Request

```
1. User Request
   └─> employee_id=5, date_range=(2024-01-01, 2024-12-31)

2. ReportGenerator.generate_employee_summary()
   ├─> QueryProcessor.get_employee_data()
   │   ├─> DB: SELECT employee WHERE id=5
   │   ├─> DB: SELECT advances WHERE employee_id=5 AND date_range
   │   ├─> DB: SELECT bills WHERE employee_id=5 AND date_range
   │   └─> Format as JSON
   │
   ├─> RAGEngine.retrieve_context()
   │   ├─> Build query: "employee John Doe summary"
   │   ├─> Vector search: similarity_search(query, k=5)
   │   ├─> Format context: format_context(documents)
   │   └─> Return formatted string
   │
   ├─> Build Prompt
   │   ├─> System prompt (from template)
   │   ├─> RAG context
   │   ├─> Employee data (JSON)
   │   └─> Instructions
   │
   └─> LLM Call
       ├─> Try: StructuredOutputChain (with retries)
       │   └─> If fails → Fallback: RAGChain
       └─> Return response

3. Response Format
   {
     "summary": {...} or "text string",
     "data": {employee_data_json},
     "metadata": {...}
   }
```

---

## 10. Configuration

### Key Settings (`app/ai_agent/config.py`)

- **`AI_PROVIDER`**: "openai" or "huggingface"
- **`RAG_TOP_K`**: Number of documents to retrieve (default: 5)
- **`RAG_SIMILARITY_THRESHOLD`**: Minimum similarity score (default: 0.7)
- **`ENABLE_HYBRID_SEARCH`**: Use query expansion (default: true)
- **`MAX_TOKENS`**: Max LLM output tokens (default: 2000)
- **`TEMPERATURE`**: LLM creativity (default: 0.3 for consistency)

---

## Summary

### What the Agent Does ✅
- RAG-based context retrieval
- LLM-powered report generation
- Structured output parsing
- Multi-provider support (OpenAI/Hugging Face)

### What the Agent Does NOT Do ❌
- Multi-agent systems
- Tool/function calling
- Direct database queries from LLM
- Automatic knowledge base updates
- Visualization generation
- Caching or performance optimization
- Parallel processing

### Key Architecture Decisions

1. **Pre-query pattern**: Database is queried before LLM call
2. **Single agent**: No multi-agent orchestration
3. **Manual updates**: Knowledge base requires manual rebuilding
4. **Sequential processing**: No parallelization
5. **No tools**: LLM generates text only

### Recommendations for Improvement

1. **Add caching** for common queries
2. **Parallelize** DB + RAG retrieval
3. **Auto-update** knowledge base on data changes
4. **Add visualizations** in frontend or backend
5. **Implement streaming** for faster perceived response
6. **Add monitoring** to identify slow components

---

**Last Updated**: 2024-01-XX  
**Architecture Version**: Phase 2 (Single Agent, RAG-based)
