# AI Agent API Endpoints

## Overview

Phase 2.5 API Integration is complete! The AI agent is now accessible via REST API endpoints.

## Endpoints

### 1. POST `/api/ai/summarize`

Generate AI-powered summaries based on query type.

**Request Body:**
```json
{
  "query_type": "employee",  // Options: "employee", "department", "time_period", "status"
  "employee_id": 1,          // Optional: Employee ID
  "employee_name": "John Doe", // Optional: Employee name
  "date_range_start": "2024-01-01", // Optional: Start date
  "date_range_end": "2024-01-31",   // Optional: End date
  "filters": {}              // Optional: Additional filters
}
```

**Response:**
```json
{
  "success": true,
  "result": "AI-generated summary text or structured data",
  "metadata": {
    "query_type": "employee_summary",
    "employee_id": 1,
    "date_range": null,
    "format": "structured"
  },
  "error": null
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/ai/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "employee",
    "employee_id": 1
  }'
```

---

### 2. POST `/api/ai/report`

Generate AI-powered comprehensive reports.

**Request Body:**
```json
{
  "report_type": "financial",  // Options: "financial", "operational", "analytical"
  "date_range_start": "2024-01-01", // Optional: Start date
  "date_range_end": "2024-01-31",   // Optional: End date
  "employee_id": 1,              // Optional: Filter by employee
  "include_charts": false        // Optional: Include chart data
}
```

**Response:**
```json
{
  "success": true,
  "result": "AI-generated report with analysis",
  "metadata": {
    "query_type": "financial_report",
    "date_range": ["2024-01-01", "2024-01-31"],
    "employee_id": null,
    "format": "structured",
    "include_charts": false
  },
  "error": null
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/ai/report" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "financial",
    "date_range_start": "2024-01-01",
    "date_range_end": "2024-01-31"
  }'
```

---

### 3. POST `/api/ai/query`

Natural language query interface - ask questions in plain English!

**Request Body:**
```json
{
  "query": "What is the total amount of pending advances?",
  "context": {  // Optional: Additional context
    "employee_id": 1,
    "employee_name": "John Doe"
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": "AI-generated response to your query",
  "metadata": {
    "query": "What is the total amount of pending advances?",
    "context_used": true,
    "context_docs_count": 5
  },
  "error": null
}
```

**Example Queries:**
- "What is the total amount of pending advances?"
- "Show me a summary for employee John Doe"
- "Generate a financial report for last month"
- "What are the trends in advance requests?"
- "Which employees have exceeded their salary?"

**Example:**
```bash
curl -X POST "http://localhost:8000/api/ai/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me a summary for employee John Doe"
  }'
```

---

## Rate Limiting

- `/api/ai/summarize`: 10 requests per minute
- `/api/ai/report`: 10 requests per minute
- `/api/ai/query`: 20 requests per minute

## Error Handling

All endpoints return a consistent error format:

```json
{
  "success": false,
  "result": null,
  "error": "Error message describing what went wrong",
  "metadata": {}
}
```

## Testing

### Using Python requests:

```python
import requests

# Test summarize endpoint
response = requests.post(
    "http://localhost:8000/api/ai/summarize",
    json={
        "query_type": "employee",
        "employee_id": 1
    }
)
print(response.json())

# Test report endpoint
response = requests.post(
    "http://localhost:8000/api/ai/report",
    json={
        "report_type": "financial",
        "date_range_start": "2024-01-01",
        "date_range_end": "2024-01-31"
    }
)
print(response.json())

# Test query endpoint
response = requests.post(
    "http://localhost:8000/api/ai/query",
    json={
        "query": "What is the total amount of pending advances?"
    }
)
print(response.json())
```

### Using FastAPI Interactive Docs:

1. Start the server: `python main.py` or `uvicorn main:app --reload`
2. Navigate to: `http://localhost:8000/docs`
3. Find the AI endpoints under the "ai" tag
4. Click "Try it out" to test each endpoint

## Integration Notes

- All endpoints require a valid database session
- The AI agent uses RAG (Retrieval Augmented Generation) to enhance responses
- Responses are generated using the configured LLM (OpenAI or Hugging Face)
- The knowledge base must be built before using these endpoints: `python scripts/build_knowledge_base.py`

## Next Steps

- Add authentication/authorization to restrict access
- Implement caching for common queries
- Add streaming responses for long reports
- Enhance natural language query parsing
- Add support for more query types and report types
