from langchain_groq import ChatGroq
from app.config.config import *


from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)


def load_llm():
    try:
        logger.info("Loading Groq LLM...")                                         
        llm = ChatGroq(
            model="gemma2-9b-it",
            max_tokens=500,
            temperature=0.7,
            api_key=GROQ_API_KEY,
        )
        
        return llm
    except Exception as e:
        error_message = CustomException("Failed to load Groq llm",e)
        logger.error(error_message)