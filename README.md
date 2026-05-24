# AI Project Creator with Authentication

A Minimal Chatbot application with Streamlit that allows users to create projects and agents through natural language prompts, with JWT authentication and project management capabilities.

## Features

- 🤖 **AI-Powered Project Creation** - Create projects through natural language
- 💬 **Intelligent Assistant** - Conversational interface for project planning
- 📊 **Project Management** - Save and view your created projects
- 🗃️ **SQLite Database** - Persistent data storage for users and projects
- 🎯 **Project Type Detection** - Automatically identifies web apps, chatbots, data tools, etc.

## Project Root
llm-auth-app/
├── app.py                 # Main Streamlit application
├── auth.py               # Authentication and JWT functions
├── config.py             # Configuration settings
├── database.py           # Database initialization and connection
├── llm_handler.py        # AI response and project creation logic
├── project_manager.py    # Project management functions
├── requirements.txt      # Python dependencies
└── README.md            # This file


## Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd llm-auth-app

2. **Create Virtual Environment with these commands
python -m venv venv
venv\Scripts\activate

3. ** Install all Dependencies in requirements.txt file

4. **Create a .env file in the root folder with the following variables:


5. Run the App:
streamlit run app.py


Example Prompts

General Interaction
"What can you do?"
"How do I create a project?"

Project Creation
"Create a portfolio website"
"Build a weather data analyzer"


Tech Stack
Frontend: Streamlit-python
Backend: Python
DatabaseL SQLite3
AI-Integration: OpenAI

