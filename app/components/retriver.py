from langchain.chains import retrieval_qa, RetrievalQA
from langchain_core.prompts import PromptTemplate

from app.components.llm import load_llm
from app.components.vector_store import load_vector_store

from app.config.config import *

from app.common.logger import get_logger
from app.common.custom_exception import CustomException

import os

logger = get_logger(__name__)

CUSTOM_PROMPT_TEMPLATE =  """ Answer the following question in brief using only the information provided in the context 

Context: {context}

Question: {question}

Answer:
"""

def set_custom_prompt():
    return PromptTemplate(template=CUSTOM_PROMPT_TEMPLATE, input_variables=['context', 'question'])


def create_qa_chain():
    try:
        logger.info("Loading vector store for context")
        db = load_vector_store()
        
        if db is None:
            raise CustomException("Vector store is not present or empty")
        
        llm = load_llm()
        
        if llm is None:
            raise CustomException("LLM is not loaded properly")
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": set_custom_prompt()
            }
        )
        
        logger.info("QA chain created successfully")
        return qa_chain
    
    except Exception as e:
        error_message = CustomException("Failed to create QA chain", e)
        logger.error(error_message)