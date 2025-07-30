from Listen import ContinuousListener
from core.agent import system_agent
import time

def main():
    """
    Main function to run the RawWick voice assistant system.
    
    This function initializes the voice recognition system and connects it to the
    AI-powered executor that processes voice commands. The system will continue
    running until the user says 'exit', 'quit', or 'stop'.
    """
    
    # Create and start the continuous listener
    listener = ContinuousListener(on_command_received=lambda cmd: 
                                 print(f"🔔 Command received: {cmd}"))
    
    listener.start_listening(process_commands=True, processor_func=system_agent)
    
    # Wait for the listener to finish (when exit command is given)
    # This keeps the main thread alive until the listener is stopped
    try:
        # Keep the main thread alive
        while listener.listening_active:
            time.sleep(0.5)
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n⚠️ Keyboard interrupt detected. Shutting down...")
    finally:
        # Ensure we stop the listener properly
        listener.stop_listening()
        print("✅ All tasks completed. System shutdown.")

if __name__ == "__main__":
    main()