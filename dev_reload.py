"""Auto-reload wrapper for development. Restarts Schmekla when .py files change."""
import subprocess, sys, os, time, glob

def get_mtimes():
    return {f: os.path.getmtime(f) for f in glob.glob("src/**/*.py", recursive=True)}

if __name__ == "__main__":
    while True:
        mtimes = get_mtimes()
        proc = subprocess.Popen([sys.executable, "-m", "src.main"])
        try:
            while proc.poll() is None:
                time.sleep(1)
                new = get_mtimes()
                if new != mtimes:
                    print("\n[dev_reload] Code changed - restarting Schmekla...")
                    proc.terminate()
                    proc.wait(timeout=5)
                    break
            else:
                break  # App closed normally by user
        except KeyboardInterrupt:
            proc.terminate()
            break
