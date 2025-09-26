# Northbound API Overview

The Northbound API is a standardized API interface provided by the Nexent platform for partners, supporting core functions such as agent conversations, session management, and agent queries.

## Documentation Navigation

### 📚 Complete Documentation
- [Northbound API Complete Documentation](./northbound-api.md) - Detailed interface descriptions, authentication mechanisms, parameter specifications, and best practices

### 🚀 Quick Start
- [Northbound API Quick Start](./northbound-quickstart.md) - 5-minute quick start guide

### 🏗️ Technical Architecture
- [Northbound API Architecture Guide](./northbound-architecture.md) - Technical architecture and implementation details

## Main Features

### 🤖 Agent Conversations
- Support for streaming conversations with real-time agent responses
- Multiple agent type support
- Context management and conversation history

### 💬 Session Management
- Create, query, and update session information
- Session history records
- Session state management

### 🔍 Agent Queries
- Get available agent lists
- Agent detailed information
- Agent status checks

### 🔐 Security Authentication
- Dual authentication mechanism (JWT + AK/SK signature)
- Request signature verification
- Timestamp anti-replay attack protection

### 🛡️ Security Features
- Idempotency control to prevent duplicate operations
- Rate limiting to prevent abuse and attacks
- Complete audit logs

## Basic Information

| Item | Description |
|------|-------------|
| **Base Path** | `/api/nb/v1` |
| **Protocol** | HTTPS (production environment) |
| **Data Format** | JSON |
| **Streaming Response** | Server-Sent Events (SSE) |
| **Authentication** | JWT Token + AK/SK signature |
| **Supported Languages** | Python, JavaScript, Java, Go |

## Quick Start

### Health Check
```bash
curl -X GET "https://api.example.com/api/nb/v1/health"
```

### Get Agent List
```bash
curl -X GET "https://api.example.com/api/nb/v1/agents" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature"
```

### Start Conversation
```bash
curl -X POST "https://api.example.com/api/nb/v1/chat/run" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature" \
  -H "Content-Type: application/json" \
  -d '{
    "external_conversation_id": "conv_123",
    "agent_name": "assistant",
    "query": "Hello, please introduce yourself"
  }'
```

## Core Interfaces

| Interface | Method | Description |
|-----------|--------|-------------|
| `/health` | GET | Health check |
| `/agents` | GET | Get agent list |
| `/chat/run` | POST | Start agent conversation |
| `/chat/stream` | POST | Streaming conversation |
| `/conversations` | GET | Get conversation list |
| `/conversations/{id}` | GET | Get conversation details |
| `/conversations` | POST | Create new conversation |

## Authentication Mechanisms

### JWT Token Authentication
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### AK/SK Signature Authentication
```http
X-Access-Key: your_access_key
X-Timestamp: 1640995200
X-Signature: your_signature
```

## Development Resources

### Code Examples
- [Python SDK Examples](./northbound-quickstart.md#python-examples)
- [JavaScript SDK Examples](./northbound-quickstart.md#javascript-examples)
- [Complete Example Programs](./northbound-quickstart.md#complete-example-programs)

### Tools and Libraries
- [Signature Generation Tools](./northbound-quickstart.md#signature-generation-tools)
- [Error Handling Guide](./northbound-api.md#error-handling)
- [Best Practices](./northbound-api.md#best-practices)

## Support and Help

### Common Issues
- [Quick Start FAQ](./northbound-quickstart.md#common-issues)
- [Authentication Troubleshooting](./northbound-api.md#troubleshooting)
- [Performance Optimization Suggestions](./northbound-api.md#performance-optimization)

### Technical Support
- View [Complete Documentation](./northbound-api.md) for detailed information
- Refer to [Architecture Guide](./northbound-architecture.md) to understand technical implementation
- Use [Quick Start Guide](./northbound-quickstart.md) to get started quickly

---

*Northbound API Documentation - Providing powerful AI capability integration for partners*
