import logging
import threading
import json
import requests
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

from smolagents import Tool
from smolagents.models import ChatMessage

from ..utils.observer import MessageObserver, ProcessType

logger = logging.getLogger("restful_llm")

class RestfulLLMModel:
    def __init__(self, 
                 observer: MessageObserver, 
                 base_url: str,
                 api_key: str,
                 model_name: str = "qwen",
                 temperature: float = 0.2, 
                 top_p: float = 0.95,
                 timeout: int = 60,
                 *args, **kwargs):
        """
        Initialize RESTful LLM model
        
        Args:
            observer: Message observer, used to handle streaming output
            base_url: API base URL
            api_key: API key, will be used as Bearer Token
            model_name: Model name
            temperature: Temperature parameter
            top_p: top_p parameter
            timeout: Request timeout
        """
        self.observer = observer
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.timeout = timeout
        self.stop_event = threading.Event()
        
        # Set request headers
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def _convert_messages_format(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert messages from smolagents format to simple string format
        
        Args:
            messages: Original messages from smolagents
            
        Returns:
            List[Dict[str, Any]]: Converted messages with string content
        """
        converted_messages = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            # Handle different content formats
            if isinstance(content, list):
                # Extract text from complex content format
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text" and "text" in item:
                            text_parts.append(item["text"])
                        elif "text" in item:
                            text_parts.append(item["text"])
                    elif isinstance(item, str):
                        text_parts.append(item)
                content = " ".join(text_parts)
            elif not isinstance(content, str):
                content = str(content)
            
            converted_messages.append({
                "role": role,
                "content": content
            })
        
        return converted_messages

    def __call__(self, 
                 messages: List[Dict[str, Any]], 
                 stop_sequences: Optional[List[str]] = None,
                 grammar: Optional[str] = None, 
                 tools_to_call_from: Optional[List[Tool]] = None, 
                 **kwargs) -> ChatMessage:
        """
        Call RESTful LLM model
        
        Args:
            messages: Message list
            stop_sequences: Stop sequences
            grammar: Grammar rules
            tools_to_call_from: Available tool list
            **kwargs: Other parameters
            
        Returns:
            ChatMessage: Model response message
        """
        try:
            # Convert messages format if needed
            converted_messages = self._convert_messages_format(messages)
            
            # Prepare request body
            url = f"{self.base_url.rstrip('/')}/chat/completions"
            request_body = {
                "model": self.model_name,
                "stream": True,
                "messages": converted_messages,
                "temperature": self.temperature,
                "top_p": self.top_p,
                **kwargs
            }
            
            # Add stop sequences (if supported)
            if stop_sequences:
                request_body["stop"] = stop_sequences
                request_body["include_stop_str_in_output"] = True
            
            # Send streaming request
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(request_body),
                stream=True,
                timeout=self.timeout,
                verify=False
            )
            
            if response.status_code != 200:
                logger.error(f"Connection test failed: {url=}, {request_body=}, "
                             f"{response.status_code} - {response.text}")
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            chunk_list = []
            token_join = []
            role = None
            
            # Reset output mode
            self.observer.current_mode = ProcessType.MODEL_OUTPUT_THINKING
            
            # Process streaming response
            for line in response.iter_lines():
                if self.stop_event.is_set():
                    raise RuntimeError("Model is interrupted by stop event")
                
                if line:
                    # Remove "data: " prefix (if exists)
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]
                    
                    # Skip [DONE] marker
                    if line_str.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk_data = json.loads(line_str)
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            choice = chunk_data["choices"][0]
                            
                            # Process incremental content
                            if "delta" in choice:
                                delta = choice["delta"]
                                if "content" in delta and delta["content"]:
                                    new_token = delta["content"]
                                    self.observer.add_model_new_token(new_token)
                                    token_join.append(new_token)
                                
                                if "role" in delta and delta["role"]:
                                    role = delta["role"]
                            
                            chunk_list.append(chunk_data)
                    except json.JSONDecodeError:
                        logger.warning(f"Cannot parse JSON response: {line_str}")
                        continue
            
            # Send end marker
            self.observer.flush_remaining_tokens()
            model_output = "".join(token_join)
            
            # Create response message
            message = ChatMessage(
                role=role if role else "assistant",
                content=model_output
            )
            
            message.raw = chunk_list
            return message
            
        except Exception as e:
            if "context_length_exceeded" in str(e) or "token" in str(e).lower():
                raise ValueError(f"Token limit exceeded: {str(e)}")
            raise e

    def check_connectivity(self) -> bool:
        """
        Test the connection to the RESTful LLM service
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            url = f"{self.base_url.rstrip('/')}/chat/completions"
            test_message = [{"role": "user", "content": "Hello"}]
            
            # Send non-streaming request for connection test
            request_body = {
                "model": self.model_name,
                "stream": False,
                "messages": test_message
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(request_body),
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Connection test failed: {url=}, {request_body=}, {self.headers=}, "
                             f"{response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def stop(self):
        """
        Stop model running
        """
        self.stop_event.set() 