# Create Knowledge base

Tool to vectorize folder content into ChromaDB for RAG.

This script scans a folder for supported documents (markdown, text, HTML),
processes them through the RAG pipeline, stores embeddings in ChromaDB,
and saves metadata to the knowledge base database.

The tool is reentrant: re-running it will update existing documents if their
content has changed, and skip unchanged files.

## Features

Code is: `backend/tools/vectorize_folder.py`

This CLI tool leverages the existing backend services:

* DocumentLoader for loading markdown and HTML files
* RecursiveTextSplitter for chunking content
* ChromaDB with all-MiniLM-L6-v2 embeddings


* Recursive folder scanning for supported file types
* Configurable chunk size and overlap
* Category and tags metadata support
* Progress logging with file-by-file status
* Collection statistics view
* Handles .md, .markdown, .txt, and .html files
