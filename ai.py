#!/usr/bin/env python3
import os
import sys
import json
import argparse
from pathlib import Path

# Force stdout and stderr to use UTF-8 encoding on Windows to prevent UnicodeEncodeError in standard terminals.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# We import libraries inside try-except so we can give helpful installation guidance if needed.
try:
    from openai import OpenAI
    import g4f
    from g4f.client import Client as G4FClient
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.text import Text
    from rich.live import Live
    from rich.spinner import Spinner
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please run 'setup.bat' to install all required dependencies.")
    sys.exit(1)

# App configurations
APP_NAME = "Terminal AI"
HISTORY_FILE = Path.home() / ".terminal_ai_history.json"
DEFAULT_SYSTEM_PROMPT = "You are a helpful, concise AI assistant running inside a user's command prompt terminal. Keep responses clear and well-structured. Use markdown for code and lists."

# Harmonious color palette
CONSOLE_THEME = {
    "system": "bold cyan",
    "user": "bold green",
    "ai": "bold purple",
    "error": "bold red",
    "info": "yellow",
    "success": "bold green"
}

console = Console()

# Unified Model mappings
MODELS_GITHUB = {
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    "deepseek-r1": "DeepSeek-R1",
    "llama3.3": "meta-llama-3.3-70b-instruct",
    "llama3.1-405b": "meta-llama-3.1-405b-instruct",
    "phi4": "Phi-4",
    "cohere": "Cohere-command-r-plus"
}

MODELS_FREE = {
    "gpt-4o-mini": "gpt-4o-mini",
    "qwen": "qwen-2.5-72b",
    "llama3.3": "llama-3.3-70b",
    "claude": "claude-3-haiku"
}

# Explicit Provider mappings for Zero-Auth stability
FREE_PROVIDER_MAPPINGS = {
    "gpt-4o-mini": g4f.Provider.OperaAria,
    "qwen": g4f.Provider.Qwen_Qwen_3,
    "llama3.3": g4f.Provider.Qwen_Qwen_3,  # Qwen acts as a robust general proxy
    "claude": g4f.Provider.OperaAria
}

# Helpers for History Management
def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Return history and last model used
                return data.get("messages", []), data.get("model", "gpt-4o-mini"), data.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
        except Exception:
            pass
    return [], "gpt-4o-mini", DEFAULT_SYSTEM_PROMPT

def save_history(messages, model, system_prompt):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "messages": messages,
                "model": model,
                "system_prompt": system_prompt
            }, f, indent=2, ensure_ascii=False)
    except Exception as e:
        console.print(f"[error]Failed to save chat history: {e}[/error]")

def clear_history():
    if HISTORY_FILE.exists():
        try:
            HISTORY_FILE.unlink()
            console.print("[success]Chat history cleared successfully![/success]")
        except Exception as e:
            console.print(f"[error]Failed to delete history file: {e}[/error]")
    else:
        console.print("[info]No chat history to clear.[/info]")

