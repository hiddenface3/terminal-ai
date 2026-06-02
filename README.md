# ⚡ Terminal AI Assistant

A login-free, 100% free, and zero-friction command-line AI assistant for Windows. This repository is built to be cloned, installed in seconds, and immediately run from ANY terminal (CMD, PowerShell, or Windows Terminal) with **zero accounts, zero sign-ups, zero tokens, and zero cost**.

---

## ✨ Features

- 🌌 **Zero-Auth Free Providers**: Leverages optimized public web aggregators to query models anonymously without any API keys, sign-ups, or logins.
- 📸 **Vision / Screenshot Support**: Analyze any local image or screenshot directly from your command prompt using the `/vision` command!
- 🎨 **Premium Visual UI**:
  - Beautiful, character-by-character response streaming.
  - Syntax-highlighted code blocks (just like VS Code) and styled tables.
  - Live loading spinners showing AI thinking status.
- 💬 **Smart Session Control**:
  - Automatically loads and saves conversation history so you can continue your chats across sessions.
  - Full support for multi-turn chats.
- 📦 **Windows Global Integration**:
  - Seamless installer `setup.bat` creates a dedicated virtual environment (`.venv`) and configures a global shortcut command (`ai`) allowing execution from any directory.

---

## 🚀 Quick Setup (Windows)

Simply open your Command Prompt (CMD) or PowerShell and run the following:

### 1. Clone the Repository
```cmd
git clone https://github.com/hiddenface3/terminal-ai.git
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

### 2. One-Shot Command Prompts
Ask a quick question directly and exit:
```cmd
ai "How do I list listening ports on Windows CMD?"
```

### 3. Model Switcher
Explicitly start a session using a specific model:
```cmd
ai -m qwen
```

---

## 🛠️ Commands (Interactive Loop)

Use these slash commands inside the interactive chat loop:

| Command | Action |
| :--- | :--- |
| `/help` | Displays help panel with all commands and active models. |
| `/model <name>` | Switches active model on-the-fly. |
| `/vision "path" prompt` | Analyzes a local screenshot/image file. |
| `/clear` or `/reset` | Clears conversation history. |
| `/history` | Displays previous dialogue within the current thread. |
| `/exit` or `/quit` | Quits the assistant. |

---

## 🧠 Supported Models

Copy and paste these commands inside the chat to switch models instantly:

*   `/model gpt-4o-mini` - Fast, balanced general chat.
*   `/model qwen` - Qwen 2.5 (advanced reasoning and coding).
*   `/model llama3.3` - Meta Llama 3.3 (balanced conversational model).
*   `/model claude` - Claude 3 Haiku (fast balanced chat).

---

## 📸 Vision / Screenshot Analysis

You can question any local image or screenshot file by supplying its path and your question:

```text
You (gpt-4o-mini) > /vision "C:\Users\Huzaifa Ali\Desktop\chart.png" What trends do you see in this graph?
```

### How it works:
1. You supply a path to a `.png`, `.jpg`, `.jpeg`, or `.webp` file.
2. Terminal AI automatically encodes the image to Base64 in the background.
3. It passes the base64 structure along with your text query to a multimodal-enabled free model.
4. Responses stream back in standard real-time markdown formatting.

---

## ⚠️ Terms of Service & Legal Disclaimer

This tool utilizes public, unofficial reverse-engineered web interfaces for educational and prototyping purposes. Uptime and stability depend entirely on community-maintained libraries and are subject to changes or rate limits from external web platforms.
