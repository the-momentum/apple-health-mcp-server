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
import nest_asyncio

from tests.agent import AgentManager

nest_asyncio.apply()

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
    # {
    #     "input": "search for step count records between 65 and 90 steps",
    #     "tool_call": "search_health_records_duckdb"
    # },
    {
        "input": "can you search for step records with exactly 13 steps",
        "tool_call": "search_values_duckdb"
    }
])

judge_dataset = client.get_or_create_dataset(name="output_checks")

# judge_dataset.insert([
#     {
#         "input": "search for step count records between 65 and 90 steps",
#         "expected_output": """
#             I found some step count records with values between 65 and 90 steps:
#             1. **76 Steps** - **Source:** Rob’s Apple Watch - **Device:**
#             Apple Watch, model Watch6,1 - **Date:** October 25, 2020
#             - **Start Time:** 00:05:13 - **End Time:** 00:06:14
#             2. **87 Steps** - **Source:** Rob’s Apple Watch
#             - **Device:** Apple Watch, model Watch6,1
#             - **Date:** October 25, 2020 - **Start Time:** 00:06:14
#             - **End Time:** 00:07:15 3. **66 Steps** - **Source:**
#             Rob’s Apple Watch - **Device:** Apple Watch, model Watch6,1
#             - **Date:** October 25, 2020 - **Start Time:** 00:11:35 -
#             **End Time:** 00:12:37 If you need more details or additional
#             records, feel free to ask!
#         """
#     },
#     {
#         "input": "can you search for step records with exactly 13 steps",
#         "expected_output": """
#             I found two records of step count with exactly 13 steps.
#             Here are the details: 1. **Record 1:** - **Source Name:**
#             Rob’s Apple Watch - **Source Version:** 7.0.2 - **Device:**
#             Apple Watch, manufacturer: Apple Inc., model: Watch, hardware:
#             Watch6,1, software: 7.0.2 - **Start Date:** 2020-10-24
#             23:54:51 +02:00 - **End Date:** 2020-10-24 23:55:30 +02:00
#             - **Creation Date:** 2020-10-25 00:04:01 +02:00 - **Unit:**
#             Count - **Value:** 13 2. **Record 2:** - **Source Name:**
#             Rob’s Apple Watch - **Source Version:** 7.0.2 - **Device:** Apple
#             Watch, manufacturer: Apple Inc., model: Watch, hardware: Watch6,1,
#             software: 7.0.2 - **Start Date:** 2020-10-24 23:56:38 +02:00
#             - **End Date:** 2020-10-24 23:56:46 +02:00 - **Creation Date:**
#             2020-10-25 00:04:01 +02:00 - **Unit:** Count - **Value:** 13
#             Would you like further details or analysis on these records?
#         """
#     }
# ])

# eval_results = evaluate(
#     experiment_name="AgentToolSelectionExperiment",
#     dataset=dataset,
#     task=evaluation_task,
#     scoring_metrics=metrics,
#     task_threads=1,
# )

second_evals = evaluate(
    experiment_name="JudgeOutputExperiment",
    dataset=judge_dataset,
    task=evaluation_task,
    scoring_metrics=[Hallucination(), LevenshteinRatio(), AnswerRelevance(require_context=False)],
    task_threads=1,
)
