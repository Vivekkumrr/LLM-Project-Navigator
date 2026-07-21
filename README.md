# Minimal Project Navigation Agent

An AI agent that turns a plain-English project description into a real starting file structure — folders, stub files, and config skeletons — before you write any code.

Unlike tools like Cursor or Copilot (which help you edit code you've already started), this tool focuses on the step before that: giving you something to start from.

**Current scope:** Python projects only. No package installs, no network calls, no other languages (yet).

---

## What It Does

You describe a project idea. The agent:
1. Plans a small set of steps based on what it can actually do
2. Creates 1-2 files and folders for that project on prompt(broader prompt,better response)
3. Tells you exactly what succeeded and what failed — no guessing, no fake "all done" messages

---

## Setup

1. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

4. Run the app
```bash
streamlit run app.py
```

---

## How to Use It

Just describe your project idea in the chat. Examples:

- "I want a script that tracks my daily expenses and shows weekly totals"
- "Scaffold a basic CLI tool for renaming files in a folder"
- "Build a small tool that reads a CSV and summarizes it"

The agent will create the files inside the `generated/` folder and tell you what it made.

---

## What It Can Do

| Tool | What it does |
|---|---|
| `write_file` | Creates a file (supports folders inside `generated/`) |
| `read_file` | Reads a file back |
| `list_files` | Lists files in a folder |
| `search_code` | Searches project code for a keyword |
| `run_python` | Runs a Python snippet and returns the output |

---

## What It Can't Do (Yet)

- No installing packages (`pip install`, `npm install`, etc.)
- No non-Python project types (Node, Java, etc.)
- No network or internet access
- No deleting or renaming existing files

If a step needs one of these, the agent will say so instead of pretending it happened.

---

## Project Structure

```
app.py            → Streamlit UI, chat and saved-chat history
tool_handler.py    → Tools, planning, and execution logic
config.py           → OpenAI API settings
generated/           → Files the agent creates for you
```

---

## Design Principle: Honesty Over Confidence

Earlier versions of this agent would sometimes describe steps as "done" even when they failed or never ran. This version fixes that:

- The agent only plans steps it can actually perform
- Every step's real result (success or error) is tracked
- The final response is built from those real results — not a made-up summary

If something fails, you'll see exactly what failed and why, instead of a false "everything worked" message.

---
Architecture Note: One Agent, Not Multi-Agent

This is one agent that calls multiple tools.

There's no team of specialized agents (planner agent, coder agent, reviewer agent, etc.) talking to each other. It's a single loop: one LLM plans steps, picks a tool for each step, runs it, and reports the result. "Multi-tool calling" describes it accurately; "multi-agent" would not.
---
## Future Prospects

- Add Voice Command using Javascript/Typescript
- Improve UI from Streamlit to React
- Migrate from SQLite to PostqueSQL for storing chats

## Notes

- This is a demo/portfolio project, intentionally scoped small and honest rather than broad and unreliable.
- Saved chats are stored in a local SQLite database.
