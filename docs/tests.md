(dodaj strzałke do powrotu)
(i referencje w readme)

## Testing

There are 3 types of tests in this projects, all of which are included in the pipeline:

Every test is done on [pre-prepared mock apple health data](https://gist.github.com/czajkub/7ee7a01c35990f910f034f46dbf83b66):


## Unit tests:
  - Testing the importing of XML data to .parquet and database calls to DuckDB
   
## MCP Inspector tests:
  - Uses the [inspector](https://modelcontextprotocol.io/docs/tools/inspector) provided by anthropic to test connection to the server hosted with streamable http
  - Mainly used in the pipeline, but can be run locally
 
## Opik tests:
  - End-to-End tests using an agent created from [this](https://github.com/the-momentum/python-ai-kit) AI development kit
  - Two types of tests:
    -  Checking whether the correct tool was called
    -  Judging the answer from an LLM by three metrics:
       - Answer relevancy: whether the answer is relevant to the user's question
       - Hallucination: whether the answer contains misleading or false information
       - Levenshtein ratio: Heuristic checking the text structure similarity
    
# How to run tests locally:
- ### Unit tests: 
```bash
pytest tests/query_tests.py
```
 
Before running the next tests, make sure you have the server up and running:
```bash
uv run fastmcp run -t http app/main.py
```

- ### Inspector tests:
```bash
npx @modelcontextprotocol/inspector --cli http://localhost:8000/mcp --transport http --method tools/list
```

- ### Opik tests:
(dodaj zdjęcie do dodania zapytań do eksperymentów)
Make sure your `OPIK_WORKSPACE` and `OPIK_API_KEY` environmental variables are set
(Opik workspace refers to your profile name and not project name)
```bash
    uv run tests/opik/tool_calls.py
```
