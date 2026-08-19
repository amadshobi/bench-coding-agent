# Contributing to BCA (Bench Coding Agent)

Terima kasih sudah tertarik berkontribusi ke **BCA**! 🎉  
BCA adalah autonomous sandboxed benchmark framework untuk mengevaluasi coding agents secara empiris.

---

## 📋 Alur Kontribusi

1. **Fork** repository ke akun GitHub kamu:

   ```bash
   git clone https://github.com/amadshobi/bench-coding-agent.git
   cd bench-coding-agent
   ```

2. **Branching**:
   Buat branch baru dari `main` dengan format `feat/<nama-fitur>` atau `fix/<nama-bug>`:

   ```bash
   git checkout -b feat/add-aider-agent
   ```

3. **Verifikasi**:
   Pastikan seluruh test suite lolos sebelum commit:

   ```bash
   python3 -m unittest discover -s tests -p "test_*.py"
   ```

4. **Commit & PR**:
   Gunakan format **Conventional Commits**:
   ```bash
   git commit -m "feat(agent): add aider cli agent adapter"
   ```
   Push branch dan buka Pull Request ke branch `main`.

---

## 🛠️ Menambahkan Task Benchmark Baru

Setiap task benchmark baru diletakkan di dalam folder `datasets/<category>/<task-name>/`:

```
datasets/bugfix/my-new-task/
├── prompt.txt         # Instruksi/tiket issue yang dibaca agent
├── task.json          # Metadata (title, category, timeout_seconds)
├── workspace/         # Starter repo dengan bug/skeleton
└── verify.py          # Script penentu verdict (Exit code 0 = PASS, non-zero = FAIL)
```

---

## 🤖 Menambahkan Adapter Coding Agent Baru

Untuk menambahkan dukungan agent baru:

1. Buat adapter di `bca/agent/<agent_name>.py` mewarisi `BaseAgent`.
2. Implementasikan method `build_command(self, instruction: str) -> str`.
3. Daftarkan di `bca/agent/factory.py`.

---

## 📐 Coding Standards & Guidelines

- **Zero Junk**: Tidak meninggalkan `TODO`, `FIXME`, atau dead code di commit.
- **Sandboxed by Default**: Pastikan semua eksekusi runtime berjalan melalui `bca.sandbox`.
- **Clean Commits**: Format commit `type(scope): description` (lowercase, tanpa trailing period, max 72 karakter, no emojis in commit message).
