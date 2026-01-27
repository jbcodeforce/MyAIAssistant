# RAG Testing Guide

This guide explains how to test the RAG (Retrieval-Augmented Generation) system using environment engineering content.

## Overview

The RAG testing setup includes:

- **Document Specifications**: JSON file with curated environment engineering URLs
- **Test Script**: Python script to query and validate RAG functionality
- **Documentation**: This guide with step-by-step instructions

## Prerequisites

1. Backend server running and accessible
2. Database initialized with knowledge items
3. RAG service configured and ready

## Setup

### 1. Process Environment Engineering Documents

The test dataset includes 8 curated URLs from EPA covering water treatment and air quality topics.

Process the documents using the CLI:

```bash
ai-assist knowledge process data/environment_engineering_specs.json
```

This will:
- Create knowledge items in the database for each URL
- Fetch and load web content
- Chunk the content into searchable segments
- Generate embeddings and store in ChromaDB
- Index all documents

### 2. Verify Processing

Check that documents were processed successfully:

```bash
ai-assist knowledge stats
```

Expected output:
- Total chunks: Should be > 0
- Unique documents: Should match the number of URLs (8)
- Collection name: `knowledge_base`
- Embedding model: `all-MiniLM-L6-v2`

### 3. Dry Run (Optional)

To validate the JSON file without processing:

```bash
ai-assist knowledge process data/environment_engineering_specs.json --dry-run
```

This shows what would be processed without making API calls.

## Testing Queries

### Using the Test Script

The test script provides several ways to query the RAG system:

#### Run All Test Queries

```bash
python scripts/test_rag_queries.py
```

This runs a comprehensive set of test queries covering:
- Water treatment topics
- Air quality topics
- Category-filtered searches
- General queries

#### Show Statistics Only

```bash
python scripts/test_rag_queries.py --stats
```

#### Run a Single Query

```bash
python scripts/test_rag_queries.py --query "How does water treatment work?"
```

#### Query with Category Filter

```bash
python scripts/test_rag_queries.py --query "What are PM2.5 standards?" --category air_quality
```

#### Custom Backend URL

```bash
python scripts/test_rag_queries.py --backend-url http://localhost:8000/api
```

### Using the CLI

You can also query via the backend API directly using curl or httpx:

```bash
# GET endpoint
curl "http://localhost:8000/api/rag/search?q=water+treatment&n=5"

# POST endpoint
curl -X POST "http://localhost:8000/api/rag/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are drinking water standards?", "n_results": 5, "category": "water_treatment"}'
```

## Expected Results

### Query Categories

**Water Treatment Queries:**
- "How does water treatment work?"
- "What are drinking water standards?"
- "What contaminants are regulated in drinking water?"

Expected: Results from EPA water treatment pages with scores > 0.5

**Air Quality Queries:**
- "What are PM2.5 air quality standards?"
- "What are the criteria air pollutants?"
- "How is indoor air quality monitored?"

Expected: Results from EPA air quality pages with scores > 0.5

### Score Interpretation

- **0.9+**: Highly relevant match
- **0.7-0.9**: Good match
- **0.5-0.7**: Partial match
- **<0.5**: Weak match (may indicate need for more content or better query)

### Validation Checklist

- [ ] All documents indexed successfully (check stats)
- [ ] Water treatment queries return relevant results
- [ ] Air quality queries return relevant results
- [ ] Category filtering works correctly
- [ ] Scores are reasonable (>0.5 for relevant queries)
- [ ] Content previews show relevant text snippets

## Troubleshooting

### No Results Returned

**Problem**: Queries return no results

**Solutions**:
1. Verify documents were indexed: `ai-assist knowledge stats`
2. Check backend is running: `curl http://localhost:8000/health`
3. Verify ChromaDB collection exists in `data/chroma/`
4. Re-index documents: `ai-assist knowledge process data/environment_engineering_specs.json --force`

### Low Scores

**Problem**: Results have low relevance scores (<0.5)

**Solutions**:
1. Check if query matches document topics
2. Try more specific queries
3. Verify documents were fully loaded (check for errors during indexing)
4. Consider adding more relevant content

### Connection Errors

**Problem**: Cannot connect to backend

**Solutions**:
1. Verify backend is running: `ps aux | grep uvicorn` or check logs
2. Check backend URL: Default is `http://localhost:8000/api`
3. Set custom URL: `export AI_ASSIST_BACKEND_URL=http://your-backend:8000/api`
4. Check firewall/network settings

### Document Loading Errors

**Problem**: Some documents fail to load

**Solutions**:
1. Verify URLs are accessible: `curl <url>` in terminal
2. Check for authentication requirements (should be public)
3. Verify network connectivity
4. Check backend logs for specific error messages
5. Some URLs may have changed - update JSON file if needed

## Test Queries Reference

### Water Treatment

```bash
# General water treatment
python scripts/test_rag_queries.py --query "How does water treatment work?"

# Drinking water standards
python scripts/test_rag_queries.py --query "What are drinking water standards?" --category water_treatment

# Water contaminants
python scripts/test_rag_queries.py --query "What contaminants are regulated in drinking water?" --category water_treatment
```

### Air Quality

```bash
# PM2.5 standards
python scripts/test_rag_queries.py --query "What are PM2.5 air quality standards?" --category air_quality

# Criteria pollutants
python scripts/test_rag_queries.py --query "What are the criteria air pollutants?"

# Indoor air quality
python scripts/test_rag_queries.py --query "How is indoor air quality monitored?" --category air_quality
```

## Advanced Testing

### Testing with Custom Content

To test with your own content:

1. Create a new JSON file following the same structure
2. Update `document_type`, `uri`, `collection`, and metadata
3. Process with: `ai-assist knowledge process your_file.json`
4. Run test queries against your content

### Performance Testing

Monitor query performance:

```bash
time python scripts/test_rag_queries.py --query "water treatment"
```

Expected: Queries should complete in < 2 seconds for typical searches.

### Batch Testing

Run multiple queries programmatically:

```python
from scripts.test_rag_queries import RAGTester

tester = RAGTester()
queries = ["query1", "query2", "query3"]
for q in queries:
    results = tester.search(q)
    print(f"Query: {q}, Results: {len(results['results'])}")
```

## Next Steps

After successful testing:

1. Add more documents to expand knowledge base
2. Fine-tune chunk size and overlap if needed
3. Test with production queries
4. Monitor search quality and relevance scores
5. Consider adding more categories or topics

## References

- [RAG System Documentation](../implementation/rag.md)
- [Knowledge Base Documentation](../implementation/knowledge.md)
- [Agent Core Documentation](../implementation/agent_core.md)
