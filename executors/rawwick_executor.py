from typing import List
from rich.console import Console
from rich.markdown import Markdown
import re, os, webbrowser, io, subprocess
from contextlib import redirect_stdout, redirect_stderr
from typing import List, Dict, Optional
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table
import psutil
import platform
import signal
from datetime import datetime

class RawWickExecutor:
    def __init__(self, ai, fix_cache, context_manager):
        self.console = Console()
        self.console.ask_ai = ai
        self.cache = fix_cache
        self.confirm = False
        self.context_manager = context_manager
        self.running_processes: Dict[str, psutil.Process] = {}
        self.last_execution_stats = {}

    def extract_code_blocks(self, text: str) -> List[str]:
        return re.findall(r"```(?:python|bash)?\n(.*?)```", text, re.DOTALL)

    def detect_and_open_links(self, text: str) -> None:
        links = re.findall(r"https?://\S+", text)
        for url in links:
            webbrowser.open(url)
            self.console.print(f"[bold green]Opened URL:[/bold green] {url}")

    def read_file(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"[red]Failed to read file:[/red] {e}"

    def write_file(self, path: str, content: str) -> str:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"[green]Successfully wrote to file:[/green] {path}"
        except Exception as e:
            return f"[red]Failed to write to file:[/red] {e}"

    def list_dir(self, path=".") -> str:
        try:
            files = os.listdir(path)
            return "\n".join(files)
        except Exception as e:
            return f"[red]Failed to list directory:[/red] {e}"

    def walk_dir(self, root=".") -> str:
        output = []
        try:
            for dirpath, dirs, files in os.walk(root):
                output.append(f"[bold]{dirpath}[/bold]")
                for f in files:
                    output.append(f"  └── {f}")
            return "\n".join(output)
        except Exception as e:
            return f"[red]Failed to walk directory:[/red] {e}"

    def is_filesystem_task(self, code: str) -> bool:
        return any(kw in code for kw in ["open(", "os.listdir", "os.walk", "read(", "write("])

    def handle_filesystem_task(self, code: str) -> str:
        local_vars = {
            "read_file": self.read_file,
            "write_file": self.write_file,
            "list_dir": self.list_dir,
            "walk_dir": self.walk_dir,
            "os": os,
            "open": open,
        }
        try:
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exec(code, {}, local_vars)
            return stdout.getvalue() or "(Filesystem task executed)"
        except Exception as e:
            return f"[red]Filesystem Error:[/red] {e}"

    def execute_python(self, code: str) -> str:
        stdout, stderr = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exec(code, {})
        except Exception as e:
            return f"[red]Python Error:[/red] {e}\n{stderr.getvalue()}"
        return stdout.getvalue() or "(Python code executed)"

    def execute_shell(self, code: str) -> str:
        try:
            result = subprocess.run(code, shell=True, capture_output=True, text=True)
            return result.stdout or result.stderr or "(Shell command executed)"
        except Exception as e:
            return f"[red]Shell Error:[/red] {e}"

    def execute_with_timeout(self, code: str, timeout: int = 30) -> str:
        """Execute code with timeout and resource monitoring."""
        start_time = datetime.now()
        start_memory = psutil.Process().memory_info().rss

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.execute_python, code)
                result = future.result(timeout=timeout)

            end_time = datetime.now()
            end_memory = psutil.Process().memory_info().rss
            execution_time = (end_time - start_time).total_seconds()
            memory_used = end_memory - start_memory

            self.last_execution_stats = {
                "execution_time": execution_time,
                "memory_used": memory_used,
                "success": True
            }

            return result
        except TimeoutError:
            return f"[red]Execution timed out after {timeout} seconds[/red]"

    def smart_execute(self, code: str, lang: str) -> str:
        """Smart execution with context awareness and error prevention."""
        # Check for dangerous operations
        dangerous_patterns = [
            "rm -rf", "deltree", "format", "mkfs",
            "shutdown", "reboot", "halt",
            ":(){ :|:& };:"
        ]
        if any(pattern in code.lower() for pattern in dangerous_patterns):
            return "[red]⚠️ Potentially dangerous operation detected and blocked[/red]"

        # Add execution context
        execution_context = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "timestamp": datetime.now().isoformat(),
            "working_directory": os.getcwd()
        }
        self.context_manager.add_context("last_execution", execution_context)

        # Execute with monitoring
        result = self.execute_with_timeout(code)

        # Update execution history
        self.context_manager.add_command(
            command=code,
            result=result,
            success="[red]" not in result
        )

        return result

    def display_execution_stats(self):
        """Display rich execution statistics."""
        if not self.last_execution_stats:
            return

        table = Table(title="Execution Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row(
            "Execution Time",
            f"{self.last_execution_stats['execution_time']:.2f}s"
        )
        table.add_row(
            "Memory Used",
            f"{self.last_execution_stats['memory_used'] / 1024 / 1024:.2f}MB"
        )
        table.add_row(
            "Status",
            "✅ Success" if self.last_execution_stats['success'] else "❌ Failed"
        )

        self.console.print(table)

    def process(self, response: str):
        self.console.print(Markdown(f"**AI Response:**\n\n{response}"))
        self.detect_and_open_links(response)

        code_blocks = self.extract_code_blocks(response)
        for i, code in enumerate(code_blocks, 1):
            lang = "python" if "import " in code or "def " in code else "bash"
            output = self.run_with_retry(code, lang, max_retries=3)
            self.console.print(Markdown(f"**Final Output (after fix attempts) #{i}:**\n```\n{output}\n```"))

    def run_with_retry(self, code: str, lang: str, max_retries=3) -> str:
        original_code = code.strip()
        if fixed := self.cache.get(original_code):
            code = fixed

        for attempt in range(1, max_retries + 1):
            if self.is_filesystem_task(code):
                output = self.handle_filesystem_task(code)
            else:
                output = self.execute_python(code) if lang == "python" else self.execute_shell(code)

            if "Error:" not in output and "[red]" not in output:
                if original_code != code:
                    self.cache.add(original_code, code)
                return output

            self.console.print(f"[yellow]Attempt {attempt} failed. Trying to fix the code...[/yellow]")
            code = self.fix_code_with_ai(original_code, output)

        return f"[red]❌ All attempts failed after {max_retries} retries.[/red]\nLast error:\n{output}"

    def fix_code_with_ai(self, broken_code: str, error: str) -> str:
        prompt = (
            "Fix this code. Don't explain. Only return valid, working code block. "
            f"The code:\n```python\n{broken_code}\n```\n"
            f"The error was:\n```\n{error}\n```"
        )
        reply = self.console.ask_ai.chat(prompt)
        matches = self.extract_code_blocks(reply)
        return matches[0] if matches else broken_code
        
        # Show session summary
        session_stats = self.context_manager.get_session_summary()
        self.console.print(Panel.fit(
            f"Session Duration: {session_stats['session_duration']}\n"
            f"Commands Executed: {session_stats['command_count']}\n"
            f"Success Rate: {session_stats['success_rate']*100:.1f}%",
            title="Session Summary",
            border_style="blue"
        ))