import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from queue import Queue, Empty
from typing import Any, Dict, IO
import pytest

# Define the project root so the test can run from anywhere
# This goes up one level from the current file's directory (e2e) to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Add the project root to the path to allow imports from src
sys.path.insert(0, str(PROJECT_ROOT))


def create_json_rpc_request(method: str, params: Dict[str, Any], request_id: int) -> bytes:
    """Creates a valid JSON-RPC 2.0 request and encodes it to bytes."""
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id,
    }
    return (json.dumps(request) + "\\n").encode("utf-8")


def stream_reader(stream: IO[bytes], queue: Queue):
    """Reads a stream line by line and puts the lines into a queue."""
    for line in iter(stream.readline, b''):
        queue.put(line)
    stream.close()


def test_mcp_server_responds_to_list_offerings():
    """
    End-to-end test to ensure the MCP server starts and correctly
    responds to a basic ListOfferings request. This test runs synchronously
    to avoid asyncio event loop conflicts with the server.
    """
    command = [sys.executable, "-m", "src.main"]
    # Set the PYTHONPATH to the project root to ensure src is importable
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=PROJECT_ROOT,
        env=env,
    )

    # Use queues to capture stdout and stderr from threads
    stdout_queue = Queue()
    stderr_queue = Queue()

    # Start threads to read from the streams without blocking
    stdout_thread = threading.Thread(target=stream_reader, args=(process.stdout, stdout_queue), daemon=True)
    stderr_thread = threading.Thread(target=stream_reader, args=(process.stderr, stderr_queue), daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    try:
        # Give the server a moment to start and check for fatal errors
        try:
            # Read all available lines from stderr during the startup window
            startup_output = ""
            while True:
                startup_output += stderr_queue.get(timeout=3.0).decode()
        except Empty:
            # Timeout means no more output, which is good.
            # Now, check if the captured output contains a real error.
            if "Traceback (most recent call last):" in startup_output:
                pytest.fail(f"Server failed on startup with a traceback:\\n{startup_output}")
            elif startup_output:
                # Print normal logs for context, but don't fail the test
                print(f"Server startup logs:\\n{startup_output}", file=sys.stderr)

        # Send the request
        request_id = 1
        rpc_request = create_json_rpc_request(method="mcp_ListOfferings", params={}, request_id=request_id)
        process.stdin.write(rpc_request)
        process.stdin.flush()

        # Wait for the response
        try:
            response_data = stdout_queue.get(timeout=10.0)
            assert response_data, "Received an empty response from the server."
            response = json.loads(response_data)
            assert response.get("id") == request_id
            assert "result" in response or "error" in response

        except Empty:
            # Gather any final stderr output
            stderr_output = ""
            while not stderr_queue.empty():
                stderr_output += stderr_queue.get_nowait().decode()
            assert False, f"Server did not respond within the timeout. Stderr: {stderr_output}"

    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)

        # Ensure threads are joined
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1) 