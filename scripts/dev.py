#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# IPA Platform - Unified Development Environment Manager
# =============================================================================
# Manages all development services: Backend, Frontend, Docker (PostgreSQL,
# Redis, RabbitMQ).
#
# Commands:
#   python scripts/dev.py start [service]   - Start service(s)
#   python scripts/dev.py stop [service]    - Stop service(s)
#   python scripts/dev.py restart [service] - Restart service(s)
#   python scripts/dev.py status            - Check all services status
#   python scripts/dev.py logs [service]    - View service logs
#
# Services:
#   all      - All services (docker + backend + frontend)
#   backend  - FastAPI backend (uvicorn)
#   frontend - React frontend (vite)
#   docker   - Docker services (postgres, redis, rabbitmq)
#
# Examples:
#   python scripts/dev.py start             # Start all services
#   python scripts/dev.py start backend     # Start backend only
#   python scripts/dev.py stop frontend     # Stop frontend only
#   python scripts/dev.py status            # Check all services
#   python scripts/dev.py logs backend      # View backend logs
# =============================================================================

import os
import sys
import signal
import socket
import subprocess
import time
import json
import io
from pathlib import Path
from contextlib import closing
from typing import List, Optional, Dict, Any
from enum import Enum

# Fix Windows console encoding for emoji/unicode
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
PID_DIR = PROJECT_ROOT / ".pids"

# Default ports
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 3007

# Docker services
DOCKER_SERVICES = ["postgres", "redis", "rabbitmq"]
DOCKER_MONITORING_SERVICES = ["jaeger", "prometheus", "grafana"]

# Service health check URLs
HEALTH_CHECKS = {
    "backend": "http://localhost:{port}/health",
    "frontend": "http://localhost:{port}",
    "postgres": "localhost:5432",
    "redis": "localhost:6379",
    "rabbitmq": "localhost:5672",
}


