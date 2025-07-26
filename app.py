import os
import pandas as pd
from flask import Flask, render_template, request, redirect,jsonify
import fitz  # PyMuPDF for PDFs
import docx  # python-docx for DOCX files
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy

import os
import requests
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

HF_API_URL = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json"
}

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        messages = data.get("messages", [])

        # Convert messages to OpenRouter format
        formatted_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

        payload = {
            "model": "openai/gpt-3.5-turbo",  
            "messages": formatted_messages,
            "max_tokens": 300
        }

        response = requests.post(HF_API_URL, headers=headers, json=payload)
        result = response.json()

        return jsonify({"reply": result['choices'][0]['message']['content']})

    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500

# Load spaCy English NLP model
nlp = spacy.load("en_core_web_sm")

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load project dataset
dataset_path = os.path.join(UPLOAD_FOLDER, 'project_dataset.csv')
df = pd.read_csv(dataset_path)

# Define dataset skill columns
skills_columns = ['skill1', 'skill2', 'skill3', 'skill4', 'skill5', 'skill6']


# Check if uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Extract text from resume (PDF, DOCX, or TXT)
def extract_text_from_resume(file_path):
    text = ""

    if file_path.endswith('.pdf'):
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()

    elif file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    elif file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

    return text

def get_initial_prompt(project_name, level, matching_skills, missing_skills):
    base = (
        f"You are an expert AI project mentor. The user selected a project titled '{project_name}' "
        f"and chose the '{level}' difficulty level.\n"
    )
    skills = f"Their matching skills are: {', '.join(matching_skills)}\nMissing skills are: {', '.join(missing_skills)}\n"

    if level == 'Beginner':
        prompt = base + skills + (
            "Provide a beginner-friendly explanation of this project. Explain:\n"
            "- What the project is about in simple terms\n"
            "- Why it is useful or interesting\n"
            "- Easy tools or technologies to use (beginner-level only)\n"
            "- Simple step-by-step guide to build it\n"
            "- Extra tips to help a beginner understand and complete it\n"
            "Avoid complex terms, frameworks, or deep logic."
        )

    elif level == 'Intermediate':
        prompt = base + skills + (
            "Describe this project to someone with basic development knowledge. Include:\n"
            "- A moderately detailed project description\n"
            "- Suggested tech stack (frontend, backend, database)\n"
            "- Key implementation steps and flow\n"
            "- Typical challenges and how to solve them\n"
            "- Basic tips on testing or deployment\n"
            "Avoid overly simple or enterprise-level content."
        )

    elif level == 'Advanced':
        prompt = base + skills + (
            "Provide an advanced and complete technical explanation of this project. Cover:\n"
            "- Full system architecture (frontend, backend, APIs, database)\n"
            "- Security considerations\n"
            "- CI/CD and deployment process (e.g., Docker, cloud platforms)\n"
            "- Performance optimization, testing strategies\n"
            "- How to scale, maintain, and make it production-ready\n"
            "- Optional: ideas for extending the project in real-world scenarios\n"
            "Use technical language assuming the user has solid development experience."
        )

    return prompt


# Extract skills from text using spaCy
def extract_skills_from_text(text):
    doc = nlp(text)
    all_skills = pd.concat([df[col] for col in skills_columns]).dropna().unique().tolist()
    all_skills_lower = [skill.lower() for skill in all_skills]

    extracted = [ent.text.lower() for ent in doc.ents if ent.text.lower() in all_skills_lower]
    return list(set(extracted))


# Get project recommendations based on user's skills
def get_project_recommendations(user_skills):
    recommendations = []
    user_skills = [skill.lower().strip() for skill in user_skills]

    df['combined_skills'] = df[skills_columns].fillna('').agg(' '.join, axis=1).str.lower()

    tfidf = TfidfVectorizer()
    skill_corpus = [' '.join(user_skills)] + df['combined_skills'].tolist()
    tfidf_matrix = tfidf.fit_transform(skill_corpus)

    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    for idx, similarity in enumerate(cosine_similarities):
        if similarity > 0:
            project = df.iloc[idx]
            project_skills = project[skills_columns].fillna('').str.lower().tolist()

            matching = [skill for skill in user_skills if skill in project_skills]
            missing = [skill for skill in project_skills if skill and skill not in user_skills]

            recommendations.append({
                'project_name': project['Project Name'],
                'matching_count': len(matching),
                'matching_skills': matching,
                'missing_skills': missing,
                'similarity_score': similarity
            })

    sorted_recommendations = sorted(
        recommendations,
       key=lambda x: (-int(x['matching_count'] > 0), -x['matching_count'], -x['similarity_score'])
    )

    return sorted_recommendations[:]


# Home route
@app.route('/')
def index():
    skills_list = pd.concat([df[col] for col in skills_columns]).dropna().unique().tolist()
    return render_template('index.html', all_skills=skills_list)


# Resume upload route
@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return 'No file part', 400

    file = request.files['resume']
    if file.filename == '':
        return 'No selected file', 400

    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        text = extract_text_from_resume(filepath)
        skills = extract_skills_from_text(text)

        if not skills:
            return "No skills extracted. Try another resume or format.", 400

        skills_string = ','.join(skills)
        return redirect(f"/submit_skills?skills={skills_string}")

    return 'Unsupported file format.', 400


# Project recommendation based on skills
@app.route('/submit_skills', methods=['GET', 'POST'])
def submit_skills():
    try:
        if request.method == 'POST':
            skills_string = request.form.get('skills', '')
        else:
            skills_string = request.args.get('skills', '')

        if not skills_string:
            return redirect('/')

        # Pagination
        page = int(request.args.get('page', 1))
        per_page = 10

        skills = [s.strip() for s in skills_string.split(',') if s.strip()]
        recommendations = get_project_recommendations(skills)

        total = len(recommendations)
        paginated = recommendations[(page - 1) * per_page : page * per_page]

        return render_template(
            'recommendations.html',
            top_projects=paginated,
            all_projects=recommendations,  
            skills=skills,
            skills_string=skills_string
        )
    except Exception as e:
        print("Error:", e)
        return "An error occurred. Please try again.", 500



# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
