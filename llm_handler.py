from http import client
import os
import openai
from functools import lru_cache
from config import OPENAI_API_KEY, OPENAI_MODEL, get_openai_status, is_valid_openai_key
import logging
import json

import uuid
from logging_system import (
    logger,
    TokenCounter,
    UsageTracker,
    track_api_request,
    log_api_response,
    log_error_with_context
)

usage_tracker = UsageTracker()

# Configure basic structured logging
# Now handled by logging_system

@lru_cache(maxsize=1)
def get_openai_client():
    if OPENAI_API_KEY and is_valid_openai_key(OPENAI_API_KEY):
        return openai.OpenAI(api_key=OPENAI_API_KEY)
    return None

@lru_cache(maxsize=1)
def get_llm_status():
    status = get_openai_status()
    status["openai_client_ready"] = bool(get_openai_client())
    return status

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

@track_api_request(user_id="default")
def call_openai_api(prompt, chat_history=None):
    client = get_openai_client()
    if not client:
        return "❌ Error: No valid OpenAI API key configured."
    
    request_id = str(uuid.uuid4())
    user_id = "default"
    
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
        else:
            messages.append({
                "role": "user",
                "content": prompt
            })

        # Count input tokens
        input_text = json.dumps(messages)
        input_tokens = TokenCounter.count(input_text)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        # Count output tokens
        output_tokens = TokenCounter.count(content)
        cost = 0.00091
        
        usage_tracker.add_usage(input_tokens, output_tokens, cost)
        log_api_response(request_id, user_id, input_tokens, output_tokens, cost)
        
        return content
        
    except openai.AuthenticationError as e:
        log_error_with_context(e, request_id, user_id)
        return "❌ Authentication Error: Invalid OpenAI API key."
    except openai.RateLimitError as e:
        log_error_with_context(e, request_id, user_id)
        return "❌ Rate Limit Error: Too many requests. Please try again later."
    except openai.APIError as e:
        log_error_with_context(e, request_id, user_id)
        return f"❌ API Error: {str(e)}"
    except Exception as e:
        log_error_with_context(e, request_id, user_id)
        return f"❌ Unexpected error: {str(e)}"
# handle other LLM-related functions like summarization, critique and decision making here as needed
def summarize_chat_history(chat_history):
    """Summarize chat history using OpenAI API"""
    client = get_openai_client()
    if not client:
        return "❌ Error: No valid OpenAI API key configured."
    
    try:
        summary_prompt = f"""
        Summarize the following conversation between a user and an AI assistant. Focus on key points, decisions, and action items. Be concise but informative.
        
        Conversation:
        {''.join([f"{msg['role'].capitalize()}: {msg['content']}\n" for msg in chat_history])}
        
        Summary:
        """
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=500,
            temperature=0.5
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error summarizing chat history: {str(e)}"



def advanced_llm_response(user_message, user_id=None, chat_history=None):
    """LLM response function using real OpenAI API"""
    logger.info(json.dumps({"event": "message_received", "user_message": user_message}, ensure_ascii=False))
    
    try:
        # Check if this is a project creation request
        if is_feedback_request(user_message):
            logger.info(json.dumps({"event": "detected_feedback"}))
            
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
            logger.info(json.dumps({"event": "detected_project_creation"}))
            
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
            logger.info(json.dumps({"event": "detected_general_conversation"}))
            
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
        
        logger.error(json.dumps({"event": "error_in_response", "error": str(e)}))
        return error_response

