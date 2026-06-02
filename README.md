# ⚡ Terminal AI Assistant

A login-free, premium, and zero-friction command-line AI assistant for Windows. This repository is built to be cloned, installed in seconds, and immediately run from ANY terminal (CMD, PowerShell, or Windows Terminal) with **zero accounts, zero sign-ups, and zero cost**.

---

## ✨ Features

- 🌌 **Dual-Mode Intelligence**:
  - **Zero-Auth Mode (Default)**: Leverages public web aggregators (`g4f` / DuckDuckGo AI) to query models anonymously without any API keys, sign-ups, or logins.
  - **Premium Mode**: Auto-elevates to ultra-stable, high-speed official **GitHub Models API** if a `GITHUB_TOKEN` environment variable is detected.
- 🎨 **Premium Visual UI**:
  - Beautiful, character-by-character response streaming.
  - Syntax-highlighted code blocks (just like VS Code) and styled tables.
  - Live loading spinners showing AI thinking status.
- 💬 **Smart Session Control**:
  - Automatically loads and saves conversation history so you can continue your chats across sessions.
  - Full support for multi-turn chats.
- 📦 **Windows Global Integration**:
  - Seamless installer `setup.bat` creates a dedicated virtual environment (`.venv`) and configures a global shortcut command (`ai`).
  - Access the assistant globally from any directory.

---

## 🚀 Quick Setup (Windows)

Simply open your Command Prompt (CMD) or PowerShell and run the following:

### 1. Clone the Repository
```cmd
git clone https://github.com/your-username/terminal-ai.git
cd terminal-ai
```

### 2. Run the Installer
```cmd
setup.bat
```
The script will set up Python, install the visual dependencies, and deploy a global launcher shortcut `ai.bat` inside your user PATH.

---

## 💡 Usage

Once installed, you can start the assistant from **any terminal directory** in Windows:

### 1. Interactive Chat Session
Start a full conversational chat loop:
```cmd
ai
```
*Inside the chat, you can type questions normally or use commands like `/clear` or `/model`.*

### 2. One-Shot Command Prompts
Ask a quick question directly and exit:
```cmd
ai "How do I list listening ports on Windows CMD?"
```

### 3. Model Switcher
Explicitly start a session using a specific model:
```cmd
ai -m deepseek
```
*Note: Available models depend on the active mode (Zero-Auth vs Premium Mode).*

---

## 🛠️ Commands (Interactive Loop)

Use these slash commands inside the interactive chat loop:

| Command | Action |
| :--- | :--- |
| `/help` | Displays help panel with all commands and active models. |
| `/model <name>` | Switches active model on-the-fly. |
| `/clear` or `/reset` | Clears conversation history. |
| `/history` | Displays previous dialogue within the current thread. |
| `/exit` or `/quit` | Quits the assistant. |

---

## 🧠 Supported Models

### Default Mode (Zero-Auth)
- `gpt-4o-mini` (Fast and balanced)
- `gpt-4o` (Advanced reasoning)
- `deepseek` (DeepSeek-V3 Chat)
- `gemini` (Gemini Flash)
- `llama3.3` (Llama 3.3 70B Instruct)
- `claude` (Claude 3 Haiku)

### Premium Mode (Using `GITHUB_TOKEN`)
If you have a GitHub account, you can generate a free Personal Access Token (PAT) with `models:read` scope and set it as an environment variable:
```cmd
setx GITHUB_TOKEN "your_token_here"
```
Once set, the CLI automatically elevates, unlocking official, high-speed access to:
- `gpt-4o`
- `gpt-4o-mini`
- `deepseek-r1` (DeepSeek R1 reasoning model)
- `llama3.3` (Meta Llama 3.3 70B)
- `llama3.1-405b` (Massive 405B reasoning model)
- `phi4` (Microsoft Phi-4)
- `cohere` (Cohere Command R+)

---

## ⚠️ Terms of Service & Legal Disclaimer

This tool features a **Zero-Auth Mode** which utilizes public, unofficial reverse-engineered web interfaces for educational and prototyping purposes. Uptime and stability in Zero-Auth mode depend entirely on community-maintained libraries and are subject to changes or rate limits from external web platforms. 

For critical or high-volume workflows, setting up a free `GITHUB_TOKEN` is highly recommended to guarantee official, high-performance, and stable API endpoints.
