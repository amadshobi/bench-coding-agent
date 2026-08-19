# AGENTS.md — BCA (Bench Coding Agent) Guidelines

## 🌟 Philosophy & Overview

**BCA (Bench Coding Agent)** adalah framework benchmarking & red-teaming otonom untuk menguji kemampuan Coding Agent CLI (`OpenCode`, `CommandCode`, `Antigravity CLI`, dll) di dalam lingkungan **Shadow Clone Sandbox**.

---

## 🛡️ Rules & Safety Boundaries

1. **Sandboxed Execution Only**: Seluruh eksekusi coding agent WAJIB berjalan di dalam Sandbox (`bca/sandbox/`), default menggunakan `ShadowCloneSandbox` (CoW Read-Only Mirror) untuk mencegah kerusakan pada host.
2. **Zero Secrets in Logs**: Dilarang mencetak API keys, token, atau environment variables sensitif ke stdout/stderr atau storage log.
3. **Deterministic Verifiers**: Setiap task evaluasi wajib memiliki script verifikasi mandiri (`verify.py` atau `verify.sh`) yang mengembalikan exit code `0` (PASS) atau non-zero (FAIL).
4. **Git Discipline**: Jangan commit/push ke repository tanpa persetujuan eksplisit. Gunakan format **Conventional Commits**.

---

## 🏗️ Architecture & Modules

```
bca/
├── core/            # Types, TaskSpec, Trajectory, TrialResult, WildnessMetrics
├── sandbox/         # Sandboxing layer: ShadowCloneSandbox (bwrap), DockerSandbox, LocalSandbox
├── agent/           # Coding Agent Adapters (OpenCode, CommandCode, Antigravity, Generic CLI)
├── dataset/         # Task Loader & Empirical Test Verifier
├── storage/         # SQLite DB (bca.sqlite3) & JSON store
├── package/         # Summarizer (USD/IDR, Leaderboard) & Context Exporter
├── interfaces/      # Multi-Frontends: CLI (bca run), TUI Monitor (bca tui), Web (bca web)
└── runner.py        # Trial Orchestrator Pipeline
```

---

## 📁 Dataset & Task Authoring Standard

Setiap task baru di `datasets/` wajib mengikuti struktur berikut:

```
datasets/<category>/<task-name-kebab-case>/
├── prompt.txt / instruction.md   # Deskripsi issue / tiket yang dibaca agent
├── task.json                     # Metadata (title, category, difficulty, timeout)
├── workspace/                    # Starter code repo
└── verify.py / verify.sh         # Script penentu verdict (Exit 0 = PASS)
```

---

## 🚀 Execution & Verification Commands

```bash
# Jalankan benchmark agent
python3 -m bca run --agent opencode --task <task_id>

# Run test suite BCA
python3 -m unittest discover -s tests -p "test_*.py"

# Inspect tasks & agents
python3 -m bca task list
python3 -m bca agent list
```

---

## 📜 Commit Conventions

- Format: `type(scope): description` (contoh: `feat(sandbox): add network isolation to shadow clone`).
- Tipe yang diperbolehkan: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`.
- Maksimal 72 karakter, lowercase, tanpa emoji di commit message.
