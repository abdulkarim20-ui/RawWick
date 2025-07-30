from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import uuid
from models.groq import GroqModel
from executors.rawwick_executor import RawWickExecutor
from utils.cache import FixCache
from Secure.ApiKeys import GROQ_API_KEY
from core.context_manager import ContextManager
from rich.live import Live
from rich.layout import Layout
import os

class TaskExecutor:
    def __init__(self):
        self.console = Console()
        self.context_manager = ContextManager()
        self.ai = GroqModel(api_key=GROQ_API_KEY)
        self.cache = FixCache()
        self.executor = RawWickExecutor(
            ai=self.ai,
            fix_cache=self.cache,
            context_manager=self.context_manager
        )
        self.thread_pool = ThreadPoolExecutor(max_workers=5)
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.fields[desc]}", justify="right"),
            BarColumn(),
            TimeElapsedColumn(),
            transient=True,
        )
        self.progress_lock = threading.Lock()
        self.progress.start()

    def process_query(self, query: str):
        if not query.strip():
            return

        # Update workspace context
        self.context_manager.update_workspace_state(os.getcwd())

        # Get relevant history for context
        relevant_history = self.context_manager.get_relevant_history(query)
        if relevant_history:
            context_prompt = "\n\nRelevant command history:\n" + \
                "\n".join(f"- {cmd['command']} ({cmd['success']})" 
                          for cmd in relevant_history)
            query += context_prompt

        task_id = str(uuid.uuid4())[:6]
        task_desc = f"Processing: {query[:30]}..."

        with self.progress_lock:
            task = self.progress.add_task(description=task_desc, total=100, desc=task_desc)

        def background_task():
            try:
                for _ in range(5):
                    time.sleep(0.5)
                    with self.progress_lock:
                        self.progress.update(task, advance=20)
                response = self.ai.chat(query)
                self.executor.process(response)
            except Exception as e:
                self.console.print(f"[red]Error during task:[/red] {e}")
            finally:
                with self.progress_lock:
                    self.progress.remove_task(task)

        self.thread_pool.submit(background_task)

assistant = TaskExecutor()

def system_agent(query: str):
    """Processes a command string using the RawWick AI executor system."""
    assistant.process_query(query)