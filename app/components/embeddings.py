from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.common.logger import get_logger
from app.common.custom_exception import CustomException
from dotenv import load_dotenv

# Load environment variables from .env file (e.g., GOOGLE_API_KEY)
load_dotenv()

logger = get_logger(__name__)

def get_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    
    logger.info("Initializing GoogleGenerativeAIEmbeddings model...")
    try:
      
        embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        logger.info("GoogleGenerativeAIEmbeddings model initialized successfully.")
        return embeddings_model
        
    except Exception as e:
     
        logger.error(f"Failed to initialize embedding model: {e}")
        
       
        raise CustomException("Error occurred while loading embedding model") from e