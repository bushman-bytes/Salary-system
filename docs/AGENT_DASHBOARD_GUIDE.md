# AI Agent Dashboard Guide

## Overview

The AI Agent Dashboard is a dedicated testing interface for Phase 2 AI features. It provides an easy way to test all three AI endpoints before integrating them into Phase 3 (notifications).

## Access

1. Start your FastAPI server:
   ```bash
   python main.py
   # or
   uvicorn main:app --reload
   ```

2. Navigate to:
   ```
   http://localhost:8000/agent-dashboard
   ```

## Features

### 1. 📊 Summarize Tab

Generate AI-powered summaries for different query types.

**Query Types:**
- **Employee Summary**: Get a comprehensive summary for a specific employee
- **Department Summary**: Aggregate statistics for a department (coming soon)
- **Time Period Summary**: Summary for a specific date range
- **Status Summary**: Summary of pending/completed transactions (coming soon)

**How to Use:**
1. Select a query type
2. Optionally provide:
   - Employee ID or Name
   - Date range (start and end dates)
3. Click "Generate Summary"
4. View the AI-generated result

**Example:**
- Query Type: `Employee Summary`
- Employee ID: `1`
- Result: AI-generated summary with employee data, advances, bills, and insights

---

### 2. 📈 Report Tab

Generate comprehensive AI-powered reports.

**Report Types:**
- **Financial Report**: Financial analysis with trends and projections
- **Operational Report**: Operational metrics and workflow status (coming soon)
- **Analytical Report**: Trend analysis and anomaly detection (coming soon)

**How to Use:**
1. Select a report type
2. Optionally provide:
   - Date range
   - Employee ID filter
   - Check "Include Chart Data" for visualization data
3. Click "Generate Report"
4. View the comprehensive report

**Example:**
- Report Type: `Financial Report`
- Date Range: `2024-01-01` to `2024-01-31`
- Result: Financial analysis with trends, anomalies, and recommendations

---

### 3. 💬 Natural Language Query Tab

Ask questions in plain English and get AI-powered responses.

**How to Use:**
1. Type your question in the text area
2. Optionally provide context:
   - Employee ID
   - Employee Name
3. Click "Ask Question"
4. View the AI-generated response

**Example Queries:**
- "What is the total amount of pending advances?"
- "Show me a summary for employee John Doe"
- "Generate a financial report for last month"
- "What are the trends in advance requests?"
- "Which employees have exceeded their salary?"

**Tips:**
- Click on example queries to auto-fill them
- Be specific in your questions for better results
- Use employee names or IDs in context for employee-specific queries

---

## UI Features

### Visual Design
- **Dark Theme**: Matches existing dashboard design system
- **Responsive**: Works on desktop, tablet, and mobile
- **Modern UI**: Clean, professional interface with smooth animations

### User Experience
- **Tab Navigation**: Easy switching between different AI features
- **Loading States**: Visual feedback during API calls
- **Error Handling**: Clear error messages if something goes wrong
- **Result Display**: 
  - Formatted JSON for structured data
  - Plain text for natural language responses
  - Metadata display showing query details

### Interactive Elements
- **Example Queries**: Click to auto-fill common questions
- **Form Validation**: Required fields are validated
- **Status Badges**: Visual indicators for success/error states

---

## Testing Workflow

### Before Testing
1. **Build Knowledge Base**: Ensure your vector store is populated
   ```bash
   python scripts/build_knowledge_base.py
   ```

2. **Verify Configuration**: Check that AI provider settings are correct in `.env`

3. **Start Server**: Make sure the FastAPI server is running

### Testing Steps

1. **Start with Natural Language Query**
   - Easiest to test
   - Try: "What is the total amount of pending advances?"

2. **Test Employee Summary**
   - Use an existing employee ID from your database
   - Try with and without date ranges

3. **Test Financial Report**
   - Generate a report for a specific time period
   - Compare results with actual database data

4. **Iterate and Refine**
   - Try different queries
   - Test edge cases
   - Verify accuracy of responses

---

## Troubleshooting

### "No result returned"
- Check that the knowledge base is built
- Verify database connection
- Check API endpoint logs

### "Error generating summary"
- Verify employee ID exists in database
- Check date range is valid
- Review server logs for detailed error

### "Failed to parse structured output"
- This is normal - the system falls back to text output
- Structured output requires specific LLM responses

### Slow Responses
- First request may be slower (cold start)
- Check LLM provider API status
- Verify network connection

---

## Integration Notes

This dashboard is designed for **testing only**. For Phase 3 integration:

1. **Extract UI Components**: Reuse form components in main dashboards
2. **Add to Navigation**: Add AI features to admin/manager dashboards
3. **Customize Output**: Format results for your specific use case
4. **Add Permissions**: Restrict access based on user roles
5. **Add Caching**: Cache common queries for better performance

---

## Next Steps

After testing in the Agent Dashboard:

1. ✅ Verify all endpoints work correctly
2. ✅ Test with real data from your database
3. ✅ Refine prompts if needed
4. ✅ Plan Phase 3 integration
5. ✅ Design UI components for main dashboards
6. ✅ Add authentication/authorization
7. ✅ Implement notification triggers

---

## API Endpoints Used

The dashboard uses these endpoints:
- `POST /api/ai/summarize` - Generate summaries
- `POST /api/ai/report` - Generate reports
- `POST /api/ai/query` - Natural language queries

See `docs/AI_API_ENDPOINTS.md` for detailed API documentation.

---

## Support

If you encounter issues:
1. Check browser console for JavaScript errors
2. Check server logs for API errors
3. Verify environment variables are set correctly
4. Ensure knowledge base is built and populated

Happy testing! 🚀
