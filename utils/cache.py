import json
import os

class FixCache:
    """
    A simple caching system for RawWick to store and retrieve fixed code snippets.
    
    This class provides persistent storage of code fixes, allowing RawWick to
    remember solutions to common problems and apply them automatically in
    future sessions.
    """
    def __init__(self, path="fix_cache.json"):
        """
        Initialize the cache with a file path.
        
        Args:
            path: The file path where cache data will be stored
        """
        
        self.path = path
        self.data = self.load()

    def load(self):
        """
        Load the cache data from disk.
        
        Returns:
            The loaded cache data, or an empty dict if the file doesn't exist
        """
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                return json.load(f)
        return {}

    def save(self):
        """
        Save the current cache data to disk.
        """
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def get(self, code: str):
        """
        Retrieve a fixed version of code from the cache.
        
        Args:
            code: The broken code to look up
            
        Returns:
            The fixed code if found, otherwise None
        """
        return self.data.get(code.strip())

    def add(self, broken_code: str, fixed_code: str):
        """
        Add a new code fix to the cache.
        
        Args:
            broken_code: The problematic code
            fixed_code: The corrected version of the code
        """
        self.data[broken_code.strip()] = fixed_code.strip()
        self.save()