# Query Engine
class AIQueryEngine:
    def __init__(self, use_free=False):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.use_free = use_free or not self.github_token
        
        if not self.use_free:
            # Initialize GitHub Models Client
            self.client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=self.github_token
            )
            self.mode = "GitHub Models (Premium)"
        else:
            # Initialize g4f Zero-Auth Client
            self.client = G4FClient()
            self.mode = "Zero-Auth Free Providers"

    def get_available_models(self):
        if not self.use_free:
            return list(MODELS_GITHUB.keys())
        else:
            return list(MODELS_FREE.keys())

    def get_actual_model_name(self, model_alias):
        if not self.use_free:
            return MODELS_GITHUB.get(model_alias, MODELS_GITHUB["gpt-4o-mini"])
        else:
            return MODELS_FREE.get(model_alias, MODELS_FREE["gpt-4o-mini"])

    def query(self, messages, model_alias):
        actual_model = self.get_actual_model_name(model_alias)
        
        if not self.use_free:
            # GitHub Models streaming query
            try:
                response = self.client.chat.completions.create(
                    model=actual_model,
                    messages=messages,
                    stream=True
                )
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content is not None:
                        yield content
            except Exception as e:
                console.print(f"\n[error]GitHub Models API Error: {e}[/error]")
                console.print("[info]Attempting fallback to Zero-Auth free mode...[/info]")
                # Fallback to Free Mode
                self.use_free = True
                self.client = G4FClient()
                self.mode = "Zero-Auth Free Providers (Fallback)"
                yield from self.query(messages, model_alias)
        else:
            # g4f Zero-Auth streaming query using explicitly mapped reliable providers
            provider = FREE_PROVIDER_MAPPINGS.get(model_alias)
            try:
                response = self.client.chat.completions.create(
                    model=actual_model,
                    provider=provider,
                    messages=messages,
                    stream=True
                )
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content is not None:
                        yield content
            except Exception as e:
                # If explicit provider fails, try general auto-fallback
                try:
                    response = self.client.chat.completions.create(
                        model=actual_model,
                        messages=messages,
                        stream=True
                    )
                    for chunk in response:
                        content = chunk.choices[0].delta.content
                        if content is not None:
                            yield content
                except Exception as fallback_err:
                    yield f"\n[error]Error in Free Provider Query: {fallback_err}[/error]\nSome providers might be temporarily offline. Please try switching models (e.g. /model qwen or /model gpt-4o-mini)."

# Gorgeous Welcome Banner
def print_welcome_banner(engine, model):
    console.print()
    banner = Text()
    banner.append("⚡ Terminal AI Assistant ⚡\n", style="bold magenta")
    banner.append(f"Mode: {engine.mode} | Active Model: {model}\n", style="dim cyan")
    banner.append("Type your prompt to chat. Commands: /help, /clear, /model <name>, /exit", style="italic gray")
    
    console.print(Panel(banner, border_style="bold purple", title="[bold white]Welcome[/bold white]", title_align="center"))
    console.print()

def print_help(engine):
    console.print("\n[bold white]Available Terminal Commands:[/bold white]")
    console.print("  [system]/help[/system]            - Show this list of available commands.")
    console.print("  [system]/clear[/system] or [system]/reset[/system]  - Clear conversation history.")
    console.print("  [system]/history[/system]         - View the conversation history.")
    console.print("  [system]/exit[/system] or [system]/quit[/system]   - Close this session.")
    console.print("  [system]/model <name>[/system]    - Switch AI model dynamically.")
    
    console.print(f"\n[bold white]Available Models for current mode ({engine.mode}):[/bold white]")
    for m in engine.get_available_models():
        desc = "Official high-performance model" if not engine.use_free else "Zero-auth community proxy"
        console.print(f"  • [info]{m}[/info] - {desc}")
    console.print()

# Standard CLI Prompt Runner (One-Shot)
def run_one_shot(engine, prompt, model, system_prompt, history):
    # Formulate messages list
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append history if available
    for msg in history:
        messages.append(msg)
        
    messages.append({"role": "user", "content": prompt})
    
    console.print(f"\n[user]You:[/user] {prompt}")
    console.print(f"[ai]{model} is thinking...[/ai]")
    
    full_response = ""
    # Stream response
    with Live(Spinner("dots", text="Generating response...", style="bold purple"), refresh_per_second=10) as live:
        try:
            chunks = engine.query(messages, model)
            first = True
            for chunk in chunks:
                if first:
                    live.update("")
                    first = False
                full_response += chunk
                live.update(Markdown(full_response))
        except KeyboardInterrupt:
            console.print("\n[error]Generation cancelled by user.[/error]")
            return

    # Save to history
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": full_response})
    save_history(history, model, system_prompt)
    console.print()

