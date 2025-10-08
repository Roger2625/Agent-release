# Application Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                     │
│              (React + TypeScript)                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  Login   │  │Dashboard │  │ Terminal │         │
│  │  Page    │  │   Page   │  │Component │         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       │             │              │               │
│       └─────────────┴──────────────┘               │
│                     │                               │
│                Wails Bridge                         │
│                     │                               │
├─────────────────────┼───────────────────────────────┤
│                     │                               │
│                ┌────▼────┐                         │
│                │  App.go │                         │
│                └────┬────┘                         │
│                     │                               │
│      ┌──────────────┼──────────────┐              │
│      │              │               │              │
│  ┌───▼───┐    ┌────▼────┐    ┌────▼────┐         │
│  │ API   │    │ Config  │    │ Session │         │
│  │Client │    │ Manager │    │ Manager │         │
│  └───┬───┘    └────┬────┘    └────┬────┘         │
│      │             │               │              │
│      │        ┌────▼────┐          │              │
│      │        │ Report  │          │              │
│      │        │Generator│          │              │
│      │        └─────────┘          │              │
│      │                              │              │
├──────┼──────────────────────────────┼──────────────┤
│      │                              │              │
│  ┌───▼────┐                    ┌───▼────┐        │
│  │ Remote │                    │  OS    │        │
│  │ Server │                    │ Shell  │        │
│  └────────┘                    └────────┘        │
└──────────────────────────────────────────────────┘
```

## Component Architecture

### Frontend Layer (React)

```
┌────────────────────────────────────┐
│           App.tsx                  │
│  - Routing                         │
│  - Auth state                      │
│  - Config loading                  │
└────────┬───────────────────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼─────┐
│Login │  │Dashboard│
│Page  │  │  Page   │
└──────┘  └────┬────┘
               │
        ┌──────┴──────┐
        │             │
    ┌───▼───┐   ┌────▼────┐
    │Sidebar│   │Terminal │
    │       │   │Component│
    └───────┘   └─────────┘
```

### Backend Layer (Go)

```
┌─────────────────────────────────────┐
│          main.go                    │
│  - Wails initialization             │
│  - Window configuration             │
└────────┬────────────────────────────┘
         │
    ┌────▼────┐
    │ App.go  │
    │ - Binds │
    └────┬────┘
         │
    ┌────┴────────────────────┐
    │                          │
┌───▼────┐  ┌────────┐  ┌─────▼─────┐
│API     │  │Config  │  │Session    │
│Client  │  │Manager │  │Manager    │
└────────┘  └────────┘  └───────────┘
                         ┌────────────┐
                         │Report      │
                         │Generator   │
                         └────────────┘
```

## Data Flow

### Authentication Flow

```
User Input → Login Component → ValidateAPIKey()
                                      ↓
                                  API Client
                                      ↓
                               Remote Server
                                      ↓
                              Token Response
                                      ↓
                              SaveConfiguration()
                                      ↓
                              Config Manager
                                      ↓
                           ~/.agent-app/config.json
```

### Command Execution Flow

```
User Command → Terminal Component → ExecuteCommand()
                                          ↓
                                   Session Manager
                                          ↓
                                    Go exec.Command
                                          ↓
                                      OS Shell
                                          ↓
                                   Capture Output
                                          ↓
                                   Store in History
                                          ↓
                                Return to Frontend
                                          ↓
                                  Display Output
```

### Report Generation Flow

```
Create Request → Dashboard → CreateReport()
                                    ↓
                            Report Generator
                                    ↓
                              Generate ID
                                    ↓
                            Format as JSON
                                    ↓
                               Save File
                                    ↓
                    ~/.agent-app/reports/report_*.json
                                    ↓
                            Return Metadata
```

## Module Dependencies

### Go Modules

```
main.go
  └── imports app.go
        └── imports backend/
              ├── api.go
              │     └── net/http
              ├── config.go
              │     └── os, json
              ├── session.go
              │     └── os/exec
              └── report.go
                    └── json, time
```

### Frontend Modules

```
main.tsx
  └── App.tsx
        ├── pages/Login.tsx
        │     └── wailsjs/go/main/App
        └── pages/Dashboard.tsx
              ├── components/Sidebar.tsx
              └── components/Terminal.tsx
                    └── wailsjs/go/main/App
