from typing import List
import os
from platform import system, machine, python_version
import requests

class GroqModel:
    """
    Groq API integration for RawWick assistant.
    
    This class handles communication with the Groq API to generate responses
    to user commands. It maintains a conversation history and formats system
    prompts to ensure the AI responds with executable code.
    """
    def __init__(self, api_key: str, model="llama3-70b-8192", temperature=0.2, max_tokens=1024):
        """
        Initialize the Groq model with API credentials and parameters.
        
        Args:
            api_key: Your Groq API key
            model: The model to use (default: llama3-70b-8192)
            temperature: Controls randomness (0.0-1.0, lower is more deterministic)
            max_tokens: Maximum number of tokens in the response
        """
        
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.chat_history = []
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def chat(self, query: str) -> str:
        """
        Send a query to the Groq API and get a response.
        
        This method formats the conversation with system context and user query,
        then sends it to the Groq API. The response is expected to contain
        executable code that the RawWick executor can run.
        
        Args:
            query: The user's command or question
            
        Returns:
            The AI's response containing executable code
        """
        
        shell = os.environ.get("SHELL") or os.environ.get("COMSPEC") or "unknown"
        platform_info = (
            f"OS: {system().lower()}, "
            f"Shell: {os.path.basename(shell).lower()}, "
            f"Arch: {machine()}, "
            f"Python: {python_version()}"
        )

        self.chat_history.append({
            "role": "system",
            "content": (
                "You're RawWick, a voice-activated AI assistant created by AbdulKarim. "
                "If a task is asked (e.g. 'open notepad', 'launch camera', 'list files'), respond only with Python or shell code "
                "that performs the task. Never explain or give instructions. Wrap the code in triple backticks (```), so it can be executed. "
                "Don't ask the user for permission. Assume full access to OS APIs, commands, and disk. Avoid assistant-like responses. "
                "Focus on clean architecture, scalability, and real-world applications. "
                "Remember: Backend is home, frontend is playground, and systems are the gym. "
                f"Platform context: {platform_info}."
            )
        })
        self.chat_history.append({"role": "user", "content": query})

        body = {
            "model": self.model,
            "messages": self.chat_history,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        res = requests.post(self.api_url, headers=self.headers, json=body)
        res.raise_for_status()
        reply = res.json()["choices"][0]["message"]["content"]
        self.chat_history.append({"role": "assistant", "content": reply})
        return reply