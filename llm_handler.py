import os
import openai
from config import OPENAI_API_KEY, OPENAI_MODEL

print("🔧 llm_handler.py is loading...")
print(f"🔧 OPENAI_API_KEY present: {bool(OPENAI_API_KEY)}")

# Initialize OpenAI client
if OPENAI_API_KEY and OPENAI_API_KEY.startswith('sk-'):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI client initialized with valid API key")
else:
    client = None
    print("❌ No valid OpenAI API key found")

def is_project_creation_request(message):
    """More precise project creation detection"""
    message_lower = message.lower().strip()
    
    # More specific patterns that clearly indicate project creation intent
    explicit_patterns = [
        'create a project',
        'build a project', 
        'make a project',
        'develop a project',
        'design a project',
        'generate a blueprint',
        'create blueprint',
        'project blueprint',
        'give me a blueprint',
        'i want to create a',
        'i need to build a',
        'help me create a',
        'help me build a',
        'can you create a',
        'can you build a',
        'build me a',
        'create me a',
        'design me a'
    ]
    
    # Check for explicit project creation requests
    has_explicit_pattern = any(pattern in message_lower for pattern in explicit_patterns)
    
    # Additional check: must mention specific project types
    project_types = [
        'web application', 'web app', 'website', 'dashboard', 'api',
        'mobile app', 'chatbot', 'bot', 'tool', 'system', 'platform',
        'automation', 'script', 'application', 'software', 'app'
    ]
    
    mentions_project_type = any(ptype in message_lower for ptype in project_types)
    
    # More restrictive: need both explicit intent AND project type mention
    return has_explicit_pattern and mentions_project_type
def is_feedback_request(message):
    """Detect if user is providing feedback"""
    message_lower = message.lower().strip()
    
    feedback_patterns = [
        'thanks', 'thank you', 'great', 'good', 'excellent', 'perfect',
        'helpful', 'nice', 'awesome', 'cool', 'amazing', 'wonderful',
        'not good', 'bad', 'terrible', 'wrong', 'incorrect', 'error',
        'doesn\'t work', 'not working', 'issue', 'problem',
        'feedback', 'comment', 'suggestion', 'improve'
    ]
    
    # Check if it's a short message (likely feedback)
    is_short = len(message.split()) <= 5
    
    # Check for feedback keywords
    has_feedback_keywords = any(pattern in message_lower for pattern in feedback_patterns)
    
    return is_short and has_feedback_keywords

def call_openai_api(prompt, chat_history=None):
    if not client:
        return "❌ Error: No valid OpenAI API key configured."
    
    try:
        # Build messages with full history
        messages = [
            {
                "role": "system",
                "content": """You are an AI Project Architect assistant. You help users create detailed project plans, 
                analyze requirements, and provide technical guidance. Be helpful, detailed, and professional."""
            }
        ]
        
        # Add conversation history (excluding the latest message)
        if chat_history:
            for msg in chat_history[:-1]:  # exclude last since it's the current prompt
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except openai.AuthenticationError:
        return "❌ Authentication Error: Invalid OpenAI API key."
    except openai.RateLimitError:
        return "❌ Rate Limit Error: Too many requests. Please try again later."
    except openai.APIError as e:
        return f"❌ API Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

def advanced_llm_response(user_message, user_id=None, chat_history=None):
    """LLM response function using real OpenAI API"""
    print(f"📨 Received message: '{user_message}'")
    
    try:
        # Check if this is a project creation request
        if is_feedback_request(user_message):
            print("💬 Detected feedback message")
            
            feedback_responses = [
                "Thank you for your feedback! 😊 How can I help you create something amazing today?",
                "I appreciate that! What project would you like to work on?",
                "Thanks! Feel free to ask me to create any project blueprint you need.",
                "Great to hear! What would you like me to help you build?",
                "Thank you! I'm here to help you create detailed project plans whenever you're ready."
            ]
            
            import random
            return random.choice(feedback_responses)
        elif is_project_creation_request(user_message):
            print("🎯 Detected project creation request")
            
            # Use real OpenAI API for project creation
            project_prompt = f"""
            The user wants to create a project. Here's their request: "{user_message}"
            
            As an AI Project Architect, provide a comprehensive project blueprint including:
            1. Project title and description
            2. Key features and functionality
            3. Recommended technology stack
            4. Estimated timeline
            5. Potential challenges and solutions
            
            Make it detailed, professional, and actionable. Use markdown formatting for better readability.
            """
            
            ai_response = call_openai_api(project_prompt)
            
            response = f"🎯 **PROJECT BLUEPRINT CREATED**\n\n"
            response += f"**Based on your request:** '{user_message}'\n\n"
            response += f"{ai_response}"
            
            return response
        else:
            # Use real OpenAI API for general conversation
            print("💬 General conversation detected")
            
            conversation_prompt = f"""
            You are an AI Project Architect assistant. You specialize in helping users:
            - Create detailed project plans and blueprints
            - Analyze technical requirements
            - Suggest technology stacks
            - Provide development guidance
            
            User message: "{user_message}"
            Instructions:
            -If the user asks a question, answer it directly and completely. Do not defer.
            -If the user asks for a plan, timeline, critique, or breakdown - generate it immediately with full detail.
            -If the user asks about agents, architecture, or Ai systems - explain thoroughly examples.
            -Only ask a follow-up question if critical information is missing (e.g. no topic mentioned at all).
            -Never respond with phrases like "when you're ready","feel free to share","just let me know".
            -Be direct, technical and actionable. Use markdown formatting for clarity.
            """
            
            ai_response = call_openai_api(conversation_prompt)
            return ai_response
            
    except Exception as e:
        error_response = f"""❌ **Error occurred:** {str(e)}
        
        Please check your OpenAI API key and try again."""
        
        print(f"❌ Error in advanced_llm_response: {e}")
        return error_response

print("✅ llm_handler.py loaded successfully")