# Interactive Terminal Chat Loop
def run_interactive_loop(engine, model, system_prompt, history):
    print_welcome_banner(engine, model)
    
    while True:
        try:
            # Custom prompt style
            prompt = console.input(f"[user]You ({model})[/user] > ").strip()
            
            if not prompt:
                continue
                
            # Check for commands
            if prompt.startswith("/"):
                cmd_parts = prompt.split()
                cmd = cmd_parts[0].lower()
                
                if cmd in ["/exit", "/quit"]:
                    console.print("[info]Exiting Terminal AI. Goodbye![/info]")
                    break
                    
                elif cmd in ["/clear", "/reset"]:
                    history = []
                    clear_history()
                    continue
                    
                elif cmd == "/help":
                    print_help(engine)
                    continue
                    
                elif cmd == "/history":
                    if not history:
                        console.print("[info]Conversation history is empty.[/info]")
                    else:
                        console.print("\n[bold white]Conversation History:[/bold white]")
                        for msg in history:
                            role = "You" if msg["role"] == "user" else "AI"
                            color = "green" if msg["role"] == "user" else "purple"
                            console.print(f"[{color}]{role}:[/{color}] {msg['content']}")
                        console.print()
                    continue
                    
                elif cmd == "/model":
                    if len(cmd_parts) < 2:
                        console.print(f"[error]Please specify a model name. Available: {', '.join(engine.get_available_models())}[/error]")
                        continue
                    new_model = cmd_parts[1].lower()
                    if new_model in engine.get_available_models():
                        model = new_model
                        save_history(history, model, system_prompt)
                        console.print(f"[success]Switched active model to: {model}[/success]\n")
                    else:
                        console.print(f"[error]Invalid model: '{new_model}'. Available: {', '.join(engine.get_available_models())}[/error]")
                    continue
                else:
                    console.print(f"[error]Unknown command: '{cmd}'. Type /help to see all commands.[/error]")
                    continue
            
            # Prepare query messages
            messages = [{"role": "system", "content": system_prompt}]
            for msg in history:
                messages.append(msg)
            messages.append({"role": "user", "content": prompt})
            
            # Visual text generator
            full_response = ""
            console.print()
            with Live(Spinner("dots", text=f"Querying {model}...", style="bold purple"), refresh_per_second=10) as live:
                try:
                    chunks = engine.query(messages, model)
                    first = True
                    for chunk in chunks:
                        if first:
                            live.update("")
                            first = False
                        full_response += chunk
                        live.update(Markdown(full_response))
                except KeyboardInterrupt:
                    console.print("\n[error]Generation cancelled by user.[/error]")
                    continue
                except Exception as e:
                    live.update(f"[error]An error occurred: {e}[/error]")
                    continue
            
            # Save turns to history
            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": full_response})
            save_history(history, model, system_prompt)
            console.print()
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[info]Exiting Terminal AI. Goodbye![/info]")
            break

def main():
    parser = argparse.ArgumentParser(
        description="Terminal AI - A login-free, high-performance command-line AI assistant.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("prompt", nargs="?", default=None, help="Optional one-shot query. If omitted, starts interactive chat.")
    parser.add_argument("-m", "--model", help="Specify AI model to use.")
    parser.add_argument("--free", action="store_true", help="Force Zero-Auth free mode (ignore GitHub token).")
    parser.add_argument("--clear", action="store_true", help="Clear conversation history and exit.")
    parser.add_argument("-s", "--system", help="Set custom system prompt instruction.")
    
    args = parser.parse_args()
    
    if args.clear:
        clear_history()
        sys.exit(0)
        
    # Initialize Engine
    engine = AIQueryEngine(use_free=args.free)
    
    # Load past session
    history, saved_model, saved_system_prompt = load_history()
    
    # Resolve system prompt
    system_prompt = args.system if args.system else saved_system_prompt
    
    # Resolve model
    active_model = args.model.lower() if args.model else saved_model
    if active_model not in engine.get_available_models():
        active_model = engine.get_available_models()[0] # Fallback to first available
        
    # Execute prompt or run interactive loop
    if args.prompt:
        run_one_shot(engine, args.prompt, active_model, system_prompt, history)
    else:
        run_interactive_loop(engine, active_model, system_prompt, history)

if __name__ == "__main__":
    main()
