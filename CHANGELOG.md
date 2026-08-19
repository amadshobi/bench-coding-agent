# Changelog

All notable changes to the **BCA (Bench Coding Agent)** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-19

### Added

- **Core Engine**: Initial release of BCA (Bench Coding Agent).
- **Shadow Clone Sandboxing**: Linux Bubblewrap (`bwrap`) Read-Only Host Mirror with isolated workspace scratchpad as default.
- **Docker Sandbox**: Containerized execution fallback for Docker environments.
- **Wildness & Blast Radius Telemetry**: Detection of out-of-bounds writes, destructive patterns, and safety scoring.
- **Agent Drivers**: Built-in adapters for `OpenCode`, `CommandCode`, `Antigravity CLI`, and configurable `GenericCLIAgent`.
- **Dataset & Empirical Verifiers**: Directory-based benchmark task loader with automated test execution (`verify.py`/`verify.sh`).
- **Storage Layer**: SQLite storage (`bca.sqlite3`) and structured JSON store for metrics, trajectories, and verdicts.
- **Reporting & Summarizer**: Deterministic leaderboard generation with dual currency (USD & IDR) and failure categorization.
- **Context Exporter**: Markdown export with heuristic syntax highlighting for AI analysis.
- **Multi-Interface Frontends**: Unified CLI (`bca run/task/agent/report`), Terminal Dashboard TUI (`bca tui`), and local Web Dashboard (`bca web`).
