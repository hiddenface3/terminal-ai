#!/usr/bin/env python3
import os
import sys
import json
import argparse
import base64
from pathlib import Path

# Force stdout and stderr to use UTF-8 encoding on Windows to prevent UnicodeEncodeError in standard terminals.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# We import libraries inside try-except so we can give helpful installation guidance if needed.
try:
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

# Zero-Auth Model mappings
MODELS_FREE = {
    "gpt-4o-mini": "gpt-4o-mini",
    "qwen": "qwen-2.5-72b",
    "llama3.3": "llama-3.3-70b",
    "claude": "claude-3-haiku"
}

# Known working zero-auth providers to use as fallbacks
def get_fallback_providers(model_alias):
    # A list of string names for robust free providers
    provider_names = [
        "Blackbox",
        "DDG",
        "PollinationsAI",
        "Jmuz",
        "DeepInfraChat",
        "HuggingChat",
        "OperaAria",
        "Qwen_Qwen_3"
    ]
    
    providers = []
    
    # Priority providers based on model
    if model_alias == "gpt-4o-mini":
        if hasattr(g4f.Provider, "OperaAria"):
            providers.append(g4f.Provider.OperaAria)
    elif model_alias == "qwen":
        if hasattr(g4f.Provider, "Qwen_Qwen_3"):
            providers.append(g4f.Provider.Qwen_Qwen_3)
            
    for name in provider_names:
        if hasattr(g4f.Provider, name):
            p = getattr(g4f.Provider, name)
            if p not in providers:
                providers.append(p)
                
    # Add None at the end to let g4f auto-select its internal fallback RetryProvider
    providers.append(None)
    
    return providers

# Helpers for History Management
def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("messages", []), data.get("model", "gpt-4o-mini"), data.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
        except Exception:
            pass
    return [], "gpt-4o-mini", DEFAULT_SYSTEM_PROMPT

def save_history(messages, model, system_prompt):
    try:
        # Filter out heavy vision base64 image data from saved files to prevent bloated history
        clean_messages = []
        for msg in messages:
            if isinstance(msg.get("content"), list):
                # This is a vision message, save only the text part in history
                text_content = ""
                for part in msg["content"]:
                    if part.get("type") == "text":
                        text_content += part.get("text", "")
                clean_messages.append({"role": msg["role"], "content": f"[Image analyzed] {text_content}"})
            else:
                clean_messages.append(msg)

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "messages": clean_messages,
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

# Image Base64 encoder helper
def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        console.print(f"[error]Failed to read/encode image: {e}[/error]")
        return None

# Robust content extraction from stream chunks (handles None, strings, dicts, and OpenAI response objects)
def safe_extract_content(chunk):
    if chunk is None:
        return None
    
    # 1. Handle raw string chunks (sometimes yielded by simple providers)
    if isinstance(chunk, str):
        return chunk
        
    # 2. Handle dictionary-style chunks
    if isinstance(chunk, dict):
        try:
            return chunk.get("choices", [{}])[0].get("delta", {}).get("content")
        except Exception:
            return None
            
    # 3. Handle standard OpenAI ChatCompletionChunk objects
    try:
        if hasattr(chunk, 'choices') and chunk.choices:
            choice = chunk.choices[0]
            if hasattr(choice, 'delta') and choice.delta:
                if hasattr(choice.delta, 'content'):
                    return choice.delta.content
                elif isinstance(choice.delta, dict):
                    return choice.delta.get("content")
    except Exception:
        pass
        
    return None

