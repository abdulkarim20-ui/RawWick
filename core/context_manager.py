from typing import Dict, List, Optional
import json
import os
from datetime import datetime

class ContextManager:
    """
    Manages context and history for the RawWick assistant.
    
    This class keeps track of command history, workspace state, and other
    contextual information to help the AI provide more relevant and
    personalized responses based on previous interactions.
    """
    def __init__(self):
        """
        Initialize the context manager with empty history and context.
        """
        
        self.command_history: List[Dict] = []
        self.context_memory: Dict[str, any] = {}
        self.workspace_state: Dict[str, any] = {}
        self.session_start = datetime.now()

    def add_command(self, command: str, result: str, success: bool):
        """
        Add a command and its result to the history.
        
        Args:
            command: The command that was executed
            result: The result or output of the command
            success: Whether the command executed successfully
        """
        self.command_history.append({
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "result": result,
            "success": success
        })

    def get_relevant_history(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Find commands from history that are relevant to the current query.
        
        This method uses a simple word-matching algorithm to find commands
        that share words with the current query, which helps provide context
        for the AI to understand related commands.
        
        Args:
            query: The current user query
            limit: Maximum number of relevant history items to return
            
        Returns:
            A list of the most relevant command history entries
        """
        # Simple relevance scoring based on command similarity
        scored_history = [
            (entry, len(set(query.lower().split()) & set(entry["command"].lower().split())))
            for entry in self.command_history
        ]
        return [entry for entry, score in sorted(scored_history, key=lambda x: x[1], reverse=True)[:limit]]

    def update_workspace_state(self, path: str):
        """
        Update the current workspace information.
        
        This method scans the current directory to gather information about
        available files and folders, which helps the AI understand the
        user's working environment.
        
        Args:
            path: The directory path to scan
        """
        self.workspace_state = {
            "current_dir": os.path.abspath(path),
            "files": [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))],
            "dirs": [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        }

    def add_context(self, key: str, value: any):
        """
        Store a value in the context memory.
        
        Args:
            key: The identifier for the context value
            value: The value to store
        """
        self.context_memory[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }

    def get_context(self, key: str) -> Optional[any]:
        """
        Retrieve a value from the context memory.
        
        Args:
            key: The identifier for the context value
            
        Returns:
            The stored value, or None if not found
        """
        return self.context_memory.get(key, {}).get("value")

    def get_session_summary(self) -> Dict:
        """
        Generate a summary of the current session.
        
        Returns:
            A dictionary containing session statistics
        """
        return {
            "session_duration": str(datetime.now() - self.session_start),
            "command_count": len(self.command_history),
            "success_rate": sum(1 for cmd in self.command_history if cmd["success"]) / len(self.command_history) if self.command_history else 0
        }