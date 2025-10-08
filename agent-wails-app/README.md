# Agent Application - Wails

A modern desktop application for security testing and automation, rebuilt with Wails (Go + React).

## Features

- Server connection management with API key authentication
- Interactive terminal with command execution and history
- Report generation and management
- Modern UI with dark theme
- Cross-platform support (Linux, macOS, Windows)

## Prerequisites

- Go 1.21 or later
- Node.js 18 or later
- Wails CLI v2.8.0 or later

## Installation

1. Install Wails CLI:
```bash
go install github.com/wailsapp/wails/v2/cmd/wails@latest
```

2. Install dependencies:
```bash
cd agent-wails-app
wails doctor
```

## Development

Run the application in development mode:

```bash
wails dev
```

## Building

Build the application for production:

```bash
wails build
```

The compiled binary will be in the `build/bin` directory.

## Project Structure

```
agent-wails-app/
├── backend/           # Go backend code
│   ├── api.go        # API client
│   ├── config.go     # Configuration management
│   ├── session.go    # Terminal session management
│   └── report.go     # Report generation
├── frontend/         # React frontend
│   └── src/
│       ├── pages/    # Page components
│       ├── components/ # Reusable components
│       └── styles/   # CSS modules
├── app.go           # Main application logic
├── main.go          # Entry point
└── wails.json       # Wails configuration
```

## Configuration

Configuration is stored in `~/.agent-app/client.conf.json` and includes:
- Server URL
- Authentication token

## Usage

1. Launch the application
2. Enter your server URL and API key
3. Access the terminal to execute commands
4. View and manage reports in the Reports section

## Original Application

This is a rebuild of the Python/Tkinter application with the following improvements:
- Modern architecture using Wails framework
- Better performance with Go backend
- Type-safe React frontend with TypeScript
- Improved UI/UX with CSS modules
- Better code organization and maintainability
