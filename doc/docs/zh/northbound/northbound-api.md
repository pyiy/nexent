# 北向接口文档

## 概述

北向接口（Northbound API）是 Nexent 平台为合作伙伴提供的标准化 API 接口，支持智能体对话、会话管理、智能体查询等核心功能。本文档详细介绍了接口的使用方法、认证机制、参数说明和最佳实践。

## 目录

- [快速开始](#快速开始)
- [认证机制](#认证机制)
- [接口规范](#接口规范)
- [API 接口](#api-接口)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

## 快速开始

### 基础信息

- **基础路径**: `/api/nb/v1`
- **协议**: HTTPS（生产环境）
- **数据格式**: JSON
- **字符编码**: UTF-8
- **流式响应**: Server-Sent Events (SSE)

### 环境准备

1. **获取访问凭证**
   - JWT Token：用于用户身份验证
   - Access Key (AK)：用于 API 访问
   - Secret Key (SK)：用于签名验证

2. **配置请求头**
   ```http
   Authorization: Bearer <your_jwt_token>
   X-Access-Key: <your_access_key>
   X-Timestamp: <unix_timestamp>
   X-Signature: <hmac_signature>
   Content-Type: application/json
   ```

## 认证机制

### 双重认证体系

北向接口采用双重认证机制，确保接口安全：

1. **JWT Token 认证**
   - 验证用户身份和权限
   - 从 JWT 中提取 `user_id` 和 `tenant_id`

2. **AK/SK 签名认证**
   - 验证请求的完整性和来源
   - 防止请求被篡改和重放攻击

### 签名算法

#### 签名步骤

1. **构造待签名字符串**
   ```
   string_to_sign = access_key + timestamp + request_body
   ```

2. **计算 HMAC-SHA256 签名**
   ```python
   import hmac
   import hashlib
   
   signature = hmac.new(
       secret_key.encode('utf-8'),
       string_to_sign.encode('utf-8'),
       hashlib.sha256
   ).hexdigest()
   ```

3. **设置请求头**
   ```http
   X-Access-Key: your_access_key
   X-Timestamp: 1640995200
   X-Signature: a1b2c3d4e5f6...
   ```

#### 签名示例

**Python 示例**
```python
import hmac
import hashlib
import json
import time

def generate_signature(access_key, secret_key, body=None):
    timestamp = str(int(time.time()))
    body_str = "" if body is None else json.dumps(body, separators=(',', ':'))
    string_to_sign = f"{access_key}{timestamp}{body_str}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return timestamp, signature

# 使用示例
access_key = "your_access_key"
secret_key = "your_secret_key"
body = {"conversation_id": "test-123", "query": "你好"}

timestamp, signature = generate_signature(access_key, secret_key, body)
```

**JavaScript 示例**
```javascript
const crypto = require('crypto');

function generateSignature(accessKey, secretKey, body = null) {
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const bodyStr = body ? JSON.stringify(body) : '';
    const stringToSign = `${accessKey}${timestamp}${bodyStr}`;
    const signature = crypto
        .createHmac('sha256', secretKey)
        .update(stringToSign, 'utf8')
        .digest('hex');
    return { timestamp, signature };
}
```

## 接口规范

### 请求规范

#### 通用请求头

| 请求头 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `Authorization` | string | 是 | Bearer JWT Token |
| `X-Access-Key` | string | 是 | 访问密钥 |
| `X-Timestamp` | string | 是 | Unix 时间戳（秒） |
| `X-Signature` | string | 是 | HMAC-SHA256 签名 |
| `Content-Type` | string | 是 | application/json |
| `X-Request-Id` | string | 否 | 请求追踪 ID |
| `Idempotency-Key` | string | 否 | 幂等性键值 |

#### 响应格式

**成功响应**
```json
{
    "message": "success",
    "data": { ... },
    "requestId": "req-123456"
}
```

**错误响应**
```json
{
    "message": "错误描述信息"
}
```

### 流式响应规范

流式接口使用 Server-Sent Events (SSE) 格式：

```
data: {"type":"chunk","content":"部分响应内容"}
data: {"type":"chunk","content":"更多内容..."}
data: {"type":"done"}
```

## API 接口

### 1. 健康检查

检查服务状态，无需认证。

**接口信息**
- **URL**: `GET /health`
- **认证**: 无需
- **响应**: JSON

**请求示例**
```bash
curl -X GET "https://api.example.com/api/nb/v1/health"
```

**响应示例**
```json
{
    "status": "healthy",
    "service": "northbound-api"
}
```

### 2. 启动对话（流式）

启动智能体对话，支持流式响应。

**接口信息**
- **URL**: `POST /chat/run`
- **认证**: 需要
- **响应**: SSE 流式

**请求参数**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `conversation_id` | string | 是 | 外部会话 ID |
| `agent_name` | string | 是 | 智能体名称 |
| `query` | string | 是 | 用户问题 |

**请求示例**
```bash
curl -X POST "https://api.example.com/api/nb/v1/chat/run" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-key-123" \
  -d '{
    "conversation_id": "conv-123",
    "agent_name": "assistant",
    "query": "你好，请介绍一下自己"
  }'
```

**响应示例**
```
data: {"type":"chunk","content":"你好！我是"}
data: {"type":"chunk","content":"一个智能助手"}
data: {"type":"chunk","content":"，很高兴为您服务。"}
data: {"type":"done"}
```

### 3. 停止对话

停止正在进行的对话。

**接口信息**
- **URL**: `GET /chat/stop/{conversation_id}`
- **认证**: 需要
- **响应**: JSON

**路径参数**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `conversation_id` | string | 是 | 外部会话 ID |

**请求示例**
```bash
curl -X GET "https://api.example.com/api/nb/v1/chat/stop/conv-123" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature"
```

**响应示例**
```json
{
    "message": "successfully stopped agent run and/or preprocess tasks for user_id xxx, conversation_id yyy",
    "data": "conv-123",
    "requestId": "req-123456"
}
```

### 4. 获取会话历史

获取指定会话的历史消息。

**接口信息**
- **URL**: `GET /conversations/{conversation_id}`
- **认证**: 需要
- **响应**: JSON

**路径参数**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `conversation_id` | string | 是 | 外部会话 ID |

**请求示例**
```bash
curl -X GET "https://api.example.com/api/nb/v1/conversations/conv-123" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature"
```

**响应示例**
```json
{
    "message": "success",
    "data": {
        "conversation_id": "conv-123",
        "history": [
            {
                "role": "user",
                "content": "你好"
            },
            {
                "role": "assistant",
                "content": "你好！有什么可以帮助您的吗？"
            }
        ]
    },
    "requestId": "req-123456"
}
```

### 5. 获取智能体列表

获取租户下可用的智能体列表。

**接口信息**
- **URL**: `GET /agents`
- **认证**: 需要
- **响应**: JSON

**请求示例**
```bash
curl -X GET "https://api.example.com/api/nb/v1/agents" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature"
```

**响应示例**
```json
{
    "message": "success",
    "data": [
        {
            "name": "assistant",
            "display_name": "智能助手",
            "description": "通用智能助手",
            "is_available": true
        },
        {
            "name": "code_helper",
            "display_name": "代码助手",
            "description": "编程相关问题的专业助手",
            "is_available": true
        }
    ],
    "requestId": "req-123456"
}
```

### 6. 获取会话列表

获取租户下的所有会话列表。

**接口信息**
- **URL**: `GET /conversations`
- **认证**: 需要
- **响应**: JSON

**请求示例**
```bash
curl -X GET "https://api.example.com/api/nb/v1/conversations" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature"
```

**响应示例**
```json
{
    "message": "success",
    "data": [
        {
            "conversation_id": "conv-123",
            "conversation_title": "技术讨论",
            "create_time": 1640995200000,
            "update_time": 1640995800000
        },
        {
            "conversation_id": "conv-124",
            "conversation_title": "产品咨询",
            "create_time": 1640994000000,
            "update_time": 1640994600000
        }
    ],
    "requestId": "req-123456"
}
```

### 7. 更新会话标题

更新指定会话的标题。

**接口信息**
- **URL**: `PUT /conversations/{conversation_id}/title`
- **认证**: 需要
- **响应**: JSON

**路径参数**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `conversation_id` | string | 是 | 外部会话 ID |

**查询参数**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 新标题 |

**请求示例**
```bash
curl -X PUT "https://api.example.com/api/nb/v1/conversations/conv-123/title?title=新的标题" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature" \
  -H "Idempotency-Key: unique-key-456"
```

**响应示例**
```json
{
    "message": "success",
    "data": "conv-123",
    "requestId": "req-123456",
    "idempotency_key": "unique-key-456"
}
```

## 错误处理

### HTTP 状态码

| 状态码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | 正常处理响应 |
| 400 | 请求错误 | 检查请求参数 |
| 401 | 认证失败 | 检查 JWT Token 和签名 |
| 429 | 请求过多 | 实施退避重试策略 |
| 500 | 服务器错误 | 联系技术支持 |

### 常见错误

#### 认证错误

**401 Unauthorized**
```json
{
    "message": "Unauthorized: No authorization header found"
}
```

**解决方案**：
- 检查 `Authorization` 请求头是否正确设置
- 确认 JWT Token 未过期
- 验证 AK/SK 签名是否正确

#### 签名错误

**401 Unauthorized - Invalid Signature**
```json
{
    "message": "Unauthorized: invalid signature"
}
```

**解决方案**：
- 检查签名算法实现
- 确认时间戳与服务器时间同步
- 验证请求体参与签名的字符串是否一致

#### 频率限制

**429 Too Many Requests**
```json
{
    "message": "Too Many Requests: rate limit exceeded"
}
```

**解决方案**：
- 实施指数退避重试策略
- 使用 `Idempotency-Key` 避免重复请求
- 降低请求频率

## 最佳实践

### 安全最佳实践

1. **密钥管理**
   - 使用环境变量存储敏感信息
   - 定期轮换 AK/SK 密钥
   - 不要在代码中硬编码密钥

2. **时间同步**
   - 确保客户端时间与服务器时间同步
   - 使用 NTP 服务同步时间
   - 签名时间戳应在合理范围内

3. **请求安全**
   - 始终使用 HTTPS 协议
   - 验证响应完整性
   - 记录请求日志用于审计

### 性能优化

1. **连接复用**
   - 使用 HTTP 连接池
   - 启用 Keep-Alive
   - 合理设置超时时间

2. **流式处理**
   - 使用支持 SSE 的客户端
   - 及时处理流式数据
   - 避免阻塞主线程

3. **错误重试**
   - 实施指数退避策略
   - 设置最大重试次数
   - 区分可重试和不可重试错误

### 幂等性处理

1. **使用 Idempotency-Key**
   ```python
   import uuid
   
   idempotency_key = str(uuid.uuid4())
   headers = {
       "Idempotency-Key": idempotency_key,
       # ... 其他请求头
   }
   ```

2. **重试策略**
   ```python
   import time
   import random
   
   def retry_with_backoff(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               wait_time = (2 ** attempt) + random.uniform(0, 1)
               time.sleep(wait_time)
   ```

## 故障排除

### 常见问题

#### 1. 签名验证失败

**问题现象**：返回 401 错误，提示签名无效

**排查步骤**：
1. 检查 AK/SK 是否正确
2. 验证时间戳格式和范围
3. 确认请求体字符串与签名时一致
4. 检查字符编码是否为 UTF-8

#### 2. JWT Token 无效

**问题现象**：返回 401 错误，提示认证失败

**排查步骤**：
1. 检查 Token 格式：`Bearer <token>`
2. 验证 Token 是否过期
3. 确认 Token 中的 `sub` 字段存在
4. 检查租户绑定关系

#### 3. 流式响应中断

**问题现象**：SSE 连接意外断开

**排查步骤**：
1. 检查网络连接稳定性
2. 增加连接超时时间
3. 实现断线重连机制
4. 检查服务器端日志

#### 4. 频率限制

**问题现象**：频繁返回 429 错误

**解决方案**：
1. 降低请求频率
2. 使用 `Idempotency-Key` 避免重复请求
3. 实施请求队列管理
4. 联系技术支持调整限制

### 调试工具

#### 1. 请求日志记录

```python
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def log_request(method, url, headers, body=None):
    logger.debug(f"Request: {method} {url}")
    logger.debug(f"Headers: {headers}")
    if body:
        logger.debug(f"Body: {body}")
```

#### 2. 签名验证工具

```python
def verify_signature(access_key, secret_key, timestamp, signature, body=""):
    """验证签名是否正确"""
    string_to_sign = f"{access_key}{timestamp}{body}"
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature == expected_signature
```

#### 3. 响应时间监控

```python
import time

def monitor_response_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Response time: {end_time - start_time:.2f}s")
        return result
    return wrapper
```

### 联系支持

如果遇到无法解决的问题，请提供以下信息：

1. **请求信息**
   - 完整的请求 URL
   - 请求头和请求体
   - 时间戳和签名

2. **错误信息**
   - 完整的错误响应
   - 错误发生时间
   - 重现步骤

3. **环境信息**
   - 客户端版本
   - 操作系统信息
   - 网络环境

---

*本文档最后更新时间：2024年1月*