```

## State Management

### Frontend State

```
App.tsx
  ├── isAuthenticated: boolean
  └── isLoading: boolean

Dashboard.tsx
  ├── history: HistoryItem[]
  └── activeView: string

Terminal.tsx
  ├── input: string
  └── isExecuting: boolean

Login.tsx
  ├── serverURL: string
  ├── apiKey: string
  ├── error: string
  └── isLoading: boolean
```

### Backend State

```
App struct
  ├── ctx: context.Context
  ├── api: *API
  ├── config: *Config
  ├── session: *Session
  └── reportGen: *ReportGenerator

Session struct
  └── history: []CommandHistory

Config struct
  ├── ServerURL: string
  └── Token: string
```

## API Interface

### Go to Frontend (Exposed Methods)

```go
// Authentication
ValidateAPIKey(serverURL, apiKey string) (map, error)
SaveConfiguration(serverURL, token string) error
LoadConfiguration() (map, error)

// Commands
ExecuteCommand(command string) (string, error)
GetSessionHistory() []map

// Reports
CreateReport(title, content map) (map, error)
ListReports() ([]map, error)
GetReport(id string) (map, error)
DeleteReport(id string) error

// Data
GetData(serverURL, token string, params map) (map, error)
```

## File System Structure

```
~/.agent-app/
  ├── client.conf.json          # Configuration
  └── reports/                  # Reports directory
        ├── report_20231201_*.json
        ├── report_20231202_*.json
        └── ...
```

## Security Architecture

### Token Flow

```
API Key → Server Validation → Token
                                 ↓
                         Store in Config
                                 ↓
                          File (0600 mode)
                                 ↓
                      Load on Startup
                                 ↓
                   Use in API Requests
                                 ↓
                   Authorization Header
```

### Data Protection

- Configuration files: 0600 permissions (owner only)
- Passwords: Never stored, only tokens
- API communication: HTTPS (server-side)
- Input validation: Both frontend and backend

## Build Architecture

### Development Build

```
Source Files → Vite Dev Server → Hot Reload
                                      ↓
Go Source → Go Compiler → Hot Reload
                                      ↓
                              Wails Dev Mode
                                      ↓
                            Browser Window
```

### Production Build

```
Frontend Source → Vite Build → Static Files
                                      ↓
                                  Embed
                                      ↓
Go Source + Embedded Assets → Go Compiler
                                      ↓
                              Native Binary
                                      ↓
                           Platform Executable
```

## Deployment Architecture

```
┌─────────────────────────────────┐
│     Single Binary Package       │
│  - Compiled Go code             │
│  - Embedded web assets          │
│  - No external dependencies     │
└─────────────────────────────────┘
                │
                ├── Linux (ELF)
                ├── macOS (Mach-O)
                └── Windows (PE)
```

## Communication Patterns

### Synchronous Calls

```
Frontend → Wails Bridge → Go Function → Return Value → Frontend
```

### Error Handling

```
Go Error → Return (nil, error) → Frontend Catch → Display Error
```

### Event Flow

```
User Action → React Event → Wails Binding → Go Handler → Response
```

## Performance Considerations

### Frontend Optimization
- Component memoization
- CSS modules (scoped styles)
- Code splitting (ready for future)
- Virtual DOM updates

### Backend Optimization
- Concurrent command execution (ready)
- Efficient JSON parsing
- Minimal memory allocations
- Fast binary search for reports

### Build Optimization
- Minified frontend assets
- Compressed binary
- Tree shaking
- Dead code elimination

## Scalability

### Current Limitations
- Single user per instance
- Local file storage
- No concurrent sessions

### Future Extensions
- Database integration (Supabase ready)
- Multi-user support
- Cloud storage
- Real-time collaboration

## Technology Integration Points

```
React ←→ Wails ←→ Go ←→ OS
  ↓                      ↓
Vite              File System
  ↓                      ↓
TypeScript        Network
```

This architecture provides:
- Clear separation of concerns
- Easy testing
- Simple deployment
- Excellent performance
- Room for growth
