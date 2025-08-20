from pinecone import Pinecone, ServerlessSpec
import os
from app.components.embeddings import get_embeddings_model

# Assuming langchain_pinecone is installed for Pinecone integration with Langchain
# If you don't have it, install it: pip install langchain-pinecone
from langchain_pinecone import Pinecone as LangchainPinecone
from langchain_core.documents import Document

from app.common.logger import get_logger
from app.common.custom_exception import CustomException

from dotenv import load_dotenv

load_dotenv()


PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
PINECONE_API_ENV = os.environ.get('PINECONE_API_ENV')
PINECONE_INDEX_NAME = os.environ.get('PINECONE_INDEX_NAME', 'my-knowledge-index')


logger = get_logger(__name__)

pc = None
try:
    if PINECONE_API_KEY :
       
        pc = Pinecone(api_key=PINECONE_API_KEY)
        logger.info("Pinecone client initialized successfully.")
    else:
        logger.error("PINECONE_API_KEY or PINECONE_API_ENV not found in environment variables. Please set them.")
except Exception as e:
    logger.error(f"Failed to initialize Pinecone client: {e}")
    pc = None 

def load_vector_store():
    
    try:
 
        if pc is None:
            raise CustomException("Pinecone client is not initialized. Cannot load vector store.")

        embedding_model = get_embeddings_model()
        

        existing_indexes_response = pc.list_indexes()
        index_names = [idx.name for idx in existing_indexes_response.indexes]

        if PINECONE_INDEX_NAME in index_names:
            logger.info(f"Connecting to existing Pinecone index: '{PINECONE_INDEX_NAME}'")
            
            vector_store = LangchainPinecone.from_existing_index(
                index_name=PINECONE_INDEX_NAME, 
                embedding=embedding_model,
            )
            logger.info("Vector store loaded from Pinecone successfully.")
            return vector_store
        else:
            logger.warning(f"Pinecone index '{PINECONE_INDEX_NAME}' not found. A new one will be created when data is saved.")
            return None 
            
    except Exception as e:
        error_message = CustomException(f"Error occurred while loading vector store from Pinecone: {e}", e)
        logger.error(str(error_message))
        return None
    
def save_vector_store(text_chunks: list[Document]):
    try:
        if pc is None:
            raise CustomException("Pinecone client is not initialized. Cannot save vector store.")

        if not text_chunks:
            raise CustomException("No text chunks provided to save in vector store.")
        
        logger.info("Preparing to save new vector store data to Pinecone...")

        embedding_model = get_embeddings_model()
        
        
        try:
            
            sample_embedding = embedding_model.embed_query("A test sentence for dimension calculation.")
            dimension = len(sample_embedding)
        except Exception as embed_err:
            raise CustomException(f"Failed to get embedding dimension from the model: {embed_err}. Ensure the embedding model is functional.")

        
        index_names = pc.list_indexes().names() 
        
        if PINECONE_INDEX_NAME not in index_names:
            logger.info(f"Pinecone index '{PINECONE_INDEX_NAME}' does not exist. Creating a new one with dimension={dimension} and metric='cosine'.")
            
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=dimension,
                metric='cosine', 
                spec=ServerlessSpec(
                    cloud='aws', 
                    region='us-east-1'
                )
            )
            logger.info(f"Pinecone index '{PINECONE_INDEX_NAME}' created successfully.")
        else:
            logger.info(f"Pinecone index '{PINECONE_INDEX_NAME}' already exists. Appending new data (upserting).")
        
        
        db = LangchainPinecone.from_documents(
            text_chunks, 
            embedding_model, 
            index_name=PINECONE_INDEX_NAME,
            # environment=PINECONE_API_ENV 
        )
        
        logger.info("Vector store data saved/upserted to Pinecone successfully.")
        
        return db
    except Exception as e:
        error_message = CustomException(f"Failed to create or save new vector store in Pinecone: {e}", e)
        logger.error(str(error_message))
        return None
