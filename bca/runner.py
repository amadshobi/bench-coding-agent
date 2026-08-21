"""Trial runner and orchestrator pipeline connecting Task, Agent, Sandbox, Verifier, Pricing, and Judge."""

import time
import uuid
from pathlib import Path
from typing import List, Optional

from bca.core.types import (
    Verdict,
    AgentStatus,
    ExecutionMetrics,
    DiffStats,
    TokenUsage,
    WildnessMetrics,
    QualityScore,
)
from bca.core.task import TaskSpec
from bca.core.trial import TrialResult, AgentResult, VerifierResult
from bca.agent.base import BaseAgent
from bca.sandbox import create_sandbox, BaseSandbox, ShadowCloneSandbox
from bca.dataset.verifier import TaskVerifier
from bca.llm.pricing import PricingEngine
from bca.package.judge import AnalyticsJudgeAgent


class TrialRunner:
    """
    Orchestrates the lifecycle of a benchmark trial:
    Setup Sandbox -> Run Agent -> Extract Diff -> Run Verifier -> Teardown -> Judge -> Pricing -> Record Metrics.
    """

    def __init__(
        self,
        sandbox_mode: str = "shadow",
        preserve_sandbox: bool = False,
        enable_judge: bool = True,
    ):
        self.sandbox_mode = sandbox_mode
        self.preserve_sandbox = preserve_sandbox
        self.enable_judge = enable_judge
        self.verifier = TaskVerifier()
        self.judge = AnalyticsJudgeAgent() if enable_judge else None

    def run_trial(
        self,
        task: TaskSpec,
        agent: BaseAgent,
        trial_id: Optional[str] = None,
    ) -> TrialResult:
        """Executes a single end-to-end trial."""
        trial_id = trial_id or str(uuid.uuid4())
        total_start = time.perf_counter()

        # 1. Spin up isolated sandbox (Default: Shadow Clone)
        sandbox: BaseSandbox = create_sandbox(
            mode=self.sandbox_mode,
            trial_id=trial_id,
            preserve_on_exit=self.preserve_sandbox,
        )

        setup_start = time.perf_counter()
        sandbox.setup(starter_dir=task.workspace_dir)
        setup_duration = time.perf_counter() - setup_start

        # 2. Setup Agent in Sandbox
        agent.setup(sandbox)

        # 3. Run Agent with instruction
        timeout = task.requirements.timeout_seconds
        agent_res: AgentResult = agent.run(
            instruction=task.instruction,
            sandbox=sandbox,
            timeout_seconds=timeout,
        )

        # 4. Extract Git Diff & Wildness Metrics
        diff_stats: DiffStats = sandbox.get_diff()
        wildness_metrics = (
            sandbox.get_wildness_metrics()
            if isinstance(sandbox, ShadowCloneSandbox)
            else WildnessMetrics()
        )

        # 5. Run Verifier to determine empirical correctness
        verifier_res: VerifierResult = self.verifier.verify(
            verifier_script=task.verifier_script,
            sandbox=sandbox,
        )

        # 6. Teardown Sandbox
        sandbox.cleanup()

        total_duration = round(time.perf_counter() - total_start, 3)

        # 7. Evaluate with Analytics Judge Agent
        quality_score = QualityScore()
        if self.judge:
            eval_res = self.judge.evaluate(
                task=task,
                agent_result=agent_res,
                verdict=verifier_res.verdict,
                patch_diff=diff_stats.patch,
            )
            quality_score = QualityScore(
                overall_quality=eval_res.quality_score,
                correctness=eval_res.correctness_score,
                cleanliness=eval_res.cleanliness_score,
                rule_compliance=eval_res.rule_compliance_score,
                efficiency=eval_res.efficiency_score,
                critique=eval_res.critique,
            )

        # 8. Calculate Real-time Dual-Currency Pricing
        # Estimate or extract actual tokens from trajectory
        in_toks = 8000
        out_toks = 400
        if agent_res.trajectory and agent_res.trajectory.steps:
            in_toks = len(agent_res.trajectory.steps) * 3500
            out_toks = len(agent_res.trajectory.steps) * 250

        cost_usd, cost_idr = PricingEngine.calculate_cost(agent.model_id, in_toks, out_toks)
        token_usage = TokenUsage(
            input_tokens=in_toks,
            output_tokens=out_toks,
            total_tokens=in_toks + out_toks,
            estimated_cost_usd=cost_usd,
            estimated_cost_idr=cost_idr,
        )

        # 9. Assemble final metrics & verdict
        metrics = ExecutionMetrics(
            duration_seconds=total_duration,
            setup_duration_seconds=round(setup_duration, 3),
            agent_duration_seconds=agent_res.duration_seconds,
            verifier_duration_seconds=verifier_res.duration_seconds,
            turn_count=len(agent_res.trajectory.steps) if agent_res.trajectory else 1,
            tokens=token_usage,
            diff=diff_stats,
            wildness=wildness_metrics,
            quality=quality_score,
        )

        final_verdict = verifier_res.verdict

        return TrialResult(
            trial_id=trial_id,
            task_id=task.task_id,
            category=task.category,
            agent_id=agent.agent_id,
            model_id=agent.model_id,
            verdict=final_verdict,
            agent_result=agent_res,
            verifier_result=verifier_res,
            metrics=metrics,
        )

    def run_suite(
        self,
        tasks: List[TaskSpec],
        agent: BaseAgent,
    ) -> List[TrialResult]:
        """Runs a sequence of benchmark tasks sequentially."""
        results: List[TrialResult] = []
        for task in tasks:
            res = self.run_trial(task=task, agent=agent)
            results.append(res)
        return results
