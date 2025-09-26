# 北向接口概览

北向接口（Northbound API）是 Nexent 平台为合作伙伴提供的标准化 API 接口，支持智能体对话、会话管理、智能体查询等核心功能。

## 文档导航

### 📚 完整文档
- [北向接口完整文档](./northbound-api.md) - 详细的接口说明、认证机制、参数说明和最佳实践

### 🚀 快速开始
- [北向接口快速开始](./northbound-quickstart.md) - 5分钟快速上手指南

### 🏗️ 技术架构
- [北向接口架构说明](./northbound-architecture.md) - 技术架构和实现细节

## 主要功能

### 🤖 智能体对话
- 支持流式对话，实时返回智能体响应
- 多种智能体类型支持
- 上下文管理和会话历史

### 💬 会话管理
- 创建、查询、更新会话信息
- 会话历史记录
- 会话状态管理

### 🔍 智能体查询
- 获取可用的智能体列表
- 智能体详细信息
- 智能体状态检查

### 🔐 安全认证
- 双重认证机制（JWT + AK/SK 签名）
- 请求签名验证
- 时间戳防重放攻击

### 🛡️ 安全特性
- 幂等性控制，防止重复操作
- 频率限制，防止滥用和攻击
- 完整的审计日志

## 基础信息

| 项目 | 说明 |
|------|------|
| **基础路径** | `/api/nb/v1` |
| **协议** | HTTPS（生产环境） |
| **数据格式** | JSON |
| **流式响应** | Server-Sent Events (SSE) |
| **认证方式** | JWT Token + AK/SK 签名 |
| **支持语言** | Python, JavaScript, Java, Go |

## 快速开始

### 健康检查
```bash
curl -X GET "https://api.example.com/api/nb/v1/health"
```

### 获取智能体列表
```bash
curl -X GET "https://api.example.com/api/nb/v1/agents" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature"
```

### 开始对话
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
    "query": "你好，请介绍一下自己"
  }'
```

## 核心接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/agents` | GET | 获取智能体列表 |
| `/chat/run` | POST | 开始智能体对话 |
| `/chat/stream` | POST | 流式对话 |
| `/conversations` | GET | 获取会话列表 |
| `/conversations/{id}` | GET | 获取会话详情 |
| `/conversations` | POST | 创建新会话 |

## 认证机制

### JWT Token 认证
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### AK/SK 签名认证
```http
X-Access-Key: your_access_key
X-Timestamp: 1640995200
X-Signature: your_signature
```

## 开发资源

### 代码示例
- [Python SDK 示例](./northbound-quickstart.md#python-示例)
- [JavaScript SDK 示例](./northbound-quickstart.md#javascript-示例)
- [完整示例程序](./northbound-quickstart.md#完整示例程序)

### 工具和库
- [签名生成工具](./northbound-quickstart.md#签名生成工具)
- [错误处理指南](./northbound-api.md#错误处理)
- [最佳实践](./northbound-api.md#最佳实践)

## 支持与帮助

### 常见问题
- [快速开始常见问题](./northbound-quickstart.md#常见问题)
- [认证问题排查](./northbound-api.md#故障排除)
- [性能优化建议](./northbound-api.md#性能优化)

### 技术支持
- 查看 [完整文档](./northbound-api.md) 获取详细信息
- 参考 [架构说明](./northbound-architecture.md) 了解技术实现
- 使用 [快速开始指南](./northbound-quickstart.md) 快速上手

---

*北向接口文档 - 为合作伙伴提供强大的 AI 能力集成*
