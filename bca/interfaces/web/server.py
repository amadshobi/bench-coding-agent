"""Lightweight built-in Web dashboard and results visualizer for BCA."""

import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional

from bca.storage.sqlite import SQLiteStorage

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BCA — Bench Coding Agent Dashboard</title>
    <style>
        :root {
            --bg: #0d1117;
            --card-bg: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --heading: #f0f6fc;
            --pass: #238636;
            --fail: #da3633;
            --accent: #58a6ff;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 24px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }
        h1 { color: var(--heading); margin: 0; font-size: 24px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .stat-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
        .stat-val { font-size: 28px; font-weight: bold; color: var(--heading); margin-top: 8px; }
        table { width: 100%; border-collapse: collapse; background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); font-size: 14px; }
        th { background: #21262d; color: var(--heading); font-weight: 600; }
        .badge { padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }
        .badge-pass { background: rgba(35, 134, 54, 0.2); color: #3fb950; border: 1px solid rgba(63, 185, 80, 0.4); }
        .badge-fail { background: rgba(218, 54, 51, 0.2); color: #f85149; border: 1px solid rgba(248, 81, 73, 0.4); }
        code { background: #21262d; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏗️ BCA (Bench Coding Agent) Dashboard</h1>
            <div>Status: <strong>Active</strong></div>
        </header>
        <div class="stats-grid">
            <div class="stat-card"><div>Total Trials</div><div class="stat-val">__TOTAL__</div></div>
            <div class="stat-card"><div>Passed</div><div class="stat-val" style="color: #3fb950">__PASSED__</div></div>
            <div class="stat-card"><div>Pass Rate</div><div class="stat-val" style="color: var(--accent)">__PASS_RATE__%</div></div>
            <div class="stat-card"><div>Avg Duration</div><div class="stat-val">__AVG_DUR__s</div></div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Trial ID</th>
                    <th>Category</th>
                    <th>Task ID</th>
                    <th>Agent</th>
                    <th>Verdict</th>
                    <th>Duration</th>
                    <th>Diff</th>
                    <th>Created At</th>
                </tr>
            </thead>
            <tbody>
                __ROWS__
            </tbody>
        </table>
    </div>
</body>
</html>
"""


class BCADashboardHandler(SimpleHTTPRequestHandler):
    db_path: Path = Path.cwd() / "results" / "bca.sqlite3"

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            storage = SQLiteStorage(self.db_path)
            stats = storage.get_summary_stats()
            trials = storage.list_trials(limit=50)

            rows_html = ""
            for t in trials:
                verdict_badge = (
                    '<span class="badge badge-pass">PASS</span>'
                    if t["verdict"] == "PASS"
                    else '<span class="badge badge-fail">FAIL</span>'
                )
                diff = f"+{t['insertions']}/-{t['deletions']}"
                rows_html += f"""
                <tr>
                    <td><code>{t['trial_id'][:8]}</code></td>
                    <td><code>{t['category']}</code></td>
                    <td><strong>{t['task_id']}</strong></td>
                    <td><code>{t['agent_id']}</code></td>
                    <td>{verdict_badge}</td>
                    <td>{t['duration_seconds']}s</td>
                    <td><code>{diff}</code></td>
                    <td>{t['created_at'][:19]}</td>
                </tr>
                """

            html = HTML_TEMPLATE
            html = html.replace("__TOTAL__", str(stats["total_runs"]))
            html = html.replace("__PASSED__", str(stats["passed"]))
            html = html.replace("__PASS_RATE__", str(stats["pass_rate_pct"]))
            html = html.replace("__AVG_DUR__", str(stats["avg_duration_seconds"]))
            html = html.replace("__ROWS__", rows_html or "<tr><td colspan='8'>No trials found</td></tr>")

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_error(404, "Not found")


def run_web_server(port: int = 8080, db_path: Optional[Path] = None) -> None:
    """Starts the built-in HTTP dashboard server."""
    BCADashboardHandler.db_path = db_path or Path.cwd() / "results" / "bca.sqlite3"
    server = HTTPServer(("0.0.0.0", port), BCADashboardHandler)
    print(f"🌐 [BCA Web] Dashboard running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 [BCA Web] Server stopped.")
        server.server_close()
