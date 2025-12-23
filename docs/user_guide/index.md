# User Guide

This guide covers how to use the main features of MyAIAssistant. As a web application, the configuration is set using a `config.yaml`, to specify where to access the database for the main entities, like tasks, organizations, documents, and where to access the vector store to keep document chunks and embeddings.

As of now this tool should run locally. LLM is done locally, or remotely using one of the existing service.

## Setup

### configuration

There is a `config.yaml` to set access to the database and vector DB used. There is no need to change anything for first utilisation. There is a default database to support this user guide.

In the future, a user may change the following elements of the config.yaml, to separate knowledge and project per major context. Like a student working for his/her university projects, then later for a company during a internship. The student may use two databases for that. The same way, a consultant who wants to have separate databases for very different set of activities linked to different knowledge and customer industry:

```yaml
# Database settings
database_url: "sqlite+aiosqlite:////app/data/myaiassistant.db"

# Knowledge base / Vector store settings
chroma_persist_directory: "/app/data/chroma"
chroma_collection_name: "km-db"
```

* `database_url` can be another name to keep data for a separate context. The data folder will include the database file,
* `chroma_persist_directory:`: the reference to the folder to persiste vector store and document chunks
* `chroma_collection_name`: chrome collection name. From now there is one collection. It may be relevant in the future to support adding more collection and to query at the collection level.


### Launch the application

* If you have docker and docker compose:
   ```bash
   docker-compose up -d
   ```

* If you are on Mac with MacOS Tahoe, and use the [container cli](https://github.com/apple/container): TBD

* Run with python and nodes:
      * Backend:
         ```bash
         cd backend
         uv sync
         uv run uvicorn app.main:app --reload
         ```
      * Frontend:
         ```bash
         cd frontend
         npm install
         npm run dev
         ```

* The application access points:
      - Frontend: [http://localhost:80](http://localhost:80)
      - Backend API: http://localhost:8000
      - API Documentation: http://localhost:8000/docs


## Knowledge Base

The Knowledge Base stores references to documents and web resources that you want to search and query using AI.

### Adding Knowledge Items

1. Navigate to the **Knowledge** page from the main navigation
2. Click **+ Add Knowledge** in the top right
3. Fill in the form:
   - **Title**: A descriptive name for the document
   - **Description**: Optional summary of the content
   - **Document Type**: Choose between Markdown or Website
   - **Source**: For Markdown, enter a local file path or URL. For websites, enter the URL
   - **Category**: Optional grouping (e.g., "Documentation", "Reference")
   - **Tags**: Comma-separated keywords for filtering
4. Click **Create** to save

### Indexing Documents

Before you can search or chat with your knowledge base, documents must be indexed:

- **Index a single item**: Click the index button (magnifying glass with plus) on any row
- **Index all items**: Click **Index All** in the header to index all active/pending items

Indexing extracts text from documents and creates vector embeddings for semantic search.

### Filtering Knowledge Items

Use the filter bar to narrow down items:

- **Type**: Filter by Markdown or Website
- **Status**: Filter by Active, Pending, Error, or Archived
- **Category**: Filter by assigned category
- **Tag**: Search by tag name

Click on any tag in the table to filter by that tag.

---

## Querying the Knowledge Base (RAG Chat)

Once you have indexed documents, you can ask questions and get AI-powered answers based on your knowledge base content.

### Starting a Chat Session

1. Go to the **Knowledge** page
2. Click the green **Ask AI** button in the header
3. A chat window opens where you can ask questions

### Asking Questions

Type your question in the input field and press Enter or click the send button. The AI will:

1. Search your indexed documents for relevant content
2. Use the most relevant passages as context
3. Generate an answer based on that context

### Suggested Prompts

When you first open the chat, you'll see suggested prompts to get started:

- "What topics are covered?" - Get an overview of your knowledge base
- "Summarize main points" - Get a summary of key information
- "Key concepts" - Identify important concepts from your documents

### Viewing Sources

Each AI response shows which documents were used to generate the answer:

1. Below the response, click **"X sources used"** to expand
2. View the source document title, relevance score, and snippet
3. Use this to verify the information or explore the original document

### Tips for Better Results

- **Be specific**: "How do I configure Docker deployment?" works better than "Docker?"
- **Ask one question at a time**: Complex multi-part questions may get incomplete answers
- **Reference context**: "Based on the API documentation, how do I..." helps focus the search
- **Index relevant documents**: The AI can only answer based on what's been indexed

### Conversation Context

The chat maintains conversation history within a session. You can:

- Ask follow-up questions that reference previous answers
- Clarify or drill down into topics
- Request more detail on specific points

The conversation resets when you close the chat window.

---

## Todo Management

### The Eisenhower Matrix

The Dashboard displays todos in a 2x2 matrix based on urgency and importance:

| | Urgent | Not Urgent |
|---|--------|------------|
| **Important** | Do First | Schedule |
| **Not Important** | Delegate | Eliminate |

### Creating Todos

1. Click **+ Add Todo** or click in any quadrant
2. Enter the todo title and optional description
3. Set urgency and importance levels
4. Click **Create**

### Moving Todos

Drag and drop todos between quadrants to change their priority classification.

### Completing Todos

Click the checkbox on a todo card to mark it complete. Completed todos move to the archive.

### Unclassified Todos

Todos without urgency/importance settings appear in the **Unclassified** view. Assign them to quadrants to include them in the matrix.

---

## Chat with Todos

From the Dashboard, you can chat with the AI about specific tasks:

1. Click the chat icon on any todo card
2. Ask questions about how to approach the task
3. The AI uses your knowledge base to provide relevant context and suggestions

This helps when planning complex tasks by connecting your reference materials to your action items.


--- 

## Vectorize a folder


* In backend folder

```sh
# First run - creates all documents
uv run python -m tools.vectorize_folder /path/to/docs --extensions .md .txt .html --chunk-size 500 --category "Docs" --tags "api,reference"

# Re-run - skips unchanged files
uv run python -m tools.vectorize_folder /path/to/docs --category "Docs" --tags "api,reference"

# Force re-index everything
uv run python -m tools.vectorize_folder /path/to/docs --force

# View current collection stats
python -m tools.vectorize_folder --stats-only .
```

* Tools:
    ```sh
    cd backend
    uv run tools/vectorize_folder.py
    ```
