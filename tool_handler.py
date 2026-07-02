import os
import json
import subprocess
import openai
from config import OPENAI_API_KEY, OPENAI_MODEL

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ── Tool definitions sent to OpenAI ──────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file inside the generated/ folder",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Filename only, e.g. app.py"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and return the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file, e.g. config.py"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Path to the directory, e.g. . or ./generated"
                    }
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search all .py files in the project for a keyword and return matching file paths and lines",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The keyword or phrase to search for, e.g. def call_openai_api"
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Execute a Python code snippet and return stdout and stderr",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"}
                },
                "required": ["code"]
            }
        }
    }
]

# ── Actual Python functions that execute the tools ────────────────────────────

def read_file(path: str) -> str:
    try:
        # Safety: restrict to current working directory
        safe_path = os.path.realpath(path)
        cwd = os.path.realpath(".")
        if not safe_path.startswith(cwd):
            return "❌ Access denied: path is outside project directory."

        with open(safe_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"❌ File not found: {path}"
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"


def write_file(filename: str, content: str) -> str:
    try:
        if os.path.basename(filename) != filename:
            return "❌ Only plain filenames allowed (no paths). Use e.g. 'app.py'."
        output_path = os.path.join(os.path.realpath("."), "generated", filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Written to generated/{filename}"
    except Exception as e:
        return f"❌ Error writing file: {str(e)}"


def list_files(directory: str) -> str:
    try:
        safe_dir = os.path.realpath(directory)
        cwd = os.path.realpath(".")
        if not safe_dir.startswith(cwd):
            return "❌ Access denied: path is outside project directory."

        entries = os.listdir(safe_dir)
        if not entries:
            return "Directory is empty."
        return "\n".join(sorted(entries))
    except FileNotFoundError:
        return f"❌ Directory not found: {directory}"
    except Exception as e:
        return f"❌ Error listing files: {str(e)}"


def search_code(keyword: str) -> str:
    try:
        cwd = os.path.realpath(".")
        matches = []

        for root, _, files in os.walk(cwd):
            for filename in files:
                if not filename.endswith(".py"):
                    continue
                filepath = os.path.join(root, filename)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, start=1):
                        if keyword.lower() in line.lower():
                            rel_path = os.path.relpath(filepath, cwd)
                            matches.append(f"{rel_path}:{line_num}  {line.rstrip()}")

        if not matches:
            return f"No matches found for '{keyword}'."
        return "\n".join(matches)
    except Exception as e:
        return f"❌ Error searching code: {str(e)}"


def run_python(code: str) -> str:
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        if error:
            return f"stdout: {output}\nstderr: {error}"
        return output or "✅ Code ran with no output."
    except subprocess.TimeoutExpired:
        return "❌ Execution timed out (10s limit)."
    except Exception as e:
        return f"❌ Error running code: {str(e)}"


# ── Dispatcher: maps tool name → function ────────────────────────────────────

def execute_tool(name: str, args: dict) -> str:
    try:
        if name == "write_file":
            return write_file(**args)
        elif name == "read_file":
            return read_file(**args)
        elif name == "list_files":
            return list_files(**args)
        elif name == "search_code":
            return search_code(**args)
        elif name == "run_python":
            return run_python(**args)
        else:
            return f"❌ Unknown tool: {name}"
    except TypeError as e:
        return f"❌ Wrong arguments for '{name}': {str(e)}"


# ── Internal helpers ───────────────────────────────────────────────────────

def _extract_plan(response_text: str) -> list[str]:
    try:
        # Try JSON first
        parsed = json.loads(response_text)
        if isinstance(parsed, dict) and "steps" in parsed:
            return [str(step) for step in parsed["steps"]]
        if isinstance(parsed, list):
            return [str(step) for step in parsed]
    except Exception:
        pass

    # Fallback: parse numbered lines
    lines = [line.strip() for line in response_text.splitlines() if line.strip()]
    steps = []
    for line in lines:
        if line[0].isdigit() and (line[1:2] in [".", ")"]):
            steps.append(line[2:].strip())
        elif line.lower().startswith("step"):
            parts = line.split(" ", 1)
            if len(parts) == 2:
                steps.append(parts[1].strip())
        else:
            steps.append(line)
    return steps


def _execute_tool_calls(message, messages):
    for tool_call in message.tool_calls:
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            result = f"❌ Malformed arguments from LLM: {tool_call.function.arguments}"
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
            continue

        result = execute_tool(name, args)
        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
    return messages


# ── Core: plan then execute flow ─────────────────────────────────────────────

def call_with_tools(user_message: str) -> str:
    system = {
        "role": "system",
        "content": "You are a planning assistant. First create a structured plan of steps to complete the user's request. Then execute each step in order, review results, and answer fully."
    }

    plan_prompt = (
        "Create a structured plan for the user request. "
        "Return only a JSON object with a single key named steps, e.g. {\"steps\": [\"...\"]}."
    )

    plan_response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[system, {"role": "user", "content": user_message + "\n\n" + plan_prompt}],
        max_tokens=500,
        temperature=0.3
    )

    plan_text = plan_response.choices[0].message.content or ""
    steps = _extract_plan(plan_text)
    if not steps:
        steps = [plan_text.strip()]

    messages = [system, {"role": "user", "content": user_message}, {"role": "assistant", "content": f"PLAN:\n{plan_text}"}]

    for idx, step in enumerate(steps, start=1):
        step_prompt = f"Execute step {idx}/{len(steps)}: {step}"
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages + [{"role": "user", "content": step_prompt}],
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message
        if not message.tool_calls:
            result_text = message.content or ""
            messages.append({"role": "assistant", "content": result_text})
            continue

        messages.append(message)
        messages = _execute_tool_calls(message, messages)

        followup = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages + [{"role": "user", "content": f"Review the tool results for step {idx} and provide the executed result."}],
            max_tokens=500,
            temperature=0.3
        )
        messages.append(followup.choices[0].message)

    final_review = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages + [{"role": "user", "content": "Review all steps, summarize results, and answer the original request completely."}],
        max_tokens=1000,
        temperature=0.4
    )

    final_answer = final_review.choices[0].message.content or ""

    plan_display = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
    return f"**Plan**\n{plan_display}\n\n**Result**\n{final_answer}"


