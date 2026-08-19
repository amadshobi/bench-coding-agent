"""Modern Command Line Interface for BCA (Bench Coding Agent)."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from bca.agent import get_agent, AGENT_REGISTRY
from bca.dataset import DatasetLoader
from bca.runner import TrialRunner
from bca.storage import SQLiteStorage
from bca.package import ResultExporter, BenchmarkSummarizer, ContextExporter
from bca.core.types import Verdict
from bca.interfaces.tui import render_tui_dashboard
from bca.interfaces.web import run_web_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bca",
        description="🏗️ BCA (Bench Coding Agent) — Autonomous Sandboxed Benchmark Framework",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # `bca run`
    run_p = subparsers.add_parser("run", help="Execute benchmark trials on coding agents")
    run_p.add_argument("-a", "--agent", required=True, help="Agent adapter (opencode, commandcode, antigravity)")
    run_p.add_argument("-m", "--model", help="Target model ID (e.g. anthropic/claude-3.7-sonnet)")
    run_p.add_argument("-t", "--task", help="Specific task ID to run")
    run_p.add_argument("-c", "--category", help="Filter tasks by category (bugfix, feature, refactor)")
    run_p.add_argument("--sandbox", choices=["local", "docker"], default="local", help="Sandbox isolation mode")
    run_p.add_argument("--preserve", action="store_true", help="Keep sandbox directory for inspection")
    run_p.add_argument("--datasets-dir", default="datasets", help="Path to benchmark tasks directory")

    # `bca task`
    task_p = subparsers.add_parser("task", help="Inspect and list available benchmark tasks")
    task_sub = task_p.add_subparsers(dest="task_command")
    list_t = task_sub.add_parser("list", help="List all benchmark tasks")
    list_t.add_argument("-c", "--category", help="Filter by category")
    list_t.add_argument("--datasets-dir", default="datasets", help="Path to benchmark tasks directory")

    # `bca agent`
    agent_p = subparsers.add_parser("agent", help="Inspect registered coding agents")
    agent_sub = agent_p.add_subparsers(dest="agent_command")
    agent_sub.add_parser("list", help="List all supported agent drivers")

    # `bca report`
    report_p = subparsers.add_parser("report", help="View benchmark history and stats")
    report_p.add_argument("--limit", type=int, default=20, help="Number of records to show")

    # `bca tui`
    tui_p = subparsers.add_parser("tui", help="Launch terminal dashboard monitor")
    tui_p.add_argument("--limit", type=int, default=15, help="Number of records to show")

    # `bca web`
    web_p = subparsers.add_parser("web", help="Start web dashboard results server")
    web_p.add_argument("-p", "--port", type=int, default=8080, help="Web server port")

    return parser


def handle_run(args: argparse.Namespace) -> int:
    root_dir = Path.cwd()
    datasets_dir = (root_dir / args.datasets_dir).resolve()
    loader = DatasetLoader(datasets_dir)

    all_tasks = loader.list_tasks(category_filter=args.category)
    if args.task:
        all_tasks = [t for t in all_tasks if t.task_id == args.task or t.name == args.task]

    if not all_tasks:
        print(f"❌ [BCA] No matching tasks found in '{datasets_dir}'")
        return 1

    print(f"🚀 [BCA] Preparing benchmark suite ({len(all_tasks)} task(s))")
    print(f"   Agent   : {args.agent}")
    print(f"   Model   : {args.model or 'default'}")
    print(f"   Sandbox : {args.sandbox}\n")

    agent = get_agent(agent_id=args.agent, model_id=args.model)
    runner = TrialRunner(sandbox_mode=args.sandbox, preserve_sandbox=args.preserve)

    db_path = root_dir / "results" / "bca.sqlite3"
    storage = SQLiteStorage(db_path)
    exporter = ResultExporter(root_dir / "results")
    summarizer = BenchmarkSummarizer(root_dir / "results")
    context_exporter = ContextExporter(root_dir / "results")

    results = []
    for idx, task in enumerate(all_tasks, start=1):
        print(f"[{idx}/{len(all_tasks)}] Running task: {task.name} ... ", end="", flush=True)
        trial_res = runner.run_trial(task, agent)
        results.append(trial_res)
        storage.save_trial(trial_res)

        icon = "✅" if trial_res.verdict == Verdict.PASS else "❌"
        diff_str = f"+{trial_res.metrics.diff.insertions}/-{trial_res.metrics.diff.deletions}"
        print(f"{icon} {trial_res.verdict.value} ({trial_res.metrics.duration_seconds}s, diff: {diff_str})")

    # Export full summary files, rankings, dual currency reports, and markdown context
    exporter.export_csv(results)
    summarizer.generate_summary_markdown(results, filename="results.md")
    context_exporter.export_tasks_context(all_tasks, filename="benchmark_context.md")

    stats = storage.get_summary_stats()
    print("\n" + "=" * 50)
    print(f"📊 Benchmark Finished! Total: {stats['total_runs']} | Passed: {stats['passed']} | Pass Rate: {stats['pass_rate_pct']}%")
    print(f"📁 Reports saved to {root_dir / 'results'}")
    return 0


def handle_task_list(args: argparse.Namespace) -> int:
    loader = DatasetLoader(Path(args.datasets_dir).resolve())
    tasks = loader.list_tasks(category_filter=args.category)
    print(f"\n📋 Available BCA Benchmark Tasks ({len(tasks)}):")
    print("-" * 60)
    for t in tasks:
        print(f"• [{t.category}] {t.task_id} — {t.title}")
    return 0


def handle_agent_list() -> int:
    print("\n🤖 Supported Coding Agents:")
    print("-" * 40)
    for name in AGENT_REGISTRY:
        print(f"• {name}")
    print("\nTip: Any other CLI tool can be passed as an agent name.")
    return 0


def handle_report(args: argparse.Namespace) -> int:
    db_path = Path.cwd() / "results" / "bca.sqlite3"
    if not db_path.exists():
        print("ℹ️ No benchmark trials found in database.")
        return 0

    storage = SQLiteStorage(db_path)
    trials = storage.list_trials(limit=args.limit)
    stats = storage.get_summary_stats()

    print(f"\n📊 BCA Summary: Total Runs: {stats['total_runs']} | Pass Rate: {stats['pass_rate_pct']}%")
    print("-" * 75)
    print(f"{'Trial ID':<10} | {'Category':<10} | {'Task':<15} | {'Agent':<10} | {'Verdict':<8} | {'Duration':<8}")
    print("-" * 75)
    for t in trials:
        tid = t["trial_id"][:8]
        print(f"{tid:<10} | {t['category']:<10} | {t['task_id']:<15} | {t['agent_id']:<10} | {t['verdict']:<8} | {t['duration_seconds']}s")
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "run":
        sys.exit(handle_run(args))
    elif args.command == "task":
        if args.task_command == "list" or not args.task_command:
            sys.exit(handle_task_list(args))
    elif args.command == "agent":
        sys.exit(handle_agent_list())
    elif args.command == "report":
        sys.exit(handle_report(args))
    elif args.command == "tui":
        render_tui_dashboard(limit=args.limit)
    elif args.command == "web":
        run_web_server(port=args.port)


if __name__ == "__main__":
    main()
