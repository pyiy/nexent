# Northbound API Documentation

## Overview

The Northbound API is a standardized API interface provided by the Nexent platform for partners, supporting core functions such as agent conversations, session management, and agent queries. This document provides detailed information on interface usage, authentication mechanisms, parameter specifications, and best practices.

## Table of Contents

- [Quick Start](#quick-start)
- [Authentication Mechanism](#authentication-mechanism)
- [Interface Specifications](#interface-specifications)
- [API Interfaces](#api-interfaces)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Basic Information

- **Base Path**: `/api/nb/v1`
- **Protocol**: HTTPS (production environment)
- **Data Format**: JSON
- **Character Encoding**: UTF-8
- **Streaming Response**: Server-Sent Events (SSE)

### Environment Setup

1. **Get Access Credentials**
   - JWT Token: For user identity authentication
   - Access Key (AK): For API access
   - Secret Key (SK): For signature verification

2. **Configure Request Headers**
   ```http
   Authorization: Bearer <your_jwt_token>
   X-Access-Key: <your_access_key>
   X-Timestamp: <unix_timestamp>
   X-Signature: <hmac_signature>
   Content-Type: application/json
   ```

## Authentication Mechanism

### Dual Authentication System

The Northbound API uses a dual authentication mechanism to ensure interface security:

1. **JWT Token Authentication**
   - Verify user identity and permissions
   - Extract `user_id` and `tenant_id` from JWT

2. **AK/SK Signature Authentication**
   - Verify request integrity and source
   - Prevent request tampering and replay attacks

### Signature Algorithm

#### Signature Steps

1. **Construct String to Sign**
   ```
   string_to_sign = access_key + timestamp + request_body
   ```

2. **Calculate HMAC-SHA256 Signature**
   ```python
   import hmac
   import hashlib
   
   signature = hmac.new(
       secret_key.encode('utf-8'),
       string_to_sign.encode('utf-8'),
       hashlib.sha256
   ).hexdigest()
   ```

3. **Set Request Headers**
   ```http
   X-Access-Key: your_access_key
   X-Timestamp: 1640995200
   X-Signature: a1b2c3d4e5f6...
   ```

#### Signature Examples

**Python Example**
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

# Usage example
access_key = "your_access_key"
secret_key = "your_secret_key"
body = {"conversation_id": "test-123", "query": "Hello"}

timestamp, signature = generate_signature(access_key, secret_key, body)
```

**JavaScript Example**
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

## Interface Specifications

### Request Specifications

#### Common Request Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | Bearer JWT Token |
| `X-Access-Key` | string | Yes | Access key |
| `X-Timestamp` | string | Yes | Unix timestamp (seconds) |
| `X-Signature` | string | Yes | HMAC-SHA256 signature |
| `Content-Type` | string | Yes | application/json |
| `X-Request-Id` | string | No | Request tracking ID |
| `Idempotency-Key` | string | No | Idempotency key |

#### Response Format

**Success Response**
```json
{
    "message": "success",
    "data": { ... },
    "requestId": "req-123456"
}
```

**Error Response**
```json
{
    "message": "Error description"
}
```

### Streaming Response Specifications

Streaming interfaces use Server-Sent Events (SSE) format:

```
data: {"type":"chunk","content":"Partial response content"}
data: {"type":"chunk","content":"More content..."}
data: {"type":"done"}
```

## API Interfaces

### 1. Health Check

Check service status, no authentication required.

**Interface Information**
- **URL**: `GET /health`
- **Authentication**: Not required
- **Response**: JSON

**Request Example**
```bash
curl -X GET "https://api.example.com/api/nb/v1/health"
```

**Response Example**
```json
{
    "status": "healthy",
    "service": "northbound-api"
}
```

### 2. Start Conversation (Streaming)

Start agent conversation with streaming response support.

**Interface Information**
- **URL**: `POST /chat/run`
- **Authentication**: Required
- **Response**: SSE streaming

**Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conversation_id` | string | Yes | External conversation ID |
| `agent_name` | string | Yes | Agent name |
| `query` | string | Yes | User question |

**Request Example**
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
    "query": "Hello, please introduce yourself"
  }'
```

**Response Example**
```
data: {"type":"chunk","content":"Hello! I am"}
data: {"type":"chunk","content":"an intelligent assistant"}
data: {"type":"chunk","content":", happy to serve you."}
data: {"type":"done"}
```

### 3. Stop Conversation

Stop an ongoing conversation.

**Interface Information**
- **URL**: `GET /chat/stop/{conversation_id}`
- **Authentication**: Required
- **Response**: JSON

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conversation_id` | string | Yes | External conversation ID |

**Request Example**
```bash
curl -X GET "https://api.example.com/api/nb/v1/chat/stop/conv-123" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature"
```

**Response Example**
```json
{
    "message": "successfully stopped agent run and/or preprocess tasks for user_id xxx, conversation_id yyy",
    "data": "conv-123",
    "requestId": "req-123456"
}
```

### 4. Get Conversation History

Get historical messages for a specified conversation.

**Interface Information**
- **URL**: `GET /conversations/{conversation_id}`
- **Authentication**: Required
- **Response**: JSON

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conversation_id` | string | Yes | External conversation ID |

**Request Example**
```bash
curl -X GET "https://api.example.com/api/nb/v1/conversations/conv-123" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature"
```

**Response Example**
```json
{
    "message": "success",
    "data": {
        "conversation_id": "conv-123",
        "history": [
            {
                "role": "user",
                "content": "Hello"
            },
            {
                "role": "assistant",
                "content": "Hello! How can I help you?"
            }
        ]
    },
    "requestId": "req-123456"
}
```

### 5. Get Agent List

Get the list of available agents for the tenant.

**Interface Information**
- **URL**: `GET /agents`
- **Authentication**: Required
- **Response**: JSON

**Request Example**
```bash
curl -X GET "https://api.example.com/api/nb/v1/agents" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature"
```

**Response Example**
```json
{
    "message": "success",
    "data": [
        {
            "name": "assistant",
            "display_name": "Intelligent Assistant",
            "description": "General-purpose intelligent assistant",
            "is_available": true
        },
        {
            "name": "code_helper",
            "display_name": "Code Assistant",
            "description": "Professional assistant for programming-related questions",
            "is_available": true
        }
    ],
    "requestId": "req-123456"
}
```

### 6. Get Conversation List

Get all conversation lists for the tenant.

**Interface Information**
- **URL**: `GET /conversations`
- **Authentication**: Required
- **Response**: JSON

**Request Example**
```bash
curl -X GET "https://api.example.com/api/nb/v1/conversations" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature"
```

**Response Example**
```json
{
    "message": "success",
    "data": [
        {
            "conversation_id": "conv-123",
            "conversation_title": "Technical Discussion",
            "create_time": 1640995200000,
            "update_time": 1640995800000
        },
        {
            "conversation_id": "conv-124",
            "conversation_title": "Product Consultation",
            "create_time": 1640994000000,
            "update_time": 1640994600000
        }
    ],
    "requestId": "req-123456"
}
```

### 7. Update Conversation Title

Update the title of a specified conversation.

**Interface Information**
- **URL**: `PUT /conversations/{conversation_id}/title`
- **Authentication**: Required
- **Response**: JSON

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conversation_id` | string | Yes | External conversation ID |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | New title |

**Request Example**
```bash
curl -X PUT "https://api.example.com/api/nb/v1/conversations/conv-123/title?title=New Title" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "X-Access-Key: your_access_key" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature" \
  -H "Idempotency-Key: unique-key-456"
```

**Response Example**
```json
{
    "message": "success",
    "data": "conv-123",
    "requestId": "req-123456",
    "idempotency_key": "unique-key-456"
}
```

## Error Handling

### HTTP Status Codes

| Status Code | Description | Handling Suggestion |
|-------------|-------------|---------------------|
| 200 | Success | Process response normally |
| 400 | Bad Request | Check request parameters |
| 401 | Authentication Failed | Check JWT Token and signature |
| 429 | Too Many Requests | Implement backoff retry strategy |
| 500 | Server Error | Contact technical support |

### Common Errors

#### Authentication Errors

**401 Unauthorized**
```json
{
    "message": "Unauthorized: No authorization header found"
}
```

**Solution**:
- Check if `Authorization` request header is set correctly
- Confirm JWT Token is not expired
- Verify AK/SK signature is correct

#### Signature Errors

**401 Unauthorized - Invalid Signature**
```json
{
    "message": "Unauthorized: invalid signature"
}
```

**Solution**:
- Check signature algorithm implementation
- Confirm timestamp is synchronized with server time
- Verify request body string used in signature is consistent

#### Rate Limiting

**429 Too Many Requests**
```json
{
    "message": "Too Many Requests: rate limit exceeded"
}
```

**Solution**:
- Implement exponential backoff retry strategy
- Use `Idempotency-Key` to avoid duplicate requests
- Reduce request frequency

## Best Practices

### Security Best Practices

1. **Key Management**
   - Use environment variables to store sensitive information
   - Regularly rotate AK/SK keys
   - Never hardcode keys in code

2. **Time Synchronization**
   - Ensure client time is synchronized with server time
   - Use NTP service for time synchronization
   - Signature timestamp should be within reasonable range

3. **Request Security**
   - Always use HTTPS protocol
   - Verify response integrity
   - Log requests for audit purposes

### Performance Optimization

1. **Connection Reuse**
   - Use HTTP connection pooling
   - Enable Keep-Alive
   - Set reasonable timeout values

2. **Streaming Processing**
   - Use SSE-capable clients
   - Process streaming data promptly
   - Avoid blocking main thread

3. **Error Retry**
   - Implement exponential backoff strategy
   - Set maximum retry count
   - Distinguish between retryable and non-retryable errors

### Idempotency Handling

1. **Use Idempotency-Key**
   ```python
   import uuid
   
   idempotency_key = str(uuid.uuid4())
   headers = {
       "Idempotency-Key": idempotency_key,
       # ... other request headers
   }
   ```

2. **Retry Strategy**
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

## Troubleshooting

### Common Issues

#### 1. Signature Verification Failed

**Problem**: Returns 401 error, indicating invalid signature

**Troubleshooting Steps**:
1. Check if AK/SK are correct
2. Verify timestamp format and range
3. Confirm request body string matches signature
4. Check if character encoding is UTF-8

#### 2. Invalid JWT Token

**Problem**: Returns 401 error, indicating authentication failed

**Troubleshooting Steps**:
1. Check Token format: `Bearer <token>`
2. Verify Token is not expired
3. Confirm `sub` field exists in Token
4. Check tenant binding relationship

#### 3. Streaming Response Interrupted

**Problem**: SSE connection unexpectedly disconnected

**Troubleshooting Steps**:
1. Check network connection stability
2. Increase connection timeout
3. Implement reconnection mechanism
4. Check server-side logs

#### 4. Rate Limiting

**Problem**: Frequently returns 429 errors

**Solution**:
1. Reduce request frequency
2. Use `Idempotency-Key` to avoid duplicate requests
3. Implement request queue management
4. Contact technical support to adjust limits

### Debugging Tools

#### 1. Request Logging

```python
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def log_request(method, url, headers, body=None):
    logger.debug(f"Request: {method} {url}")
    logger.debug(f"Headers: {headers}")
    if body:
        logger.debug(f"Body: {body}")
```

#### 2. Signature Verification Tool

```python
def verify_signature(access_key, secret_key, timestamp, signature, body=""):
    """Verify if signature is correct"""
    string_to_sign = f"{access_key}{timestamp}{body}"
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature == expected_signature
```

#### 3. Response Time Monitoring

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

### Contact Support

If you encounter issues that cannot be resolved, please provide the following information:

1. **Request Information**
   - Complete request URL
   - Request headers and body
   - Timestamp and signature

2. **Error Information**
   - Complete error response
   - Error occurrence time
   - Reproduction steps

3. **Environment Information**
   - Client version
   - Operating system information
   - Network environment

---

*This document was last updated: January 2024*
