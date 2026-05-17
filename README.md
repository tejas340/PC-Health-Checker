# PC Health Checker – System Monitoring Dashboard

> A real-time, local system health monitoring dashboard built for IT support diagnostics. Displays CPU, RAM, disk, battery, network, and uptime data in a clean dark-themed web interface — with automated health scoring and actionable recommendations.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-black?logo=flask)
![psutil](https://img.shields.io/badge/psutil-6.1-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Screenshots

> Add screenshots to the `/screenshots` folder and reference them here.

| Dashboard Overview | Warnings & Health Score |
|---|---|
| *(screenshot here)* | *(screenshot here)* |

---

## Features

- **CPU Monitoring** – Live usage percentage, status label (Normal / Moderate / High), and core count
- **RAM Monitoring** – Total, used, and available memory with percentage and status
- **Disk Monitoring** – Primary drive usage with space breakdown and warnings at 75 % and 90 %
- **Battery Status** – Percentage, charging state, and low-battery alerts (works gracefully on desktops with no battery)
- **Network Statistics** – Bytes and packets sent/received since boot, in human-readable units
- **System Uptime** – Formatted uptime, boot timestamp, and active process count
- **Overall Health Score** – Calculated 0–100 score across CPU, RAM, disk, and battery; labelled Excellent / Good / Needs Attention / Critical
- **Warnings & Recommendations** – Actionable alerts for each detected issue
- **Auto-Refresh Dashboard** – Polls the API every 5 seconds; no page reload required
- **Manual Refresh & Export** – Refresh button and one-click plain-text report download
- **Secure Local-Only Design** – Binds to 127.0.0.1 only; security headers on every response; no shell commands; no external API calls

---

## Tech Stack

| Layer     | Technology          |
|-----------|---------------------|
| Backend   | Python 3.8+, Flask  |
| System    | psutil, platform, socket, datetime |
| Frontend  | HTML5, CSS3, Vanilla JavaScript |
| Config    | python-dotenv       |

---

## Project Structure

```
PC-Health-Checker/
│
├── app.py                  # Flask application – routes, API, helper functions
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── README.md               # This file
│
├── templates/
│   └── index.html          # Dashboard HTML page
│
├── static/
│   ├── style.css           # Dark IT dashboard stylesheet
│   └── script.js           # Auto-refresh and DOM update logic
│
└── screenshots/
    └── .gitkeep            # Placeholder – add screenshots here
```

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Steps

**1. Clone the repository**

```bash
git clone https://github.com/your-username/PC-Health-Checker.git
cd PC-Health-Checker
```

**2. (Optional but recommended) Create a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

```bash
cp .env.example .env
# Open .env and set a strong FLASK_SECRET_KEY
```

---

## How to Run

```bash
python app.py
```

Then open your browser and navigate to:

```
http://127.0.0.1:5000
```

The dashboard will load and begin refreshing automatically every 5 seconds.

To stop the server press `Ctrl + C`.

---

## API Reference

The backend exposes a single JSON endpoint:

### `GET /api/system-health`

Returns a JSON object with all system metrics. Example response:

```json
{
  "cpu": {
    "percent": 35.0,
    "status": "Normal",
    "core_count": 8,
    "physical_cores": 4
  },
  "memory": {
    "total": "16.00 GB",
    "used": "6.40 GB",
    "available": "9.60 GB",
    "percent": 40.0,
    "status": "Normal"
  },
  "disk": {
    "total": "512.00 GB",
    "used": "210.00 GB",
    "free": "302.00 GB",
    "percent": 41.0,
    "status": "Good"
  },
  "battery": {
    "available": true,
    "percent": 82.0,
    "plugged": true,
    "status": "Charging"
  },
  "system": {
    "os": "Windows",
    "os_version": "10.0.22621",
    "architecture": "AMD64",
    "processor": "Intel(R) Core(TM) i7-10750H",
    "hostname": "DESKTOP-ABC123",
    "boot_time": "2026-05-17 08:30 AM",
    "uptime": "6h 45m",
    "process_count": 210
  },
  "network": {
    "bytes_sent": "250.30 MB",
    "bytes_received": "1.80 GB",
    "packets_sent": 185000,
    "packets_received": 240000
  },
  "health": {
    "score": 90,
    "label": "Excellent"
  },
  "warnings": [
    "✔ No major issues detected. System health looks good."
  ],
  "timestamp": "2026-05-17 03:15:00 PM"
}
```

---

## Security Notes

This project is designed with security in mind even though it runs locally:

- **Local-only binding** – Flask binds to `127.0.0.1`, never `0.0.0.0`
- **Security headers** – Every response includes `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and a strict `Content-Security-Policy`
- **No shell commands** – System data is collected only through `psutil`, `platform`, `socket`, and `datetime`; `os.system()`, `subprocess`, and `eval()` are never used
- **Safe JavaScript** – Frontend uses `textContent` (not `innerHTML`) and creates DOM nodes with `createElement()` to prevent XSS
- **No data exfiltration** – All data stays on your machine; no external API calls are made
- **Environment variables** – The Flask secret key is loaded from `.env`, not hard-coded

> ⚠️ Do not expose this application publicly without adding authentication and HTTPS.

---

## Suggested Screenshots for GitHub

Take these screenshots to include in your README and portfolio:

1. **Full dashboard** – open browser at 100 % zoom, full screen, all cards visible
2. **Health score card** – zoom into the health score and status badge
3. **Warnings section** – simulate high CPU or low battery to trigger a warning
4. **Mobile view** – narrow the browser window to ~375 px to show the responsive layout
5. **Export report** – screenshot the downloaded `.txt` file contents

---

## Future Improvements

- [ ] Historical graph: chart CPU / RAM usage over the session using Chart.js
- [ ] Scan history stored in SQLite so you can compare snapshots over time
- [ ] Email or desktop notification when health score drops below a threshold
- [ ] Top-N process list showing the most resource-hungry processes
- [ ] Light / dark theme toggle
- [ ] Configurable refresh interval in the UI
- [ ] Docker container for easy deployment

---

## Resume Bullets

```
PC Health Checker – System Monitoring Dashboard                     Python · Flask · psutil
──────────────────────────────────────────────────────────────────────────────────────────
• Built a real-time PC health monitoring dashboard using Python Flask and psutil, displaying
  CPU, memory, disk, battery, uptime, and network usage through a clean web interface.

• Added automated health scoring logic (0–100 scale) to identify performance, storage, and
  battery-related issues, with categorised labels (Excellent / Good / Needs Attention / Critical).

• Implemented a system warnings engine that generates actionable recommendations for high
  CPU usage, high RAM consumption, low disk space, and low battery, supporting desktop
  troubleshooting workflows.

• Applied secure coding practices: local-only execution (127.0.0.1), HTTP security headers
  (CSP, X-Frame-Options, Referrer-Policy), no shell command execution, safe DOM manipulation
  (textContent / createElement), and environment-variable-based secret management.

• Designed a responsive dark-themed dashboard (CSS Grid, mobile-first breakpoints) with
  auto-refreshing data via JavaScript fetch() polling the /api/system-health JSON endpoint
  every 5 seconds and a one-click plain-text report export feature.
```

---

## License

MIT – free to use, modify, and distribute.
