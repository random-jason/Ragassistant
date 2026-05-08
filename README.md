# AI Helpdesk

RAG-Powered Workorder Management & Customer Service Platform

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](requirements.txt)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## Features

### RAG Knowledge Base
- TF-IDF + cosine similarity search over knowledge entries
- Configurable confidence scoring and usage tracking
- Auto-suggestion based on historical resolutions

### Workorder Management
- Full CRUD with RBAC permissions (admin, ops, module owner, viewer)
- Feishu spreadsheet sync (bidirectional)
- AI-powered suggestion generation for resolution
- Process history tracking and audit trail

### Online Chat
- Real-time chat via WebSocket + HTTP fallback
- Context-aware multi-turn conversations
- Knowledge base integration for instant answers
- Session management and conversation history

### Bot Integrations
- **Feishu Bot**: Webhook-based messaging, group/DM support
- **WeChat Bot**: Framework ready (interface defined, implementation in progress)

### Analytics & Monitoring
- Token usage tracking and cost estimation
- AI success rate monitoring
- System health dashboard (CPU, memory, disk)
- Configurable alert rules and notifications

### Authentication
- JWT-based authentication
- Role-based access control
- User management (admin, operator, viewer)

## Quick Start

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd ai-helpdesk

# 2. Create environment config
cp .env.example .env
# Edit .env with your API keys and settings

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize the database
python init_database.py

# 5. Start the server
python start_dashboard.py

# 6. Open http://localhost:5000
```

## Architecture

```
src/
├── agent/              # Agent core (planner, executor, tool manager)
├── analytics/          # Token monitor, AI success monitor, alert system
├── config/             # Unified config (env-based)
├── core/               # Database, models, auth, backup, cache
├── dialogue/           # Chat manager, conversation history
├── integrations/       # Feishu, WeChat, AI suggestion service
├── knowledge_base/     # TF-IDF vectorizer and search
├── utils/              # Helpers, encoding, similarity
└── web/                # Flask app, blueprints, templates, static
    ├── blueprints/     # 15 API blueprints
    ├── templates/      # HTML templates
    └── static/         # JS, CSS, images
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask, SQLAlchemy, WebSocket |
| Frontend | Vanilla JS (ES6 modules), Bootstrap 5, Chart.js |
| AI | LLM-agnostic (default: Alibaba Qwen), RAG with TF-IDF |
| Database | SQLite (default), MySQL/PostgreSQL supported |
| Cache | Redis (optional) |
| Bots | Feishu webhook, WeChat webhook (framework) |

## Configuration

All configuration is environment-variable driven via `.env`. See `.env.example` for all available keys.

Key config groups:
- **LLM**: Provider, API key, model, temperature
- **Database**: Connection URL, pool settings
- **Redis**: Host, port, password (optional)
- **Feishu**: App ID, secret, table ID
- **WeChat**: App ID, secret, token
- **Auth**: JWT secret key, token expiry

## What's Implemented

- [x] RAG knowledge base with TF-IDF search
- [x] Workorder CRUD with RBAC permissions
- [x] Real-time chat (WebSocket + HTTP)
- [x] Feishu bot webhook integration
- [x] Feishu spreadsheet bidirectional sync
- [x] AI suggestion generation for workorders
- [x] Analytics dashboard with Chart.js
- [x] Alert system with configurable rules
- [x] User authentication (JWT)
- [x] Unified .env-based configuration
- [x] Docker deployment support
- [x] System health monitoring

## Roadmap

- [ ] WeChat bot full implementation
- [ ] Vector database integration (replacing TF-IDF)
- [ ] Multi-tenant support
- [ ] API rate limiting per tenant
- [ ] Webhook integrations (Slack, Discord, etc.)
- [ ] Alembic database migrations
- [ ] Comprehensive test suite
- [ ] API documentation (OpenAPI/Swagger)

## Development

```bash
# Run in debug mode
SERVER_DEBUG=true python start_dashboard.py

# Initialize/reset database
python init_database.py
```

## Deployment

### Docker

```bash
docker-compose up -d
```

### Manual

```bash
# See scripts/ directory for deployment scripts
# nginx.conf for reverse proxy configuration
```

## License

MIT
