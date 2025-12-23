# Frontend Architecture

The frontend is a single-page application built with Vue 3 and the Composition API.

## Tech Stack

| Technology | Purpose |
| ---------- | ------- |
| Vue 3 | Reactive UI framework with Composition API |
| Pinia | Centralized state management |
| Vue Router | Client-side routing with history mode |
| Axios | HTTP client for API communication |
| Vite | Development server and build tooling |
| TipTap | Rich text editor for todo descriptions |
| Marked | Markdown parsing for chat responses |

## Project Structure

```
frontend/src/
├── main.js              # App entry point and plugin registration
├── App.vue              # Root component with layout
├── router/
│   └── index.js         # Route definitions
├── stores/
│   ├── todoStore.js     # Todo state and API operations
│   ├── knowledgeStore.js # Knowledge base state
│   └── uiStore.js       # Modal and UI state
├── services/
│   └── api.js           # Axios API client
├── views/
│   ├── Dashboard.vue    # Eisenhower Matrix view
│   ├── Unclassified.vue # Unclassified todos
│   ├── ArchivedTodos.vue # Completed/cancelled todos
│   ├── Projects.vue     # Project management
│   ├── Organizations.vue # Organization management
│   ├── Knowledge.vue    # Knowledge base
│   └── Documentation.vue # Embedded MkDocs
└── components/
    ├── common/          # Shared UI components
    ├── todo/            # Todo-related components
    └── chat/            # AI chat components
```

## Application Layout

The app uses a sidebar navigation pattern with a collapsible sidebar.

```
┌─────────────────────────────────────────────────────────────┐
│ TopBar                                                      │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│ Sidebar  │  Main Content Area                               │
│          │  (router-view with transitions)                  │
│          │                                                  │
│          │                                                  │
└──────────┴──────────────────────────────────────────────────┘
```

The `App.vue` component provides:

- Sidebar navigation with collapsible state
- TopBar with settings access
- Vue Router view slot with fade transitions
- Settings modal for preferences

## State Management

### todoStore

Manages todo data and provides computed properties for each Eisenhower quadrant:

```javascript
const todoStore = useTodoStore()

// Computed quadrant filters
todoStore.urgentImportant        // Q1: Do First
todoStore.notUrgentImportant     // Q2: Schedule
todoStore.urgentNotImportant     // Q3: Delegate
todoStore.notUrgentNotImportant  // Q4: Eliminate

// CRUD operations
await todoStore.fetchTodos({ status: 'Open,Started', limit: 500 })
await todoStore.createTodo({ title: 'New task', urgency: 'Urgent', importance: 'Important' })
await todoStore.updateTodo(id, { status: 'Completed' })
await todoStore.deleteTodo(id)
```

### uiStore

Controls modal visibility and UI state:

```javascript
const uiStore = useUiStore()

uiStore.openCreateModal()
uiStore.openEditModal(todoId)
uiStore.closeCreateModal()
```

## API Service

The `api.js` module configures Axios and exports typed API clients:

```javascript
import { todosApi, knowledgeApi, ragApi, chatApi, settingsApi } from '@/services/api'

// Todo operations
await todosApi.list({ status: 'Open' })
await todosApi.create({ title: 'Task' })
await todosApi.update(id, { status: 'Started' })
await todosApi.delete(id)
await todosApi.listByQuadrant('Urgent', 'Important')

// Chat operations
await chatApi.sendMessage(todoId, 'Help me with this task')
await chatApi.ragChat('Search my knowledge base')
```

The API base URL is `/api`, which Vite proxies to the backend during development.

## Routing

Routes are defined in `router/index.js` with page title metadata:

| Path | Component | Description |
| ---- | --------- | ----------- |
| `/` | Dashboard | Eisenhower Matrix view |
| `/unclassified` | Unclassified | Todos without priority |
| `/archived` | ArchivedTodos | Completed/cancelled todos |
| `/projects` | Projects | Project management |
| `/organizations` | Organizations | Organization management |
| `/knowledge` | Knowledge | Knowledge base CRUD |
| `/documentation` | Documentation | Embedded MkDocs site |

The router uses `createWebHistory()` for clean URLs without hash fragments.

## Key Components

### TodoCanvas

The main dashboard displays todos in a 2x2 Eisenhower Matrix grid. Features:

- Four quadrants with distinct color gradients
- Drag-and-drop between quadrants to update priority
- Card view for 2 or fewer items per quadrant
- Table view for 3+ items with compact display
- Due date badges with color coding (overdue, due soon, later)

### TodoCard

Individual task card with:

- Title and description preview
- Status indicator
- Category badge
- Due date display
- Action buttons (edit, delete, chat, plan)
- Draggable for priority updates

### Sidebar

Collapsible navigation with:

- Logo and collapse toggle
- Nested Tasks submenu (Unclassified, Archived, Projects)
- Direct links (Organizations, Knowledge, Docs)
- New Todo button

## MkDocs Documentation Integration

The project documentation is built with MkDocs and embedded within the Vue application.

### How It Works

The documentation is generated from markdown files in the `docs/` directory using MkDocs with the Material theme. The generated static site is then served alongside the Vue frontend.

### Development Mode

During development, Vite serves the MkDocs `site/` directory via a custom plugin:

```javascript
// vite.config.js
function serveMkDocs() {
  return {
    name: 'serve-mkdocs',
    configureServer(server) {
      const siteDir = resolve(__dirname, '../site')
      const serve = sirv(siteDir, { dev: true, single: false })
      server.middlewares.use('/docs', serve)
    }
  }
}
```

This mounts the pre-built MkDocs site at `/docs` on the Vite dev server.

### Production Build

The Docker build process handles the integration:

```dockerfile
# Build frontend
FROM node:18-alpine as build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Serve with nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY site /usr/share/nginx/html/docs  # Copy MkDocs site
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
```

### nginx Configuration

The nginx config routes `/docs` requests to the MkDocs static files:

```nginx
location /docs {
    alias /usr/share/nginx/html/docs;
    index index.html;
    try_files $uri $uri/ $uri/index.html =404;
}
```

### Documentation View Component

The `Documentation.vue` view embeds the MkDocs site in an iframe:

```vue
<template>
  <div class="documentation-view">
    <div class="docs-header">
      <h2>Documentation</h2>
      <button @click="openInNewTab">Open in new tab</button>
      <button @click="refreshDocs">Refresh</button>
    </div>
    <iframe 
      :src="docsUrl"
      class="docs-iframe"
      @load="onFrameLoad"
    />
  </div>
</template>

<script setup>
const docsUrl = '/docs/index.html'
</script>
```

Features:

- Full-height iframe embedding
- Loading overlay during page load
- Open in new tab button
- Refresh button

### Building Documentation

To update the documentation:

```bash
# Install MkDocs (one-time)
pip install mkdocs-material

# Build the site
mkdocs build

# The site/ directory contains the static files
```

The build process should run `mkdocs build` before the Docker image is created to include the latest documentation.

## Development

### Local Development

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on port 3000 with API proxy to `http://localhost:8000`.

### Build for Production

```bash
npm run build
```

Output goes to `dist/` directory.

### Proxy Configuration

Vite proxies `/api` requests to the backend:

```javascript
// vite.config.js
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## Styling

The application uses:

- CSS variables for theming
- Scoped component styles
- Dark mode support via `.dark` class on `<html>`
- Gradient backgrounds for visual hierarchy
- JetBrains Mono font for branding elements

Color scheme follows a dark sidebar with light main content area aesthetic.

