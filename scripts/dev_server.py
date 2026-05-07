#!/usr/bin/env python
# =============================================================================
# IPA Platform - Development Server Management Script
# =============================================================================
# Solves Windows uvicorn port binding issues (TIME_WAIT state)
#
# Commands:
#   python scripts/dev_server.py start [port]   - Start server
#   python scripts/dev_server.py stop [port]    - Stop server
#   python scripts/dev_server.py restart [port] - Restart server
#   python scripts/dev_server.py status [port]  - Check status
#
# Features:
#   - Auto-cleanup of old processes before starting
#   - Smart port selection (auto-fallback if port unavailable)
#   - Cross-platform support (Windows and Linux/Mac)
#   - PID file management for graceful shutdown
#   - Graceful shutdown with timeout, then force kill
# =============================================================================

import os
import sys
import signal
import socket
import subprocess
import time
from pathlib import Path
from contextlib import closing
from typing import List, Optional

DEFAULT_PORT = 8000
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
PID_DIR = PROJECT_ROOT / ".pids"


def get_pid_file(port: int) -> Path:
    """Get PID file path for the given port."""
    PID_DIR.mkdir(exist_ok=True)
    return PID_DIR / f"uvicorn_{port}.pid"


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
                                pids.append(int(parts[-1]))
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
    try:
        if sys.platform == 'win32':
            args = ['taskkill', '/PID', str(pid)]
            if force:
                args.insert(1, '/F')
            result = subprocess.run(args, capture_output=True, timeout=10)
            return result.returncode == 0
        else:
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)
            return True
    except Exception as e:
        print(f"  Failed to terminate process {pid}: {e}")
        return False


