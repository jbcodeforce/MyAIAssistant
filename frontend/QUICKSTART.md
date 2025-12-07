# Frontend Quick Start Guide

This guide will help you get the frontend up and running.

## Prerequisites

- Node.js 18 or higher
- npm or yarn
- Backend API running on `http://localhost:8000`

## Installation

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

## First Time Setup

1. Ensure the backend API is running on port 8000
2. Open your browser and navigate to `http://localhost:3000`
3. You should see the Dashboard with the Eisenhower Matrix
4. Click "+ New Todo" to create your first todo

## Available Scripts

### Development

```bash
npm run dev
```

Starts the Vite development server with hot module replacement.

### Production Build

```bash
npm run build
```

Creates an optimized production build in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

Serves the production build locally for testing.

## Docker Deployment

### Build the Docker image:

```bash
docker build -t myaiassistant-frontend .
```

### Run the container:

```bash
docker run -p 80:80 myaiassistant-frontend
```

The application will be available at `http://localhost`.

## Configuration

### API Endpoint

The API endpoint is configured in `vite.config.js`:

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

For production builds, configure the API endpoint in your nginx configuration or environment variables.

## Features

### Dashboard

- View todos organized in the Eisenhower Matrix
- Drag and drop todos between quadrants
- Edit and delete todos

### Unclassified Todos

- View todos without urgency/importance classification
- Classify todos by editing them

### Todo Management

- Create new todos with title, description, status, urgency, importance, category, and due date
- Update existing todos
- Delete todos
- View todo status with color-coded badges

## Troubleshooting

### API Connection Issues

If you see errors connecting to the backend:

1. Verify the backend is running on port 8000
2. Check the browser console for CORS errors
3. Ensure the proxy configuration in `vite.config.js` is correct

### Build Errors

If you encounter build errors:

1. Delete `node_modules` and `package-lock.json`
2. Run `npm install` again
3. Clear the Vite cache: `rm -rf node_modules/.vite`

### Development Server Issues

If the development server fails to start:

1. Check if port 3000 is already in use
2. Try changing the port in `vite.config.js`
3. Restart your terminal and try again

