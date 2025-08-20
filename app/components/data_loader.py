import os

from app.components.vector_store import save_vector_store
from app.components.pdf_loader import load_pdf_files, create_text_chunks

from app.config.config import * 
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

def process_and_store_pdfs():
    try:
        logger.info("Making the vectorestore....")
        
        documents = load_pdf_files()
        
        text_chunks = create_text_chunks(documents)
        
        save_vector_store(text_chunks)
        
        logger.info("Vectorstore created successfully ..")
        
    except Exception as e:
        error_message = CustomException("Failed to create vectorstore")
        logger.error(str(error_message))


if __name__ == "__main__":
    process_and_store_pdfs()