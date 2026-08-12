# Aero Sovereign - Windows 7 Rebirth

A sovereign desktop operating environment that captures the legendary speed, clean modularity, and glass aesthetic of Windows 7 while stripping away modern telemetry, cloud lock-in, and bloatware.

## Features

### 🎨 Aero-Sovereign UI Shell & Glass Compositor
- **Hardware-accelerated translucent window borders** (DWM-style acrylic blur)
- **Deep obsidian dark-mode palettes** with neon telemetry accents
- **Modular taskbar & start menu** with instant command search
- **Real-time hardware status indicators** in notification tray
- **Floating Command Deck** - IBEN-Genesis HUD architecture as desktop overlay

### 🔒 Local-First Data Sovereignty
- Complete decoupling from cloud synchronization
- All user data locally owned, encrypted (AES-256-GCM), and indexed
- Zero telemetry - hardened firewall rules block all outbound telemetry calls

### ⚡ Unrestricted Execution Engine
- Full support for native Win32/64 execution
- Custom DLL injection hooks
- Local background automation daemons without sandbox limitations
- Ternary & Quaternary logic integration for system monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Interface Layer                       │
│  (HTML5/CSS3/WebGPU - Aero Glass UI Shell)              │
│  - Taskbar & Start Menu                                  │
│  - Window Manager                                        │
│  - Floating Command Deck                                 │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                   Tauri Host Layer                       │
│  (Rust - Native Bridge & System Hooks)                  │
│  - Window Management                                     │
│  - System Tray                                           │
│  - Hardware Hooks                                        │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                   Sovereign Core                         │
│  (Rust Backend Daemon)                                   │
│  - Local Data Storage (Encrypted)                        │
│  - Script Execution Engine                               │
│  - Ternary/Quaternary Logic Modules                      │
│  - Telemetry Blocking Network Rules                      │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Node.js 18+
- Rust 1.70+
- Tauri CLI (`cargo install tauri-cli`)

### Development

```bash
# Install dependencies
npm install

# Run in development mode (browser)
npm run dev

# Run in Tauri mode (native desktop app)
npm run tauri:dev
```

### Build Production

```bash
# Build frontend
npm run build

# Build native executable
npm run tauri:build
```

## Project Structure

```
aero-sovereign/
├── public/                 # Static assets & HTML entry point
├── src/
│   ├── components/         # Vue UI components
│   │   ├── App.vue
│   │   ├── AeroTaskbar.vue
│   │   ├── FloatingCommandDeck.vue
│   │   ├── WindowManager.vue
│   │   └── StartMenu.vue
│   ├── styles/             # Aero glass CSS
│   │   └── aero.css
│   └── main.js             # Entry point
├── tauri-src/
│   ├── src/
│   │   └── main.rs         # Rust backend daemon
│   ├── Cargo.toml          # Rust dependencies
│   └── tauri.conf.json     # Tauri configuration
├── package.json            # Node dependencies
└── vite.config.js          # Vite bundler config
```

## Core Technologies

| Layer | Technology | Purpose |
|-------|------------|---------|
| UI Framework | Vue 3 + Vite | Reactive UI components |
| Styling | CSS3 + backdrop-filter | Aero glass effects |
| Native Host | Tauri 2.0 | Desktop application wrapper |
| Backend | Rust | System-level operations |
| Encryption | AES-256-GCM | Local data protection |
| Logic Gates | Custom Ternary/Quaternary | System monitoring |

## Telemetry Blocking

The Sovereign Core automatically blocks connections to known telemetry endpoints:

- `telemetry.microsoft.com`
- `vortex.data.microsoft.com`
- `settings-win.data.microsoft.com`
- `watson.telemetry.microsoft.com`
- And 8+ more endpoints

## License

MIT - Sovereign Software License

---

**Windows 7 Rebirth** - The Aero lives on.
