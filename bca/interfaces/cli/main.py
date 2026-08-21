"""Modern Ergonomic Command Line Interface for BCA (Bench Coding Agent)."""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

from bca.agent import get_agent, AGENT_REGISTRY
from bca.dataset import DatasetLoader
from bca.llm import ModelRegistry
from bca.llm.config import BCAConfig
from bca.runner import TrialRunner
from bca.storage import SQLiteStorage
from bca.package import ResultExporter, BenchmarkSummarizer, ContextExporter
from bca.package.report_cli import ReportCLI
from bca.core.types import Verdict
from bca.interfaces.tui import render_tui_dashboard
from bca.interfaces.web import run_web_server

BACKEND_ALIASES = {
    "oc": "opencode",
    "opencode": "opencode",
    "cmd": "commandcode",
    "commandcode": "commandcode",
    "cc": "commandcode",
    "omp": "omp",
    "pi": "omp",
    "oh-my-pi": "omp",
    "gw": "gateway",
    "gateway": "gateway",
    "omp-g": "gateway",
    "omp-gateway": "gateway",
    "direct": "gateway",
    "openai": "gateway",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bca",
        description="🏗️ BCA (Bench Coding Agent) — Modern Autonomous Sandboxed Benchmark Framework",
        usage="bca [command | backend] [options]\n\n"
              "Quick Examples:\n"
              "  bca -l                      # Quick status / summary\n"
              "  bca -l task                 # List numbered benchmark tasks\n"
              "  bca -l model                # List configured model aliases\n"
              "  bca oc -m gemini-3.7-flash -t 1\n"
              "  bca gw -m gemini-3.7-flash-tiered,claude-sonnet-4-6 -t 1,2\n"
              "  bca cmd -m kimi-k3 -t all\n"
    )

    # Top-level short options
    parser.add_argument("-l", "--list", nargs="?", const="summary", choices=["summary", "task", "tasks", "t", "model", "models", "m", "agent", "agents", "a"], help="List tasks, models, or agents")
    parser.add_argument("-m", "--model", help="Target model ID or comma-separated list of models (e.g. gemini-3.7-flash,claude-sonnet-4-6)")
    parser.add_argument("-t", "--task", help="Target task ID, index number, or comma-separated numbers (e.g. 1, 1,2, all)")
    parser.add_argument("-c", "--category", help="Filter tasks by category (bugfix, feature, refactor)")
    parser.add_argument("--sandbox", choices=["shadow", "local", "docker"], default="shadow", help="Sandbox isolation mode (default: shadow)")
    parser.add_argument("--preserve", action="store_true", help="Keep sandbox directory for inspection")
    parser.add_argument("--datasets-dir", default="datasets", help="Path to benchmark tasks directory")

    subparsers = parser.add_subparsers(dest="command", help="Subcommands / Backends")

    # `bca run`
    run_p = subparsers.add_parser("run", help="Execute benchmark trials")
    run_p.add_argument("-a", "--agent", required=True, help="Agent adapter (oc, cmd, omp, gw)")
    run_p.add_argument("-m", "--model", help="Target model ID or comma-separated list")
    run_p.add_argument("-t", "--task", help="Task ID or number")
    run_p.add_argument("-c", "--category", help="Filter tasks by category")
    run_p.add_argument("--sandbox", choices=["shadow", "local", "docker"], default="shadow", help="Sandbox isolation mode")
    run_p.add_argument("--preserve", action="store_true", help="Keep sandbox directory")
    run_p.add_argument("--datasets-dir", default="datasets", help="Path to benchmark tasks directory")

    # Shorthand backends directly as subcommands: `bca oc`, `bca cmd`, `bca omp`, `bca gw`
    for b_alias in ("oc", "opencode", "cmd", "commandcode", "omp", "pi", "gw", "gateway", "omp-g"):
        bp = subparsers.add_parser(b_alias, help=f"Run benchmark with {b_alias} backend")
        bp.add_argument("-m", "--model", help="Target model ID or comma-separated list (e.g. gemini-3.7-flash)")
        bp.add_argument("-t", "--task", help="Target task index or ID (e.g. 1, 1,2, all)")
        bp.add_argument("-c", "--category", help="Filter tasks by category")
        bp.add_argument("--sandbox", choices=["shadow", "local", "docker"], default="shadow", help="Sandbox isolation mode")
        bp.add_argument("--preserve", action="store_true", help="Keep sandbox directory")
        bp.add_argument("--datasets-dir", default="datasets", help="Path to benchmark tasks directory")

    # `bca model`
    model_p = subparsers.add_parser("model", help="Inspect and list synchronized available models")
    model_sub = model_p.add_subparsers(dest="model_command")
    list_m = model_sub.add_parser("list", help="List active models across backends")
    list_m.add_argument("-b", "--backend", choices=["opencode", "commandcode", "omp", "gateway", "all"], default="all", help="Filter by backend")

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

    # `bca report` / `bca -r`
    report_p = subparsers.add_parser("report", help="View benchmark leaderboard, markdown, or json reports")
    report_p.add_argument("-b", "--board", action="store_true", help="Display 4-dimension rankings leaderboard")
    report_p.add_argument("-md", "--markdown", action="store_true", help="Render formatted markdown report")
    report_p.add_argument("--json", action="store_true", help="Output machine-readable JSON data")
    report_p.add_argument("--limit", type=int, default=20, help="Number of records to show")

    # Top-level short -r flag support
    parser.add_argument("-r", "--report", action="store_true", help="Quick report trigger")
    parser.add_argument("-b", "--board", action="store_true", help="Show leaderboard")
    parser.add_argument("-md", "--markdown", action="store_true", help="Show markdown")
    parser.add_argument("--json", action="store_true", help="Show JSON")

    # `bca tui`
    tui_p = subparsers.add_parser("tui", help="Launch terminal dashboard monitor")
    tui_p.add_argument("--limit", type=int, default=15, help="Number of records to show")

    # `bca web`
    web_p = subparsers.add_parser("web", help="Start web dashboard results server")
    web_p.add_argument("-p", "--port", type=int, default=8080, help="Web server port")

    return parser


