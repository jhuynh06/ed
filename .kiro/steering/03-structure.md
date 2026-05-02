---
title: Theodore — Project Structure
inclusion: always
---

# Project Structure

```
theodore/
├── .kiro/                    # Kiro AI agent configuration
│   ├── agents/               # Custom subagent definitions
│   ├── hooks/                # Automation hooks
│   ├── settings/             # MCP server config
│   ├── specs/                # Feature specifications
│   └── steering/             # AI guidance documents
├── firmware/                 # ESP32-S3 PlatformIO project
│   ├── src/
│   │   ├── main.cpp          # Entry point, WiFi + WebSocket setup
│   │   ├── sensors/          # Sensor drivers (IMU, HR, touch, mic)
│   │   ├── actuators/        # Speaker, motor, LED control
│   │   └── comms/            # WebSocket client, message protocol
│   ├── include/
│   └── platformio.ini
├── backend/                  # Python FastAPI server
│   ├── app/
│   │   ├── main.py           # FastAPI app, WebSocket endpoint
│   │   ├── agents/           # LangGraph agent definitions
│   │   │   ├── perception.py # Sensor fusion + IoT-LLM translation
│   │   │   ├── risk.py       # Agitation scoring + sundowning detection
│   │   │   ├── memory.py     # Memory retrieval + active curation
│   │   │   ├── planner.py    # Intervention planning (Sonnet)
│   │   │   └── executor.py   # Action dispatch to bear
│   │   ├── memory/           # Memory architecture
│   │   │   ├── episodic.py   # Episode capture + storage
│   │   │   ├── semantic.py   # Consolidated patterns
│   │   │   ├── workflow.py   # Comfort recipe storage
│   │   │   └── tools.py      # consolidate_pattern, evict, link
│   │   ├── tools/            # Claude tool definitions
│   │   ├── models/           # Pydantic schemas
│   │   └── sse.py            # Server-Sent Events for dashboard
│   ├── pyproject.toml
│   └── .env.example
├── dashboard/                # Next.js 15 caregiver dashboard
│   ├── src/
│   │   ├── app/              # App Router pages
│   │   ├── components/       # React components
│   │   │   ├── timeline/     # Agitation timeline
│   │   │   ├── vitals/       # HR trends, circadian patterns
│   │   │   ├── episodes/     # Event log with audio playback
│   │   │   └── family/       # Voice clip management
│   │   └── lib/              # SSE client, API helpers
│   ├── package.json
│   └── tailwind.config.ts
├── docker-compose.yml        # Optional: backend + dashboard + chroma
├── LICENSE                   # OSI-approved open source license
└── README.md
```

## Naming Conventions
- Firmware: `snake_case` for files and functions (C++ Arduino convention)
- Backend: `snake_case` for files, functions, variables (Python PEP 8)
- Dashboard: `kebab-case` for files, `PascalCase` for components, `camelCase` for functions
- Specs: `kebab-case` directory names under `.kiro/specs/`