class ServiceType(Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    DOCKER = "docker"
    ALL = "all"


# =============================================================================
# Utility Functions
# =============================================================================

def find_python_executable(python_version: Optional[str] = None) -> List[str]:
    """
    查找指定版本的 Python 可執行文件。

    Args:
        python_version: Python 版本號 (如 "3.13", "3.12")，None 表示使用當前 Python

    Returns:
        可執行命令列表 (如 ['py', '-3.13'] 或 [sys.executable])
    """
    if python_version is None:
        return [sys.executable]

    # Windows: 使用 py launcher
    if sys.platform == 'win32':
        try:
            result = subprocess.run(
                ['py', f'-{python_version}', '--version'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                print(f"  Found Python {python_version}: {result.stdout.strip()}")
                return ['py', f'-{python_version}']
        except Exception as e:
            print(f"  Warning: Could not find Python {python_version} via py launcher: {e}")

    # Linux/Mac: 嘗試 python3.X
    else:
        python_cmd = f'python{python_version}'
        try:
            result = subprocess.run(
                [python_cmd, '--version'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                print(f"  Found Python {python_version}: {result.stdout.strip()}")
                return [python_cmd]
        except Exception as e:
            print(f"  Warning: Could not find {python_cmd}: {e}")

    # 回退到當前 Python
    print(f"  Falling back to current Python: {sys.executable}")
    return [sys.executable]


def get_pid_file(service: str, port: int = 0) -> Path:
    """Get PID file path for the given service."""
    PID_DIR.mkdir(exist_ok=True)
    if port:
        return PID_DIR / f"{service}_{port}.pid"
    return PID_DIR / f"{service}.pid"


def is_port_available(port: int) -> bool:
    """Check if the specified port is available."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('0.0.0.0', port))
            return True
        except OSError:
            return False


def is_process_alive(pid: int) -> bool:
    """Check if a process with given PID is actually running."""
    if sys.platform == 'win32':
        try:
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}', '/NH'],
                capture_output=True, text=True, timeout=5, shell=True
            )
            return str(pid) in result.stdout
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def find_process_on_port(port: int) -> List[int]:
    """Find process IDs using the specified port (supports IPv4 and IPv6)."""
    pids = []
    if sys.platform == 'win32':
        try:
            # Use netstat -ano without -p flag (Windows syntax differs from Linux)
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True, text=True, timeout=10
            )
            port_str = str(port)
            for line in result.stdout.split('\n'):
                # Only check TCP LISTENING lines
                if 'LISTENING' not in line or 'TCP' not in line:
                    continue
                # Match patterns like:
                # "  TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       12345"
                # "  TCP    [::1]:3005             [::]:0                 LISTENING       12345"
                parts = line.split()
                if len(parts) >= 5:
                    local_addr = parts[1]  # e.g., "0.0.0.0:8000" or "[::1]:3005"
                    # Extract port from address
                    if ':' in local_addr:
                        addr_port = local_addr.rsplit(':', 1)[-1]
                        if addr_port == port_str:
                            try:
                                pid = int(parts[-1])
                                # Verify process actually exists (netstat can show stale PIDs)
                                if is_process_alive(pid):
                                    pids.append(pid)
                            except ValueError:
                                pass
        except subprocess.TimeoutExpired:
            print("  Warning: netstat timed out")
    else:
        try:
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True, text=True, timeout=10
            )
            for pid in result.stdout.strip().split('\n'):
                if pid:
                    pids.append(int(pid))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    return list(set(pids))


def kill_process(pid: int, force: bool = False) -> bool:
    """Terminate a process by PID."""
    # First check if process actually exists
    if not is_process_alive(pid):
        return True  # Already dead

    try:
        if sys.platform == 'win32':
            # Try taskkill first
            args = ['taskkill', '/PID', str(pid)]
            if force:
                args.insert(1, '/F')
            result = subprocess.run(args, capture_output=True, timeout=10, shell=True)

            if result.returncode == 0:
                return True

            # Fallback to PowerShell Stop-Process (more reliable)
            if force:
                ps_cmd = f'Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue'
            else:
                ps_cmd = f'Stop-Process -Id {pid} -ErrorAction SilentlyContinue'

            result = subprocess.run(
                ['powershell', '-Command', ps_cmd],
                capture_output=True, timeout=10
            )

            # Verify process is gone
            time.sleep(0.5)
            return not is_process_alive(pid)
        else:
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)
            return True
    except Exception as e:
        print(f"  Failed to terminate process {pid}: {e}")
        return False


def wait_for_port_release(port: int, timeout: int = 5) -> bool:
    """Wait for port to be released."""
    for _ in range(timeout * 2):
        if is_port_available(port):
            return True
        time.sleep(0.5)
    return False


def run_command(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, -1, "", "Command timed out")


# =============================================================================
# Docker Service Management
# =============================================================================

def docker_status() -> Dict[str, str]:
    """Get Docker services status."""
    status = {}
    try:
        result = run_command(['docker-compose', 'ps', '--format', 'json'], PROJECT_ROOT)
        if result.returncode == 0 and result.stdout.strip():
            # Parse JSON lines
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        container = json.loads(line)
                        name = container.get('Name', '').replace('ipa-', '')
                        state = container.get('State', 'unknown')
                        status[name] = state
                    except json.JSONDecodeError:
                        pass
    except Exception:
        # Fallback to simple ps
        result = run_command(['docker-compose', 'ps'], PROJECT_ROOT)
        if result.returncode == 0:
            for line in result.stdout.split('\n')[2:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0].replace('ipa-', '')
                        state = 'running' if 'Up' in line else 'stopped'
                        status[name] = state
    return status


def docker_start(monitoring: bool = False) -> bool:
    """Start Docker services."""
    print("\n🐳 Starting Docker services...")

    cmd = ['docker-compose', 'up', '-d']
    if monitoring:
        cmd = ['docker-compose', '--profile', 'monitoring', 'up', '-d']

    result = run_command(cmd, PROJECT_ROOT, timeout=120)

    if result.returncode == 0:
        print("  ✅ Docker services started")
        # Wait for health checks
        print("  Waiting for services to be healthy...")
        time.sleep(5)
        return True
    else:
        print(f"  ❌ Failed to start Docker services")
        print(f"  Error: {result.stderr}")
        return False


def docker_stop() -> bool:
    """Stop Docker services."""
    print("\n🐳 Stopping Docker services...")

    result = run_command(['docker-compose', 'down'], PROJECT_ROOT, timeout=60)

    if result.returncode == 0:
        print("  ✅ Docker services stopped")
        return True
    else:
        print(f"  ❌ Failed to stop Docker services")
        print(f"  Error: {result.stderr}")
        return False


def docker_logs(service: Optional[str] = None, follow: bool = False) -> None:
    """View Docker service logs."""
    cmd = ['docker-compose', 'logs']
    if follow:
        cmd.append('-f')
    if service:
        cmd.append(service)

    subprocess.run(cmd, cwd=str(PROJECT_ROOT))


# =============================================================================
# Backend Service Management
# =============================================================================

def backend_status(port: int = DEFAULT_BACKEND_PORT) -> Dict[str, Any]:
    """Get backend service status."""
    pid_file = get_pid_file("backend", port)
    pids = find_process_on_port(port)
    port_available = is_port_available(port)

    return {
        "running": len(pids) > 0,
        "pids": pids,
        "port": port,
        "port_available": port_available,
        "pid_file_exists": pid_file.exists(),
    }


def backend_start(port: int = DEFAULT_BACKEND_PORT, foreground: bool = False,
                  python_version: Optional[str] = None) -> Optional[int]:
    """
    Start the backend server.

    Args:
        port: Port number (default: 8000)
        foreground: Run in foreground mode
        python_version: Specific Python version to use (e.g., "3.13")
    """
    print(f"\n🚀 Starting backend server...")

    # Check for existing processes
    existing = find_process_on_port(port)
    if existing:
        print(f"  Port {port} in use by PID(s): {', '.join(map(str, existing))}")
        print("  Stopping existing server...")
        backend_stop(port)
        time.sleep(1)

    # Check port availability
    actual_port = port
    if not is_port_available(port):
        print(f"  Port {port} unavailable (likely TIME_WAIT state)")
        alt_ports = [port + 1, port + 10, port + 80, port + 100]
        for alt in alt_ports:
            if is_port_available(alt):
                actual_port = alt
                print(f"  Using alternative port: {actual_port}")
                break
        else:
            print("  ❌ No available ports found")
            return None

    # Verify backend directory
    if not BACKEND_DIR.exists():
        print(f"  ❌ Backend directory not found: {BACKEND_DIR}")
        return None

    # Sprint 57.6 US-1 (R1 / 57.5 D-12+27): real V2 entry is `backend/src/api/main.py`
    # (has _lifespan + create_app + 7 routers). The legacy `backend/main.py`
    # stub from Sprint 49.1 has been removed per AD-Reality-1.
    main_py = BACKEND_DIR / "src" / "api" / "main.py"
    if not main_py.exists():
        print(f"  ❌ api/main.py not found in {BACKEND_DIR}/src")
        return None

    # Start uvicorn
    print(f"  Starting uvicorn on port {actual_port}...")

    # Get Python executable
    python_cmd = find_python_executable(python_version)
    if python_version:
        print(f"  Using Python command: {' '.join(python_cmd)}")

    uvicorn_args = [
        # Sprint 57.6 US-1: target real V2 entry `api.main:app` (NOT `main:app`
        # which loaded the now-removed Sprint 49.1 stub). Closes 57.5 D-12.
        # Requires PYTHONPATH=backend/src so uvicorn can resolve `api.main`.
        *python_cmd, '-m', 'uvicorn', 'api.main:app',
        '--reload',
        '--host', '0.0.0.0',
        '--port', str(actual_port),
        '--timeout-graceful-shutdown', '10',
        '--app-dir', 'src',
    ]

    if sys.platform == 'win32' and not foreground:
        process = subprocess.Popen(
            uvicorn_args,
            cwd=str(BACKEND_DIR),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        pid_file = get_pid_file("backend", actual_port)
        pid_file.write_text(str(process.pid))

        time.sleep(2)
        running = find_process_on_port(actual_port)

        if running:
            print(f"\n  ✅ Backend started successfully!")
            print(f"  PID: {process.pid}")
            print(f"  API: http://localhost:{actual_port}")
            print(f"  Docs: http://localhost:{actual_port}/docs")
        else:
            print(f"  ⚠️  Server may have failed to start")
    else:
        os.chdir(str(BACKEND_DIR))
        print(f"  Running in foreground (Ctrl+C to stop)...")
        # Use subprocess.run to support multi-part python commands (e.g., ['py', '-3.13'])
        try:
            subprocess.run(uvicorn_args, check=True)
        except KeyboardInterrupt:
            print("\n  Stopped by user")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Server exited with code {e.returncode}")

    return actual_port


def backend_stop(port: int = DEFAULT_BACKEND_PORT) -> bool:
    """Stop the backend server."""
    print(f"\n🛑 Stopping backend server on port {port}...")

    pids = find_process_on_port(port)
    if not pids:
        print("  No running server found")
        pid_file = get_pid_file("backend", port)
        if pid_file.exists():
            pid_file.unlink()
        return True

    # Graceful shutdown first
    print(f"  Found {len(pids)} process(es): {', '.join(map(str, pids))}")
    for pid in pids:
        print(f"  Sending SIGTERM to PID {pid}...")
        kill_process(pid, force=False)

    # Wait for graceful shutdown
    print("  Waiting for graceful shutdown...")
    for i in range(10):
        time.sleep(0.5)
        remaining = find_process_on_port(port)
        if not remaining:
            print("  ✅ Server stopped gracefully")
            break
    else:
        remaining = find_process_on_port(port)
        if remaining:
            print(f"  Graceful shutdown timeout, force killing...")
            for pid in remaining:
                kill_process(pid, force=True)
            time.sleep(0.5)

    # Clean up PID file
    pid_file = get_pid_file("backend", port)
    if pid_file.exists():
        pid_file.unlink()

    if find_process_on_port(port):
        print("  ⚠️  Some processes may still be running")
        return False

    print("  ✅ Backend stopped successfully")
    return True


# =============================================================================
# Frontend Service Management
# =============================================================================

def frontend_status(port: int = DEFAULT_FRONTEND_PORT) -> Dict[str, Any]:
    """Get frontend service status."""
    pid_file = get_pid_file("frontend", port)
    pids = find_process_on_port(port)
    port_available = is_port_available(port)

    return {
        "running": len(pids) > 0,
        "pids": pids,
        "port": port,
        "port_available": port_available,
        "pid_file_exists": pid_file.exists(),
    }


def frontend_start(port: int = DEFAULT_FRONTEND_PORT, foreground: bool = False) -> Optional[int]:
    """Start the frontend dev server."""
    print(f"\n🎨 Starting frontend server...")

    # Check for existing processes
    existing = find_process_on_port(port)
    if existing:
        print(f"  Port {port} in use by PID(s): {', '.join(map(str, existing))}")
        print("  Stopping existing server...")
        frontend_stop(port)
        time.sleep(1)

    # Verify frontend directory
    if not FRONTEND_DIR.exists():
        print(f"  ❌ Frontend directory not found: {FRONTEND_DIR}")
        return None

    package_json = FRONTEND_DIR / "package.json"
    if not package_json.exists():
        print(f"  ❌ package.json not found in {FRONTEND_DIR}")
        return None

    # Check node_modules
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("  Installing dependencies...")
        result = run_command(['npm', 'install'], FRONTEND_DIR, timeout=300)
        if result.returncode != 0:
            print(f"  ❌ Failed to install dependencies: {result.stderr}")
            return None

    # Start vite
    print(f"  Starting Vite dev server on port {port}...")

    npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'

    if sys.platform == 'win32' and not foreground:
        process = subprocess.Popen(
            [npm_cmd, 'run', 'dev'],
            cwd=str(FRONTEND_DIR),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        pid_file = get_pid_file("frontend", port)
        pid_file.write_text(str(process.pid))

        time.sleep(3)

        print(f"\n  ✅ Frontend started successfully!")
        print(f"  PID: {process.pid}")
        print(f"  URL: http://localhost:{port}")
    else:
        os.chdir(str(FRONTEND_DIR))
        print(f"  Running in foreground (Ctrl+C to stop)...")
        os.execvp(npm_cmd, [npm_cmd, 'run', 'dev'])

    return port


def frontend_stop(port: int = DEFAULT_FRONTEND_PORT) -> bool:
    """Stop the frontend server."""
    print(f"\n🛑 Stopping frontend server on port {port}...")

    pids = find_process_on_port(port)
    if not pids:
        print("  No running server found")
        pid_file = get_pid_file("frontend", port)
        if pid_file.exists():
            pid_file.unlink()
        return True

    # Kill processes
    print(f"  Found {len(pids)} process(es): {', '.join(map(str, pids))}")
    for pid in pids:
        kill_process(pid, force=True)

    time.sleep(1)

    # Clean up PID file
    pid_file = get_pid_file("frontend", port)
    if pid_file.exists():
        pid_file.unlink()

    print("  ✅ Frontend stopped successfully")
    return True


# =============================================================================
# Unified Commands
# =============================================================================

def cmd_status() -> None:
    """Show all services status."""
    print("\n" + "=" * 60)
    print("  IPA Platform - Development Environment Status")
    print("=" * 60)

    # Docker services
    print("\n🐳 Docker Services:")
    docker_st = docker_status()
    if docker_st:
        for service, state in docker_st.items():
            icon = "✅" if state == "running" else "❌"
            print(f"  {icon} {service}: {state}")
    else:
        print("  ❌ Docker services not running or docker-compose not available")

    # Backend
    print("\n🚀 Backend (FastAPI/Uvicorn):")
    backend_st = backend_status()
    if backend_st["running"]:
        print(f"  ✅ Running on port {backend_st['port']} (PID: {', '.join(map(str, backend_st['pids']))})")
        print(f"     API: http://localhost:{backend_st['port']}")
        print(f"     Docs: http://localhost:{backend_st['port']}/docs")
    else:
        print(f"  ❌ Not running (port {backend_st['port']} {'available' if backend_st['port_available'] else 'in TIME_WAIT'})")

    # Frontend
    print("\n🎨 Frontend (React/Vite):")
    frontend_st = frontend_status()
    if frontend_st["running"]:
        print(f"  ✅ Running on port {frontend_st['port']} (PID: {', '.join(map(str, frontend_st['pids']))})")
        print(f"     URL: http://localhost:{frontend_st['port']}")
    else:
        print(f"  ❌ Not running")

    print("\n" + "=" * 60)


def cmd_start(service: str = "all", backend_port: int = DEFAULT_BACKEND_PORT,
              frontend_port: int = DEFAULT_FRONTEND_PORT, monitoring: bool = False,
              python_version: Optional[str] = None) -> bool:
    """Start services."""
    success = True

    if service in ["all", "docker"]:
        success = docker_start(monitoring) and success
        time.sleep(2)  # Wait for docker services to be ready

    if service in ["all", "backend"]:
        result = backend_start(backend_port, python_version=python_version)
        success = (result is not None) and success

    if service in ["all", "frontend"]:
        result = frontend_start(frontend_port)
        success = (result is not None) and success

    if success:
        print("\n✅ All requested services started successfully!")
    else:
        print("\n⚠️  Some services failed to start")

    return success


def cmd_stop(service: str = "all", backend_port: int = DEFAULT_BACKEND_PORT,
             frontend_port: int = DEFAULT_FRONTEND_PORT) -> bool:
    """Stop services."""
    success = True

    if service in ["all", "frontend"]:
        success = frontend_stop(frontend_port) and success

    if service in ["all", "backend"]:
        success = backend_stop(backend_port) and success

    if service in ["all", "docker"]:
        success = docker_stop() and success

    if success:
        print("\n✅ All requested services stopped successfully!")
    else:
        print("\n⚠️  Some services failed to stop")

    return success


def cmd_restart(service: str = "all", backend_port: int = DEFAULT_BACKEND_PORT,
                frontend_port: int = DEFAULT_FRONTEND_PORT) -> bool:
    """Restart services."""
    print(f"\n🔄 Restarting {service}...")
    cmd_stop(service, backend_port, frontend_port)
    time.sleep(2)
    return cmd_start(service, backend_port, frontend_port)


def cmd_logs(service: str, follow: bool = False) -> None:
    """View service logs."""
    if service in DOCKER_SERVICES or service in DOCKER_MONITORING_SERVICES:
        docker_logs(service, follow)
    elif service == "docker":
        docker_logs(follow=follow)
    else:
        print(f"For {service} logs, check the console window or use the appropriate tool.")


def show_help() -> None:
    """Show help message."""
    print("""
IPA Platform - Unified Development Environment Manager

Usage:
  python scripts/dev.py <command> [service] [options]

Commands:
  start [service]   - Start service(s)
  stop [service]    - Stop service(s)
  restart [service] - Restart service(s)
  status            - Show all services status
  logs [service]    - View service logs

Services:
  all      - All services (default)
  backend  - FastAPI backend (uvicorn, port 8000)
  frontend - React frontend (vite, port 3005)
  docker   - Docker services (postgres, redis, rabbitmq)

Options:
  --backend-port <port>  - Backend port (default: 8000)
  --frontend-port <port> - Frontend port (default: 3005)
  --python <version>     - Python version for backend (e.g., 3.13, 3.12)
  --monitoring           - Include monitoring services (jaeger, prometheus, grafana)
  --fg                   - Run in foreground

Examples:
  python scripts/dev.py start              # Start all services
  python scripts/dev.py start backend      # Start backend only
  python scripts/dev.py start backend --python 3.13  # Start backend with Python 3.13
  python scripts/dev.py start docker --monitoring  # Start docker with monitoring
  python scripts/dev.py stop frontend      # Stop frontend only
  python scripts/dev.py restart backend    # Restart backend
  python scripts/dev.py status             # Check all services
  python scripts/dev.py logs postgres      # View postgres logs
  python scripts/dev.py logs docker -f     # Follow all docker logs

Quick Start (First Time):
  1. python scripts/dev.py start docker    # Start database services
  2. python scripts/dev.py start backend   # Start API server
  3. python scripts/dev.py start frontend  # Start UI (optional)

  Or simply: python scripts/dev.py start   # Start everything
""")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    # Parse arguments
    service = "all"
    backend_port = DEFAULT_BACKEND_PORT
    frontend_port = DEFAULT_FRONTEND_PORT
    monitoring = False
    follow = False
    python_version = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--backend-port' and i + 1 < len(args):
            backend_port = int(args[i + 1])
            i += 2
        elif arg == '--frontend-port' and i + 1 < len(args):
            frontend_port = int(args[i + 1])
            i += 2
        elif arg == '--python' and i + 1 < len(args):
            python_version = args[i + 1]
            i += 2
        elif arg == '--monitoring':
            monitoring = True
            i += 1
        elif arg in ['-f', '--follow']:
            follow = True
            i += 1
        elif not arg.startswith('-'):
            service = arg
            i += 1
        else:
            i += 1

    # Execute command
    if command == 'start':
        success = cmd_start(service, backend_port, frontend_port, monitoring, python_version)
        sys.exit(0 if success else 1)
    elif command == 'stop':
        success = cmd_stop(service, backend_port, frontend_port)
        sys.exit(0 if success else 1)
    elif command == 'restart':
        success = cmd_restart(service, backend_port, frontend_port)
        sys.exit(0 if success else 1)
    elif command == 'status':
        cmd_status()
    elif command == 'logs':
        cmd_logs(service, follow)
    elif command == 'mock':
        # Sprint 51.0 — dispatch to standalone scripts/mock_dev.py
        # Avoids weaving mock_services into ServiceType enum (low risk).
        mock_args = sys.argv[2:] if len(sys.argv) > 2 else []
        if not mock_args or mock_args[0] not in ('start', 'stop', 'status'):
            print("usage: python scripts/dev.py mock {start|stop|status}")
            sys.exit(2)
        mock_dev = Path(__file__).parent / 'mock_dev.py'
        result = subprocess.run(
            [sys.executable, str(mock_dev), mock_args[0]],
            check=False,
        )
        sys.exit(result.returncode)
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