def parse_selected_tasks(task_input: Optional[str], all_tasks: List[Any]) -> List[Any]:
    """Resolves task parameter by index (1-based), comma-separated indices, ID, or 'all'."""
    if not task_input or task_input.lower() == "all":
        return all_tasks

    selected = []
    tokens = [t.strip() for t in task_input.split(",") if t.strip()]

    for tok in tokens:
        if tok.isdigit():
            idx = int(tok)
            if 1 <= idx <= len(all_tasks):
                selected.append(all_tasks[idx - 1])
        else:
            for t in all_tasks:
                if tok.lower() in (t.task_id.lower(), t.name.lower()):
                    if t not in selected:
                        selected.append(t)

    return selected if selected else all_tasks


def handle_execute_trials(
    agent_name: str,
    models_arg: Optional[str],
    task_arg: Optional[str],
    category_arg: Optional[str],
    sandbox_mode: str,
    preserve_sandbox: bool,
    datasets_dir_str: str,
) -> int:
    root_dir = Path.cwd()
    datasets_dir = (root_dir / datasets_dir_str).resolve()
    loader = DatasetLoader(datasets_dir)

    all_tasks = loader.list_tasks(category_filter=category_arg)
    target_tasks = parse_selected_tasks(task_arg, all_tasks)

    if not target_tasks:
        print(f"❌ [BCA] No matching tasks found in '{datasets_dir}'")
        return 1

    canonical_backend = BACKEND_ALIASES.get(agent_name.lower().strip(), agent_name)

    # Parse multi-models
    model_tokens = [m.strip() for m in models_arg.split(",")] if models_arg else [None]

    # Resolve each model alias via BCAConfig
    resolved_models = []
    for m in model_tokens:
        if m:
            resolved = BCAConfig.resolve_model(canonical_backend, m)
            resolved_models.append((m, resolved))
        else:
            resolved_models.append(("default", None))

    total_runs = len(resolved_models) * len(target_tasks)
    model_str_list = [f"{alias} -> {res or 'default'}" for alias, res in resolved_models]
    print(f"\n🚀 [BCA] Executing Benchmark Matrix ({total_runs} trial(s))")
    print(f"   Backend : {canonical_backend.upper()} (input: '{agent_name}')")
    print(f"   Sandbox : {sandbox_mode}")
    print(f"   Models  : {', '.join(model_str_list)}")
    print(f"   Tasks   : {len(target_tasks)} task(s)\n")

    runner = TrialRunner(sandbox_mode=sandbox_mode, preserve_sandbox=preserve_sandbox)
    db_path = root_dir / "results" / "bca.sqlite3"
    storage = SQLiteStorage(db_path)
    exporter = ResultExporter(root_dir / "results")
    summarizer = BenchmarkSummarizer(root_dir / "results")
    context_exporter = ContextExporter(root_dir / "results")

    results = []
    run_idx = 1

    for alias, resolved_model in resolved_models:
        agent = get_agent(agent_id=canonical_backend, model_id=resolved_model)
        for task in target_tasks:
            model_tag = alias if alias != "default" else "default"
            print(f"[{run_idx}/{total_runs}] [{canonical_backend}] [{model_tag}] task: {task.name} ... ", end="", flush=True)
            trial_res = runner.run_trial(task, agent)
            results.append(trial_res)
            storage.save_trial(trial_res)

            icon = "✅" if trial_res.verdict == Verdict.PASS else "❌"
            diff_str = f"+{trial_res.metrics.diff.insertions}/-{trial_res.metrics.diff.deletions}"
            print(f"{icon} {trial_res.verdict.value} ({trial_res.metrics.duration_seconds}s, diff: {diff_str})")
            run_idx += 1

    # Export full summary files, rankings, dual currency reports, and markdown context
    exporter.export_csv(results)
    summarizer.generate_summary_markdown(results, filename="results.md")
    context_exporter.export_tasks_context(target_tasks, filename="benchmark_context.md")

    stats = storage.get_summary_stats()
    print("\n" + "=" * 50)
    print(f"📊 Benchmark Finished! Total: {stats['total_runs']} | Passed: {stats['passed']} | Pass Rate: {stats['pass_rate_pct']}%")
    print(f"📁 Reports saved to {root_dir / 'results'}")
    return 0


