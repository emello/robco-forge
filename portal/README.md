# RobCo Forge Portal

Web portal for the RobCo Forge platform - a self-service cloud engineering workstation platform.

## Features

- **Modern & Retro Themes**: Switch between a modern UI and a retro terminal-style interface
- **Workspace Management**: Provision, start, stop, and manage AWS WorkSpaces
- **Cost Dashboard**: Real-time cost tracking and optimization recommendations
- **Lucy AI Integration**: Chat with Lucy, your AI assistant for workspace management
- **Blueprint Management**: Create and manage workspace templates
- **Real-time Updates**: WebSocket integration for live status updates

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **API Client**: Axios
- **Code Quality**: ESLint, Prettier

## Getting Started

### Prerequisites

- Node.js 18.0.0 or higher
- npm or yarn
- Access to Forge API (running on http://localhost:8000 by default)

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Update .env.local with your configuration
```

### Development

```bash
# Start development server
npm run dev

# Open http://localhost:3000 in your browser
```

### Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Code Quality

```bash
# Run ESLint
npm run lint

# Format code with Prettier
npm run format

# Type check
npm run type-check
```

## Project Structure

```
portal/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # React components
│   ├── lib/             # Utility functions and API clients
│   ├── hooks/           # Custom React hooks
│   ├── types/           # TypeScript type definitions
│   └── styles/          # Global styles
├── public/              # Static assets
└── ...config files
```

## Environment Variables

See `.env.example` for required environment variables:

- `NEXT_PUBLIC_API_URL`: Forge API URL
- `NEXT_PUBLIC_OKTA_DOMAIN`: Okta SSO domain
- `NEXT_PUBLIC_OKTA_CLIENT_ID`: Okta client ID
- `NEXT_PUBLIC_ENABLE_RETRO_THEME`: Enable retro theme toggle

## Themes

### Modern Theme
Clean, professional interface with modern design patterns.

### Retro Theme
Terminal-style interface with:
- Scanline effects
- Monochrome green color scheme
- Bitmap fonts (VT323, Share Tech Mono)
- CRT monitor aesthetics

## Requirements

Implements requirements from the RobCo Forge specification:
- 22.1: Dual theme support (modern and retro)
- 22.2: Real-time state synchronization
- 22.3: RBAC enforcement in UI
- 22.4: Budget enforcement in UI
- 22.5: Consistent error messages

## License

PROPRIETARY - RobCo Industries
