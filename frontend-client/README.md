# Frontend Client Microservice

Frontend microservice for the Hitachi AI Advisor platform. This React application serves as the manager dashboard (IS #4 in the architecture) for reviewing, approving, and managing AI-generated suggestions.

## Architecture Context

This microservice is part of a larger microservices architecture:
- **Backend Client**: WebServer #2 (Node.js + Express) at port 3000
- **Database**: PostgreSQL connected to the backend
- **AI Agent**: Worker node for generating suggestions
- **Message Broker**: Redis for async communication
- **Webhook Manager**: Receives GitHub webhook events

This frontend communicates exclusively with the **WebServer #2** via REST APIs to:
- Fetch AI suggestions
- Approve/reject recommendations
- View analytics and trends

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **ESLint** - Code linting

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- npm or yarn

### Installation

1. Clone the repository and navigate to this directory:
```bash
cd frontend-client
```

2. Install dependencies:
```bash
npm install
```

3. Create environment configuration:
```bash
cp .env.example .env
```

4. Update `.env` if needed to match your backend API URL:
```
VITE_API_URL=http://localhost:3000
VITE_APP_TITLE=Hitachi AI Advisor
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

The dev server includes a proxy to the backend API, so requests to `/api/*` are forwarded to the WebServer.

### Building

Build for production:
```bash
npm run build
```

Preview the production build locally:
```bash
npm run preview
```

### Code Quality

Run linting:
```bash
npm run lint
```

Type checking:
```bash
npm run type-check
```

## Docker Deployment

Build the Docker image:
```bash
docker build -t hitachi-ai-advisor-frontend:latest .
```

Run the container:
```bash
docker run -p 5173:5173 hitachi-ai-advisor-frontend:latest
```

## API Integration

### Configuration

API calls are configured through:
- **Base URL**: Set via `VITE_API_URL` environment variable
- **Client**: Configured in `src/config/api.ts` using axios
- **Endpoints**: Defined in `src/config/constants.ts`

### Making API Calls

Use the custom `useApi` hook for fetching data:

```typescript
import { useApi } from '../hooks/useApi'

function MyComponent() {
  const { data, loading, error, refetch } = useApi('/api/suggestions')
  
  if (loading) return <p>Loading...</p>
  if (error) return <p>Error: {error.message}</p>
  
  return <div>{/* Use data */}</div>
}
```

Or directly with the API client:

```typescript
import apiClient from '../config/api'

apiClient.get('/api/suggestions').then(res => {
  console.log(res.data)
})
```

## Related Microservices

- [WebServer](../backend-client/) - REST API server
- [AI Agent](../agent/) - Suggestion generator
- [Webhook Manager](../webhook-manager/) - GitHub webhook receiver
- [Database](../database/) - PostgreSQL setup
