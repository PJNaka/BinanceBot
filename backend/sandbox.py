import docker
import tempfile
import os
import time

# Default Python image to use for the sandbox
DEFAULT_PYTHON_IMAGE = "python:3.10-slim" 

class SandboxExecutionResult:
    def __init__(self, stdout: str = "", stderr: str = "", error: str | None = None, exit_code: int | None = None, execution_time: float = 0.0):
        self.stdout = stdout
        self.stderr = stderr
        self.error = error # e.g., "TimeoutError", "RuntimeError", "DockerError"
        self.exit_code = exit_code
        self.execution_time = execution_time

    def to_dict(self):
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
        }

def execute_python_code_in_docker(code_string: str, python_image: str = DEFAULT_PYTHON_IMAGE, timeout_seconds: int = 30) -> SandboxExecutionResult:
    client = None
    try:
        # Attempt to connect to the Docker daemon using environment variables.
        # This is the standard way to initialize the Docker client.
        client = docker.from_env()
    except docker.errors.DockerException as e:
        # This typically means Docker is not running or not accessible.
        return SandboxExecutionResult(error=f"Docker daemon not available or configuration error: {e}")

    # Create a temporary file on the host to hold the user's Python code.
    # The code is written to this file, which is then volume-mounted into the Docker container.
    # This approach is generally safer than passing complex code directly via command line arguments,
    # especially for multi-line scripts or scripts with special characters.
    # `delete=False` is used because the file needs to exist until Docker is done with it;
    # manual unlinking is done in the `finally` block.
    tmp_script_name_host = "" # Initialize to prevent NameError in finally if tempfile.NamedTemporaryFile fails
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w') as tmp_script:
            tmp_script_name_host = tmp_script.name
            tmp_script_name_container = "/app/temp_script.py" # Path inside the container
            tmp_script.write(code_string)
    except Exception as e:
        return SandboxExecutionResult(error=f"Failed to create temporary script file: {e}")
    
    container = None
    start_time = time.time()
    
    try:
        # Ensure the image is available locally, pull if not.
        try:
            client.images.get(python_image)
        except docker.errors.ImageNotFound:
            print(f"Image {python_image} not found locally. Pulling...")
            client.images.pull(python_image)
            print("Image pulled.")

        # Define volume mapping: host's temporary script file to a fixed path inside the container.
        # 'ro' mode ensures the script cannot be modified from within the container, enhancing security.
        volumes_spec = {tmp_script_name_host: {'bind': tmp_script_name_container, 'mode': 'ro'}}
        
        # Run the Docker container.
        # - image: The specified Python image (e.g., "python:3.10-slim").
        # - command: The command to run inside the container (execute the Python script).
        # - volumes: Mounts the temporary script file (read-only).
        # - detach=True: Runs the container in the background and returns a Container object.
        # - mem_limit="256m": Restricts container memory usage to 256MB.
        # - network_mode: Defaults to 'bridge', allowing outbound network access.
        #   For stricter isolation where no network is needed: network_mode='none'.
        #   However, bridge mode is often needed for packages or data fetching.
        container = client.containers.run(
            image=python_image,
            command=["python", tmp_script_name_container],
            volumes=volumes_spec,
            detach=True, 
            mem_limit="256m", # Resource limit: Memory
            # stop_signal="SIGKILL", # More forceful stop, but can prevent cleanup in script. Default is SIGTERM.
            # ulimits: Can set ulimits if needed, e.g., for CPU time or file sizes (more complex).
            # security_opt: Can set security options like "no-new-privileges".
        )

        try:
            # Resource limit: Timeout mechanism.
            # container.wait() can block indefinitely if the underlying HTTP request times out
            # or if the container itself hangs. This loop provides a more proactive timeout.
            # container.wait() can block indefinitely if timeout is not handled by requests
            # Using a loop with status check for more robust timeout for the container itself
            for _ in range(timeout_seconds * 2): # Check status twice per second
                time.sleep(0.5)
                container.reload() # Get fresh status
                if container.status == 'exited':
                    break
            
            if container.status != 'exited':
                container.stop(timeout=5) # Stop if still running
                execution_time = time.time() - start_time
                return SandboxExecutionResult(error=f"Execution timed out after {timeout_seconds} seconds.", execution_time=execution_time)

            result = container.wait() # Should return immediately as status is 'exited'
            exit_code = result.get("StatusCode")

        except docker.errors.NotFound: # Container might be removed by another process or due to OOM
            execution_time = time.time() - start_time
            # Check logs if possible, but container is gone
            return SandboxExecutionResult(error="Container not found during execution, possibly due to OOM error or external removal.", exit_code=None, execution_time=execution_time)
        except Exception as e: # Catch other exceptions during wait/stop, e.g. ReadTimeout from requests
            # This catch block is to handle timeouts from the `container.wait()` call itself (less likely with the loop),
            # or other docker-py/requests issues during the wait/stop operations.
            if container and container.status != 'exited': # Check if container exists and is running
                try:
                    container.stop(timeout=5) # Attempt to stop it gracefully if primary timeout failed
                except docker.errors.APIError as stop_err:
                    print(f"Error stopping container during exception handling: {stop_err}")

            execution_time = time.time() - start_time
            # Check if the error message string indicates a timeout from the requests library used by docker-py
            if "read timed out" in str(e).lower() or "timeout" in str(e).lower():
                 return SandboxExecutionResult(error=f"Execution timed out after {timeout_seconds} seconds (docker-py/requests op).", execution_time=execution_time)
            return SandboxExecutionResult(error=f"Error during container wait/stop: {e}", execution_time=execution_time)


        execution_time = time.time() - start_time
        
        # Retrieve logs from the container.
        # `errors='ignore'` helps prevent issues with non-UTF-8 characters in output.
        stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='ignore').strip()
        stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='ignore').strip()

        if exit_code == 0:
            return SandboxExecutionResult(stdout=stdout, stderr=stderr, exit_code=exit_code, execution_time=execution_time)
        else:
            # Differentiate between actual runtime error in code vs other non-zero exits
            error_type = "RuntimeError" 
            # Common exit codes for signals (e.g., 137 for SIGKILL often due to OOM, 139 for SIGSEGV)
            if exit_code == 137: # OOM killed
                error_type = "MemoryLimitExceeded"
                stderr += "\nProcess killed, possibly due to memory limit (256m)."
            elif exit_code == 139: # Segmentation fault
                 error_type = "SegmentationFault"
                 stderr += "\nProcess terminated with segmentation fault."

            return SandboxExecutionResult(stdout=stdout, stderr=stderr, error=error_type, exit_code=exit_code, execution_time=execution_time)

    except docker.errors.ImageNotFound:
        execution_time = time.time() - start_time if start_time else 0
        return SandboxExecutionResult(error=f"Docker image {python_image} not found.", execution_time=execution_time)
    except docker.errors.APIError as e: # Covers container creation failure, image pull issues not caught by ImageNotFound, etc.
        execution_time = time.time() - start_time if 'start_time' in locals() else 0
        return SandboxExecutionResult(error=f"Docker API error: {e}", execution_time=execution_time)
    except Exception as e: # Catch-all for any other unexpected errors.
        execution_time = time.time() - start_time if 'start_time' in locals() else 0
        return SandboxExecutionResult(error=f"An unexpected error occurred in sandbox execution: {e}", execution_time=execution_time)
    finally:
        # Ensure cleanup of container and temporary script file.
        if container:
            try:
                container.remove(force=True) # Force removal ensures it's cleaned up even if stopped abruptly.
            except docker.errors.APIError as e:
                print(f"Warning: Could not remove container {container.id[:12] if hasattr(container, 'id') else 'unknown'}: {e}")
        if tmp_script_name_host and os.path.exists(tmp_script_name_host):
            try:
                os.unlink(tmp_script_name_host) # Delete the temporary script from the host.
            except Exception as e:
                print(f"Warning: Could not remove temporary script {tmp_script_name_host}: {e}")


