# MyAIAssistant

???- info "Versions"
    Creation Dec 2025: tasks management, org, project, meeting management.

    Update 02/2026: User Guide, agents management, workspace management, CLI


## Project Goals

MyAIAssistant helps users organize tasks, reference subject-matter knowledge, and leverage AI for semantic search, note summarization, task extraction and recommendations. The tool links knowledge artifacts to tasks to provide better context when addressing work.

Based on [Stephen Covey's "7 Habits of Highly Effective People"](https://jbcodeforce.github.io/leadership/7_habits/) the system helps manage priorities efficiently using the Eisenhower Matrix (Urgent/Important classification).

![](./images/aia_dashboard.png)

## Project Principles

1. **Run locally** - All core features work without external API dependencies
2. **External configuration** - Environment-based configuration for flexibility
3. **Privacy-first** - Data stays on local infrastructure
4. **Efficient prioritization** - Eisenhower Matrix helps focus on high-impact work

With a drag-and-drop user interface it is easy to continuously re-prioritize tasks. With AI assistant, the tool helps to better run a working day, query what was done last wee, last month, last quarter...

The goal is to run locally, with local or remote LLM, and using isolate environment or workspace to separate works, from learning or home work.

[Access the webApp local once started](http://localhost:80).

## Why I built this?

There are ton of to do apps, why a new one? The main drivers for creating this app:

* How I can augment myself and my day-to-day outcomes?
* Address what are the things I can do more, related ot what I value? I think the answer is learning, but how to organize time for it, and how to really track, learning activities? 
* I used paper or digital notes based on the  Eisenhower matrix to track my tasks, but I think, AI can enhance the plannification, the decomposition and the semantic search of my current knowledge, my past work, and projects.
* Address how to maximize my time on desired activities and minimize time on overhead?
* While tracking task with app, it is easy to build weekly report, an essential tool for management. 
* NotebookLM, Glean, RAG, GraphRAG... are excellent tools to start managing knowledge and query it, but they are not related to my work directly. I think it may be possible to fill this gap, by linking all the information about organizations, projects, tasks, assets all together.
* The tool should also helps to address the efficient use of AI, by helping the step of clear thinking (getting a clear statement of the problem), clear writing (by formalizing in simple sentences the problem, to explain what you want to do), to build prompts for more efficient AI.
* Apply agentic architecture for a simple day-to-day application, as a learning experience.


## Core Features

| Feature | Status | Description |
| ------- | ------ | ----------- |
| Kanban-style Todo Management | Completed | Todos categorized by Importance/Urgency (Eisenhower Matrix) |
| Organization Management | Completed | Track organizations with stakeholders, team, strategy, and related products |
| Project Management | Completed | Manage projects with status lifecycle (Draft, Active, On Hold, Completed, Cancelled) linked to organizations |
| Knowledge Base | Completed | Metadata storage referencing documents, notes, and website links |
| Semantic Search (RAG) | Completed | AI-powered search across the knowledge base using embeddings |
|Agents and  LLM Chat Support | Completed | AI chat for task planning and knowledge base queries, and agents catalog for different expertize |
| Task/Note Integration | Planned | Automatic linking of Todos to relevant knowledge artifacts |


## Quick Start

[See user guide](./user_guide/index.md)

## Understanding the implementation

[See design and implementation chapter](./implementation/index.md).


## Activities

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
