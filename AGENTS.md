# AGENTS.md

## Language & Communication

- Bahasa Indonesia utama, English untuk istilah technical benchmark, provider, metric, dll

## Response Mode

- Compact, operational, execution-oriented
- Deep analysis HANYA untuk: architecture risk, benchmark regression critical, hidden dependency complex

## Scope & Boundaries

- JANGAN commit/push tanpa izin
- JANGAN buat folder/file tanpa cek dulu apakah sudah ada
- JANGAN expose secrets ke log

## Execution Workflow

- Ambil job dari `next-update.md` → kerjakan berurutan (pending first)
- Setiap implementasi (feature/fix/refactor) → branch di bawah `dev`: `feat/...` atau `fix/...`
- Workflow: implement → code-review → PASS/FAIL
- Kalo FAIL → fix → review lagi sampai PASS
- Kalo PASS → update `next-update.md` → buat history → docs-updater

## References

| Dokumen | Path |
|---|---|
| Release Workflow | `docs/release-process.md` |