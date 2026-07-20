# Desktop Guide

The desktop build wraps the existing Next.js frontend in Electron. It preserves the same API and WebSocket paths as the web application.

## Package

```powershell
cd frontend
npm run desktop:pack
```

Expected outputs:

```text
frontend/release/Boardroom AI-Setup-1.0.0-rc.1.exe
frontend/release/Boardroom AI-Portable-1.0.0-rc.1.exe
```

## Smoke Test

```powershell
cd frontend
npm run desktop:dir
```

The package starts a local Next server and opens the Boardroom AI shell. The backend stack must still be running separately for meetings, history, exports, enterprise workspace, and business intelligence.

## Desktop UX

The desktop shell includes:

- splash screen
- native window metadata
- offline awareness in the renderer
- command palette
- notification center
- friendly backend recovery errors

