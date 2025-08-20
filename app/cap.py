from flask import Flask, render_template, request, session, redirect, url_for, flash
from app.components.retriver import create_qa_chain
from app.components.data_loader import process_and_store_pdfs
from dotenv import load_dotenv
import os
from werkzeug.utils import secure_filename
from markupsafe import Markup

load_dotenv()


app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure upload folder and allowed file extensions
UPLOAD_FOLDER = 'data2'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

def allowed_file(filename):
    """Checks if a file has a PDF extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def nl2br(value):
    """A custom Jinja2 filter to replace newlines with HTML breaks."""
    return Markup(value.replace('\n', '<br>'))

app.jinja_env.filters['nl2br'] = nl2br


@app.route('/', methods=['GET', 'POST'])
def index():
    if "messages" not in session:
        session["messages"] = []
    
    if request.method == 'POST':
        # Check for file upload submission first
        if 'pdf-upload' in request.files:
            files = request.files.getlist('pdf-upload')
            pdf_paths = []
            
            if len(files) > 20:
                flash("You can only upload a maximum of 20 PDF files.", 'error')
                return redirect(url_for('index'))

            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    pdf_paths.append(filepath)
                else:
                    flash(f"Invalid file type for: {file.filename}. Only PDF files are allowed.", 'error')
            
            # The key step: If files were uploaded, process the entire `data` folder.
            # You can either pass the newly uploaded files or just trigger a process
            # that scans the whole folder. The prompt asks for it to "detect the data folder".
            if pdf_paths:
                try:
                    # You don't need to pass the list, just call a function that processes the folder
                    flash("PDFs uploaded. Processing all files in the data folder...", 'success')
                    # process_and_store_pdfs() should be modified to scan the UPLOAD_FOLDER
                    process_and_store_pdfs(app.config['UPLOAD_FOLDER'])
                    flash("All PDFs in the data folder have been processed and are ready for chat!", 'success')
                except Exception as e:
                    flash(f"Error processing PDFs: {str(e)}", 'error')
            
            return redirect(url_for('index'))
        
        # Then, check for chat prompt submission
        user_input = request.form.get('prompt')
        if user_input:
            # Your existing chat logic
            messages = session.get("messages", [])
            messages.append({"role": "user", "content": user_input})
            session["messages"] = messages
            
            try:
                qa_chain = create_qa_chain()
                response = qa_chain.invoke({"query": user_input})
                result = response.get('result', 'No response')
                
                messages.append({"role": "assistant", "content": result})
                session["messages"] = messages
            
            except Exception as e:
                error_message = f"Error: {str(e)}"
                flash(error_message, 'error')
            
            return redirect(url_for('index'))
    
    return render_template("index.html", messages=session.get('messages', []))

@app.route('/clear')
def clear():
    session.pop('messages', None)
    # Note: Clearing the chat doesn't delete the processed PDFs on the server.
    flash("Chat history cleared!", 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)