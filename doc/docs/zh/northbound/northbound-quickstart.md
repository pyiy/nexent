# 北向接口快速开始

## 5分钟快速上手

本指南将帮助您在5分钟内完成北向接口的集成和测试。

## 前置条件

- 已获得有效的 JWT Token
- 已获得 Access Key (AK) 和 Secret Key (SK)
- 具备基本的 HTTP 客户端编程能力

## 步骤1：环境准备

### 获取访问凭证

联系平台管理员获取以下凭证：

1. **JWT Token**：用于用户身份验证
2. **Access Key**：API 访问密钥
3. **Secret Key**：用于签名验证的密钥

### 配置环境变量

```bash
# 设置环境变量
export JWT_TOKEN="your_jwt_token_here"
export ACCESS_KEY="your_access_key_here"
export SECRET_KEY="your_secret_key_here"
export API_BASE_URL="https://api.example.com/api/nb/v1"
```

## 步骤2：健康检查

首先验证服务是否可用：

```bash
curl -X GET "${API_BASE_URL}/health"
```

期望响应：
```json
{
    "status": "healthy",
    "service": "northbound-api"
}
```

## 步骤3：实现签名算法

### Python 实现

```python
import hmac
import hashlib
import json
import time
import requests

def generate_signature(access_key, secret_key, body=None):
    """生成请求签名"""
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
    """发送认证请求"""
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

### JavaScript 实现

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

## 步骤4：测试基础功能

### 1. 获取智能体列表

```python
# Python
response = make_authenticated_request("GET", "/agents")
print("智能体列表:", response.json())
```

```javascript
// JavaScript
const response = await makeAuthenticatedRequest("GET", "/agents");
const data = await response.json();
console.log("智能体列表:", data);
```

### 2. 启动对话（流式）

```python
# Python - 流式对话
import httpx

