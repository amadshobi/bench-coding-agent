# 🏗️ BCA — Bench Coding Agent

> **Autonomous Sandboxed Benchmark & Red-Teaming Framework for AI Coding Agents**

![Python](https://img.shields.io/badge/Python-3.14.4-3776AB?style=flat&logo=python&logoColor=white)
![Sandboxing](https://img.shields.io/badge/Sandbox-Bubblewrap%20CoW%20%7C%20Docker-blue?style=flat)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat)

---

## 📖 Overview

**BCA (Bench Coding Agent)** adalah framework benchmarking generasi baru untuk menguji kemampuan otonom coding agent (`OpenCode`, `CommandCode`, `Antigravity CLI`, `Claude Code`, dll) di dalam lingkungan **Shadow Clone Sandbox**.

BCA tidak sekadar menguji prompt teks LLM, melainkan mengukur:

1. **Empirical Correctness** — Apakah agent mampu menyelesaikan issue dan meloloskan automated test suite (`verify.py` / `verify.sh`).
2. **Blast Radius & Wildness** — Menguji keliaran model: mendeteksi perintah destruktif (`rm -rf`, `chmod 777`, `kill`) dan percobaan akses di luar workspace.
3. **Efficiency & Cost** — Mengukur durasi turn, diff footprint (`+insertions / -deletions`), dan token consumption.

---

## 🛡️ Sandboxing Engine (Shadow Clone Default)

Secara default, BCA menggunakan **Shadow Clone Sandbox** berbasis Linux **Bubblewrap (`bwrap`)**:

- **Read-Only Host Mirror**: Seluruh filesystem host, binary, dan toolchains dicerminkan dalam mode _Strictly Read-Only_.
- **Ephemeral Writable Workspace**: Agent hanya diperbolehkan menulis file di dalam `/tmp/bca/trials/<trial_id>/workspace`.
- **Zero Host Risk**: Setiap aksi agresif atau halusinasi liar model AI diisolasi dan dicatat tanpa risiko merusak host.
- **Docker Ready**: Mendukung mode `--sandbox docker` untuk containerization penuh di CI/CD.

---

## 🧱 Architecture

```
bca/
├── bca/
│   ├── core/                    # TaskSpec, Trajectory, TrialResult, WildnessMetrics
│   ├── sandbox/                 # Shadow Clone (CoW Read-Only Mirror) & Docker
│   ├── agent/                   # Coding Agent Drivers (OpenCode, CommandCode, Antigravity, Generic CLI)
│   ├── dataset/                 # Benchmark Task Loader & Automated Test Verifiers
│   ├── storage/                 # SQLite Database (bca.sqlite3) & JSON store
│   ├── package/                 # Dual-currency Summarizer (USD & IDR) & Context Exporter
│   ├── interfaces/              # Multi-Interface: CLI, TUI Monitor, Web Dashboard
│   └── runner.py                # Trial Orchestrator Pipeline
│
├── datasets/                    # Benchmark Task Suites (bugfix, feature, refactor)
└── tests/                       # Unit & Integration Test Suites
```

---

## 🚀 Quick Start

### 1. Jalankan Benchmark

```bash
# Menjalankan task spesifik dengan OpenCode agent
python3 -m bca run --agent opencode --task fix-calculator-divide-zero

# Menjalankan seluruh kategori bugfix
python3 -m bca run --agent opencode --category bugfix

# Menjalankan dengan model tertentu
python3 -m bca run --agent opencode --model anthropic/claude-3.7-sonnet
```

### 2. Inspeksi Tasks & Registered Agents

```bash
# List semua task benchmark yang tersedia
python3 -m bca task list

# List semua adapter agent yang didukung
python3 -m bca agent list
```

### 3. Reporting & Dashboards

```bash
# Riwayat benchmark di terminal
python3 -m bca report --limit 20

# Buka Live Terminal UI (TUI) Dashboard
python3 -m bca tui

# Buka Web Dashboard Visualizer
python3 -m bca web --port 8080
```

---

## 🧪 Testing

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

---

## 📄 License

MIT License
