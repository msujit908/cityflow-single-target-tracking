"""
Launch Demonstration Script.

Starts the interactive web dashboard on http://localhost:8088/,
opens the dashboard in the user's default browser, and launches
the multi-camera tracking video in the default media player.
"""

import os
import sys
import time
import threading
import webbrowser
from pathlib import Path

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.dashboard import run_dashboard_server, find_available_port


def launch():
    print(f"\n{'='*75}", flush=True)
    print(" Launching CityFlow Single-Target Multi-Camera Tracking Demonstration", flush=True)
    print(f"{'='*75}", flush=True)

    port = find_available_port(8090)
    url = f"http://localhost:{port}/"

    # 1. Start Web Dashboard server in background thread FIRST
    server_thread = threading.Thread(target=run_dashboard_server, args=(port,), daemon=True)
    server_thread.start()
    time.sleep(1.0)
    print(f"[+] Web Dashboard active at: {url}", flush=True)

    # 2. Launch browser and video in non-blocking background threads
    def try_open_browser():
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[!] Browser launcher note: {e}", flush=True)

    def try_open_video():
        video_path = os.path.join(ROOT_DIR, "outputs", "videos", "dashboard_proposed_adaptive.mp4")
        if os.path.exists(video_path):
            try:
                os.startfile(video_path)
            except Exception as e:
                print(f"[!] Video launcher note: {e}", flush=True)

    threading.Thread(target=try_open_browser, daemon=True).start()
    threading.Thread(target=try_open_video, daemon=True).start()

    print("\n[+] Demonstration is running live!", flush=True)
    print(f"    Web Dashboard: {url}", flush=True)
    print("    Press Ctrl+C to terminate.", flush=True)

    # Keep main thread alive
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[*] Demonstration terminated.", flush=True)


if __name__ == "__main__":
    launch()
