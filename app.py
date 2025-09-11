import os
import pandas as pd
from flask import Flask, render_template, request, redirect, jsonify
import fitz  # PyMuPDF for PDFs
import docx  # python-docx for DOCX files
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import re
from fuzzywuzzy import fuzz

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

# Dynamically detect skill columns
skill_columns = [col for col in df.columns if col.startswith('skill')]

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

# Create skill synonyms and variations dictionary
def create_skill_synonyms():
    synonyms = {
        'javascript': ['js', 'javascript', 'ecmascript', 'es6', 'es2015', 'node.js', 'nodejs'],
        'python': ['python', 'py', 'python3', 'python2'],
        'react': ['react', 'reactjs', 'react.js', 'react native', 'reactnative'],
        'node.js': ['node', 'nodejs', 'node.js', 'express', 'expressjs'],
        'mongodb': ['mongo', 'mongodb', 'mongo db'],
        'postgresql': ['postgres', 'postgresql', 'psql'],
        'mysql': ['mysql', 'my sql'],
        'firebase': ['firebase', 'google firebase'],
        'aws': ['amazon web services', 'aws', 'amazon aws'],
        'docker': ['docker', 'containerization'],
        'kubernetes': ['kubernetes', 'k8s', 'kube'],
        'api': ['api', 'rest api', 'restful api', 'restful apis', 'web api'],
        'html': ['html', 'html5', 'hypertext markup language'],
        'css': ['css', 'css3', 'cascading style sheets'],
        'sql': ['sql', 'structured query language'],
        'git': ['git', 'github', 'version control'],
        'machine learning': ['ml', 'machine learning', 'artificial intelligence', 'ai'],
        'django': ['django', 'python django'],
        'flask': ['flask', 'python flask'],
        'spring boot': ['spring', 'spring boot', 'springboot'],
        'kotlin': ['kotlin', 'android kotlin'],
        'swift': ['swift', 'ios swift', 'apple swift'],
        'java': ['java', 'core java', 'java se', 'java ee'],
        'c++': ['cpp', 'c++', 'c plus plus'],
        'c#': ['csharp', 'c#', 'c sharp'],
        'php': ['php', 'php7', 'php8'],
        'ruby': ['ruby', 'ruby on rails', 'rails'],
        'flutter': ['flutter', 'dart flutter'],
        'dart': ['dart', 'flutter dart'],
        'tensorflow': ['tensorflow', 'tf', 'tensor flow'],
        'pytorch': ['pytorch', 'torch', 'py torch']
    }
    return synonyms

# Improved skill extraction function
def extract_skills_from_text(text):
    # Get all unique skills from dataset
    all_dataset_skills = set()
    for col in skill_columns:
        skills = df[col].dropna().unique()
        all_dataset_skills.update([skill.lower().strip() for skill in skills])
    
    # Convert to list for processing
    dataset_skills_list = list(all_dataset_skills)
    
    # Create skill synonyms
    skill_synonyms = create_skill_synonyms()
    
    # Clean and preprocess text
    text_clean = text.lower()
    text_clean = re.sub(r'[^\w\s\.\+\-#]', ' ', text_clean)  # Keep dots, plus, hash for tech terms
    
    extracted_skills = set()
    
    # Method 1: Direct matching with dataset skills
    for skill in dataset_skills_list:
        if skill in text_clean:
            extracted_skills.add(skill)
    
    # Method 2: Synonym-based matching
    for canonical_skill, variations in skill_synonyms.items():
        for variation in variations:
            if variation in text_clean:
                # Check if canonical skill exists in dataset
                if canonical_skill in dataset_skills_list:
                    extracted_skills.add(canonical_skill)
                # If not, check if any variation exists in dataset
                else:
                    for var in variations:
                        if var in dataset_skills_list:
                            extracted_skills.add(var)
                            break
    
    # Method 3: Fuzzy matching for close matches
    words = text_clean.split()
    for word in words:
        if len(word) > 2:  # Skip very short words
            for dataset_skill in dataset_skills_list:
                # Use fuzzy matching for skills with ratio > 85
                if fuzz.ratio(word, dataset_skill) > 85:
                    extracted_skills.add(dataset_skill)
    
    # Method 4: Pattern-based extraction for common tech terms
    tech_patterns = [
        r'\b(?:react|vue|angular)(?:js|\.js)?\b',
        r'\b(?:node|express)(?:js|\.js)?\b',
        r'\b(?:mongo|mysql|postgres|sqlite)(?:db)?\b',
        r'\b(?:python|java|javascript|kotlin|swift)\b',
        r'\b(?:html|css|php|ruby|dart)\d*\b',
        r'\b(?:api|rest|graphql|jwt|oauth)\b',
        r'\b(?:aws|azure|gcp|docker|kubernetes)\b'
    ]
    
    for pattern in tech_patterns:
        matches = re.findall(pattern, text_clean)
        for match in matches:
            # Check if match or its variations exist in dataset
            match_clean = match.lower().strip()
            if match_clean in dataset_skills_list:
                extracted_skills.add(match_clean)
    
    # Method 5: spaCy NER for additional entity recognition
    doc = nlp(text)
    for ent in doc.ents:
        ent_text = ent.text.lower().strip()
        if ent_text in dataset_skills_list:
            extracted_skills.add(ent_text)
    
    # Remove empty strings and return unique skills
    final_skills = [skill for skill in extracted_skills if skill and skill.strip()]
    return list(set(final_skills))

# Get project recommendations based on user's skills
def get_project_recommendations(user_skills):
    recommendations = []
    user_skills = [skill.lower().strip() for skill in user_skills if skill.strip()]

    # Create combined skills column dynamically
    df['combined_skills'] = df[skill_columns].fillna('').agg(' '.join, axis=1).str.lower()

    tfidf = TfidfVectorizer()
    skill_corpus = [' '.join(user_skills)] + df['combined_skills'].tolist()
    tfidf_matrix = tfidf.fit_transform(skill_corpus)

    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    for idx, similarity in enumerate(cosine_similarities):
        if similarity > 0:
            project = df.iloc[idx]
            project_skills = []
            
            # Collect all non-null skills from skill columns
            for col in skill_columns:
                skill = project[col]
                if pd.notna(skill) and skill.strip():
                    project_skills.append(skill.lower().strip())

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

    return sorted_recommendations

# Home route
@app.route('/')
def index():
    # Dynamically get all unique skills from all skill columns
    all_skills = set()
    for col in skill_columns:
        skills = df[col].dropna().unique()
        all_skills.update(skills)
    
    skills_list = sorted(list(all_skills))
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