# Agent Application - Documentation Index

Welcome to the Agent Application documentation. This index will help you navigate all available documentation.

## Quick Links

### 🚀 Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - Get up and running in 5 minutes
- **[INSTALL.md](INSTALL.md)** - Detailed installation instructions
- **[README.md](README.md)** - Project overview and features

### 📚 Understanding the Project
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project summary
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture details
- **[COMPARISON.md](COMPARISON.md)** - Original vs new comparison

### 🔄 Migration
- **[MIGRATION.md](MIGRATION.md)** - Migration guide from Python/Tkinter

## Documentation by Role

### For New Users
Start here if you just want to use the application:

1. [README.md](README.md) - Understand what the app does
2. [QUICKSTART.md](QUICKSTART.md) - Get started quickly
3. User guide (coming soon)

### For Developers
Start here if you want to develop or contribute:

1. [INSTALL.md](INSTALL.md) - Set up development environment
2. [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the architecture
3. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - See what's implemented
4. Code walkthrough (below)

### For Decision Makers
Start here if you're evaluating the migration:

1. [COMPARISON.md](COMPARISON.md) - Original vs new comparison
2. [MIGRATION.md](MIGRATION.md) - Migration benefits and details
3. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - What was delivered

### For Maintainers
Start here if you need to maintain the application:

1. [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
2. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Code organization
3. Build and deployment (below)

## Documentation by Topic

### Installation & Setup
- [INSTALL.md](INSTALL.md) - Platform-specific installation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- Prerequisites and dependencies
- Environment setup

### Architecture & Design
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- Component design
- Data flow
- Security model

### Development
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Code structure
- Development workflow
- Testing guidelines
- Build process

### Migration
- [MIGRATION.md](MIGRATION.md) - Full migration guide
- [COMPARISON.md](COMPARISON.md) - Feature comparison
- Breaking changes
- Upgrade path

### Reference
- [README.md](README.md) - General overview
- API documentation (in code)
- Configuration reference
- Command reference

## Code Walkthrough

### Backend (Go)
```
backend/
├── api.go         - HTTP client for server communication
├── config.go      - Configuration management
├── session.go     - Terminal session and commands
└── report.go      - Report generation
```

**Read in this order:**
1. `config.go` - Simple, handles configuration
2. `api.go` - HTTP communication
3. `session.go` - Command execution
4. `report.go` - Report handling

### Frontend (React)
```
frontend/src/
├── pages/
│   ├── Login.tsx      - Login page
│   └── Dashboard.tsx  - Main dashboard
├── components/
│   ├── Sidebar.tsx    - Navigation sidebar
│   └── Terminal.tsx   - Terminal component
├── App.tsx            - Root component
└── main.tsx           - Entry point
```

**Read in this order:**
1. `main.tsx` - Entry point
2. `App.tsx` - Routing and auth
3. `pages/Login.tsx` - Authentication
4. `pages/Dashboard.tsx` - Main app
5. `components/Terminal.tsx` - Terminal UI

### Main Files
```
├── main.go    - Application entry point
├── app.go     - Wails bindings
└── wails.json - Configuration
```

## Common Tasks

### Running the Application

**Development mode:**
```bash
wails dev
```
See: [QUICKSTART.md](QUICKSTART.md)

**Production build:**
```bash
wails build
./build/bin/agent-app
```
See: [INSTALL.md](INSTALL.md)

### Adding a New Feature

1. Add backend logic in `backend/` directory
2. Add method to `app.go` to expose to frontend
3. Create/update frontend component
4. Update documentation

See: [ARCHITECTURE.md](ARCHITECTURE.md)

### Modifying UI

1. Edit React components in `frontend/src/`
2. Update CSS modules for styling
3. Test with hot reload (`wails dev`)

See: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

### Troubleshooting

Common issues and solutions:
- [INSTALL.md](INSTALL.md#troubleshooting)
- [QUICKSTART.md](QUICKSTART.md#troubleshooting)

## Build & Deployment

### Development Build
```bash
make dev           # Start dev server
```

### Production Build
```bash
make build         # Build native binary
```

### Clean Build
```bash
make clean         # Remove build artifacts
make install       # Reinstall dependencies
make build         # Build again
```

See: [INSTALL.md](INSTALL.md) for details

## Testing

### Manual Testing
1. Start dev server: `wails dev`
2. Test login flow
3. Test terminal commands
4. Test report generation

### Automated Testing (Future)
- Unit tests for Go backend
- Component tests for React
- Integration tests
- E2E tests

## Contributing

### Code Style
- Go: Follow standard Go conventions
- React: Use functional components with hooks
- TypeScript: Enable strict mode
- CSS: Use CSS modules

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "Add feature"

# Push and create PR
git push origin feature/my-feature
```

## Resources

### Documentation
- Wails: https://wails.io/docs/
- React: https://react.dev/
- Go: https://go.dev/doc/
- TypeScript: https://www.typescriptlang.org/docs/

### Community
- Wails Discord
- GitHub Issues
- Stack Overflow

## Version History

### v1.0.0 (Current)
- Initial Wails migration
- Core features implemented
- Cross-platform support

See: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## FAQ

### Q: How do I run the application?
A: See [QUICKSTART.md](QUICKSTART.md)

### Q: How do I build for production?
A: See [INSTALL.md](INSTALL.md)

### Q: What's different from the Python version?
A: See [COMPARISON.md](COMPARISON.md)

### Q: How does the architecture work?
A: See [ARCHITECTURE.md](ARCHITECTURE.md)

### Q: How do I add a new feature?
A: See [ARCHITECTURE.md](ARCHITECTURE.md) and [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## Support

For issues or questions:
1. Check this documentation
2. Review code comments
3. Check Wails documentation
4. Open a GitHub issue

## License

[Add license information here]

## Credits

Original Python/Tkinter application migrated to modern Wails stack.

---

**Navigation Tips:**
- Start with [QUICKSTART.md](QUICKSTART.md) to get running
- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
- Check [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for implementation details
- See [COMPARISON.md](COMPARISON.md) for migration benefits

Happy coding! 🚀
