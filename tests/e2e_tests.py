import asyncio
import pytest

from pydantic_ai import capture_run_messages
from pydantic_ai.messages import ToolCallPart

from tests.agent import AgentManager


agent_manager = AgentManager()
asyncio.run(agent_manager.initialize())


async def tool_call_template(query: str, tool_name: str):
    with capture_run_messages() as messages:
        try:
            await agent_manager.handle_message(query)
        except ExceptionGroup:
            pytest.fail("Failed to connect with MCP server", False)
        finally:
            print(messages)
            assert len(messages) == 4
            resp = messages[1]
            assert isinstance(resp.parts[0], ToolCallPart)
            assert resp.parts[0].tool_name == tool_name


async def llm_opinion_template(query: str, expected: str):
    with capture_run_messages() as messages:
        try:
            await agent_manager.handle_message(query)
            assert len(messages) == 4
            output = messages[3]
            resp = await agent_manager.handle_message(f"""
                You are a judge that determines on a scale from 0-100%
                how close two messages are to each other. You will receive
                two inputs. Respond only with a percentage, e.g. "81", without % sign.
                Consider things like missing or differing data, you can ignore
                things like honorifics, your highest priority is data itself

                Input nr. 1:
                    {output.parts[0].content}

                Input nr. 2:
                    {expected}

            """)
            percent = int(resp)
            assert 75 <= percent <= 100

        except ExceptionGroup:
            pytest.fail("Failed to connect with MCP server", False)
        finally:
            print(messages)



@pytest.mark.asyncio
async def test_summary():
    await tool_call_template("please give me a summary of my health from duckdb",
                                                  'get_health_summary_duckdb')

@pytest.mark.asyncio
async def test_judge():
    await llm_opinion_template("please give me a summary of my health from duckdb",
                               """Here's a summary of your health data from DuckDB:
                                - **Heart Rate**: 17 records - **Basal Energy Burned**: 17 records
                                 - **Step Count**: 10 records - **Body Mass Index (BMI)**: 8 records
                                  - **Dietary Water Intake**: 1 record""")



# @pytest.mark.asyncio
# async def test_stats():
#     await query_template("please give me statistics of my step counts from duckdb")
#
# @pytest.mark.asyncio
# async def test_trend():
#     await query_template("please give me trend data for my heart rate")