if __name__ == '__main__':
    print("Testing Python code execution in Docker sandbox...")

    # Test 1: Simple print
    code1 = "print('Hello from Dockerized Python!')"
    print(f"\nExecuting code 1:\n{code1}")
    result1 = execute_python_code_in_docker(code1)
    print(f"Result 1: {result1.to_dict()}")

    # Test 2: Code with an error
    code2 = "print('About to error')\nresult = 1/0"
    print(f"\nExecuting code 2:\n{code2}")
    result2 = execute_python_code_in_docker(code2)
    print(f"Result 2: {result2.to_dict()}")

    # Test 3: Code that should time out
    code3 = "import time\nprint('Starting long task...')\ntime.sleep(10)\nprint('Long task finished.')"
    print(f"\nExecuting code 3 (should timeout in 5s):\n{code3}")
    result3 = execute_python_code_in_docker(code3, timeout_seconds=5)
    print(f"Result 3: {result3.to_dict()}")
    
    # Test 4: Code that uses a lot of memory (illustrative, actual limit enforcement by Docker)
    # This code attempts to allocate a large string. If it exceeds mem_limit, Docker should kill it.
    # The exit code 137 is common for OOM killer.
    code4 = "print('Allocating memory...')\na = ' ' * (200 * 1024 * 1024) # Try to allocate 200MB, mem_limit is 256MB\nprint('Memory allocated or process killed before this point.')"
    print(f"\nExecuting code 4 (memory intensive, should be killed by OOM if >256MB):\n{code4}")
    result4 = execute_python_code_in_docker(code4, timeout_seconds=20) # Give it time to be OOM killed
    print(f"Result 4: {result4.to_dict()}")
    
    # Test 5: Simulate a very long print to test stdout handling
    code5 = "for i in range(5000): print(f'Line {i}')" # Approx 50KB of output
    print(f"\nExecuting code 5 (large stdout):\n{code5[:100]}...") # Print snippet
    result5 = execute_python_code_in_docker(code5, timeout_seconds=10)
    print(f"Result 5 (stdout length: {len(result5.stdout)}): {result5.to_dict()['error']}, Exit: {result5.to_dict()['exit_code']}")
    if len(result5.stdout) > 1000:
        print(f"Result 5 stdout (first 1000 chars): {result5.stdout[:1000]}...")
    else:
        print(f"Result 5 stdout: {result5.stdout}")

    # Test 6: Code with non-ASCII characters
    code6 = "print('こんにちは世界')"
    print(f"\nExecuting code 6:\n{code6}")
    result6 = execute_python_code_in_docker(code6)
    print(f"Result 6: {result6.to_dict()}")

    # Test 7: Code that produces a lot of stderr
    code7 = "import sys\nfor i in range(100): sys.stderr.write(f'Error line {i}\\n')"
    print(f"\nExecuting code 7 (large stderr):\n{code7}")
    result7 = execute_python_code_in_docker(code7, timeout_seconds=10)
    print(f"Result 7 (stderr length: {len(result7.stderr)}): {result7.to_dict()['error']}, Exit: {result7.to_dict()['exit_code']}")
    if len(result7.stderr) > 1000:
        print(f"Result 7 stderr (first 1000 chars): {result7.stderr[:1000]}...")
    else:
        print(f"Result 7 stderr: {result7.stderr}")

    # Test 8: No code (empty string)
    code8 = ""
    print(f"\nExecuting code 8 (empty string):\n'{code8}'")
    result8 = execute_python_code_in_docker(code8)
    print(f"Result 8: {result8.to_dict()}")
    
    # Test 9: Malformed python code (SyntaxError)
    code9 = "print('Hello'\nprint 'world')" # Syntax error in Python 3
    print(f"\nExecuting code 9 (syntax error):\n{code9}")
    result9 = execute_python_code_in_docker(code9)
    print(f"Result 9: {result9.to_dict()}")

    # Test 10: Using a non-existent image (to test ImageNotFound error handling)
    # print(f"\nExecuting with non-existent image:")
    # result10 = execute_python_code_in_docker("print('test')", python_image="nonexistent/image:latest", timeout_seconds=5)
    # print(f"Result 10: {result10.to_dict()}")
    # Note: Test 10 is commented out by default as it will attempt to pull and fail, which can be slow.
    # Uncomment to test this specific error path.

    print("\nFinished all tests.")