# Query Engine
class AIQueryEngine:
    def __init__(self):
        self.client = G4FClient()
        self.mode = "Zero-Auth Free Providers"

    def get_available_models(self):
        return list(MODELS_FREE.keys())

    def get_actual_model_name(self, model_alias):
        return MODELS_FREE.get(model_alias, MODELS_FREE["gpt-4o-mini"])

    def query(self, messages, model_alias):
        actual_model = self.get_actual_model_name(model_alias)
        providers_to_try = get_fallback_providers(model_alias)
        
        last_error = None
        
        for provider in providers_to_try:
            try:
                # Attempt to create the chat completion with the current provider
                response = self.client.chat.completions.create(
                    model=actual_model,
                    provider=provider,
                    messages=messages,
                    stream=True
                )
                
                # Fetch chunks, tracking if any yielded
                iterator = iter(response)
                
                # Try to get the first chunk (this will often raise MissingAuthError if broken)
                try:
                    first_chunk = next(iterator)
                except StopIteration:
                    last_error = "Provider returned empty response."
                    continue
                    
                first_content = safe_extract_content(first_chunk)
                yielded_any = False
                
                if first_content is not None:
                    # Detect fake success where provider returns backend error strings as content
                    error_signatures = [
                        "NoneType' object has no attribute",
                        "color: var(--color-red",
                        "Invalid model or alias",
                        "API key is required",
                        "Something went wrong"
                    ]
                    if any(sig in first_content for sig in error_signatures):
                        last_error = f"Provider returned internal error: {first_content.strip()}"
                        continue
                        
                    yield first_content
                    yielded_any = True
                    
                # If first chunk succeeded, continue streaming the rest
                for chunk in iterator:
                    content = safe_extract_content(chunk)
                    if content is not None:
                        yield content
                        yielded_any = True
                        
                # If we yielded anything, we consider this provider a success
                if yielded_any:
                    return
                else:
                    last_error = "Provider yielded no text content."
                    continue
                    
            except Exception as e:
                # E.g. MissingAuthError, 401 Unauthorized, ConnectionError
                last_error = str(e)
                continue
                
        # If all providers fail
        yield f"\n[error]Error: All zero-auth providers failed. Last error: {last_error}[/error]\nPlease try switching models (e.g., /model qwen or /model gpt-4o-mini)."

# Gorgeous Welcome Banner
def print_welcome_banner(engine, model):
    console.print()
    banner = Text()
    banner.append("⚡ Terminal AI Assistant ⚡\n", style="bold magenta")
    banner.append(f"Mode: {engine.mode} | Active Model: {model}\n\n", style="dim cyan")
    
    banner.append("📋 Copy and paste commands below to switch models instantly:\n", style="bold yellow")
    banner.append("  /model gpt-4o-mini\n", style="system")
    banner.append("  /model qwen\n", style="system")
    banner.append("  /model llama3.3\n", style="system")
    banner.append("  /model claude\n\n", style="system")

    banner.append("📸 To analyze a screenshot or local image, type:\n", style="bold yellow")
    banner.append("  /vision \"C:\\path\\to\\screenshot.png\" What is shown here?\n\n", style="system")

    banner.append("Other Commands: /help, /clear, /exit", style="italic gray")
    
    console.print(Panel(banner, border_style="bold purple", title="[bold white]Welcome[/bold white]", title_align="center"))
    console.print()

def print_help():
    console.print("\n[bold white]Available Terminal Commands:[/bold white]")
    console.print("  [system]/help[/system]            - Show this list of available commands.")
    console.print("  [system]/clear[/system] or [system]/reset[/system]  - Clear conversation history.")
    console.print("  [system]/history[/system]         - View the conversation history.")
    console.print("  [system]/exit[/system] or [system]/quit[/system]   - Close this session.")
    
    console.print("\n[bold yellow]Copy-pasteable commands to switch models:[/bold yellow]")
    console.print("  [system]/model gpt-4o-mini[/system]   - Switch to GPT-4o-mini (OperaAria - fast general chat)")
    console.print("  [system]/model qwen[/system]           - Switch to Qwen 2.5 (Qwen 3 - advanced reasoning & coding)")
    console.print("  [system]/model llama3.3[/system]       - Switch to Llama 3.3 70B (Qwen 3 - balanced chat)")
    console.print("  [system]/model claude[/system]         - Switch to Claude 3 Haiku (OperaAria - fast balanced chat)")
    
    console.print("\n[bold yellow]Image/Screenshot analysis command:[/bold yellow]")
    console.print("  [system]/vision \"path_to_image\" prompt[/system] - Analyze any local image or screenshot.")
    console.print()

