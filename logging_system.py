import logging
import json
import uuid
import traceback
import functools
from datetime import datetime
try:
    import tiktoken
except ImportError:
    tiktoken = None

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        
        for field in ["request_id", "user_id", "input_tokens", "output_tokens", "cost", "error_context"]:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
                
        if record.exc_info:
            log_data["error_context"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logger():
    logger = logging.getLogger("agent_chatbot")
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()

class TokenCounter:
    @staticmethod
    def count(text: str, model: str = "cl100k_base") -> int:
        if tiktoken is None:
            # Simple heuristic fallback (approx. 4 characters per token)
            return len(str(text)) // 4
        try:
            encoding = tiktoken.get_encoding(model)
            return len(encoding.encode(str(text)))
        except Exception:
            return len(str(text)) // 4

class UsageTracker:
    def __init__(self):
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0

    def add_usage(self, input_tokens: int, output_tokens: int, cost: float):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost
        self.total_requests += 1

def track_api_request(user_id=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())
            current_user = kwargs.get("user_id", user_id) or "anonymous"
            logger.info(f"Starting request {func.__name__}", extra={"request_id": request_id, "user_id": current_user})
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_error_with_context(e, request_id, current_user)
                raise
        return wrapper
    return decorator

def log_api_response(request_id, user_id, input_tokens, output_tokens, cost):
    logger.info("API Response", extra={
        "request_id": request_id,
        "user_id": user_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost
    })

def log_error_with_context(e, request_id, user_id):
    logger.error(f"Error: {str(e)}", exc_info=True, extra={
        "request_id": request_id,
        "user_id": user_id
    })
