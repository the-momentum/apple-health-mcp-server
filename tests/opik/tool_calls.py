import asyncio

import opik
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
        # super().__init__(name)
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
        # This is where you call your agent with the input message and get the real execution results.
        resp = (agent_manager.agent.run_sync(user_message_content))
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


metrics = [ToolSelectionQuality()]

client = opik.Opik()

dataset = client.get_dataset(name="tool_calls")

dataset.insert([
    {
        "input": "give me a summary of my health from duckdb",
        "tool_call": "get_health_summary_duckdb"
    },
    {
        "input": "give me some statistics about my heart rate",
        "tool_call": "get_statistics_by_type_duckdb"
    },
    {
        "input": "give me trend data for my step count in october 2024 from duckdb",
        "tool_call": "get_trend_data_duckdb"
    }
])

judge_dataset = client.get_or_create_dataset(name="output_checks")

# judge_dataset.insert([
#     {
#         "input": "give me a summary of my health from duckdb",
#         "expected_output": """
#             Here is a summary of your health data from DuckDB:
#             - **Basal Energy Burned**: 18 records - **Heart Rate**:
#             17 records - **Step Count**: 10 records - **Body Mass Index
#             (BMI)**: 8 records - **Dietary Water**: 1 record If you
#             need more detailed information or specific statistics
#             on any of these categories, feel free to ask!
#         """
#     },
#     {
#         "input": "give me some statistics about my heart rate",
#         "expected_output": """
#             idk yet
#         """
#     },
#     {
#         "input": "give me trend data for my step count in october 2024 from duckdb",
#         "expected_output": """
#             idk yet
#         """
#     }
# ])

eval_results = evaluate(
    experiment_name="AgentToolSelectionExperiment",
    dataset=dataset,
    task=evaluation_task,
    scoring_metrics=metrics,
    task_threads=1,
)

# second_evals = evaluate(
#     experiment_name="JudgeOutputExperiment",
#     dataset=judge_dataset,
#     task=evaluation_task,
#     scoring_metrics=[Hallucination(), LevenshteinRatio(), AnswerRelevance(require_context=False)],
#     task_threads=1,
# )
