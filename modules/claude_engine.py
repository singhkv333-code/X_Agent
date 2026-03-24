import subprocess
import json
import re


def ask_claude(prompt: str, system_instruction: str = "", timeout: int = 120) -> str:
    """Send a one-shot prompt to Claude via Claude Code CLI and return the response."""
    cmd = ["claude", "--print"]
    if system_instruction:
        cmd.extend(["--system-prompt", system_instruction])
    cmd.append(prompt)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI error: {result.stderr}")
    return result.stdout.strip()


def ask_claude_json(prompt: str, system_instruction: str = "", timeout: int = 120) -> any:
    """
    Send a prompt to Claude and parse the response as JSON.
    Strips markdown code fences if present before parsing.
    """
    raw = ask_claude(prompt, system_instruction=system_instruction, timeout=timeout)

    # Strip ```json ... ``` or ``` ... ``` fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    return json.loads(cleaned)
