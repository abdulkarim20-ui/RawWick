# Example: Using RawWick with custom command handling

from Listen import ContinuousListener
from core.agent import TaskExecutor
from models.groq import GroqModel
from executors.rawwick_executor import RawWickExecutor
from utils.cache import FixCache
from core.context_manager import ContextManager
import time
import os

def custom_command_example():
    """
    Demonstrates how to use RawWick with custom command handling.
    
    This example shows how to:
    1. Create a custom TaskExecutor instance
    2. Add pre-processing for commands
    3. Handle specific commands directly without AI
    """
    print("\n===== RawWick Custom Commands Example =====\n")
    print("This example shows how to handle custom commands.")
    print("Try saying 'hello', 'time', or any other command.")
    print("Say 'exit' or press Ctrl+C to quit.\n")
    
    # Create a custom command processor
    class CustomCommandProcessor:
        def __init__(self):
            # Initialize the context manager
            self.context_manager = ContextManager()
            
            # Initialize with a mock API key (replace with your actual key)
            # In a real application, load this from a secure source
            api_key = os.environ.get("GROQ_API_KEY", "your-api-key-here")
            
            # Initialize the AI model
            self.ai = GroqModel(api_key=api_key)
            
            # Initialize the cache
            self.cache = FixCache()
            
            # Initialize the executor
            self.executor = RawWickExecutor(
                ai=self.ai,
                fix_cache=self.cache,
                context_manager=self.context_manager
            )
        
        def process_command(self, command):
            # Pre-process the command
            command = command.strip().lower()
            
            # Handle custom commands directly
            if command == "hello":
                print("👋 Hello! I'm RawWick, your voice assistant.")
                return
                
            elif command == "time":
                current_time = time.strftime("%H:%M:%S", time.localtime())
                print(f"🕒 The current time is {current_time}")
                return
            
            # For all other commands, use the AI executor
            print(f"🧠 Processing with AI: {command}")
            
            # Update workspace context
            self.context_manager.update_workspace_state(os.getcwd())
            
            # Process with AI
            try:
                response = self.ai.chat(command)
                self.executor.process(response)
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Create the processor
    processor = CustomCommandProcessor()
    
    # Create and start the listener
    listener = ContinuousListener(
        on_command_received=lambda cmd: print(f"📝 Command received: \"{cmd}\"")
    )
    
    # Start listening with our custom processor
    listener.start_listening(
        process_commands=True, 
        processor_func=processor.process_command
    )
    
    try:
        # Keep the main thread alive
        while listener.listening_active:
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted. Exiting example.")
        
    finally:
        # Always stop the listener properly
        if listener:
            listener.stop_listening()
            print("✅ Listener stopped. Example complete.")

if __name__ == "__main__":
    custom_command_example()