# AI Project Recommender

## Overview
AI Project Recommender is a Flask web application that helps users discover suitable software projects based on their skills. Users can upload their resume (PDF, DOCX, or TXT), and the app extracts relevant skills using NLP. It then recommends projects from a dataset, matching the user's skills and providing beginner, intermediate, or advanced explanations for each project.

## Features
- Resume upload and skill extraction (PDF, DOCX, TXT)
- Skill-based project recommendations using TF-IDF and cosine similarity
- Explanations tailored to user-selected difficulty level (Beginner, Intermediate, Advanced)
- Interactive web interface with pagination
- Uses spaCy for NLP and scikit-learn for similarity calculations

## Tech Stack
- Python (Flask, pandas, scikit-learn, spaCy, python-docx, PyMuPDF)
- HTML/CSS/JavaScript (templates and static files)
- OpenRouter API for chat-based explanations

## File Structure
- app.py: Main Flask application
- requirements.txt: Python dependencies
- static: JS and CSS files
- templates: HTML templates
- project_dataset.csv: Project dataset

## How to Run
1. Install dependencies:  
   `pip install -r requirements.txt`
2. Download spaCy model:  
   `python -m spacy download en_core_web_sm`
3. Set your OpenRouter API key in a .env file.
4. Run the app:  
   `python app.py`