import asyncio
import os

from opik import Opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import (
    base_metric,
    score_result,
    Hallucination,
    LevenshteinRatio,
    AnswerRelevance
)

from tests.agent import AgentManager


agent_manager = AgentManager()
asyncio.run(agent_manager.initialize())


class ToolSelectionQuality(base_metric.BaseMetric):
    def __init__(self, name: str = "tool_selection_quality"):
        super().__init__(name)
        self.name = name

    def score(self, tool_calls, expected_tool_calls, **kwargs):
        try:
            actual_tool = tool_calls[0]["function_name"]
            expected_tool = expected_tool_calls[0]["function_name"]

            if actual_tool == expected_tool:
                return score_result.ScoreResult(
                    name=self.name,
                    value=1,
                    reason=f"Correct tool selected: {actual_tool}"
                )
            else:
                return score_result.ScoreResult(
                    name=self.name,
                    value=0,
                    reason=f"Wrong tool. Expected {expected_tool}, got {actual_tool}"
                )
        except Exception as e:
            return score_result.ScoreResult(
                name=self.name,
                value=0,
                reason=f"Scoring error: {e}"
            )


def evaluation_task(dataset_item):
    try:
        user_message_content = dataset_item["input"]
        expected_tool = dataset_item.get("tool_call", "")
        reference = dataset_item.get("expected_output", "")

        resp = agent_manager.agent.run_sync(user_message_content)
        result = resp.new_messages()
        tool_calls = [{"function_name": result[1].parts[0].tool_name,
                       "function_parameters": {}}]

        return {
            "input": user_message_content,
            "output": resp.output,
            "reference": reference,
            "tool_calls": tool_calls,
            "expected_tool_calls": [{"function_name": expected_tool, "function_parameters": {}}]
        }
    except Exception as e:
        return {
            "input": dataset_item.get("input", {}),
            "output": "Error processing input.",
            "reference": dataset_item.get("expected_output", ""),
            "tool_calls": [],
            "expected_tool_calls": [{"function_name": "unknown", "function_parameters": {}}],
            "error": str(e)
        }

# refer to https://github.com/comet-ml/opik/issues/2118

opik_workspace = os.getenv("OPIK_WORKSPACE")
opik_api_key = os.getenv("OPIK_API_KEY")

os.environ["OPIK_WORKSPACE"] = opik_workspace
os.environ["OPIK_API_KEY"] = opik_api_key

client = Opik(
    workspace=opik_workspace,
    api_key=opik_api_key
)

dataset = client.get_dataset(name="tool_calls")

judge_dataset = client.get_dataset(name="output_checks")


tool_call_evals = evaluate(
    experiment_name="AgentToolSelectionExperiment",
    dataset=dataset,
    task=evaluation_task,
    scoring_metrics=[ToolSelectionQuality()],
    task_threads=1,
)

print(tool_call_evals.test_results)

output_test_evals = evaluate(
    experiment_name="JudgeOutputExperiment",
    dataset=judge_dataset,
    task=evaluation_task,
    scoring_metrics=[Hallucination(), LevenshteinRatio(), AnswerRelevance(require_context=False)],
    task_threads=1,
)

print(output_test_evals.test_results)