def is_port_available(port: int) -> bool:
    """Check if the specified port is available."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('0.0.0.0', port))
            return True
        except OSError:
            return False


def wait_for_port_release(port: int, timeout: int = 5) -> bool:
    """Wait for port to be released."""
    for _ in range(timeout * 2):
        if is_port_available(port):
            return True
        time.sleep(0.5)
    return False


def cmd_status(port: int) -> None:
    """Show server status."""
    pid_file = get_pid_file(port)
    pids = find_process_on_port(port)
    port_available = is_port_available(port)

    print(f"\nPort {port} Status:")
    print("-" * 40)

    if pids:
        print(f"  Status: RUNNING")
        print(f"  PID(s): {', '.join(map(str, pids))}")
    elif pid_file.exists():
        saved_pid = pid_file.read_text().strip()
        print(f"  Status: STOPPED (stale PID file)")
        print(f"  Saved PID: {saved_pid}")
        pid_file.unlink()
        print("  (Cleaned up stale PID file)")
    else:
        print(f"  Status: STOPPED")

    print(f"  Port available: {'Yes' if port_available else 'No (in use or TIME_WAIT)'}")

    if not port_available and not pids:
        print(f"  Note: Port may be in TIME_WAIT state, wait ~30-60 seconds")
    print()


def cmd_stop(port: int) -> bool:
    """Stop the server gracefully."""
    print(f"\nStopping server on port {port}...")

    pids = find_process_on_port(port)
    if not pids:
        print("  No running server found")
        # Clean up PID file if exists
        pid_file = get_pid_file(port)
        if pid_file.exists():
            pid_file.unlink()
        return True

    # Try graceful shutdown first
    print(f"  Found {len(pids)} process(es): {', '.join(map(str, pids))}")
    for pid in pids:
        print(f"  Sending SIGTERM to PID {pid}...")
        kill_process(pid, force=False)

    # Wait for graceful shutdown
    print("  Waiting for graceful shutdown...")
    for i in range(10):  # Wait up to 5 seconds
        time.sleep(0.5)
        remaining = find_process_on_port(port)
        if not remaining:
            print("  Server stopped gracefully")
            break
    else:
        # Force kill if still running
        remaining = find_process_on_port(port)
        if remaining:
            print(f"  Graceful shutdown timeout, force killing...")
            for pid in remaining:
                kill_process(pid, force=True)
            time.sleep(0.5)

    # Clean up PID file
    pid_file = get_pid_file(port)
    if pid_file.exists():
        pid_file.unlink()

    # Verify
    if find_process_on_port(port):
        print("  Warning: Some processes may still be running")
        return False

    print("  Server stopped successfully")
    return True


def cmd_start(port: int, foreground: bool = False) -> Optional[int]:
    """Start the server, returning actual port used."""
    print(f"\nStarting server...")

    # 1. Clean up any existing processes
    existing = find_process_on_port(port)
    if existing:
        print(f"  Port {port} in use by PID(s): {', '.join(map(str, existing))}")
        print("  Stopping existing server...")
        cmd_stop(port)
        time.sleep(1)

    # 2. Check port availability, find alternative if needed
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
            print("  ERROR: No available ports found")
            print(f"  Tried: {port}, {', '.join(map(str, alt_ports))}")
            return None

    # 3. Verify backend directory
    if not BACKEND_DIR.exists():
        print(f"  ERROR: Backend directory not found: {BACKEND_DIR}")
        return None

    main_py = BACKEND_DIR / "main.py"
    if not main_py.exists():
        print(f"  ERROR: main.py not found in {BACKEND_DIR}")
        return None

    # 4. Start uvicorn
    print(f"  Starting uvicorn on port {actual_port}...")

    uvicorn_args = [
        # Sprint 57.6 US-1 — same fix as dev.py: target real V2 `api.main:app`
        # entry (NOT removed `main:app` 49.1 stub). Closes 57.5 D-12.
        sys.executable, '-m', 'uvicorn', 'api.main:app',
        '--reload',
        '--host', '0.0.0.0',
        '--port', str(actual_port),
        '--timeout-graceful-shutdown', '10',
        '--app-dir', 'src',
    ]

    if sys.platform == 'win32' and not foreground:
        # Windows: Start in new console window
        process = subprocess.Popen(
            uvicorn_args,
            cwd=str(BACKEND_DIR),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        # Save PID
        pid_file = get_pid_file(actual_port)
        pid_file.write_text(str(process.pid))

        # Wait a moment and verify
        time.sleep(2)
        running = find_process_on_port(actual_port)

        if running:
            print(f"\n  Server started successfully!")
            print(f"  PID: {process.pid}")
            print(f"  API: http://localhost:{actual_port}")
            print(f"  Docs: http://localhost:{actual_port}/docs")
            print(f"\n  Use 'python scripts/dev_server.py stop {actual_port}' to stop")
        else:
            print(f"  Warning: Server may have failed to start")
            print(f"  Check the new console window for errors")
    else:
        # Linux/Mac or foreground mode: exec replaces current process
        os.chdir(str(BACKEND_DIR))
        print(f"  Running in foreground (Ctrl+C to stop)...")
        os.execvp(sys.executable, uvicorn_args)

    return actual_port


def cmd_restart(port: int) -> None:
    """Restart the server."""
    print(f"\nRestarting server on port {port}...")
    cmd_stop(port)
    time.sleep(1)
    cmd_start(port)


def show_help() -> None:
    """Show help message."""
    print("""
IPA Platform - Development Server Manager

Usage:
  python scripts/dev_server.py <command> [port]

Commands:
  start [port]   - Start the development server (default port: 8000)
  stop [port]    - Stop the server on the specified port
  restart [port] - Restart the server
  status [port]  - Show server status

Options:
  --fg           - Run in foreground (for start command)

Examples:
  python scripts/dev_server.py start          # Start on port 8000
  python scripts/dev_server.py start 8080     # Start on port 8080
  python scripts/dev_server.py stop 8080      # Stop server on 8080
  python scripts/dev_server.py restart        # Restart on port 8000
  python scripts/dev_server.py status         # Check status of port 8000
""")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    # Parse port
    port = DEFAULT_PORT
    foreground = False

    for arg in sys.argv[2:]:
        if arg == '--fg':
            foreground = True
        elif arg.isdigit():
            port = int(arg)

    # Execute command
    if command == 'start':
        result = cmd_start(port, foreground)
        sys.exit(0 if result else 1)
    elif command == 'stop':
        success = cmd_stop(port)
        sys.exit(0 if success else 1)
    elif command == 'restart':
        cmd_restart(port)
    elif command == 'status':
        cmd_status(port)
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
