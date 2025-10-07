[← Back to README](../README.md)

## Testing 🧪

There are 3 types of tests in this projects, all of which are included in the pipeline:

Every test is done on [pre-prepared mock apple health data](https://gist.github.com/czajkub/7ee7a01c35990f910f034f46dbf83b66):


## Unit tests 🔧:
  - Testing the importing of XML data to .parquet and database calls to DuckDB
   
## MCP Inspector tests 🔍:
  - Uses the [inspector](https://modelcontextprotocol.io/docs/tools/inspector) provided by anthropic to test connection to the server hosted with streamable http
  - Mainly used in the pipeline, but can be run locally
 
## Opik tests 🤖:
  - End-to-End tests using an agent created from [this](https://github.com/the-momentum/python-ai-kit) AI development kit
  - Two types of tests:
    -  Checking whether the correct tool was called
    -  Judging the answer from an LLM by three metrics:
       - Answer relevancy: whether the answer is relevant to the user's question 🎯
       - Hallucination: whether the answer contains misleading or false information 🚫
       - Levenshtein ratio: Heuristic checking the text structure similarity 📊
    
# How to run tests locally 💻:
- ### Unit tests 🔧: 
```bash
pytest tests/query_tests.py
```
 
Before running the next tests, make sure you have the server up and running:
```bash
uv run fastmcp run -t http app/main.py
```

- ### Inspector tests 🔍:
```bash
npx @modelcontextprotocol/inspector --cli http://localhost:8000/mcp --transport http --method tools/list
```

- ### Opik tests 🤖:
Make sure your `OPIK_WORKSPACE` and `OPIK_API_KEY` environmental variables are set
(Opik workspace refers to your profile name and not project name)
```bash
uv run tests/opik/tool_calls.py
```

### How to run Opik tests in pipeline:
- Create an account on Opik if you already haven't
- Copy your `OPIK_API_KEY` and `OPIK_WORKSPACE` to Github secrets


To add new tests, you can either do it in the code ([example from opik](https://www.comet.com/docs/opik/evaluation/manage_datasets)):
```python
import opik
# Get or create a dataset
client = opik.Opik()
dataset = client.get_or_create_dataset(name="My dataset")
# Add dataset items to it
dataset.insert([
    {"user_question": "Hello, world!", "expected_output": {"assistant_answer": "Hello, world!"}},
    {"user_question": "What is the capital of France?", "expected_output": {"assistant_answer": "Paris"}},
])
```

Or add it on the website:
<img width="1919" height="873" alt="image" src="https://github.com/user-attachments/assets/dc9f3807-40b4-4227-b4c2-5a1ea44396e7" />

When adding tool call questions, make sure the `input` and `tool_call` values are present, and when adding output checks make sure `input` and `expected_output` are set correctly.

[← Back to README](../README.md)
