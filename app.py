import os
import streamlit as st
from tool_handler import stream_with_tools

CHAT_HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_histories")


def ensure_history_dir():
    os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)


def get_initial_messages():
    return [
        {"role": "assistant", "content": "Hi! I’m your demo AI agent. Ask me anything and I’ll respond."}
    ]


def list_saved_chats():
    ensure_history_dir()
    files = [f for f in os.listdir(CHAT_HISTORY_DIR) if f.endswith(".txt")]
    return sorted([os.path.splitext(f)[0] for f in files])


def save_chat_history(chat_name, messages):
    ensure_history_dir()
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in chat_name.strip()) or "chat"
    path = os.path.join(CHAT_HISTORY_DIR, f"{safe_name}.txt")

    with open(path, "w", encoding="utf-8") as handle:
        for message in messages:
            role = message.get("role", "")
            content = (message.get("content") or "").strip()
            if not content:
                continue
            if role == "user":
                handle.write(f"User: {content}\n")
            elif role == "assistant":
                handle.write(f"Assistant: {content}\n")

    return safe_name


def load_chat_history(chat_name):
    path = os.path.join(CHAT_HISTORY_DIR, f"{chat_name}.txt")
    if not os.path.exists(path):
        return get_initial_messages()

    messages = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith("User:"):
                messages.append({"role": "user", "content": line[len("User:"):].strip()})
            elif line.startswith("Assistant:"):
                messages.append({"role": "assistant", "content": line[len("Assistant:"):].strip()})

    return messages or get_initial_messages()


def delete_chat_history(chat_name):
    path = os.path.join(CHAT_HISTORY_DIR, f"{chat_name}.txt")
    if os.path.exists(path):
        os.remove(path)


def main():
    st.set_page_config(
        page_title="Demo AI Agent",
        page_icon="✨",
        layout="centered"
    )

    st.markdown(
        """
        <style>
        .block-container { padding-top: 1rem; max-width: 900px; }
        .demo-agent-card {
            padding: 1.2rem 1.4rem;
            border-radius: 16px;
            background: linear-gradient(135deg, #ffffff, #f5f7ff);
            border: 1px solid #e5e7eb;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="demo-agent-card">
            <h1 style="margin-bottom:0.2rem;">Demo AI Agent</h1>
            <p style="margin:0; color:#4b5563;">A simple assistant experience for showcasing your agent.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = get_initial_messages()

    with st.sidebar:
        st.header("💬 Chat History")

        if st.button("🆕 New Chat"):
            st.session_state.messages = get_initial_messages()
            st.session_state.current_chat_name = ""
            st.rerun()

        chat_name = st.text_input("Save as", value=st.session_state.get("current_chat_name", ""), key="chat_name_input")
        if st.button("💾 Save Chat"):
            saved_name = save_chat_history(chat_name or "chat", st.session_state.messages)
            st.session_state.current_chat_name = saved_name
            st.success(f"Saved as {saved_name}")

        saved = list_saved_chats()
        if saved:
            st.subheader("Saved Chats")
            selected = st.selectbox("Load a chat", ["-- select --"] + saved, key="selected_chat")
            cols = st.columns(2)
            if cols[0].button("📂 Load") and selected != "-- select --":
                st.session_state.messages = load_chat_history(selected)
                st.session_state.current_chat_name = selected
                st.rerun()
            if cols[1].button("🗑️ Delete") and selected != "-- select --":
                delete_chat_history(selected)
                st.session_state.messages = get_initial_messages()
                st.session_state.current_chat_name = ""
                st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    st.caption("Try one of these:")
    examples = [
        "Explain this project in one sentence.",
        "Suggest three ideas for a startup app.",
        "Write a short product description."
    ]
    cols = st.columns(len(examples))
    for col, example in zip(cols, examples):
        if col.button(example, use_container_width=True):
            st.session_state.pending_prompt = example

    prompt = st.session_state.pop("pending_prompt", None) if "pending_prompt" in st.session_state else None
    if prompt is None:
        prompt = st.chat_input("Ask the demo agent...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            output = st.empty()
            response = ""
            with st.spinner("Thinking..."):
                for chunk in stream_with_tools(prompt):
                    if chunk.startswith(("⏳", "⚙️", "🔧", "**Plan**", "**Result**")):
                        continue
                    response += chunk
                    output.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()