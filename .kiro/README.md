# Ed — `.kiro/` Configuration Guide

This directory contains the complete Kiro AI agent configuration for Ed, an emotionally intelligent companion bear for elderly users with dementia.

## Directory Structure

```
.kiro/
├── agents/                    # 8 custom subagents
│   ├── firmware-expert.md     # ESP32/PlatformIO specialist
│   ├── backend-expert.md      # FastAPI/LangGraph/Anthropic specialist
│   ├── dashboard-expert.md    # Next.js/React/shadcn specialist
│   ├── ml-audio-expert.md     # VAD/Whisper/wav2vec2/NumPy signal processing
│   ├── memory-architect.md    # Chroma/SQLite memory tiers, consolidation, retrieval
│   ├── eval-specialist.md     # Synthetic scenarios, intervention scoring, test harness
│   ├── devops-agent.md        # Docker Compose, env setup, deployment
│   └── research-agent.md      # Documentation and API reference lookup
├── hooks/                     # 6 automation hooks
│   ├── env-validation.md      # Validates .env files on edit (fileEdited)
│   ├── python-quality-gate.md # Python type hints, async, Pydantic checks (fileEdited)
│   ├── dashboard-quality-gate.md # TypeScript strict, a11y, shadcn usage (fileEdited)
│   ├── block-secrets.md       # Scans for API keys before commit (userTriggered)
│   ├── commit-helper.md       # Conventional commit generator (userTriggered)
│   └── memory-consolidation.md # Episodic→semantic memory consolidation (userTriggered)
├── settings/
│   └── mcp.json               # 6 MCP servers (context7, memory, sequential-thinking, fetch, chroma, aws-docs)
├── specs/                     # Feature specifications (requirements → design → tasks)
│   ├── _TEMPLATE/             # Spec template
│   ├── sensor-fusion/         # IoT-LLM perception pipeline
│   ├── memory-system/         # Three-tier memory with active curation
│   ├── agent-pipeline/        # LangGraph multi-agent with MAR
│   ├── caregiver-dashboard/   # Real-time Next.js dashboard
│   └── synthetic-eval/        # Self-evaluating test harness
├── steering/                  # 12 AI guidance documents
│   ├── 01-product.md          # Product context, domain terms, constraints
│   ├── 02-tech-stack.md       # Full stack: ESP32 + Python + Next.js
│   ├── 03-structure.md        # Monorepo layout and naming conventions
│   ├── 04-code-standards.md   # Language-specific rules, LSP-first, git conventions
│   ├── 05-sensor-patterns.md  # IoT-LLM translation, sensor fusion, agitation scoring
│   ├── 06-memory-architecture.md # Episodic/semantic/workflow memory, confidence weighting
│   ├── 07-safety-ethics.md    # Clinical safety, MAR notification critics, privacy
│   ├── 08-fastapi-langgraph.md # Backend patterns, agent pipeline, tool definitions
│   ├── 09-nextjs-dashboard.md # Dashboard patterns, SSE, wireframes, component conventions
│   ├── 10-esp32-firmware.md   # Firmware patterns, timing budget, message formats
│   ├── 11-demo-mode.md        # 3-minute demo sequence with exact timing and talking points
│   └── 12-dev-workflow.md     # Build order, agent routing, parallelization, time budget
└── README.md                  # This file
```

## How Kiro Was Used

### Steering Docs (12 files, always-on)
Steering docs are the "constitution" for AI-assisted development. They ensure every code generation request is grounded in Ed's specific architecture, domain constraints, and research-backed patterns. Key examples:
- **05-sensor-patterns.md** enforces IoT-LLM translation (arxiv.org/html/2410.02429) — raw sensor values are never sent to Claude, with concrete agitation scoring code
- **06-memory-architecture.md** defines the three-tier memory system inspired by A-MEM (Zettelkasten), DAM-LLM (confidence weighting), and Memory as Action patterns, with retrieval and consolidation code
- **07-safety-ethics.md** mandates Multi-Agent Reflexion (arxiv.org/html/2512.20845) on all caregiver notifications, with full MAR implementation pattern
- **11-demo-mode.md** scripts the exact 3-minute demo sequence with timing, actions, and talking points
- **12-dev-workflow.md** defines the build order dependency graph, agent routing table, and 13-hour time budget

### Spec-Driven Development (5 feature specs, 3 files each)
Each major feature has the full spec trilogy: requirements.md (EARS notation) → design.md (architecture, data models, code patterns) → tasks.md (phased implementation with file paths and verification criteria). This structure prevents scope creep and gives Kiro clear implementation targets with enough detail to generate production-quality code on first pass.

### Agent Hooks (6 hooks)
- **Automatic hooks** (fileEdited): env-validation, python-quality-gate, dashboard-quality-gate — enforce code quality on every save
- **Security hook** (userTriggered): block-secrets scans staged files for API key patterns before commit — hard block, no exceptions
- **Manual hooks** (userTriggered): commit-helper generates conventional commits scoped by subsystem; memory-consolidation demonstrates the episodic→semantic pipeline during demo

### Custom Subagents (8 agents)
Domain-specialized agents with scoped tool access. Kiro auto-selects the right agent based on the task. The firmware-expert only gets read/write/shell (no web), while the research-agent only gets read/web (no write). This prevents cross-domain mistakes. The dev-workflow steering doc defines explicit routing rules for when to use each agent.

Agent roster: firmware-expert, backend-expert, dashboard-expert, ml-audio-expert, memory-architect, eval-specialist, devops-agent, research-agent. Each has a distinct description so Kiro can match tasks to the right specialist — e.g., "set up Silero VAD" routes to ml-audio-expert, "tune Chroma retrieval" routes to memory-architect.

### MCP Servers (6 servers)
- **context7**: Library documentation lookup for accurate API usage
- **memory**: Knowledge graph for persistent project context across sessions
- **sequential-thinking**: Structured problem-solving for complex architecture decisions
- **fetch**: Web content retrieval for documentation and API references
- **chroma**: Direct Chroma vector DB operations — query/manage memory collections during development
- **aws-docs**: AWS documentation lookup — shows judges we use the AWS MCP ecosystem (it's an AWS-sponsored hackathon)
