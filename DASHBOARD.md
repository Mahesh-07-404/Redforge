# RedForge React Dashboard Operations Guide

This document describes the RedForge frontend dashboard, which communicates exclusively with the REST/WebSocket API Gateway.

---

## Technical Stack

* **Core Framework**: React 19, TypeScript, Vite
* **Styling**: Tailwind CSS v4, custom glassmorphism layers, and color tokens for Light/Dark mode toggling.
* **Routing**: React Router DOM (v6)
* **Testing**: Vitest unit testing framework
* **Icons**: Lucide React
* **State Management**: Context-based shared providers for Connection Settings and Target Sessions.

---

## Directory Structure

```
dashboard/
  ├── package.json
  ├── vite.config.ts
  ├── tsconfig.json
  ├── index.html
  └── src/
      ├── main.tsx
      ├── App.tsx
      ├── index.css
      ├── types/
      │   └── index.ts          # Shared TypeScript interfaces
      ├── contexts/
      │   ├── SettingsContext.tsx # API URLs, auth key context
      │   └── SessionContext.tsx  # Loaded sessions context & switcher
      ├── services/
      │   ├── api.ts            # Client SDK for REST & WebSockets
      │   └── api.test.ts       # Service mock unit tests
      ├── layouts/
      │   └── DashboardLayout.tsx # Main frame navigation
      └── pages/
          ├── Overview.tsx      # Dashboard main metrics and findings
          ├── Chat.tsx          # Real-time WebSocket AI assistant chat
          ├── Workflows.tsx     # Workflow template launcher
          ├── Sessions.tsx      # Target session manager
          ├── Reports.tsx       # Audit compile and preview center
          ├── Evidence.tsx      # Live interactive scanner runner
          ├── Memory.tsx        # Operations memory note repository
          ├── Plugins.tsx       # System extension toggle lists
          └── Settings.tsx      # Auth login configurations
```

---

## Features

1. **Operations Overview**:
   A summary displaying target details, running workflow indicators, recent severity breakdowns, and total API telemetry.
2. **AI Copilot Terminal**:
   Live streaming token assistant chatting via `/ws/chat` socket connection.
3. **Workflows launcher**:
   Triggers multi-stage scans and monitors progression rates using `/ws/workflow` socket.
4. **Target Session Manager**:
   Add new domain/IP scopes, toggle active session contexts, and delete completed records.
5. **Interactive Runner**:
   Execute individual CLI tools and view live process logs streamed over `/ws/execution`.
6. **Audit compiler**:
   Download SARIF, JSON, and Markdown summaries, preview contents, and set remediation inclusions.
7. **Auth Configuration**:
   Validate API Key access scopes, log in via Operator JWT auth, and toggle Dark Mode interface styles.

---

## Build & Run Guide

To start the local developer dashboard:

```bash
# Navigate to project root
cd dashboard

# Install dependencies
npm install

# Run vitest unit tests
npm run test

# Launch dev server (vite)
npm run dev
```

The dashboard binds by default to `http://localhost:5173`. Configure your connection settings targeting the backend server at `http://127.0.0.1:8000` inside the **Settings** view.
