# Northbound API Quick Start

## 5-Minute Quick Start

This guide will help you complete Northbound API integration and testing in 5 minutes.

## Prerequisites

- Valid JWT Token obtained
- Access Key (AK) and Secret Key (SK) obtained
- Basic HTTP client programming skills

## Step 1: Environment Setup

### Get Access Credentials

Contact the platform administrator to obtain the following credentials:

1. **JWT Token**: For user identity authentication
2. **Access Key**: API access key
3. **Secret Key**: Key for signature verification

### Configure Environment Variables

```bash
# Set environment variables
export JWT_TOKEN="your_jwt_token_here"
export ACCESS_KEY="your_access_key_here"
export SECRET_KEY="your_secret_key_here"
export API_BASE_URL="https://api.example.com/api/nb/v1"
```

## Step 2: Health Check

First, verify if the service is available:

```bash
curl -X GET "${API_BASE_URL}/health"
```

Expected response:
```json
{
    "status": "healthy",
    "service": "northbound-api"
}
```

## Step 3: Implement Signature Algorithm

### Python Implementation

```python
import hmac
import hashlib
import json
import time
import requests

def generate_signature(access_key, secret_key, body=None):
    """Generate request signature"""
    timestamp = str(int(time.time()))
    body_str = "" if body is None else json.dumps(body, separators=(',', ':'))
    string_to_sign = f"{access_key}{timestamp}{body_str}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return timestamp, signature

def make_authenticated_request(method, endpoint, body=None):
    """Send authenticated request"""
    timestamp, signature = generate_signature(ACCESS_KEY, SECRET_KEY, body)
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "X-Access-Key": ACCESS_KEY,
        "X-Timestamp": timestamp,
        "X-Signature": signature,
        "Content-Type": "application/json"
    }
    
    url = f"{API_BASE_URL}{endpoint}"
    
    if method.upper() == "GET":
        response = requests.get(url, headers=headers)
    else:
        response = requests.post(url, headers=headers, json=body)
    
    return response
```

### JavaScript Implementation

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

async function makeAuthenticatedRequest(method, endpoint, body = null) {
    const { timestamp, signature } = generateSignature(ACCESS_KEY, SECRET_KEY, body);
    
    const headers = {
        'Authorization': `Bearer ${JWT_TOKEN}`,
        'X-Access-Key': ACCESS_KEY,
        'X-Timestamp': timestamp,
        'X-Signature': signature,
        'Content-Type': 'application/json'
    };
    
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined
    });
    
    return response;
}
```

## Step 4: Test Basic Functions

### 1. Get Agent List

```python
# Python
response = make_authenticated_request("GET", "/agents")
print("Agent list:", response.json())
```

```javascript
// JavaScript
const response = await makeAuthenticatedRequest("GET", "/agents");
const data = await response.json();
console.log("Agent list:", data);
```

### 2. Start Conversation (Streaming)

```python
# Python - Streaming conversation
import httpx

