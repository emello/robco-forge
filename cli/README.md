# Forge CLI

Command-line interface for the RobCo Forge platform - a self-service cloud engineering workstation platform.

## Installation

```bash
npm install
npm run build
```

## Development

```bash
# Run in development mode
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run format
```

## Usage

```bash
# Show help
forge --help

# Provision a workspace
forge launch --bundle PERFORMANCE --blueprint data-science

# List workspaces
forge list

# Start a workspace
forge start ws-abc123

# Stop a workspace
forge stop ws-abc123

# Terminate a workspace
forge terminate ws-abc123

# Get workspace details
forge describe ws-abc123

# View costs
forge costs

# Ask Lucy a question
forge ask "I need a GPU workspace"

# Manage configuration
forge config set api-url https://forge.example.com
forge config get api-url
forge config list
```

## Configuration

The CLI can be configured via:

1. Environment variables (`.env` file)
2. Command-line flags
3. Configuration file (`~/.forge/config.json`)

### Environment Variables

- `FORGE_API_URL` - Forge API endpoint (default: http://localhost:8000)
- `FORGE_AUTH_TOKEN` - JWT authentication token

### Command-line Flags

- `--api-url <url>` - Override API URL
- `--json` - Output in JSON format
- `--no-color` - Disable colored output
- `--debug` - Enable debug logging

## Requirements

- Node.js >= 18.0.0
- TypeScript 5.3+

## Architecture

The CLI is built with:

- **Commander.js** - Command-line framework
- **TypeScript** - Type-safe development with strict mode
- **Axios** - HTTP client for API communication
- **Chalk** - Terminal styling
- **cli-table3** - Table formatting
- **Ora** - Loading spinners

## Project Structure

```
cli/
├── src/
│   ├── index.ts           # CLI entry point
│   ├── commands/          # Command implementations
│   ├── api/               # Forge API client
│   ├── config/            # Configuration management
│   ├── utils/             # Utility functions
│   └── types/             # TypeScript type definitions
├── dist/                  # Compiled output
├── package.json           # Dependencies and scripts
├── tsconfig.json          # TypeScript configuration
├── jest.config.js         # Test configuration
└── README.md              # This file
```

## Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

## License

PROPRIETARY - RobCo Industries