# Standard CLI Prompt Runner (One-Shot)
def run_one_shot(engine, prompt, model, system_prompt, history):
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": prompt})
    
    console.print(f"\n[user]You:[/user] {prompt}")
    console.print(f"[ai]{model} is thinking...[/ai]")
    
    full_response = ""
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

    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": full_response})
    save_history(history, model, system_prompt)
    console.print()

# Interactive Terminal Chat Loop
def run_interactive_loop(engine, model, system_prompt, history):
    print_welcome_banner(engine, model)
    
    while True:
        try:
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
                    print_help()
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
                        console.print(f"[error]Please specify a model. Available: {', '.join(engine.get_available_models())}[/error]")
                        continue
                    new_model = cmd_parts[1].lower()
                    if new_model in engine.get_available_models():
                        model = new_model
                        save_history(history, model, system_prompt)
                        console.print(f"[success]Switched active model to: {model}[/success]\n")
                    else:
                        console.print(f"[error]Invalid model: '{new_model}'. Available: {', '.join(engine.get_available_models())}[/error]")
                    continue
                
                elif cmd == "/vision":
                    # Parse syntax: /vision "path" prompt
                    cmd_text = prompt[len("/vision"):].strip()
                    if cmd_text.startswith('"'):
                        end_quote = cmd_text.find('"', 1)
                        if end_quote == -1:
                            console.print("[error]Syntax error. Example: /vision \"C:\\screenshot.png\" What is this?[/error]")
                            continue
                        image_path = cmd_text[1:end_quote]
                        prompt_text = cmd_text[end_quote+1:].strip()
                    else:
                        parts = cmd_text.split(maxsplit=1)
                        if len(parts) < 2:
                            console.print("[error]Syntax error. Example: /vision C:\\screenshot.png What is this?[/error]")
                            continue
                        image_path = parts[0]
                        prompt_text = parts[1]
                    
                    # Verify file exists
                    path_obj = Path(image_path)
                    if not path_obj.exists():
                        console.print(f"[error]Image file not found: {image_path}[/error]")
                        continue
                    
                    # Base64 encode image
                    console.print(f"[info]Encoding image: {path_obj.name}...[/info]")
                    base64_image = encode_image(image_path)
                    if not base64_image:
                        continue
                    
                    # Build Vision Payload
                    image_data_url = f"data:image/jpeg;base64,{base64_image}"
                    vision_content = [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": image_data_url}}
                    ]
                    
                    # Setup messaging context (Vision must be queried using multimodal models like gpt-4o-mini)
                    messages = [{"role": "system", "content": system_prompt}]
                    for msg in history:
                        messages.append(msg)
                    messages.append({"role": "user", "content": vision_content})
                    
                    # Execute streaming query
                    full_response = ""
                    console.print()
                    with Live(Spinner("dots", text=f"Analyzing image using {model}...", style="bold purple"), refresh_per_second=10) as live:
                        try:
                            # Direct query
                            chunks = engine.query(messages, model)
                            first = True
                            for chunk in chunks:
                                if first:
                                    live.update("")
                                    first = False
                                full_response += chunk
                                live.update(Markdown(full_response))
                        except KeyboardInterrupt:
                            console.print("\n[error]Analysis cancelled by user.[/error]")
                            continue
                        except Exception as vision_err:
                            live.update(f"[error]Analysis failed: {vision_err}[/error]")
                            continue
                    
                    # Add standard text versions to saved history to avoid bloating
                    history.append({"role": "user", "content": f"[Image: {path_obj.name}] {prompt_text}"})
                    history.append({"role": "assistant", "content": full_response})
                    save_history(history, model, system_prompt)
                    console.print()
                    continue

                else:
                    console.print(f"[error]Unknown command: '{cmd}'. Type /help to see all commands.[/error]")
                    continue
            
            # Prepare standard text query messages
            messages = [{"role": "system", "content": system_prompt}]
            for msg in history:
                messages.append(msg)
            messages.append({"role": "user", "content": prompt})
            
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
    parser.add_argument("--clear", action="store_true", help="Clear conversation history and exit.")
    parser.add_argument("-s", "--system", help="Set custom system prompt instruction.")
    
    args = parser.parse_args()
    
    if args.clear:
        clear_history()
        sys.exit(0)
        
    # Initialize Engine
    engine = AIQueryEngine()
    
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
