import nest_asyncio
nest_asyncio.apply()

from flask import Flask, render_template, request, session, redirect, url_for, flash
from app.components.retriver import create_qa_chain
from app.components.data_loader import process_and_store_pdfs
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import os
from app.common.logger import get_logger
from app.components.mongodata import insert_document
from app.config.config import *
import json

logger = get_logger(__name__)

load_dotenv()
HF_TOKEN = os.environ.get("HF_TOKEN")

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'data2'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

def allowed_file(filename):
    """Checks if a file has a PDF extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_uploaded_files():
    """Get list of uploaded files with their info"""
    files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if allowed_file(filename):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file_size = os.path.getsize(filepath)
                # Convert bytes to human readable format
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024*1024:
                    size_str = f"{file_size/1024:.1f} KB"
                else:
                    size_str = f"{file_size/(1024*1024):.1f} MB"
                
                files.append({
                    'filename': filename,
                    'size': size_str
                })
    return files

from markupsafe import Markup
def nl2br(value):
    return Markup(value.replace('\n', '\n'))

app.jinja_env.filters['nl2br'] = nl2br

@app.route("/", methods=["GET", "POST"])
def index():
    
    if "messages" not in session:
        session["messages"] = []

    if request.method == "POST":
        # Check if this is a chat message (not file upload)
        if 'prompt' in request.form:
            user_input = request.form.get("prompt")

            if user_input:
                messages = session["messages"]
                messages.append({"role": "user", "content": user_input})
                session["messages"] = messages

                try:
                    qa_chain = create_qa_chain()
                    if qa_chain is None:
                        raise Exception("QA chain could not be created (LLM or VectorStore issue)")
                    response = qa_chain.invoke({"query": user_input})
                    logger.info(f"Response from QA chain: {response}")
                    result = response.get("result", "No response")
                    source_docs = response.get("source_documents", [])
                    metadata = source_docs[0].metadata if source_docs and hasattr(source_docs[0], 'metadata') else {}
                    
                    # 1. Add the main assistant response to the chat
                    messages.append({"role": "assistant", "content": result})

                    # 2. Process metadata for DB and UI
                    if metadata:
                        # Prepare a clean copy for the database.
                        # We remove any existing '_id' to let MongoDB generate a new, proper ObjectId.
                        db_metadata = metadata.copy()
                        db_metadata.pop('_id', None) # Safely remove _id if it exists
                        insert_document(db_metadata)

                        # Format metadata into a user-friendly, JSON-serializable string for the session.
                        source = metadata.get('source', 'N/A')
                        page = metadata.get('page', 'N/A')
                        source_filename = os.path.basename(source) # Gets just the filename
                        
                        source_info_string = f"Source: {source_filename}, Page: {page}"
                        messages.append({"role": "metadata", "content": source_info_string})
                    
                    session["messages"] = messages
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    return render_template("index.html", 
                                         messages=session["messages"], 
                                         error=error_msg,
                                         uploaded_files=get_uploaded_files())
            
            return redirect(url_for("index"))
    
    return render_template("index.html", 
                         messages=session.get("messages", []),
                         uploaded_files=get_uploaded_files())

@app.route("/upload_document", methods=["POST"])
def upload_document():
    if request.method == 'POST':
        # Check for file upload submission
        if 'document' in request.files:
            files = request.files.getlist('document')
            pdf_paths = []
            
            if len(files) > 20:
                flash("You can only upload a maximum of 20 PDF files.", 'error')
                return redirect(url_for('index'))

            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    pdf_paths.append(filepath)
                elif file.filename != '':
                    flash(f"Invalid file type for: {file.filename}. Only PDF files are allowed.", 'error')
            
            # Process the uploaded files
            if pdf_paths:
                try:
                    flash("PDFs uploaded. Processing all files in the data folder...", 'success')
                    # Process all PDFs in the upload folder
                    process_and_store_pdfs()
                    flash("All PDFs in the data folder have been processed and are ready for chat!", 'success')
                except Exception as e:
                    flash(f"Error processing PDFs: {str(e)}", 'error')
            else:
                flash("No valid PDF files were uploaded.", 'error')
            
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.route("/remove_document", methods=["POST"])
def remove_document():
    if request.method == 'POST':
        filename = request.form.get('filename')
        if filename:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    flash(f"File '{filename}' has been removed successfully.", 'success')
                    # Reprocess remaining files after removal
                    try:
                        process_and_store_pdfs(app.config['UPLOAD_FOLDER'])
                        flash("Remaining files have been reprocessed.", 'success')
                    except Exception as e:
                        flash(f"Error reprocessing files: {str(e)}", 'error')
                else:
                    flash(f"File '{filename}' not found.", 'error')
            except Exception as e:
                flash(f"Error removing file: {str(e)}", 'error')
    
    return redirect(url_for('index'))

@app.route("/clear")
def clear():
    session.pop("messages", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)