def handle_list(list_type: str, datasets_dir_str: str = "datasets") -> int:
    """Universal lister for -l [task|model|agent|summary]."""
    lt = list_type.lower().strip()

    if lt in ("task", "tasks", "t"):
        loader = DatasetLoader(Path(datasets_dir_str).resolve())
        tasks = loader.list_tasks()
        print(f"\n📋 Available BCA Benchmark Tasks ({len(tasks)}):")
        print("=" * 65)
        print(f"{'#':<4} │ {'Category':<10} │ {'Task ID':<30} │ {'Title'}")
        print("-" * 65)
        for idx, t in enumerate(tasks, start=1):
            print(f"[{idx}]  │ {t.category:<10} │ {t.task_id:<30} │ {t.title}")
        print("\nTip: Run with `bca <backend> -t 1` or `bca <backend> -t 1,2`.")
        return 0

    if lt in ("model", "models", "m"):
        cfg_models = BCAConfig.load_backends()
        if not cfg_models:
            cfg_models = ModelRegistry.list_available_models()

        print("\n🔮 Configured Model Catalog & Aliases (config/config.yml):")
        print("=" * 75)
        for b_name, m_map in cfg_models.items():
            print(f"\n📦 [{b_name.upper()}] ({len(m_map)} model aliases):")
            print("-" * 75)
            print(f"  {'Alias (Shorthand)':<28} │ {'Target Model ID'}")
            print("-" * 75)
            if isinstance(m_map, dict):
                for alias, target in m_map.items():
                    print(f"  {alias:<28} │ {target}")
            elif isinstance(m_map, list):
                for item in m_map:
                    print(f"  {item.get('id', ''):<28} │ {item.get('name', '')}")
        print("\nTip: Run with `bca <backend> -m <alias>` (e.g. `bca oc -m gemini-3.7-flash -t 1`).")
        return 0

    if lt in ("agent", "agents", "a"):
        print("\n🤖 Supported BCA Backends & Aliases:")
        print("=" * 55)
        print(f"  {'Alias / Command':<18} │ {'Engine Type'}")
        print("-" * 55)
        print(f"  {'oc, opencode':<18} │ Full CLI Coding Agent")
        print(f"  {'cmd, commandcode':<18} │ Full CLI Coding Agent")
        print(f"  {'omp, pi':<18} │ Full CLI Coding Agent")
        print(f"  {'gw, gateway':<18} │ Direct API (OpenAI-compatible)")
        return 0

    # Default: summary
    print("\n🏗️ BCA (Bench Coding Agent) — Quick Overview")
    print("=" * 55)
    loader = DatasetLoader(Path(datasets_dir_str).resolve())
    tasks = loader.list_tasks()
    cfg_models = BCAConfig.load_backends()

    print(f"• Backends Available : oc, cmd, omp, gw (4 pillars)")
    print(f"• Configured Tasks   : {len(tasks)} tasks ready")
    print(f"• Configured Aliases : {sum(len(v) for v in cfg_models.values()) if cfg_models else 'dynamic'} aliases in config/config.yml")
    print("\nQuick Commands:")
    print("  bca -l task              # List all tasks with index numbers")
    print("  bca -l model             # List model aliases")
    print("  bca oc -m gemini-3.7-flash -t 1")
    print("  bca gw -m gemini-3.7-flash-tiered,claude-sonnet-4-6 -t 1")
    return 0


