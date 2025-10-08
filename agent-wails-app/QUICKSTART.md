# Quick Start Guide

Get the Agent application running in 5 minutes!

## Prerequisites Check

Ensure you have installed:
- Go 1.21+ (`go version`)
- Node.js 18+ (`node --version`)
- Wails CLI (`wails version`)

If not, see [INSTALL.md](INSTALL.md) for detailed installation instructions.

## Quick Start

### 1. Clone/Navigate to Project
```bash
cd agent-wails-app
```

### 2. Install Dependencies
```bash
# Install frontend dependencies
cd frontend && npm install && cd ..

# Download Go modules
go mod download
```

### 3. Run Development Server
```bash
wails dev
```

The application will open automatically with hot reload enabled.

### 4. Login
1. Enter your server URL (e.g., `https://example.com`)
2. Enter your API key
3. Click "Login"

### 5. Use the Terminal
- Type commands in the terminal input
- Press Enter to execute
- View command history and output

## Building for Production

```bash
# Build native binary
wails build

# Run the built application
./build/bin/agent-app
```

## Project Structure

```
agent-wails-app/
├── backend/              # Go backend code
│   ├── api.go           # API client for server communication
│   ├── config.go        # Configuration management
│   ├── session.go       # Terminal session and command execution
│   └── report.go        # Report generation
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Page components (Login, Dashboard)
│   │   └── styles/      # Global styles
│   ├── package.json
│   └── vite.config.ts
├── app.go              # Main app logic (binds Go to frontend)
├── main.go             # Application entry point
└── wails.json          # Wails configuration
```

## Key Features

### 1. Authentication
- Secure API key authentication
- Token-based session management
- Automatic configuration persistence

### 2. Terminal
- Execute shell commands
- View command history
- Real-time output display
- Success/error indication

### 3. Reports
- Create and manage reports
- JSON-based storage
- List all reports
- Delete reports

### 4. Configuration
- Automatic config file creation
- Stored in `~/.agent-app/`
- Secure token storage

## Common Commands

```bash
# Development with hot reload
wails dev

# Build production binary
wails build

# Clean build artifacts
make clean

# Install all dependencies
make install

# Run built application
make run
```

## Troubleshooting

### Application won't start
```bash
# Check dependencies
wails doctor

# Reinstall frontend dependencies
cd frontend && rm -rf node_modules && npm install
```

### Build errors
```bash
# Clean and rebuild
make clean
make install
wails build
```

### Configuration issues
```bash
# Remove stored config
rm ~/.agent-app/client.conf.json
```

## Next Steps

- Read [README.md](README.md) for detailed features
- Check [INSTALL.md](INSTALL.md) for platform-specific setup
- See [MIGRATION.md](MIGRATION.md) for architecture details

## Getting Help

- Wails Documentation: https://wails.io/docs/
- React Documentation: https://react.dev/
- Go Documentation: https://go.dev/doc/

## Development Tips

1. **Frontend Changes**: Automatically reload in dev mode
2. **Backend Changes**: Restart `wails dev` to see changes
3. **Styles**: Use CSS modules for component-scoped styles
4. **Debugging**: Use browser DevTools (F12) for frontend debugging

Enjoy using the Agent application!
