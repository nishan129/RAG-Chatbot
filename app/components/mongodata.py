import os
import sys
import pymongo # Make sure pymongo is imported
from app.configuration.mongo_db_connection import MongoDBClient
from app.config.config import DATABASE_NAME, COLLECTION_NAME
from app.common.custom_exception import CustomException
from app.common.logger import get_logger

logger = get_logger(__name__)

def insert_document(document):
    try:
        client_instance = MongoDBClient() 
        if client_instance.client:  
            
            collection = client_instance.database[COLLECTION_NAME]
            
            logger.info(f"Inserted document is: {document}")
            result = collection.insert_one(document)
            inserted_id = result.inserted_id
            
            logger.info(f"Inserted log entry with ID: {inserted_id}")
           
        else:
            logger.info("MongoDB is not connected.")
            raise CustomException("MongoDB client could not connect.", sys)
    except Exception as e:
        logger.error(f"Error inserting document: {e}", exc_info=True)
        raise CustomException(e, sys)

if __name__ == "__main__":
    document_to_insert = {
        'author': 'Nishant Borkar',
        'creationdate': '2025-08-01T10:24:56+00:00',
        'creator': 'Canva',
        'keywords': 'DAGu0fktpcI,BAGr0SufKqI,0',
        'moddate': '2025-08-01T10:24:55+00:00',
        'page': 0.0,
        'page_label': '1',
        'producer': 'Canva',
        'source': 'data2\\TalentScout-Hiring-Chatbot.pdf',
        'title': '💼 TalentScout-Hiring-Chatbot',
        'total_pages': 2.0
    }
    
    try:
        inserted_id = insert_document(document_to_insert)
        if inserted_id:
            logger.info(f"Document inserted successfully with ID: {inserted_id}.")
        else:
            logger.warning("Document insertion might have failed, no ID returned.")
    except CustomException as ce:
        logger.error(f"Failed to insert document: {ce}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")