def handle_report_dispatch(board: bool, markdown: bool, json_mode: bool, limit: int) -> int:
    db_path = Path.cwd() / "results" / "bca.sqlite3"
    results_dir = Path.cwd() / "results"

    if json_mode:
        ReportCLI.render_json(db_path, limit=limit)
        return 0

    if markdown:
        ReportCLI.render_markdown(results_dir)
        return 0

    # Default to beautiful Leaderboard
    ReportCLI.render_leaderboard(db_path, limit=limit)
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.list:
        sys.exit(handle_list(args.list, getattr(args, "datasets_dir", "datasets")))

    if args.report or args.board or args.markdown or args.json:
        sys.exit(handle_report_dispatch(
            board=args.board,
            markdown=args.markdown,
            json_mode=args.json,
            limit=20,
        ))

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Check if command is a backend shorthand (e.g. `bca oc ...`, `bca gw ...`)
    if args.command.lower() in BACKEND_ALIASES:
        sys.exit(handle_execute_trials(
            agent_name=args.command,
            models_arg=args.model,
            task_arg=args.task,
            category_arg=args.category,
            sandbox_mode=args.sandbox,
            preserve_sandbox=args.preserve,
            datasets_dir_str=args.datasets_dir,
        ))

    if args.command == "run":
        sys.exit(handle_execute_trials(
            agent_name=args.agent,
            models_arg=args.model,
            task_arg=args.task,
            category_arg=args.category,
            sandbox_mode=args.sandbox,
            preserve_sandbox=args.preserve,
            datasets_dir_str=args.datasets_dir,
        ))
    elif args.command == "model":
        if args.model_command == "list" or not args.model_command:
            sys.exit(handle_list("model"))
    elif args.command == "task":
        if args.task_command == "list" or not args.task_command:
            sys.exit(handle_list("task", getattr(args, "datasets_dir", "datasets")))
    elif args.command == "agent":
        sys.exit(handle_list("agent"))
    elif args.command == "report":
        sys.exit(handle_report_dispatch(
            board=getattr(args, "board", True),
            markdown=getattr(args, "markdown", False),
            json_mode=getattr(args, "json", False),
            limit=getattr(args, "limit", 20),
        ))
    elif args.command == "tui":
        render_tui_dashboard(limit=args.limit)
    elif args.command == "web":
        run_web_server(port=args.port)


if __name__ == "__main__":
    main()
