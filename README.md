# Hermes Agent Setup — Victor

> A fully automated, self-hosted AI agent system built on **Hermes Agent v0.14.0**, deployed on a Hetzner VPS. Communicate via Telegram, WhatsApp, or phone call. The agent searches jobs, manages your iCloud calendar, delivers daily news, and more — all hands-free.

---

## 🏗️ Infrastructure

| Component | Details |
|---|---|
| **Server** | Hetzner VPS — Ubuntu 24.04 (8GB RAM) |
| **IP Address** | `188.34.202.40` |
| **Hermes Version** | v0.14.0 |
| **Python venv** | `/root/hermes-venv/bin/python3` |
| **Config File** | `~/.hermes/config.yaml` |
| **Environment** | `~/.hermes/.env` |
| **Logs** | `~/.hermes/logs/` |

---

## ✅ Features

| Feature | Status | Description |
|---|---|---|
| Job Scout MCP | ✅ Live | Searches Adzuna + JSearch, filters by saved profile |
| iCloud Calendar MCP | ✅ Live | List, create, update Apple Calendar events via CalDAV |
| Telegram Integration | ✅ Live | Chat + voice input/output |
| WhatsApp Integration | ✅ Live | Chat via self-chat bridge |
| Telephony Agent | ✅ Live | Call your AI agent via Twilio phone number |
| Live Dashboard | ✅ Live | Real-time agent office at `http://188.34.202.40:5000/` |
| Daily Job Alerts | ✅ Live | Cron job delivers new job listings daily |
| Daily News Reports | ✅ Live | Tech and financial news delivered daily |
| GitHub Auto-Push | ✅ Live | Daily backup of home directory to this repo |

---

## 🤖 MCP Tool Agents

### Job Scout (`job_scout_mcp.py`)
Searches multiple job boards and filters results against your saved preferences.

- **APIs:** Adzuna + JSearch (RapidAPI)
- **Persistent storage:** `~/hermes/tools/job_scout/job_profile.json`
- **Deduplication:** `~/hermes/tools/job_scout/seen_jobs.json`
- **Current profile:** TPM / Localization Manager, Remote/Hybrid, $140k minimum, Software/Consulting

### iCloud Calendar (`icloud_calendar_mcp.py`)
Connects to Apple's CalDAV API to manage your iCloud calendar.

- **Protocol:** CalDAV over HTTPS
- **Capabilities:** List events, create events, update events
- **Auth:** App-Specific Password (not your Apple ID password)

---

## 🧠 Active Personalities

| Name | Role |
|---|---|
| `job-scout` | Job search specialist — uses Job Scout MCP |
| `calendar-assistant` | Calendar manager — uses iCloud Calendar MCP |
| `researcher` | Web research specialist |
| `Coder` | Software coding expert |
| `tech-writer` | Professional technical writer |
| `Doc-reviewer` | Technical documentation reviewer |
| `technical` | Detailed technical expert |
| `creative` | Creative thinking assistant |
| `teacher` | Patient teacher with examples |
| `manager` | Agent orchestrator — delegates to specialists |

---

## 📱 Communication Channels

### Telegram
- Text and voice messaging
- Home channel for cron job delivery
- Voice input transcribed via local Whisper

### WhatsApp
- Text messaging via Baileys self-chat bridge
- Voice message transcription supported

### Telephony (Twilio)
- Call your Twilio toll-free number
- Speak your question — Hermes responds in voice
- Supports English and Chinese (Mandarin)
- Webhook: `http://188.34.202.40:5001/voice/incoming`

---

## 📊 Live Dashboard

**URL:** `http://188.34.202.40:5000/`

Real-time Pac-Man ghost dashboard showing:
- All MCP tool agents with live status
- All personality agents
- System resources (CPU, memory, disk, network)
- Live activity log from Hermes
- Scheduled cron jobs
- VPS uptime and session count

---

## ⏰ Scheduled Cron Jobs

| Job | Schedule | Description |
|---|---|---|
| Daily Tech News | 3:00 PM UTC | Fetches and summarizes tech news |
| Daily Financial News | 4:00 PM UTC | Market summary and financial updates |
| Daily Localization Jobs | 5:00 PM UTC | New Localization Manager listings |
| Daily TPM Jobs | 5:30 PM UTC | New TPM job listings |
| GitHub Auto-Push | Midnight UTC | Backs up home directory to this repo |

---

## 🗂️ File Structure

```
/root/
├── icloud_calendar_mcp.py      # iCloud Calendar MCP server
├── job_scout_mcp.py            # Job Scout MCP server
├── hermes_dashboard_api.py     # Dashboard Flask API (port 5000)
├── hermes_telephony.py         # Telephony agent Flask server (port 5001)
├── hermes-agent-office-live.html  # Live dashboard frontend
└── hermes-venv/                # Python virtual environment

~/.hermes/
├── config.yaml                 # Hermes configuration
├── .env                        # API keys and environment variables
└── logs/
    ├── agent.log               # Agent activity
    └── mcp-stderr.log          # MCP server errors

~/.config/systemd/user/
├── hermes-gateway.service      # Main Hermes agent
├── hermes-dashboard.service    # Dashboard API
└── hermes-telephony.service    # Telephony agent
```

---

## 🔧 Services

```bash
# Main Hermes gateway
systemctl --user status hermes-gateway

# Live dashboard API
systemctl --user status hermes-dashboard

# Telephony agent
systemctl --user status hermes-telephony
```

---

## 💬 Quick Reference

```bash
# Talk to Hermes from terminal
h "find me TPM jobs"
h "what's on my calendar this week?"
h "switch to researcher and find AI news"

# Restart services
systemctl --user restart hermes-gateway
systemctl --user restart hermes-dashboard
systemctl --user restart hermes-telephony
```

---

## 📚 Documentation

- [Full Setup Guide](hermes-agent-documentation.md)
- [Live Dashboard](http://188.34.202.40:5000/)
- [Dashboard HTML](hermes-agent-office-live.html)

---

*Built with [Hermes Agent](https://github.com/hermesagent) · Hosted on Hetzner VPS · Last updated May 2026*
