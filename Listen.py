# Listen.py
#
# This module provides voice recognition capabilities for the RawWick assistant.
# It handles continuous listening for voice commands and converts speech to text
# using Google's speech recognition service.

import speech_recognition as sr
import threading
import queue
import time

# Create a recognizer instance with optimized settings
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300  # Lower threshold for better sensitivity
recognizer.pause_threshold = 0.8   # Shorter pause to detect end of speech faster
dynamic_energy_adjustment = True   # Dynamically adjust for ambient noise

# Lock for thread safety when adjusting recognizer settings
recognizer_lock = threading.Lock()

def listen():
    """Listen for speech input and convert to text.
    
    This function is designed to be non-blocking and efficient when used in a threaded context.
    It will attempt to recognize speech once, and return the result or an error message.
    """
    with sr.Microphone() as source:
        # Use a shorter duration for ambient noise adjustment to be more responsive
        with recognizer_lock:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
        
        try:
            # Set a reasonable phrase_time_limit to prevent hanging
            audio = recognizer.listen(source, timeout=2, phrase_time_limit=10)
            
            # Use Google's speech recognition service
            with recognizer_lock:
                text = recognizer.recognize_google(audio, language='en-US')
            return text.strip()
            
        except sr.WaitTimeoutError:
            # No speech detected within timeout period
            return ""
            
        except sr.UnknownValueError:
            # Speech was detected but couldn't be recognized
            return ""
            
        except sr.RequestError as e:
            # API error
            print(f"❌ API Error: {e}")
            return "Speech recognition failed."
            
        except Exception as e:
            # Unexpected error
            print(f"⚠️ Error: {e}")
            return "Unexpected error."

# Function for continuous listening with retry logic
def continuous_listen():
    """Continuously listen until valid speech is recognized."""
    while True:
        result = listen()
        if result and result not in ("Speech recognition failed.", "Unexpected error.", ""):
            return result
        # If no valid speech was detected, try again without any message

class ContinuousListener:
    """A class that handles continuous voice command listening in a separate thread.
    
    This class is the core of RawWick's voice recognition system. It:
    1. Continuously listens for voice commands in the background
    2. Converts speech to text using Google's speech recognition
    3. Processes commands through the AI system
    4. Manages a queue of commands for orderly processing
    
    The threading design allows the voice recognition to run without blocking
    the main application, creating a responsive user experience.
    """
    def __init__(self, on_command_received=None):
        """Initialize the continuous listener.
        
        Args:
            on_command_received: Optional callback function that will be called
                                when a new command is received.
        """
        self.listening_active = False
        self.command_queue = queue.Queue()
        self.on_command_received = on_command_received
        self._listener_thread = None
        self._processor_thread = None
        
    def start_listening(self, process_commands=True, processor_func=None):
        """Start the listening thread.
        
        Args:
            process_commands: Whether to also start a processor thread that
                             automatically processes commands from the queue.
            processor_func: Function to call to process each command.
                           Only used if process_commands is True.
        """
        self.listening_active = True
        
        # Start the listener thread
        self._listener_thread = threading.Thread(target=self._listener_loop)
        self._listener_thread.daemon = True
        self._listener_thread.start()
        
        # Optionally start the processor thread
        if process_commands and processor_func:
            self._processor_thread = threading.Thread(
                target=self._processor_loop, 
                args=(processor_func,)
            )
            self._processor_thread.daemon = True
            self._processor_thread.start()
        
        return self
        
    def stop_listening(self):
        """Stop the listening thread."""
        self.listening_active = False
        
        # Wait for threads to finish
        if self._listener_thread:
            self._listener_thread.join(timeout=1.0)
            
        if self._processor_thread:
            self._processor_thread.join(timeout=1.0)
            
        return self
            
    def get_next_command(self, timeout=0.5):
        """Get the next command from the queue.
        
        Args:
            timeout: How long to wait for a command before returning None.
            
        Returns:
            The next command string, or None if the queue is empty.
        """
        try:
            return self.command_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def is_exit_command(self, command):
        """Check if a command is an exit command.
        
        Args:
            command: The command string to check.
            
        Returns:
            True if the command is an exit command, False otherwise.
        """
        return command.lower() in ("exit", "quit", "stop")
            
    def _listener_loop(self):
        """The main listener loop that runs in a separate thread."""
        while self.listening_active:
            print("🎙️ Listening... (say 'exit' to quit)")
            user_input = continuous_listen().strip().lower()
            
            if user_input:
                print(f"📝 Command received: {user_input}")
                
                # Check for exit command
                if self.is_exit_command(user_input):
                    self.listening_active = False
                    self.command_queue.put(user_input)  # Put exit command in queue
                    print("👋 Exiting system agent. Bye!")
                    break
                
                # Add command to the queue for processing
                self.command_queue.put(user_input)
                
                # Call the callback if provided
                if self.on_command_received:
                    self.on_command_received(user_input)
    
    def _processor_loop(self, processor_func):
        """The main processor loop that runs in a separate thread.
        
        Args:
            processor_func: Function to call to process each command.
        """
        while self.listening_active or not self.command_queue.empty():
            try:
                # Get command with a timeout to allow checking the listening_active flag
                user_input = self.command_queue.get(timeout=0.5)
                
                if self.is_exit_command(user_input):
                    break
                    
                print(f"🧠 Processing command: {user_input}")
                processor_func(user_input)
                self.command_queue.task_done()
                
            except queue.Empty:
                # No commands in queue, continue checking
                continue


# Alternative test for continuous listening
'''
if __name__ == "__main__":
    print("\n===== Continuous Listen Test Mode =====\n")
    print("Say something to test continuous speech recognition...")
    print("(Say 'exit' to quit or press Ctrl+C)\n")
    
    try:
        listener = ContinuousListener(
            on_command_received=lambda cmd: print(f"\n✅ Command received: \"{cmd}\"\n")
        )
        
        listener.start_listening()
        
        while listener.listening_active:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted. Exiting test mode.")
        if listener:
            listener.stop_listening()
'''