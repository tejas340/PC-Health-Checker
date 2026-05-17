"""
PC Health Checker – System Monitoring Dashboard
================================================
A secure, local-only Flask application for monitoring system health.

SECURITY NOTE:
  This app is designed for local system monitoring only.
  Do NOT expose it publicly without adding authentication and HTTPS.
  Default binding: 127.0.0.1 (localhost only)
"""

import os
import platform
import socket
import datetime
import subprocess
import psutil
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables from .env file (if present)
# ---------------------------------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback-dev-key-change-in-production")

# ---------------------------------------------------------------------------
# Security headers – applied to every response
# ---------------------------------------------------------------------------
@app.after_request
def set_security_headers(response):
    """Add security headers to every HTTP response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    return response


# ---------------------------------------------------------------------------
# Helper: human-readable byte sizes
# ---------------------------------------------------------------------------
def bytes_to_readable(num_bytes):
    """Convert raw byte count to a human-readable string (KB / MB / GB)."""
    try:
        num_bytes = float(num_bytes)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:.2f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.2f} PB"
    except (TypeError, ValueError):
        return "N/A"


# ---------------------------------------------------------------------------
# CPU information
# ---------------------------------------------------------------------------
def get_cpu_info():
    """Return CPU usage percentage and a descriptive status label."""
    try:
        percent = psutil.cpu_percent(interval=0.5)

        if percent <= 50:
            status = "Normal"
        elif percent <= 80:
            status = "Moderate Load"
        else:
            status = "High Usage"

        return {
            "percent": round(percent, 1),
            "status": status,
            "core_count": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
        }
    except Exception:
        return {"percent": "N/A", "status": "Unknown", "core_count": "N/A", "physical_cores": "N/A"}


# ---------------------------------------------------------------------------
# Memory / RAM information
# ---------------------------------------------------------------------------
def get_memory_info():
    """Return RAM usage statistics."""
    try:
        mem = psutil.virtual_memory()
        percent = mem.percent

        if percent <= 60:
            status = "Normal"
        elif percent <= 85:
            status = "Moderate"
        else:
            status = "High Usage"

        return {
            "total": bytes_to_readable(mem.total),
            "used": bytes_to_readable(mem.used),
            "available": bytes_to_readable(mem.available),
            "percent": round(percent, 1),
            "status": status,
        }
    except Exception:
        return {
            "total": "N/A", "used": "N/A",
            "available": "N/A", "percent": "N/A", "status": "Unknown",
        }


# ---------------------------------------------------------------------------
# Disk information
# ---------------------------------------------------------------------------
def get_disk_info():
    """Return disk usage statistics for the primary drive."""
    try:
        disk = psutil.disk_usage("/")
        percent = disk.percent

        if percent <= 70:
            status = "Good"
        elif percent <= 90:
            status = "Warning"
        else:
            status = "Critical"

        return {
            "total": bytes_to_readable(disk.total),
            "used": bytes_to_readable(disk.used),
            "free": bytes_to_readable(disk.free),
            "percent": round(percent, 1),
            "status": status,
        }
    except Exception:
        return {
            "total": "N/A", "used": "N/A",
            "free": "N/A", "percent": "N/A", "status": "Unknown",
        }


# ---------------------------------------------------------------------------
# Battery information
# ---------------------------------------------------------------------------
def get_battery_info():
    """Return battery status. Gracefully handles systems without a battery."""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return {
                "available": False,
                "message": "Battery information not available on this device.",
            }

        percent = round(battery.percent, 1)
        plugged = battery.power_plugged

        if plugged:
            status = "Charging" if percent < 100 else "Fully Charged"
        else:
            status = "Discharging"

        return {
            "available": True,
            "percent": percent,
            "plugged": plugged,
            "status": status,
        }
    except Exception:
        return {
            "available": False,
            "message": "Unable to read battery information.",
        }


# ---------------------------------------------------------------------------
# System / OS information
# ---------------------------------------------------------------------------
def get_system_info():
    """Return OS, hostname, boot time, and uptime information."""
    try:
        boot_timestamp = psutil.boot_time()
        boot_dt = datetime.datetime.fromtimestamp(boot_timestamp)
        now = datetime.datetime.now()
        uptime_delta = now - boot_dt

        total_seconds = int(uptime_delta.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days > 0:
            uptime_str = f"{days}d {hours}h {minutes}m"
        else:
            uptime_str = f"{hours}h {minutes}m"

        try:
            process_count = len(psutil.pids())
        except Exception:
            process_count = "N/A"

        return {
            "os": platform.system(),
            "os_version": platform.version()[:80],  # truncate very long strings
            "architecture": platform.machine(),
            "processor": platform.processor()[:80] or "N/A",
            "hostname": socket.gethostname(),
            "boot_time": boot_dt.strftime("%Y-%m-%d %I:%M %p"),
            "uptime": uptime_str,
            "process_count": process_count,
        }
    except Exception:
        return {
            "os": "N/A", "os_version": "N/A", "architecture": "N/A",
            "processor": "N/A", "hostname": "N/A",
            "boot_time": "N/A", "uptime": "N/A", "process_count": "N/A",
        }


# ---------------------------------------------------------------------------
# Network information
# ---------------------------------------------------------------------------
def get_network_info():
    """Return cumulative network I/O counters since system boot."""
    try:
        net = psutil.net_io_counters()
        return {
            "bytes_sent": bytes_to_readable(net.bytes_sent),
            "bytes_received": bytes_to_readable(net.bytes_recv),
            "packets_sent": net.packets_sent,
            "packets_received": net.packets_recv,
        }
    except Exception:
        return {
            "bytes_sent": "N/A", "bytes_received": "N/A",
            "packets_sent": "N/A", "packets_received": "N/A",
        }


# ---------------------------------------------------------------------------
# Overall health score calculation
# ---------------------------------------------------------------------------
def calculate_health_score(cpu, memory, disk, battery):
    """
    Derive a 0–100 health score from key system metrics.
    Deductions:
      CPU  > 80%   → -20
      CPU  60–80%  → -10
      RAM  > 85%   → -20
      RAM  65–85%  → -10
      Disk > 90%   → -25
      Disk 75–90%  → -10
      Batt < 20% and not charging → -15
    """
    score = 100

    try:
        cpu_pct = float(cpu.get("percent", 0))
        if cpu_pct > 80:
            score -= 20
        elif cpu_pct > 60:
            score -= 10
    except (TypeError, ValueError):
        pass

    try:
        mem_pct = float(memory.get("percent", 0))
        if mem_pct > 85:
            score -= 20
        elif mem_pct > 65:
            score -= 10
    except (TypeError, ValueError):
        pass

    try:
        disk_pct = float(disk.get("percent", 0))
        if disk_pct > 90:
            score -= 25
        elif disk_pct > 75:
            score -= 10
    except (TypeError, ValueError):
        pass

    try:
        if battery.get("available") and not battery.get("plugged"):
            batt_pct = float(battery.get("percent", 100))
            if batt_pct < 20:
                score -= 15
    except (TypeError, ValueError):
        pass

    score = max(0, min(100, score))

    if score >= 90:
        label = "Excellent"
    elif score >= 70:
        label = "Good"
    elif score >= 50:
        label = "Needs Attention"
    else:
        label = "Critical"

    return {"score": score, "label": label}

# ---------------------------------------------------------------------------
# Warnings and recommendations  (structured – includes fix_action)
# ---------------------------------------------------------------------------
def generate_warnings(cpu, memory, disk, battery):
    """
    Return a list of warning dicts, each with:
      message    - human-readable description
      severity   - "ok" | "warning" | "critical"
      fix_action - key passed to /api/fix/<action>, or None
      fix_label  - button label shown in the UI, or None
    """
    warnings = []

    # CPU
    try:
        cpu_pct = float(cpu.get("percent", 0))
        if cpu_pct > 80:
            warnings.append({
                "message":    "High CPU usage detected. Open Task Manager to find and close resource-heavy processes.",
                "severity":   "critical",
                "fix_action": "task_manager",
                "fix_label":  "Open Task Manager",
            })
        elif cpu_pct > 60:
            warnings.append({
                "message":    "CPU is under moderate load. Consider closing background applications.",
                "severity":   "warning",
                "fix_action": "task_manager",
                "fix_label":  "Open Task Manager",
            })
    except (TypeError, ValueError):
        pass

    # RAM
    try:
        mem_pct = float(memory.get("percent", 0))
        if mem_pct > 85:
            warnings.append({
                "message":    "High RAM usage detected. Close unused applications to free memory.",
                "severity":   "critical",
                "fix_action": "task_manager",
                "fix_label":  "Open Task Manager",
            })
        elif mem_pct > 65:
            warnings.append({
                "message":    "Memory usage is elevated. Closing unused apps can help.",
                "severity":   "warning",
                "fix_action": "task_manager",
                "fix_label":  "Open Task Manager",
            })
    except (TypeError, ValueError):
        pass

    # Disk
    try:
        disk_pct = float(disk.get("percent", 0))
        if disk_pct > 90:
            warnings.append({
                "message":    "Critical disk space! Run Disk Cleanup to delete temporary files and free space immediately.",
                "severity":   "critical",
                "fix_action": "disk_cleanup",
                "fix_label":  "Run Disk Cleanup",
            })
        elif disk_pct > 75:
            warnings.append({
                "message":    "Disk space is getting low. Running Disk Cleanup can help free up space.",
                "severity":   "warning",
                "fix_action": "disk_cleanup",
                "fix_label":  "Run Disk Cleanup",
            })
    except (TypeError, ValueError):
        pass

    # Battery
    try:
        if battery.get("available") and not battery.get("plugged"):
            batt_pct = float(battery.get("percent", 100))
            if batt_pct < 20:
                warnings.append({
                    "message":    "Battery is critically low. Connect the charger immediately. Open Power Options to adjust power settings.",
                    "severity":   "critical",
                    "fix_action": "power_options",
                    "fix_label":  "Open Power Options",
                })
            elif batt_pct < 30:
                warnings.append({
                    "message":    "Battery is getting low. Consider connecting the charger or enabling Battery Saver.",
                    "severity":   "warning",
                    "fix_action": "battery_saver",
                    "fix_label":  "Battery Saver Settings",
                })
    except (TypeError, ValueError):
        pass

    # All clear
    if not warnings:
        warnings.append({
            "message":    "No major issues detected. System health looks good.",
            "severity":   "ok",
            "fix_action": None,
            "fix_label":  None,
        })

    return warnings


# ---------------------------------------------------------------------------
# Fix actions - safely launch system tools without shell=True
# ---------------------------------------------------------------------------

_FIX_COMMANDS = {
    "task_manager": {
        "Windows": ["taskmgr.exe"],
        "Darwin":  ["open", "-a", "Activity Monitor"],
        "Linux":   ["xterm", "-e", "htop"],
    },
    "disk_cleanup": {
        "Windows": ["cleanmgr.exe"],
        "Darwin":  ["open", "/System/Library/CoreServices/Disk Utility.app"],
        "Linux":   ["xdg-open", "/"],
    },
    "power_options": {
        "Windows": ["control.exe", "powercfg.cpl"],
        "Darwin":  ["open", "x-apple.systempreferences:com.apple.preference.energysaver"],
        "Linux":   ["xdg-open", "https://help.ubuntu.com/community/PowerManagement"],
    },
    "battery_saver": {
        "Windows": ["cmd.exe", "/c", "start", "", "ms-settings:batterysaver"],
        "Darwin":  ["open", "x-apple.systempreferences:com.apple.preference.energysaver"],
        "Linux":   ["xdg-open", "https://help.ubuntu.com/community/PowerManagement"],
    },
    "startup_apps": {
        "Windows": ["taskmgr.exe"],
        "Darwin":  ["open", "-a", "System Preferences"],
        "Linux":   ["xdg-open", "https://help.ubuntu.com/community/AutoStart"],
    },
}

_FIX_DESCRIPTIONS = {
    "task_manager": "Opens Task Manager / Activity Monitor so you can identify and close resource-heavy processes.",
    "disk_cleanup": "Launches the Disk Cleanup tool to remove temporary files and recycle bin contents.",
    "power_options": "Opens Power Options / Energy Saver settings to adjust battery and performance profiles.",
    "battery_saver": "Opens Battery Saver settings to reduce background activity and extend battery life.",
    "startup_apps":  "Opens the startup app manager so you can disable programs that launch at boot.",
}


def _launch(cmd):
    """
    Launch a process safely using a list of arguments.
    Never uses shell=True. Returns (success, error_message).
    """
    try:
        subprocess.Popen(
            cmd,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        return True, None
    except FileNotFoundError:
        return False, "Command not found: " + cmd[0]
    except PermissionError:
        return False, "Permission denied when trying to launch the tool."
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Serve the main dashboard page."""
    return render_template("index.html")


