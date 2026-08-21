"""Comprehensive unit and integration tests for BCA (Bench Coding Agent)."""

import shutil
import tempfile
import unittest
from pathlib import Path

from bca.core.types import Verdict, AgentStatus
from bca.core.task import TaskSpec
from bca.sandbox.local import LocalSandbox
from bca.agent.base import BaseAgent
from bca.agent.generic_cli import GenericCLIAgent
from bca.agent.factory import get_agent
from bca.dataset.loader import DatasetLoader
from bca.dataset.verifier import TaskVerifier
from bca.storage.sqlite import SQLiteStorage
from bca.storage.json_store import JSONStorage
from bca.package.exporter import ResultExporter
from bca.package.summarizer import BenchmarkSummarizer
from bca.package.context_exporter import ContextExporter
from bca.runner import TrialRunner


class MockSolvingAgent(BaseAgent):
    """Mock agent simulating a coding agent fixing files in the sandbox."""

    def build_command(self, instruction: str) -> str:
        # Overwrite calculator.py with the correct implementation safely
        return (
            "python3 -c \"import pathlib; "
            "pathlib.Path('calculator.py').write_text("
            "'class Calculator:\\n    def divide(self, a, b):\\n        if b == 0:\\n            raise ValueError(\\\"Cannot divide by zero\\\")\\n        return a / b\\n')\""
        )


class TestBCACore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="bca_test_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sandbox_lifecycle_and_git_diff(self):
        sandbox = LocalSandbox(base_dir=self.temp_dir / "sandbox_test")
        sandbox.setup()
        self.assertTrue(sandbox.workspace_path.exists())

        # Write file and verify diff tracking
        sandbox.write_file("test.py", "x = 10\n")
        self.assertEqual(sandbox.read_file("test.py"), "x = 10\n")

        diff = sandbox.get_diff()
        self.assertGreater(diff.files_changed, 0)
        self.assertGreater(diff.insertions, 0)

        sandbox.cleanup()
        self.assertFalse(sandbox.workspace_path.exists())

    def test_dataset_loader(self):
        datasets_dir = Path(__file__).parent.parent / "datasets"
        loader = DatasetLoader(datasets_dir)
        tasks = loader.list_tasks()
        self.assertGreaterEqual(len(tasks), 2)

        calc_task = loader.load_task("bugfix", "fix-calculator-divide-zero")
        self.assertIsNotNone(calc_task)
        self.assertEqual(calc_task.category, "bugfix")
        self.assertTrue(calc_task.verifier_script.exists())

    def test_end_to_end_trial_runner_pass(self):
        datasets_dir = Path(__file__).parent.parent / "datasets"
        loader = DatasetLoader(datasets_dir)
        task = loader.load_task("bugfix", "fix-calculator-divide-zero")
        self.assertIsNotNone(task)

        agent = MockSolvingAgent(agent_id="mock-solver")
        runner = TrialRunner(sandbox_mode="local")

        result = runner.run_trial(task, agent)
        self.assertEqual(result.verdict, Verdict.PASS)
        self.assertEqual(result.agent_result.status, AgentStatus.COMPLETED)
        self.assertEqual(result.verifier_result.exit_code, 0)
        self.assertGreater(result.metrics.diff.insertions, 0)

    def test_storage_and_exporter(self):
        datasets_dir = Path(__file__).parent.parent / "datasets"
        loader = DatasetLoader(datasets_dir)
        task = loader.load_task("bugfix", "fix-calculator-divide-zero")

        agent = MockSolvingAgent(agent_id="mock-solver")
        runner = TrialRunner(sandbox_mode="local")
        result = runner.run_trial(task, agent)

        # Test SQLite storage
        db_path = self.temp_dir / "test_bca.sqlite3"
        storage = SQLiteStorage(db_path)
        storage.save_trial(result)

        trials = storage.list_trials()
        self.assertEqual(len(trials), 1)
        self.assertEqual(trials[0]["verdict"], "PASS")

        stats = storage.get_summary_stats()
        self.assertEqual(stats["total_runs"], 1)
        self.assertEqual(stats["passed"], 1)
        self.assertEqual(stats["pass_rate_pct"], 100.0)

        # Test Exporter & Summarizer
        out_dir = self.temp_dir / "out"
        exporter = ResultExporter(out_dir)
        summarizer = BenchmarkSummarizer(out_dir)
        ctx_exp = ContextExporter(out_dir)

        csv_file = exporter.export_csv([result])
        md_file = summarizer.generate_summary_markdown([result])
        ctx_file = ctx_exp.export_tasks_context([task])

        self.assertTrue(csv_file.exists())
        self.assertTrue(md_file.exists())
        self.assertTrue(ctx_file.exists())
        self.assertIn("Leaderboard", md_file.read_text())
        self.assertIn("Task Context", ctx_file.read_text())

    def test_agent_factory_matrix(self):
        opencode = get_agent("opencode")
        self.assertEqual(opencode.agent_id, "opencode")

        cmd = get_agent("cmd")
        self.assertEqual(cmd.agent_id, "commandcode")

        omp = get_agent("omp")
        self.assertEqual(omp.agent_id, "omp")

        gateway = get_agent("gateway")
        self.assertEqual(gateway.agent_id, "gateway")

        openai = get_agent("openai")
        self.assertEqual(openai.agent_id, "gateway")


if __name__ == "__main__":
    unittest.main()