def stream_with_tools(user_message: str):
    """
    Generator version of call_with_tools.
    Yields status strings during tool execution, then streams the final answer token by token.
    """
    system = {
        "role": "system",
        "content": "You are a planning assistant. First create a structured plan of steps to complete the user's request. Then execute each step in order, review results, and answer fully."
    }

    plan_prompt = (
        "Create a structured plan for the user request. "
        "Return only a JSON object with a single key named steps, e.g. {\"steps\": [\"...\"]}."
    )

    yield "⏳ Planning..."

    plan_response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[system, {"role": "user", "content": user_message + "\n\n" + plan_prompt}],
        max_tokens=500,
        temperature=0.3
    )

    plan_text = plan_response.choices[0].message.content or ""
    steps = _extract_plan(plan_text)
    if not steps:
        steps = [plan_text.strip()]

    plan_display = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
    yield f"**Plan**\n{plan_display}\n\n"

    messages = [system, {"role": "user", "content": user_message}, {"role": "assistant", "content": f"PLAN:\n{plan_text}"}]

    for idx, step in enumerate(steps, start=1):
        yield f"⚙️ Step {idx}/{len(steps)}: {step}"

        step_prompt = f"Execute step {idx}/{len(steps)}: {step}"
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages + [{"role": "user", "content": step_prompt}],
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message
        if not message.tool_calls:
            messages.append({"role": "assistant", "content": message.content or ""})
            continue

        messages.append(message)
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            yield f"🔧 Using tool: `{name}`..."
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                result = f"❌ Malformed arguments: {str(e)}"
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
                continue
            result = execute_tool(name, args)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})

        followup = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages + [{"role": "user", "content": f"Review the tool results for step {idx} and provide the executed result."}],
            max_tokens=500,
            temperature=0.3
        )
        messages.append(followup.choices[0].message)

    # Stream the final answer token by token
    yield "**Result**\n"
    final_stream = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages + [{"role": "user", "content": "Review all steps, summarize results, and answer the original request completely."}],
        max_tokens=1000,
        temperature=0.4,
        stream=True
    )
    for chunk in final_stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token


# ── ReAct pattern: explicit thought/action/observation cycles ───────────────

REACT_SYSTEM_PROMPT = """You are an agent that solves tasks step by step using ReAct format.
On each turn, respond with EXACTLY this format and nothing else:

THOUGHT: <your reasoning about what to do next>
ACTION: <tool_name>(<param>="<value>")  OR  FINISH

If ACTION is a tool, use one of: read_file(path="..."), list_files(directory="..."), search_code(keyword="..."), write_file(filename="...", content="..."), run_python(code="...")

If you have enough information to answer, output:
THOUGHT: <final reasoning>
ACTION: FINISH
FINAL ANSWER: <your complete answer to the user>
"""

def _parse_react_action(text: str):
    """Extract tool name and args from a line like: read_file(path="main.py")"""
    import re
    match = re.search(r'(\w+)\((.*)\)', text)
    if not match:
        return None, {}
    name = match.group(1)
    args_str = match.group(2)
    args = {}
    for pair in re.findall(r'(\w+)\s*=\s*"([^"]*)"', args_str):
        args[pair[0]] = pair[1]
    return name, args


def react_agent(user_message: str, max_cycles: int = 5):
    """
    Minimal ReAct loop: yields THOUGHT/ACTION/OBSERVATION text each cycle.
    Stops when the model outputs ACTION: FINISH.
    """
    messages = [
        {"role": "system", "content": REACT_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    for cycle in range(max_cycles):
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=300,
            temperature=0.2
        )
        text = response.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": text})

        yield f"\n**Cycle {cycle + 1}**\n{text}\n"

        if "ACTION: FINISH" in text or "FINISH" in text.split("ACTION:")[-1].split("\n")[0]:
            # Try to pull FINAL ANSWER if present, otherwise return as-is
            if "FINAL ANSWER:" in text:
                yield text.split("FINAL ANSWER:", 1)[1].strip()
            return

        # Extract the ACTION line and execute the tool
        action_line = ""
        for line in text.splitlines():
            if line.strip().startswith("ACTION:"):
                action_line = line.replace("ACTION:", "").strip()
                break

        name, args = _parse_react_action(action_line)
        if not name:
            messages.append({"role": "user", "content": "OBSERVATION: Could not parse action. Use the exact format shown."})
            yield "OBSERVATION: Could not parse action."
            continue

        result = execute_tool(name, args)
        if len(result) > 800:
            result = result[:800] + "\n...[truncated]"
        observation = f"OBSERVATION: {result}"
        messages.append({"role": "user", "content": observation})
        yield observation

    yield "\n⚠️ Max cycles reached without a final answer."


# ── Quick test when run directly ─────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        "List files in this directory, then read config.py and summarize it"
    ]

    for prompt in tests:
        print(f"\n{'─'*60}")
        print(f"USER: {prompt}")
        print(f"ASSISTANT: {call_with_tools(prompt)}")