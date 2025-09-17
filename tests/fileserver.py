import argparse

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/{filename}")
async def serve_file(filename: str) -> FileResponse:
    return FileResponse(filename)


parser = argparse.ArgumentParser(
    prog="Filesystem server",
    description="Host local files in this directory on localhost",
)
parser.add_argument(
    "-p",
    "--port",
    type=int,
    help="Port on which to serve",
    default=8080,
    dest="port",
    action="store",
)

if __name__ == "__main__":
    args = parser.parse_args()
    port = args.port
    uvicorn.run(app, host="localhost", port=port)
