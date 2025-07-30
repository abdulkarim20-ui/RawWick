# Example: Basic usage of RawWick

from Listen import ContinuousListener
from core.agent import system_agent
import time

def basic_example():
    """
    Demonstrates the basic usage of RawWick with a simple voice command workflow.
    
    This example shows how to:
    1. Initialize the voice listener
    2. Process commands through the RawWick system
    3. Handle the listener lifecycle properly
    """
    print("\n===== RawWick Basic Example =====\n")
    print("This example will listen for voice commands and process them.")
    print("Say 'exit' or press Ctrl+C to quit.\n")
    
    # Create a listener with a simple callback for notifications
    listener = ContinuousListener(
        on_command_received=lambda cmd: print(f"\n✅ Command received: \"{cmd}\"\n")
    )
    
    # Start listening and connect to the RawWick system agent
    listener.start_listening(process_commands=True, processor_func=system_agent)
    
    try:
        # Keep the main thread alive while listening
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
    basic_example()