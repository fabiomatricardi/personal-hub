# MyHub

A desktop toolkit that bundles 7 apps into a single Python/Vue application: link card creator, tweet generator, command wiki, Telegram message digest, Telegram file saver, and a cron scheduler.

---

## Apps

| App | What it does | Needs API key? | Needs Telegram? |
|-----|-------------|----------------|-----------------|
| **Dashboard** | App launcher | No | No |
| **Link Card Creator** | Generate styled HTML embed cards from URLs with auto-fetched metadata | No | No |
| **Tweet Generator** | Convert articles into tweet threads using AI | Yes | No |
| **Wiki** | Browse personal command reference files | No | No |
| **Telegram Digest** | AI-summarized email digests from Telegram messages | Yes | Yes |
| **Telegram Files** | Save file attachments from Telegram to local disk | No | Yes |
| **Cron Dashboard** | Manage schedules for Telegram apps | No | No |

---

## Prerequisites

- **Python 3.12+** — [python.org](https://python.org)
- **UV** — Python package manager: `pip install uv`
- **Node.js 18+** — [nodejs.org](https://nodejs.org)

---

## Quick Start (Development)

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/personal-hub.git
cd personal-hub

# 2. Install Python dependencies
uv sync

# 3. Install frontend dependencies
cd frontend
npm install

# 4. Build the frontend
npm run build
cd ..

# 5. Run the app
run-dev.bat
```

Your browser opens to `http://localhost:8999`. The Dashboard shows all 7 apps.

---

## Build the Executable

```bash
build.bat
```

This runs a 5-step pipeline:
1. Install Python dependencies
2. Install frontend dependencies
3. Build the Vue frontend
4. Package into `MyHub.exe` with PyInstaller
5. Add Windows Defender exclusion (prompts for admin)

Output: `dist/MyHub.exe`

> **Windows Smart App Control:** If Windows blocks the exe, run `exclude-defender.bat "C:\path\to\dist"` or run `build.bat` which handles this automatically.

---

## Settings Page Reference

Click **Settings** in the sidebar. Here's what to fill in:

### LLM Provider (Required for Tweet Gen and TG Digest)

You need at least one provider configured. Most OpenAI-compatible APIs work.

| Field | What to enter | Example |
|-------|--------------|---------|
| **Provider Name** | Any label | `OpenAI`, `Groq`, `ZENMUX` |
| **API Base URL** | Provider's API endpoint | `https://api.openai.com/v1` |
| **API Key** | Your secret key | `sk-abc123...` |
| **Models** | Click "Add Model" for each model | `gpt-4o`, `groq/compound-mini` |

Click **Test Connection** to verify before saving.

**Supported providers:**
- OpenAI — `https://api.openai.com/v1`
- Groq — `https://api.groq.com/openai/v1`
- ZENMUX — `https://zenmux.ai/api/v1`
- Together AI — `https://api.together.xyz/v1`
- Any local LLM (Ollama, LM Studio, etc.)

### Telegram Bot (Required for TG Digest and TG Files)

1. Open Telegram, search for **@BotFather**
2. Send `/newbot`, follow the prompts
3. Copy the bot token (e.g., `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Paste in **Bot Token** field

> **Important:** You must start a chat with your bot (send `/start`). The bot can only see messages sent directly to it.

### Gmail (Required for TG Digest email digests)

| Field | What to enter |
|-------|--------------|
| **Gmail Address** | Your full Gmail address |
| **Gmail App Password** | 16-character app password (not your main password) |
| **Recipient Email** | Where digests are sent (can be the same as your Gmail) |

**To generate an App Password:**
1. Go to [Google Account](https://myaccount.google.com) > **Security**
2. Enable **2-Step Verification** (required)
3. Search for **App Passwords**
4. Generate a new password for "Mail"

### Schedules (Optional, has defaults)

| Setting | Default | Format |
|---------|---------|--------|
| **Daily Digest Cron** | `0 8 * * *` | Every day at 8:00 AM |
| **Weekly Digest Cron** | `0 9 * * 1` | Every Monday at 9:00 AM |
| **Files Check Cron** | `*/30 * * * *` | Every 30 minutes |

Cron format: `minute hour day month day_of_week`

### TG Files Save Directory (Optional)

| Setting | Default | Example |
|---------|---------|---------|
| **Save Directory** | `./telegram_files/` | `C:\TelegramFiles` |

Use absolute paths for reliability.

---

## Network Access

MyHub binds to `0.0.0.0:8999` by default, accessible from other devices on your network.

1. Find your IP: run `ipconfig` in Command Prompt
2. From another device, open `http://<your-ip>:8999`

---

## Project Structure

```
personal-hub/
├── backend/           FastAPI API + services
│   ├── main.py        Entry point (port 8999)
│   ├── models.py      Pydantic data models
│   ├── routers/       8 API route modules
│   └── services/      Business logic (8 modules)
├── frontend/          Vue 3 SPA
│   ├── src/
│   │   ├── App.vue    Root component
│   │   ├── components/  9 Vue views
│   │   ├── composables/  API client
│   │   └── styles/    CSS themes
│   └── vite.config.js
├── wiki/              Sample reference files
├── pyproject.toml     Python config + dependencies
├── build.py           PyInstaller build script
├── build.bat          Build pipeline
├── run-dev.bat        Development launcher
└── exclude-defender.bat  Windows Defender fix
```

---

## Adding Wiki Files

Place `.md` or `.txt` files in the `wiki/` folder. Use `# Heading` as the first line for the display title.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Windows blocks the exe | Run `exclude-defender.bat "C:\path\to\dist"` |
| "LLM not configured" warning | Add an API key in Settings |
| Port 8999 in use | Close the other app, or change `PORT` in `backend/main.py` |
| Telegram bot not responding | Send `/start` to the bot in Telegram |
| Digest emails not sending | Verify Gmail App Password (not your main password) |
| Cron jobs not running | Jobs only run while MyHub is open |

---

## License

MIT License - Fabio Matricardi (fabio.matricardi@gmail.com)