async def start_chat():
    timestamp, signature = generate_signature(ACCESS_KEY, SECRET_KEY, {
        "conversation_id": "test-123",
        "agent_name": "assistant",
        "query": "Hello, please introduce yourself"
    })
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "X-Access-Key": ACCESS_KEY,
        "X-Timestamp": timestamp,
        "X-Signature": signature,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST", 
            f"{API_BASE_URL}/chat/run",
            headers=headers,
            json={
                "conversation_id": "test-123",
                "agent_name": "assistant", 
                "query": "Hello, please introduce yourself"
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    print("Received:", data)

# Run streaming conversation
import asyncio
asyncio.run(start_chat())
```

### 3. Get Conversation History

```python
# Python
response = make_authenticated_request("GET", "/conversations/test-123")
print("Conversation history:", response.json())
```

## Step 5: Error Handling

### Implement Retry Mechanism

```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    """Retry mechanism with backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff + random jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Request failed, retrying in {wait_time:.2f} seconds... (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

# Usage example
def get_agents():
    return make_authenticated_request("GET", "/agents")

try:
    response = retry_with_backoff(get_agents)
    print("Successfully got agent list:", response.json())
except Exception as e:
    print("Failed to get agent list:", str(e))
```

## Step 6: Complete Example

### Python Complete Example

```python
#!/usr/bin/env python3
"""
Northbound API Complete Example
"""

import os
import hmac
import hashlib
import json
import time
import requests
import httpx
import asyncio
from typing import Optional

class NorthboundClient:
    def __init__(self, base_url: str, jwt_token: str, access_key: str, secret_key: str):
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.access_key = access_key
        self.secret_key = secret_key
    
    def _generate_signature(self, body: Optional[dict] = None) -> tuple[str, str]:
        """Generate request signature"""
        timestamp = str(int(time.time()))
        body_str = "" if body is None else json.dumps(body, separators=(',', ':'))
        string_to_sign = f"{self.access_key}{timestamp}{body_str}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return timestamp, signature
    
    def _get_headers(self, body: Optional[dict] = None) -> dict:
        """Get authenticated request headers"""
        timestamp, signature = self._generate_signature(body)
        return {
            "Authorization": f"Bearer {self.jwt_token}",
            "X-Access-Key": self.access_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "Content-Type": "application/json"
        }
    
    def health_check(self) -> dict:
        """Health check"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def get_agents(self) -> dict:
        """Get agent list"""
        headers = self._get_headers()
        response = requests.get(f"{self.base_url}/agents", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def get_conversations(self) -> dict:
        """Get conversation list"""
        headers = self._get_headers()
        response = requests.get(f"{self.base_url}/conversations", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def get_conversation_history(self, conversation_id: str) -> dict:
        """Get conversation history"""
        headers = self._get_headers()
        response = requests.get(f"{self.base_url}/conversations/{conversation_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def stop_chat(self, conversation_id: str) -> dict:
        """Stop conversation"""
        headers = self._get_headers()
        response = requests.get(f"{self.base_url}/chat/stop/{conversation_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def update_conversation_title(self, conversation_id: str, title: str) -> dict:
        """Update conversation title"""
        headers = self._get_headers()
        response = requests.put(
            f"{self.base_url}/conversations/{conversation_id}/title",
            headers=headers,
            params={"title": title}
        )
        response.raise_for_status()
        return response.json()
    
    async def start_chat_stream(self, conversation_id: str, agent_name: str, query: str):
        """Start streaming conversation"""
        body = {
            "conversation_id": conversation_id,
            "agent_name": agent_name,
            "query": query
        }
        headers = self._get_headers(body)
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/run",
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        try:
                            chunk = json.loads(data)
                            if chunk.get("type") == "chunk":
                                print(chunk.get("content", ""), end="", flush=True)
                            elif chunk.get("type") == "done":
                                print("\n[Conversation ended]")
                                break
                        except json.JSONDecodeError:
                            print(f"Failed to parse data: {data}")

def main():
    # Get configuration from environment variables
    base_url = os.getenv("API_BASE_URL", "https://api.example.com/api/nb/v1")
    jwt_token = os.getenv("JWT_TOKEN")
    access_key = os.getenv("ACCESS_KEY")
    secret_key = os.getenv("SECRET_KEY")
    
    if not all([jwt_token, access_key, secret_key]):
        print("Please set environment variables: JWT_TOKEN, ACCESS_KEY, SECRET_KEY")
        return
    
    # Create client
    client = NorthboundClient(base_url, jwt_token, access_key, secret_key)
    
    try:
        # 1. Health check
        print("1. Health check...")
        health = client.health_check()
        print(f"   Service status: {health}")
        
        # 2. Get agent list
        print("\n2. Get agent list...")
        agents = client.get_agents()
        print(f"   Available agents: {len(agents.get('data', []))}")
        for agent in agents.get('data', []):
            print(f"   - {agent.get('name')}: {agent.get('display_name')}")
        
        # 3. Get conversation list
        print("\n3. Get conversation list...")
        conversations = client.get_conversations()
        print(f"   Conversation count: {len(conversations.get('data', []))}")
        
        # 4. Start streaming conversation
        print("\n4. Start streaming conversation...")
        conversation_id = "quickstart-test"
        agent_name = "assistant"  # Use first available agent
        query = "Hello, please briefly introduce yourself"
        
        print(f"   Conversation ID: {conversation_id}")
        print(f"   Agent: {agent_name}")
        print(f"   Query: {query}")
        print("   Response: ", end="", flush=True)
        
        # Run streaming conversation
        asyncio.run(client.start_chat_stream(conversation_id, agent_name, query))
        
        # 5. Get conversation history
        print("\n5. Get conversation history...")
        history = client.get_conversation_history(conversation_id)
        messages = history.get('data', {}).get('history', [])
        print(f"   History messages: {len(messages)}")
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:50] + "..." if len(msg.get('content', '')) > 50 else msg.get('content', '')
            print(f"   {role}: {content}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("Please check:")
        print("1. Network connection is normal")
        print("2. Access credentials are correct")
        print("3. API address is correct")

if __name__ == "__main__":
    main()
```

### Run Example

```bash
# Set environment variables
export JWT_TOKEN="your_jwt_token"
export ACCESS_KEY="your_access_key" 
export SECRET_KEY="your_secret_key"
export API_BASE_URL="https://api.example.com/api/nb/v1"

# Run example
python northbound_example.py
```

## Common Issues

### Q: What to do if signature verification fails?

A: Check the following points:
1. Confirm AK/SK are correct
2. Check if timestamp is within valid range
3. Confirm request body string matches signature
4. Verify character encoding is UTF-8

### Q: What to do if streaming response is interrupted?

A: Implement reconnection mechanism:
```python
async def start_chat_with_retry(client, conversation_id, agent_name, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            await client.start_chat_stream(conversation_id, agent_name, query)
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Connection interrupted, retrying in {2**attempt} seconds...")
            await asyncio.sleep(2 ** attempt)
```

### Q: How to handle rate limiting?

A: Implement exponential backoff strategy:
```python
import time
import random

def retry_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limiting
                if attempt == max_retries - 1:
                    raise
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                raise
```

## Next Steps

- Read the complete [Northbound API Documentation](./northbound-api.md)
- Learn about [Error Handling Best Practices](./northbound-api.md#error-handling)
- Check out [Performance Optimization Suggestions](./northbound-api.md#best-practices)

---

*Quick Start Guide - Complete Northbound API integration in 5 minutes*
