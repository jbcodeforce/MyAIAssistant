# MyAIAssistant Frontend

Vue.js frontend for managing todos using the Eisenhower Matrix.

## Quick Start

```bash
npm install
npm run dev
```

Application available at `http://localhost:3000`.

## Features

- Eisenhower Matrix (4-quadrant) todo organization
- Drag-and-drop between quadrants
- Knowledge base management
- Semantic search interface

## Tech Stack

- Vue 3 with Composition API
- Pinia for state management
- Vue Router for navigation
- Axios for API communication
- Vite for build tooling

## Project Structure

```
src/
├── components/
│   ├── common/      # Header, Modal
│   ├── todo/        # TodoCanvas, TodoCard, TodoForm
│   └── knowledge/   # Knowledge components
├── views/           # Dashboard, Knowledge, Unclassified
├── stores/          # Pinia stores
├── services/        # API client
└── router/          # Vue Router
```

## Documentation

See [full documentation](../docs/) for detailed implementation guides.

