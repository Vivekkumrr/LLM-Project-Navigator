import streamlit as st
import json
import os
import secrets
import sqlite3
from llm_handler import advanced_llm_response
from datetime import datetime
from logging_system import logger


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm_app.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT NOT NULL,
                name TEXT NOT NULL,
                messages_json TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_id, name)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

def normalize_chat_name(chat_name):
    safe = "".join(c for c in chat_name.strip() if c.isalnum() or c in "_-")
    return safe[:80]

def save_chat(owner_id, messages, chat_name=None):
    init_db()
    if not chat_name:
        chat_name = datetime.now().strftime("%Y-%m-%d_%H-%M")
    chat_name = normalize_chat_name(chat_name) or datetime.now().strftime("%Y-%m-%d_%H-%M")
    payload = json.dumps(messages, ensure_ascii=False)

    conn = get_db_connection()
    try:
        try:
            conn.execute(
                "INSERT INTO saved_chats (owner_id, name, messages_json) VALUES (?, ?, ?)",
                (owner_id, chat_name, payload),
            )
        except sqlite3.IntegrityError:
            conn.execute(
                "UPDATE saved_chats SET messages_json = ?, updated_at = CURRENT_TIMESTAMP WHERE owner_id = ? AND name = ?",
                (payload, owner_id, chat_name),
            )
        conn.commit()
        return chat_name
    finally:
        conn.close()

def load_chat(owner_id, chat_name):
    init_db()
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT messages_json FROM saved_chats WHERE owner_id = ? AND name = ?",
            (owner_id, chat_name),
        ).fetchone()
        if not row:
            return []
        return json.loads(row["messages_json"])
    finally:
        conn.close()

def list_saved_chats(owner_id):
    init_db()
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT name FROM saved_chats WHERE owner_id = ? ORDER BY updated_at DESC, created_at DESC",
            (owner_id,),
        ).fetchall()
        return [r["name"] for r in rows]
    finally:
        conn.close()

def delete_chat(owner_id, chat_name):
    init_db()
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "DELETE FROM saved_chats WHERE owner_id = ? AND name = ?",
            (owner_id, chat_name),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def get_chat_owner_id():
    if "chat_owner_id" not in st.session_state:
        st.session_state.chat_owner_id = secrets.token_urlsafe(16)
    return st.session_state.get("username") or st.session_state.chat_owner_id

def main():
    st.set_page_config(
        page_title="LLM Project Navigator",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 LLM Project Navigator")
    st.markdown("Describe your project idea and get AI-powered project blueprints!")

    # Project creation tips
    with st.expander("💡 How to use"):
        st.write("""
        Describe your project idea in natural language. For example:
        - "Create a web application for task management"
        - "Build a data analysis tool for sales data"
        - "I need a chatbot for customer support"
        - "Develop an automation tool for social media posting"
        """)

    # FIX 1: "messages" string was missing quotes before
    if "messages" not in st.session_state:
        st.session_state.messages = []

    owner_id = get_chat_owner_id()

    # Sidebar for saving and loading chats
    with st.sidebar:
        st.header("💾 Saved Chats")

        # Save current chat
        if st.session_state.messages:
            if st.button("💾 Save Current Chat"):
                # FIX 3: was st.session_state.message (missing 's')
                chat_name = save_chat(owner_id, st.session_state.messages)
                if chat_name:
                    st.success(f"Saved as: {chat_name}")
                else:
                    st.error("Failed to save chat")

        # Load a previous chat
        saved = list_saved_chats(owner_id)
        if saved:
            st.subheader("Previous Chats")
            selected = st.selectbox("Load a chat:", ["-- select --"] + saved)
            if selected != "-- select --":
                cols = st.columns([1, 1])
                if cols[0].button("📂 Load"):
                    # FIX 3: was st.session_state.message (missing 's')
                    st.session_state.messages = load_chat(owner_id, selected)
                    st.rerun()
                if cols[1].button("🗑️ Delete"):
                    if delete_chat(owner_id, selected):
                        if st.session_state.get("messages"):
                            st.session_state.messages = []
                        st.rerun()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to create or ask?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your prompt..."):
                # FIX 2: now passes full chat_history for conversational memory
                response = advanced_llm_response(
                    prompt,
                    user_id=getattr(st.session_state, "user_id", "anonymous"),  # NEW: Track who
                    chat_history=st.session_state.messages
                )
                st.markdown(response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