@app.route("/api/system-health")
def system_health():
    """Return a JSON snapshot of all system health metrics."""
    cpu      = get_cpu_info()
    memory   = get_memory_info()
    disk     = get_disk_info()
    battery  = get_battery_info()
    system   = get_system_info()
    network  = get_network_info()
    health   = calculate_health_score(cpu, memory, disk, battery)
    warnings = generate_warnings(cpu, memory, disk, battery)

    payload = {
        "cpu":       cpu,
        "memory":    memory,
        "disk":      disk,
        "battery":   battery,
        "system":    system,
        "network":   network,
        "health":    health,
        "warnings":  warnings,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
    }
    return jsonify(payload)


@app.route("/api/fix/<action>", methods=["POST"])
def apply_fix(action):
    """
    Trigger a safe system-tool launch for the given action key.
    Only whitelisted action keys are accepted - no user-controlled commands.
    """
    if action not in _FIX_COMMANDS:
        return jsonify({
            "success": False,
            "error":   "Unknown fix action: '" + action + "'. No changes were made.",
        }), 400

    os_name = platform.system()
    cmd_map  = _FIX_COMMANDS[action]

    if os_name not in cmd_map:
        return jsonify({
            "success": False,
            "error":   "Fix action '" + action + "' is not supported on " + os_name + ".",
        }), 422

    cmd = cmd_map[os_name]
    success, err = _launch(cmd)

    if success:
        return jsonify({
            "success":     True,
            "action":      action,
            "description": _FIX_DESCRIPTIONS.get(action, ""),
            "message":     "Tool launched successfully.",
        })
    else:
        return jsonify({
            "success": False,
            "action":  action,
            "error":   err or "Failed to launch the tool.",
        }), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    print("=" * 60)
    print("  PC Health Checker - System Monitoring Dashboard")
    print("=" * 60)
    print("  Running on: http://127.0.0.1:5000")
    print("  Debug mode:", debug_mode)
    print("  Press Ctrl+C to stop the server.")
    print("=" * 60)

    # SECURITY: Bind to localhost only. Do not change to 0.0.0.0
    # without adding proper authentication and HTTPS.
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
