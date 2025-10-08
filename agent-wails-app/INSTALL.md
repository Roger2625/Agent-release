# Installation Guide

## Prerequisites

### 1. Install Go
- Download and install Go 1.21 or later from https://golang.org/dl/
- Verify installation:
  ```bash
  go version
  ```

### 2. Install Node.js
- Download and install Node.js 18 or later from https://nodejs.org/
- Verify installation:
  ```bash
  node --version
  npm --version
  ```

### 3. Install Wails CLI

```bash
go install github.com/wailsapp/wails/v2/cmd/wails@latest
```

Verify installation:
```bash
wails version
```

### 4. Install System Dependencies

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install build-essential libgtk-3-dev libwebkit2gtk-4.0-dev
```

#### macOS
On macOS, you need Xcode command line tools:
```bash
xcode-select --install
```

#### Windows
- Install MinGW-w64 or use MSYS2
- Or use Visual Studio with C++ support

## Building the Application

### 1. Navigate to project directory
```bash
cd agent-wails-app
```

### 2. Install dependencies
```bash
make install
```

Or manually:
```bash
go mod download
cd frontend && npm install
```

### 3. Check your environment
```bash
wails doctor
```

This will verify that all required dependencies are installed.

### 4. Build the application

For development (with hot reload):
```bash
make dev
# or
wails dev
```

For production build:
```bash
make build
# or
wails build
```

The compiled application will be in `build/bin/`:
- Linux: `build/bin/agent-app`
- macOS: `build/bin/agent-app.app`
- Windows: `build/bin/agent-app.exe`

## Running the Application

After building, run the application:

### Linux/macOS
```bash
./build/bin/agent-app
```

### Windows
```
build\bin\agent-app.exe
```

## Development Mode

For faster development with hot reload:

```bash
wails dev
```

This will:
- Start the Go backend
- Start the Vite dev server for the frontend
- Enable hot reload for both frontend and backend changes

## Troubleshooting

### Issue: "wails: command not found"
Make sure `$GOPATH/bin` is in your PATH:
```bash
export PATH=$PATH:$(go env GOPATH)/bin
```

### Issue: Build fails on Linux
Install missing dependencies:
```bash
sudo apt-get install gcc libgtk-3-dev libwebkit2gtk-4.0-dev
```

### Issue: Frontend build fails
Clean and reinstall dependencies:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: Go module errors
Update Go modules:
```bash
go mod tidy
go mod download
```

## Production Deployment

To create a production-ready build:

```bash
wails build -clean -platform linux/amd64
```

For multiple platforms:
```bash
wails build -clean -platform linux/amd64,darwin/amd64,windows/amd64
```

Note: Cross-compilation may require additional setup. See Wails documentation for details.