async def start_chat():
    timestamp, signature = generate_signature(ACCESS_KEY, SECRET_KEY, {
        "conversation_id": "test-123",
        "agent_name": "assistant",
        "query": "你好，请介绍一下自己"
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
                "query": "你好，请介绍一下自己"
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # 移除 "data: " 前缀
                    print("收到:", data)

# 运行流式对话
import asyncio
asyncio.run(start_chat())
```

### 3. 获取会话历史

```python
# Python
response = make_authenticated_request("GET", "/conversations/test-123")
print("会话历史:", response.json())
```

## 步骤5：错误处理

### 实现重试机制

```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    """带退避的重试机制"""
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            
            # 指数退避 + 随机抖动
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"请求失败，{wait_time:.2f}秒后重试... (尝试 {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

# 使用示例
def get_agents():
    return make_authenticated_request("GET", "/agents")

try:
    response = retry_with_backoff(get_agents)
    print("成功获取智能体列表:", response.json())
except Exception as e:
    print("获取智能体列表失败:", str(e))
```

## 步骤6：完整示例

### Python 完整示例

```python
#!/usr/bin/env python3
"""
北向接口完整示例
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
        """生成请求签名"""
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
        """获取认证请求头"""
        timestamp, signature = self._generate_signature(body)
        return {
            "Authorization": f"Bearer {self.jwt_token}",
            "X-Access-Key": self.access_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "Content-Type": "application/json"
        }
    
    def health_check(self) -> dict:
        """健康检查"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def get_agents(self) -> dict:
        """获取智能体列表"""
        headers = self._get_headers()
        response = requests.get(f"{self.base_url}/agents", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def get_conversations(self) -> dict:
        """获取会话列表"""
        headers = self._get_headers()
        response = requests.get(f"{self.base_url}/conversations", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def get_conversation_history(self, conversation_id: str) -> dict:
        """获取会话历史"""
        headers = self._get_headers()
        response = requests.get(f"{self.base_url}/conversations/{conversation_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def stop_chat(self, conversation_id: str) -> dict:
        """停止对话"""
        headers = self._get_headers()
        response = requests.get(f"{self.base_url}/chat/stop/{conversation_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def update_conversation_title(self, conversation_id: str, title: str) -> dict:
        """更新会话标题"""
        headers = self._get_headers()
        response = requests.put(
            f"{self.base_url}/conversations/{conversation_id}/title",
            headers=headers,
            params={"title": title}
        )
        response.raise_for_status()
        return response.json()
    
    async def start_chat_stream(self, conversation_id: str, agent_name: str, query: str):
        """启动流式对话"""
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
                        data = line[6:]  # 移除 "data: " 前缀
                        try:
                            chunk = json.loads(data)
                            if chunk.get("type") == "chunk":
                                print(chunk.get("content", ""), end="", flush=True)
                            elif chunk.get("type") == "done":
                                print("\n[对话结束]")
                                break
                        except json.JSONDecodeError:
                            print(f"解析数据失败: {data}")

def main():
    # 从环境变量获取配置
    base_url = os.getenv("API_BASE_URL", "https://api.example.com/api/nb/v1")
    jwt_token = os.getenv("JWT_TOKEN")
    access_key = os.getenv("ACCESS_KEY")
    secret_key = os.getenv("SECRET_KEY")
    
    if not all([jwt_token, access_key, secret_key]):
        print("请设置环境变量: JWT_TOKEN, ACCESS_KEY, SECRET_KEY")
        return
    
    # 创建客户端
    client = NorthboundClient(base_url, jwt_token, access_key, secret_key)
    
    try:
        # 1. 健康检查
        print("1. 健康检查...")
        health = client.health_check()
        print(f"   服务状态: {health}")
        
        # 2. 获取智能体列表
        print("\n2. 获取智能体列表...")
        agents = client.get_agents()
        print(f"   可用智能体: {len(agents.get('data', []))} 个")
        for agent in agents.get('data', []):
            print(f"   - {agent.get('name')}: {agent.get('display_name')}")
        
        # 3. 获取会话列表
        print("\n3. 获取会话列表...")
        conversations = client.get_conversations()
        print(f"   会话数量: {len(conversations.get('data', []))}")
        
        # 4. 启动流式对话
        print("\n4. 启动流式对话...")
        conversation_id = "quickstart-test"
        agent_name = "assistant"  # 使用第一个可用的智能体
        query = "你好，请简单介绍一下自己"
        
        print(f"   对话ID: {conversation_id}")
        print(f"   智能体: {agent_name}")
        print(f"   问题: {query}")
        print("   回答: ", end="", flush=True)
        
        # 运行流式对话
        asyncio.run(client.start_chat_stream(conversation_id, agent_name, query))
        
        # 5. 获取对话历史
        print("\n5. 获取对话历史...")
        history = client.get_conversation_history(conversation_id)
        messages = history.get('data', {}).get('history', [])
        print(f"   历史消息: {len(messages)} 条")
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:50] + "..." if len(msg.get('content', '')) > 50 else msg.get('content', '')
            print(f"   {role}: {content}")
        
        print("\n✅ 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print("请检查:")
        print("1. 网络连接是否正常")
        print("2. 访问凭证是否正确")
        print("3. API 地址是否正确")

if __name__ == "__main__":
    main()
```

### 运行示例

```bash
# 设置环境变量
export JWT_TOKEN="your_jwt_token"
export ACCESS_KEY="your_access_key" 
export SECRET_KEY="your_secret_key"
export API_BASE_URL="https://api.example.com/api/nb/v1"

# 运行示例
python northbound_example.py
```

## 常见问题

### Q: 签名验证失败怎么办？

A: 检查以下几点：
1. 确认 AK/SK 是否正确
2. 检查时间戳是否在有效范围内
3. 确认请求体字符串与签名时一致
4. 验证字符编码为 UTF-8

### Q: 流式响应中断怎么办？

A: 实现断线重连机制：
```python
async def start_chat_with_retry(client, conversation_id, agent_name, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            await client.start_chat_stream(conversation_id, agent_name, query)
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"连接中断，{2**attempt}秒后重试...")
            await asyncio.sleep(2 ** attempt)
```

### Q: 如何处理频率限制？

A: 实施指数退避策略：
```python
import time
import random

def retry_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # 频率限制
                if attempt == max_retries - 1:
                    raise
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                raise
```

## 下一步

- 阅读完整的 [北向接口文档](./northbound-api.md)
- 了解 [错误处理最佳实践](./northbound-api.md#错误处理)
- 查看 [性能优化建议](./northbound-api.md#最佳实践)

---

*快速开始指南 - 让您在5分钟内完成北向接口集成*
