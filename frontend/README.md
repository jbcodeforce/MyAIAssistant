# MyAIAssistant Frontend

A Vue.js frontend application for managing todos using the Eisenhower Matrix.

## Features

- Drag-and-drop todo organization by urgency and importance
- Eisenhower Matrix visualization (4 quadrants)
- Create, update, and delete todos
- Unclassified todos view
- Responsive design

## Tech Stack

- Vue 3 with Composition API
- Pinia for state management
- Vue Router for navigation
- Axios for API communication
- Vite for build tooling

## Development Setup

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

The development server is configured to proxy API requests to `http://localhost:8000`.

### Build for Production

```bash
npm run build
```

The production build will be output to the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── assets/              # Static assets and styles
├── components/
│   ├── common/          # Reusable UI components
│   │   ├── Header.vue
│   │   └── Modal.vue
│   └── todo/            # Todo-specific components
│       ├── TodoCanvas.vue
│       ├── TodoCard.vue
│       ├── TodoForm.vue
│       └── StatusIndicator.vue
├── services/
│   └── api.js           # API client and endpoints
├── stores/
│   ├── todoStore.js     # Todo state management
│   └── uiStore.js       # UI state management
├── views/
│   ├── Dashboard.vue    # Eisenhower Matrix view
│   └── Unclassified.vue # Unclassified todos view
├── router/
│   └── index.js         # Vue Router configuration
├── App.vue              # Root component
└── main.js              # Application entry point
```

## API Configuration

The application expects the backend API to be running on `http://localhost:8000`. This can be configured in `vite.config.js`:

```javascript
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

## Usage

### Dashboard View

The main dashboard displays todos organized in the Eisenhower Matrix with four quadrants:

- **Do First** - Urgent and Important
- **Schedule** - Not Urgent but Important
- **Delegate** - Urgent but Not Important
- **Eliminate** - Not Urgent and Not Important

Drag and drop todos between quadrants to update their urgency and importance.

### Unclassified View

View todos that have not been assigned urgency or importance values. Click on any todo to edit and classify it.

### Creating Todos

Click the "+ New Todo" button in the header to open the creation form. Fill in the details and submit.

### Editing Todos

Click the edit button on any todo card or click the card itself to open the edit form.

### Deleting Todos

Click the delete button on any todo card and confirm the deletion.

