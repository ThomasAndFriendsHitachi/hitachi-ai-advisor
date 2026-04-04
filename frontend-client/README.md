# Frontend Client Microservice

Frontend microservice for the Hitachi AI Advisor platform. This React application serves as the manager dashboard (IS #4 in the architecture) for reviewing, approving, and managing AI-generated suggestions.

## Architecture Context

This microservice is part of a larger microservices architecture:
- **Backend API**: WebServer #2 (Node.js + Express) at port 3000
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

## Project Structure

```
src/
├── components/          # Reusable React components
│   ├── common/         # Shared UI components (Header, Footer, etc.)
│   └── features/       # Feature-specific components (Dashboard, etc.)
├── config/
│   ├── api.ts         # Axios instance and interceptors
│   └── constants.ts   # App configuration and endpoints
├── hooks/              # Custom React hooks
│   └── useApi.ts      # Hook for API calls with state management
├── pages/              # Page components (routes)
├── types/              # TypeScript type definitions
├── services/           # Business logic and API services
├── styles/             # Global and shared CSS
├── App.tsx            # Main App component
├── App.css            # Main App styles
└── main.tsx           # Entry point

public/
└── index.html         # HTML template

Dockerfile            # Container configuration
.env.example          # Example environment variables
.eslintrc.cjs         # ESLint configuration
```

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

## Best Practices

1. **Type Safety**: Always define types for API responses in `src/types`
2. **Environment Variables**: Use `VITE_*` prefix for environment variables (Vite's convention)
3. **Component Organization**: Group related components in feature folders
4. **Error Handling**: Use the global error interceptor in API config for consistent error handling
5. **Code Quality**: Run linting before committing
6. **Reusability**: Create custom hooks for common logic patterns
7. **Comments**: Document complex components and utilities

## Contributing

When contributing to this microservice:

1. Follow the existing folder structure
2. Create feature branches for new changes
3. Ensure TypeScript strict mode passes (`npm run type-check`)
4. Run linting and fix any issues (`npm run lint`)
5. Keep components focused and single-responsibility
6. Add comments for complex business logic

## TODO / Implementation Checklist

- [ ] Define API endpoints in `src/config/constants.ts` based on backend implementation
- [ ] Create TypeScript interfaces for API responses in `src/types/index.ts`
- [ ] Implement page components in `src/pages/`
- [ ] Create feature components in `src/components/features/`
- [ ] Set up routing (add react-router-dom)
- [ ] Implement authentication/authorization
- [ ] Add state management if needed (Redux, Zustand, etc.)
- [ ] Create API service functions in `src/services/`
- [ ] Implement error boundaries
- [ ] Add unit tests
- [ ] Set up CI/CD pipeline

## Microservice Communication

```
Frontend Client <--REST APIs--> WebServer #2 (Node.js + Express)
                                 |
                                 v
                            PostgreSQL DB
```

The frontend only communicates with WebServer #2. All business logic and database queries are handled by the backend.

## License

ISC

## Related Microservices

- [WebServer](../backend-client/) - REST API server
- [AI Agent](../agent/) - Suggestion generator
- [Webhook Manager](../webhook-manager/) - GitHub webhook receiver
- [Database](../database/) - PostgreSQL setup
