"""
Smart Resume AI - Main Application
"""
from jobs.job_search import render_job_search
from datetime import datetime
from ui_components import (
    apply_modern_styles, hero_section, feature_card, page_header
)

import io
import base64
from streamlit_lottie import st_lottie
import requests

from config.courses import COURSES_BY_CATEGORY, RESUME_VIDEOS, INTERVIEW_VIDEOS, get_courses_for_role, get_category_for_role
from config.job_roles import JOB_ROLES
from config.database import (
    get_database_connection, save_resume_data, save_analysis_data,
    init_database, verify_admin, log_admin_action, save_ai_analysis_data
)
from utils.ai_resume_analyzer import AIResumeAnalyzer
from utils.resume_builder import ResumeBuilder
from utils.resume_analyzer import ResumeAnalyzer
import traceback
import pandas as pd
import streamlit as st
import datetime

# Set page config at the very beginning
st.set_page_config(
    page_title="Smart Resume AI",
    page_icon="🚀",
    layout="wide"
)


class ResumeApp:
    def __init__(self):
        """Initialize the application"""
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {
                'personal_info': {
                    'full_name': '',
                    'email': '',
                    'phone': '',
                    'location': '',
                    'linkedin': '',
                    'portfolio': ''
                },
                'summary': '',
                'experiences': [],
                'education': [],
                'projects': [],
                'skills_categories': {
                    'technical': [],
                    'soft': [],
                    'languages': [],
                    'tools': []
                }
            }

        # Initialize navigation state
        if 'page' not in st.session_state:
            st.session_state.page = 'home'

        # Initialize admin state
        if 'is_admin' not in st.session_state:
            st.session_state.is_admin = False

        self.pages = {
            "🏠 HOME": self.render_home,
            "🔍 RESUME ANALYZER": self.render_analyzer,
            "📝 RESUME BUILDER": self.render_builder,
           
            "🎯 JOB SEARCH": self.render_job_search,
            "ℹ️ ABOUT": self.render_about
        }

        
        

        self.analyzer = ResumeAnalyzer()
        self.ai_analyzer = AIResumeAnalyzer()
        self.builder = ResumeBuilder()
        self.job_roles = JOB_ROLES

        # Initialize session state
        if 'user_id' not in st.session_state:
            st.session_state.user_id = 'default_user'
        if 'selected_role' not in st.session_state:
            st.session_state.selected_role = None

        # Initialize database
        init_database()

        # Load external CSS
        with open('style/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

        # Load Google Fonts
        st.markdown("""
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        """, unsafe_allow_html=True)

        if 'resume_data' not in st.session_state:
            st.session_state.resume_data = []
        if 'ai_analysis_stats' not in st.session_state:
            st.session_state.ai_analysis_stats = {
                'score_distribution': {},
                'total_analyses': 0,
                'average_score': 0
            }

    def load_lottie_url(self, url: str):
        """Load Lottie animation from URL"""
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()

    def apply_global_styles(self):
        st.markdown("""
        <style>
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #1a1a1a;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: #4CAF50;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #45a049;
        }

        /* Global Styles */
        .main-header {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(255,255,255,0.1) 100%);
            z-index: 1;
        }

        .main-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 600;
            margin: 0;
            position: relative;
            z-index: 2;
        }

        /* Template Card Styles */
        .template-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
            padding: 1rem;
        }

        .template-card {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .template-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border-color: #4CAF50;
        }

        .template-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(76,175,80,0.1) 100%);
            z-index: 1;
        }

        .template-icon {
            font-size: 3rem;
            color: #4CAF50;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
        }

        .template-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1rem;
            position: relative;
            z-index: 2;
        }

        .template-description {
            color: #aaa;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
            line-height: 1.6;
        }

        /* Feature List Styles */
        .feature-list {
            list-style: none;
            padding: 0;
            margin: 1.5rem 0;
            position: relative;
            z-index: 2;
        }

        .feature-item {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            color: #ddd;
            font-size: 0.95rem;
        }

        .feature-icon {
            color: #4CAF50;
            margin-right: 0.8rem;
            font-size: 1.1rem;
        }

        /* Button Styles */
        .action-button {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            border: none;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            text-align: center;
            position: relative;
            overflow: hidden;
            z-index: 2;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(76,175,80,0.3);
        }

        .action-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%);
            transition: all 0.6s ease;
        }

        .action-button:hover::before {
            left: 100%;
        }

        /* Form Section Styles */
        .form-section {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .form-section-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1.5rem;
            padding-bottom: 0.8rem;
            border-bottom: 2px solid #4CAF50;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-label {
            color: #ddd;
            font-weight: 500;
            margin-bottom: 0.8rem;
            display: block;
        }

        .form-input {
            width: 100%;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(30, 30, 30, 0.9);
            color: white;
            transition: all 0.3s ease;
        }

        .form-input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76,175,80,0.2);
            outline: none;
        }

        /* Skill Tags */
        .skill-tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem;
            margin-top: 1rem;
        }

        .skill-tag {
            background: rgba(76,175,80,0.1);
            color: #4CAF50;
            padding: 0.6rem 1.2rem;
            border-radius: 50px;
            border: 1px solid #4CAF50;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .skill-tag:hover {
            background: #4CAF50;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76,175,80,0.2);
        }

        /* Progress Circle */
        .progress-container {
            position: relative;
            width: 150px;
            height: 150px;
            margin: 2rem auto;
        }

        .progress-circle {
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }

        .progress-circle circle {
            fill: none;
            stroke-width: 8;
            stroke-linecap: round;
            stroke: #4CAF50;
            transform-origin: 50% 50%;
            transition: all 0.3s ease;
        }

        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.5rem;
            font-weight: 600;
            color: white;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .feature-card {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Animations */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .animate-slide-in {
            animation: slideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .template-container {
                grid-template-columns: 1fr;
            }

            .main-header {
                padding: 1.5rem;
            }

            .main-header h1 {
                font-size: 2rem;
            }

            .template-card {
                padding: 1.5rem;
            }

            .action-button {
                padding: 0.8rem 1.6rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
    def add_footer(self):
        """Add a footer to all pages"""
        st.markdown("<hr style='margin-top: 50px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
           
            st.markdown("""
            
            """, unsafe_allow_html=True)
            
           
    def load_image(self, image_name):
        """Load image from static directory"""
        try:
            image_path = f"c:/Users/shree/Downloads/smart-resume-ai/{image_name}"
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            encoded = base64.b64encode(image_bytes).decode()
            return f"data:image/png;base64,{encoded}"
        except Exception as e:
            print(f"Error loading image {image_name}: {e}")
            return None


    def render_empty_state(self, icon, message):
        """Render an empty state with icon and message"""
        return f"""
            <div style='text-align: center; padding: 2rem; color: #666;'>
                <i class='{icon}' style='font-size: 2rem; margin-bottom: 1rem; color: #00bfa5;'></i>
                <p style='margin: 0;'>{message}</p>
            </div>
        """

    def analyze_resume(self, resume_text):
        """Analyze resume and store results"""
        analytics = self.analyzer.analyze_resume(resume_text)
        st.session_state.analytics_data = analytics
        return analytics

    def handle_resume_upload(self):
        """Handle resume upload and analysis"""
        uploaded_file = st.file_uploader(
            "Upload your resume", type=['pdf', 'docx'])

        if uploaded_file is not None:
            try:
                # Extract text from resume
                if uploaded_file.type == "application/pdf":
                    resume_text = extract_text_from_pdf(uploaded_file) # type: ignore
                else:
                    resume_text = extract_text_from_docx(uploaded_file) # type: ignore

                
                # Analyze resume
                analytics = self.analyze_resume(resume_text)

                return True
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")
                return False
        return False

    def render_builder(self):
        st.title("Resume Builder 📝")
        st.write("Create your professional resume")

        # Template selection
        template_options = ["Modern", "Professional", "Minimal", "Creative"]
        selected_template = st.selectbox(
    "Select Resume Template", template_options)
        st.success(f"🎨 Currently using: {selected_template} Template")

        # Personal Information
        st.subheader("Personal Information")

        col1, col2 = st.columns(2)
        with col1:
            # Get existing values from session state
            existing_name = st.session_state.form_data['personal_info']['full_name']
            existing_email = st.session_state.form_data['personal_info']['email']
            existing_phone = st.session_state.form_data['personal_info']['phone']

            # Input fields with existing values
            full_name = st.text_input("Full Name", value=existing_name)
            email = st.text_input(
    "Email",
    value=existing_email,
     key="email_input")
            phone = st.text_input("Phone", value=existing_phone)

            # Immediately update session state after email input
            if 'email_input' in st.session_state:
                st.session_state.form_data['personal_info']['email'] = st.session_state.email_input

        with col2:
            # Get existing values from session state
            existing_location = st.session_state.form_data['personal_info']['location']
            existing_linkedin = st.session_state.form_data['personal_info']['linkedin']
            existing_portfolio = st.session_state.form_data['personal_info']['portfolio']

            # Input fields with existing values
            location = st.text_input("Location", value=existing_location)
            linkedin = st.text_input("LinkedIn URL", value=existing_linkedin)
            portfolio = st.text_input(
    "Portfolio Website", value=existing_portfolio)

        # Update personal info in session state
        st.session_state.form_data['personal_info'] = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'location': location,
            'linkedin': linkedin,
            'portfolio': portfolio
        }

        # Professional Summary
        st.subheader("Professional Summary")
        summary = st.text_area("Professional Summary", value=st.session_state.form_data.get('summary', ''), height=150,
                             help="Write a brief summary highlighting your key skills and experience")

        # Experience Section
        st.subheader("Work Experience")
        if 'experiences' not in st.session_state.form_data:
            st.session_state.form_data['experiences'] = []

        if st.button("Add Experience"):
            st.session_state.form_data['experiences'].append({
                'company': '',
                'position': '',
                'start_date': '',
                'end_date': '',
                'description': '',
                'responsibilities': [],
                'achievements': []
            })

        for idx, exp in enumerate(st.session_state.form_data['experiences']):
            with st.expander(f"Experience {idx + 1}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    exp['company'] = st.text_input(
    "Company Name",
    key=f"company_{idx}",
    value=exp.get(
        'company',
         ''))
                    exp['position'] = st.text_input(
    "Position", key=f"position_{idx}", value=exp.get(
        'position', ''))
                with col2:
                    exp['start_date'] = st.text_input(
    "Start Date", key=f"start_date_{idx}", value=exp.get(
        'start_date', ''))
                    exp['end_date'] = st.text_input(
    "End Date", key=f"end_date_{idx}", value=exp.get(
        'end_date', ''))

                exp['description'] = st.text_area("Role Overview", key=f"desc_{idx}",
                                                value=exp.get(
                                                    'description', ''),
                                                help="Brief overview of your role and impact")

                # Responsibilities
                st.markdown("##### Key Responsibilities")
                resp_text = st.text_area("Enter responsibilities (one per line)",
                                       key=f"resp_{idx}",
                                       value='\n'.join(
                                           exp.get('responsibilities', [])),
                                       height=100,
                                       help="List your main responsibilities, one per line")
                exp['responsibilities'] = [r.strip()
                                                   for r in resp_text.split('\n') if r.strip()]

                # Achievements
                st.markdown("##### Key Achievements")
                achv_text = st.text_area("Enter achievements (one per line)",
                                       key=f"achv_{idx}",
                                       value='\n'.join(
                                           exp.get('achievements', [])),
                                       height=100,
                                       help="List your notable achievements, one per line")
                exp['achievements'] = [a.strip()
                                               for a in achv_text.split('\n') if a.strip()]

                if st.button("Remove Experience", key=f"remove_exp_{idx}"):
                    st.session_state.form_data['experiences'].pop(idx)
                    st.rerun()

        # Projects Section
        st.subheader("Projects")
        if 'projects' not in st.session_state.form_data:
            st.session_state.form_data['projects'] = []

        if st.button("Add Project"):
            st.session_state.form_data['projects'].append({
                'name': '',
                'technologies': '',
                'description': '',
                'responsibilities': [],
                'achievements': [],
                'link': ''
            })

        for idx, proj in enumerate(st.session_state.form_data['projects']):
            with st.expander(f"Project {idx + 1}", expanded=True):
                proj['name'] = st.text_input(
    "Project Name",
    key=f"proj_name_{idx}",
    value=proj.get(
        'name',
         ''))
                proj['technologies'] = st.text_input("Technologies Used", key=f"proj_tech_{idx}",
                                                   value=proj.get(
                                                       'technologies', ''),
                                                   help="List the main technologies, frameworks, and tools used")

                proj['description'] = st.text_area("Project Overview", key=f"proj_desc_{idx}",
                                                 value=proj.get(
                                                     'description', ''),
                                                 help="Brief overview of the project and its goals")

                # Project Responsibilities
                st.markdown("##### Key Responsibilities")
                proj_resp_text = st.text_area("Enter responsibilities (one per line)",
                                            key=f"proj_resp_{idx}",
                                            value='\n'.join(
                                                proj.get('responsibilities', [])),
                                            height=100,
                                            help="List your main responsibilities in the project")
                proj['responsibilities'] = [r.strip()
                                                    for r in proj_resp_text.split('\n') if r.strip()]

                # Project Achievements
                st.markdown("##### Key Achievements")
                proj_achv_text = st.text_area("Enter achievements (one per line)",
                                            key=f"proj_achv_{idx}",
                                            value='\n'.join(
                                                proj.get('achievements', [])),
                                            height=100,
                                            help="List the project's key achievements and your contributions")
                proj['achievements'] = [a.strip()
                                                for a in proj_achv_text.split('\n') if a.strip()]

                proj['link'] = st.text_input("Project Link (optional)", key=f"proj_link_{idx}",
                                           value=proj.get('link', ''),
                                           help="Link to the project repository, demo, or documentation")

                if st.button("Remove Project", key=f"remove_proj_{idx}"):
                    st.session_state.form_data['projects'].pop(idx)
                    st.rerun()

        # Education Section
        st.subheader("Education")
        if 'education' not in st.session_state.form_data:
            st.session_state.form_data['education'] = []

        if st.button("Add Education"):
            st.session_state.form_data['education'].append({
                'school': '',
                'degree': '',
                'field': '',
                'graduation_date': '',
                'gpa': '',
                'achievements': []
            })

        for idx, edu in enumerate(st.session_state.form_data['education']):
            with st.expander(f"Education {idx + 1}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    edu['school'] = st.text_input(
    "School/University",
    key=f"school_{idx}",
    value=edu.get(
        'school',
         ''))
                    edu['degree'] = st.text_input(
    "Degree", key=f"degree_{idx}", value=edu.get(
        'degree', ''))
                with col2:
                    edu['field'] = st.text_input(
    "Field of Study",
    key=f"field_{idx}",
    value=edu.get(
        'field',
         ''))
                    edu['graduation_date'] = st.text_input("Graduation Date", key=f"grad_date_{idx}",
                                                         value=edu.get('graduation_date', ''))

                edu['gpa'] = st.text_input(
    "GPA (optional)",
    key=f"gpa_{idx}",
    value=edu.get(
        'gpa',
         ''))

                # Educational Achievements
                st.markdown("##### Achievements & Activities")
                edu_achv_text = st.text_area("Enter achievements (one per line)",
                                           key=f"edu_achv_{idx}",
                                           value='\n'.join(
                                               edu.get('achievements', [])),
                                           height=100,
                                           help="List academic achievements, relevant coursework, or activities")
                edu['achievements'] = [a.strip()
                                               for a in edu_achv_text.split('\n') if a.strip()]

                if st.button("Remove Education", key=f"remove_edu_{idx}"):
                    st.session_state.form_data['education'].pop(idx)
                    st.rerun()

        # Skills Section
        st.subheader("Skills")
        if 'skills_categories' not in st.session_state.form_data:
            st.session_state.form_data['skills_categories'] = {
                'technical': [],
                'soft': [],
                'languages': [],
                'tools': []
            }

        col1, col2 = st.columns(2)
        with col1:
            tech_skills = st.text_area("Technical Skills (one per line)",
                                     value='\n'.join(
    st.session_state.form_data['skills_categories']['technical']),
                                     height=150,
                                     help="Programming languages, frameworks, databases, etc.")
            st.session_state.form_data['skills_categories']['technical'] = [
                s.strip() for s in tech_skills.split('\n') if s.strip()]

            soft_skills = st.text_area("Soft Skills (one per line)",
                                     value='\n'.join(
    st.session_state.form_data['skills_categories']['soft']),
                                     height=150,
                                     help="Leadership, communication, problem-solving, etc.")
            st.session_state.form_data['skills_categories']['soft'] = [
                s.strip() for s in soft_skills.split('\n') if s.strip()]

        with col2:
            languages = st.text_area("Languages (one per line)",
                                   value='\n'.join(
    st.session_state.form_data['skills_categories']['languages']),
                                   height=150,
                                   help="Programming or human languages with proficiency level")
            st.session_state.form_data['skills_categories']['languages'] = [
                l.strip() for l in languages.split('\n') if l.strip()]

            tools = st.text_area("Tools & Technologies (one per line)",
                               value='\n'.join(
    st.session_state.form_data['skills_categories']['tools']),
                               height=150,
                               help="Development tools, software, platforms, etc.")
            st.session_state.form_data['skills_categories']['tools'] = [
                t.strip() for t in tools.split('\n') if t.strip()]

        # Update form data in session state
        st.session_state.form_data.update({
            'summary': summary
        })

        # Generate Resume button
        if st.button("Generate Resume 📄", type="primary"):
            print("Validating form data...")
            print(f"Session state form data: {st.session_state.form_data}")
            print(
    f"Email input value: {
        st.session_state.get(
            'email_input',
             '')}")

            # Get the current values from form
            current_name = st.session_state.form_data['personal_info']['full_name'].strip(
            )
            current_email = st.session_state.email_input if 'email_input' in st.session_state else ''

            print(f"Current name: {current_name}")
            print(f"Current email: {current_email}")

            # Validate required fields
            if not current_name:
                st.error("⚠️ Please enter your full name.")
                return

            if not current_email:
                st.error("⚠️ Please enter your email address.")
                return

            # Update email in form data one final time
            st.session_state.form_data['personal_info']['email'] = current_email

            try:
                print("Preparing resume data...")
                # Prepare resume data with current form values
                resume_data = {
                    "personal_info": st.session_state.form_data['personal_info'],
                    "summary": st.session_state.form_data.get('summary', '').strip(),
                    "experience": st.session_state.form_data.get('experiences', []),
                    "education": st.session_state.form_data.get('education', []),
                    "projects": st.session_state.form_data.get('projects', []),
                    "skills": st.session_state.form_data.get('skills_categories', {
                        'technical': [],
                        'soft': [],
                        'languages': [],
                        'tools': []
                    }),
                    "template": selected_template
                }

                print(f"Resume data prepared: {resume_data}")

                try:
                    # Generate resume
                    resume_buffer = self.builder.generate_resume(resume_data)
                    if resume_buffer:
                        try:
                            # Save resume data to database
                            save_resume_data(resume_data)

                            # Offer the resume for download
                            st.success("✅ Resume generated successfully!")

                            # Show snowflake effect
                            st.snow()

                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{
    current_name.replace(
        ' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                on_click=lambda: st.balloons()
                            )
                        except Exception as db_error:
                            print(
    f"Warning: Failed to save to database: {
        str(db_error)}")
                            
                            st.warning(
                                "⚠️ Resume generated ")
                            
                            # Show balloons effect
                            st.balloons()

                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{
    current_name.replace(
        ' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                on_click=lambda: st.balloons()
                            )
                    else:
                        st.error(
                            "❌ Failed to generate resume. Please try again.")
                        print("Resume buffer was None")
                except Exception as gen_error:
                    print(f"Error during resume generation: {str(gen_error)}")
                    print(f"Full traceback: {traceback.format_exc()}")
                    st.error(f"❌ Error generating resume: {str(gen_error)}")

            except Exception as e:
                print(f"Error preparing resume data: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                st.error(f"❌ Error preparing resume data: {str(e)}")

        

    def render_about(self):
        """Render the about page"""
        # Apply modern styles
        from ui_components import apply_modern_styles
        import base64
        import os

        # Function to load image as base64
        def get_image_as_base64(file_path):
            try:
                with open(file_path, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode()
                    return f"data:image/jpeg;base64,{encoded}"
            except:
                return None

        # Get image path and convert to base64
        image_path = os.path.join(
    os.path.dirname(__file__),
    "assets",
     "124852522.jpeg")
        image_base64 = get_image_as_base64(image_path)

        apply_modern_styles()

        # Add Font Awesome icons and custom CSS
        st.markdown("""
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                .profile-section, .vision-section, .feature-card {
                    text-align: center;
                    padding: 2rem;
                    background: rgba(45, 45, 45, 0.9);
                    border-radius: 20px;
                    margin: 2rem auto;
                    max-width: 800px;
                }

                .profile-image {
                    width: 200px;
                    height: 200px;
                    border-radius: 50%;
                    margin: 0 auto 1.5rem;
                    display: block;
                    object-fit: cover;
                    border: 4px solid #4CAF50;
                }

                .profile-name {
                    font-size: 2.5rem;
                    color: white;
                    margin-bottom: 0.5rem;
                }

                .profile-title {
                    font-size: 1.2rem;
                    color: #4CAF50;
                    margin-bottom: 1.5rem;
                }

                .social-links {
                    display: flex;
                    justify-content: center;
                    gap: 1.5rem;
                    margin: 2rem 0;
                }

                .social-link {
                    font-size: 2rem;
                    color: #4CAF50;
                    transition: all 0.3s ease;
                    padding: 0.5rem;
                    border-radius: 50%;
                    background: rgba(76, 175, 80, 0.1);
                    width: 60px;
                    height: 60px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-decoration: none;
                }

                .social-link:hover {
                    transform: translateY(-5px);
                    background: #4CAF50;
                    color: white;
                    box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
                }

                .bio-text {
                    color: #ddd;
                    line-height: 1.8;
                    font-size: 1.1rem;
                    margin-top: 2rem;
                    text-align: left;
                }

                .vision-text {
                    color: #ddd;
                    line-height: 1.8;
                    font-size: 1.1rem;
                    font-style: italic;
                    margin: 1.5rem 0;
                    text-align: left;
                }

                .vision-icon {
                    font-size: 2.5rem;
                    color: #4CAF50;
                    margin-bottom: 1rem;
                }

                .vision-title {
                    font-size: 2rem;
                    color: white;
                    margin-bottom: 1rem;
                }

                .features-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 2rem;
                    margin: 2rem auto;
                    max-width: 1200px;
                }

                .feature-card {
                    padding: 2rem;
                    margin: 0;
                }

                .feature-icon {
                    font-size: 2.5rem;
                    color: #4CAF50;
                    margin-bottom: 1rem;
                }

                .feature-title {
                    font-size: 1.5rem;
                    color: white;
                    margin: 1rem 0;
                }

                .feature-description {
                    color: #ddd;
                    line-height: 1.6;
                }
            </style>
        """, unsafe_allow_html=True)

        # Hero Section
        st.markdown("""
            <div class="hero-section">
                <h1 class="hero-title">About Smart Resume AI</h1>
                <p class="hero-subtitle">A powerful AI-driven platform for optimizing your resume</p>
            </div>
        """, unsafe_allow_html=True)

        # Profile Section
        st.markdown(f"""
            <div class="profile-section">
                <img src="{image_base64 if image_base64 else 'https://avatars.githubusercontent.com/u/153249853?s=400&v=4'}"
                     alt="Aniket"
                     class="profile-image"
                     onerror="this.onerror=null; this.src='https://avatars.githubusercontent.com/Hunterdii';">
                <h2 class="profile-name">Aniket</h2>
                <p class="profile-title">Full Stack Developer & AI/ML Enthusiast</p>
                <div class="social-links">
                    <a href="https://github.com/Aniket78072" class="social-link" target="_blank">
                        <i class="fab fa-github"></i>
                    </a>
                    <a href="https://www.linkedin.com/in/aniket-rana-88234823b/" class="social-link" target="_blank">
                        <i class="fab fa-linkedin"></i>
                    </a>
                    <a href="aniketpathania68393@gmail.com" class="social-link" target="_blank">
                        <i class="fas fa-envelope"></i>
                    </a>
                </div>
                <p class="bio-text">
                    Hello! I'm a passionate Full Stack Developer with intrest in AI and Machine Learning.
                    I created Smart Resume AI to revolutionize how job seekers approach their career journey.
                  , I've designed this platform to provide intelligent, data-driven insights for resume optimization.
                </p>
            </div>
        """, unsafe_allow_html=True)




        # Vision Section
        st.markdown("""
            <div class="vision-section">
                <i class="fas fa-lightbulb vision-icon"></i>
                <h2 class="vision-title">Our Vision</h2>
                <p class="vision-text">
                    "Smart Resume AI represents my vision of democratizing career advancement through technology.
                    By combining cutting-edge AI with intuitive design, this platform empowers job seekers at
                    every career stage to showcase their true potential and stand out in today's competitive job market."
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Features Section
        st.markdown("""
            <div class="features-grid">
                <div class="feature-card">
                    <i class="fas fa-robot feature-icon"></i>
                    <h3 class="feature-title">AI-Powered Analysis</h3>
                    <p class="feature-description">
                        Advanced AI algorithms provide detailed insights and suggestions to optimize your resume for maximum impact.
                    </p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-chart-line feature-icon"></i>
                    <h3 class="feature-title">Data-Driven Insights</h3>
                    <p class="feature-description">
                        Make informed decisions with our analytics-based recommendations and industry insights.
                    </p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-shield-alt feature-icon"></i>
                    <h3 class="feature-title">Privacy First</h3>
                    <p class="feature-description">
                        Your data security is our priority. We ensure your information is always protected and private.
                    </p>
                </div>
            </div>
            <div style="text-align: center; margin: 3rem 0;">
                <a href="?page=analyzer" class="cta-button">
                    Start Your Journey
                    <i class="fas fa-arrow-right" style="margin-left: 10px;"></i>
                </a>
            </div>
        """, unsafe_allow_html=True)

        

    def render_analyzer(self):
        """Render the resume analyzer page"""
        apply_modern_styles()

        # Page Header
        page_header(
            "Resume Analyzer",
            "Get instant AI-powered feedback to optimize your resume"
        )

        # Create tabs for Normal Analyzer and AI Analyzer
        analyzer_tabs = st.tabs(["Standard Analyzer", "AI Analyzer"])

        with analyzer_tabs[0]:
            # Job Role Selection
            categories = list(self.job_roles.keys())
            selected_category = st.selectbox(
    "Job Category", categories, key="standard_category")

            roles = list(self.job_roles[selected_category].keys())
            selected_role = st.selectbox(
    "Specific Role", roles, key="standard_role")

            role_info = self.job_roles[selected_category][selected_role]

            # Display role information
            st.markdown(f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>{selected_role}</h3>
                <p>{role_info['description']}</p>
                <h4>Required Skills:</h4>
                <p>{', '.join(role_info['required_skills'])}</p>
            </div>
            """, unsafe_allow_html=True)

            # File Upload
            uploaded_file = st.file_uploader(
    "Upload your resume", type=[
        'pdf', 'docx'], key="standard_file")

            if not uploaded_file:
                # Display empty state with a prominent upload button
                st.markdown(
                    self.render_empty_state(
                    "fas fa-cloud-upload-alt",
                    "Upload your resume to get started with standard analysis"
                    ),
                    unsafe_allow_html=True
                )
                # Add a prominent upload button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown("""
                    <style>
                    .upload-button {
                        background: linear-gradient(90deg, #4b6cb7, #182848);
                        color: white;
                        border: none;
                        border-radius: 10px;
                        padding: 15px 25px;
                        font-size: 18px;
                        font-weight: bold;
                        cursor: pointer;
                        width: 100%;
                        text-align: center;
                        margin: 20px 0;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                        transition: all 0.3s ease;
                    }
                    .upload-button:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 6px 15px rgba(0,0,0,0.3);
                    }

                    """, unsafe_allow_html=True)

            if uploaded_file:
                # Add a prominent analyze button
                analyze_standard = st.button("🔍 Analyze My Resume",
                                    type="primary",
                                    use_container_width=True,
                                    key="analyze_standard_button")

                if analyze_standard:
                    with st.spinner("Analyzing your document..."):
                        # Get file content
                        text = ""
                        try:
                            if uploaded_file.type == "application/pdf":
                                try:
                                    text = self.analyzer.extract_text_from_pdf(uploaded_file)
                                except Exception as pdf_error:
                                    st.error(f"PDF extraction failed: {str(pdf_error)}")
                                    st.info("Trying alternative PDF extraction method...")
                                    # Try AI analyzer as backup
                                    try:
                                        text = self.ai_analyzer.extract_text_from_pdf(uploaded_file)
                                    except Exception as backup_error:
                                        st.error(f"All PDF extraction methods failed: {str(backup_error)}")
                                        return
                            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                try:
                                    text = self.analyzer.extract_text_from_docx(uploaded_file)
                                except Exception as docx_error:
                                    st.error(f"DOCX extraction failed: {str(docx_error)}")
                                    # Try AI analyzer as backup
                                    try:
                                        text = self.ai_analyzer.extract_text_from_docx(uploaded_file)
                                    except Exception as backup_error:
                                        st.error(f"All DOCX extraction methods failed: {str(backup_error)}")
                                        return
                            else:
                                text = uploaded_file.getvalue().decode()
                                
                            if not text or text.strip() == "":
                                st.error("Could not extract any text from the uploaded file. Please try a different file.")
                                return
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                            return

                        # Analyze the document
                        analysis = self.analyzer.analyze_resume({'raw_text': text}, role_info)
                        
                        # Check if analysis returned an error
                        if 'error' in analysis:
                            st.error(analysis['error'])
                            return

                        # Show snowflake effect
                        st.snow()

                       

                           

                        # Show results based on document type
                        if analysis.get('document_type') != 'resume':
                            st.error(
    f"⚠️ This appears to be a {
        analysis['document_type']} document, not a resume!")
                            st.warning(
                                "Please upload a proper resume for ATS analysis.")
                            return
                        # Display results in a modern card layout
                    col1, col2 = st.columns(2)

                    with col1:
                        # ATS Score Card with circular progress
                        st.markdown("""
                        <div class="feature-card">
                            <h2>ATS Score</h2>
                            <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
                                <div style="
                                    position: absolute;
                                    width: 150px;
                                    height: 150px;
                                    border-radius: 50%;
                                    background: conic-gradient(
                                        #4CAF50 0% {score}%,
                                        #2c2c2c {score}% 100%
                                    );
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                ">
                                    <div style="
                                        width: 120px;
                                        height: 120px;
                                        background: #1a1a1a;
                                        border-radius: 50%;
                                        display: flex;
                                        align-items: center;
                                        justify-content: center;
                                        font-size: 24px;
                                        font-weight: bold;
                                        color: {color};
                                    ">
                                        {score}
                                    </div>
                                </div>
                            </div>
                            <div style="text-align: center; margin-top: 10px;">
                                <span style="
                                    font-size: 1.2em;
                                    color: {color};
                                    font-weight: bold;
                                ">
                                    {status}
                                </span>
                            </div>
                        """.format(
                            score=analysis['ats_score'],
                            color='#4CAF50' if analysis['ats_score'] >= 80 else '#FFA500' if analysis[
                                'ats_score'] >= 60 else '#FF4444',
                            status='Excellent' if analysis['ats_score'] >= 80 else 'Good' if analysis[
                                'ats_score'] >= 60 else 'Needs Improvement'
                        ), unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)

                        

                        # Skills Match Card
                        st.markdown("""
                        <div class="feature-card">
                            <h2>Skills Match</h2>
                        """, unsafe_allow_html=True)

                        st.metric(
                            "Keyword Match", f"{int(analysis.get('keyword_match', {}).get('score', 0))}%")

                        if analysis['keyword_match']['missing_skills']:
                            st.markdown("#### Missing Skills:")
                            for skill in analysis['keyword_match']['missing_skills']:
                                st.markdown(f"- {skill}")

                        st.markdown("</div>", unsafe_allow_html=True)

                    with col2:
                        # Format Score Card
                        st.markdown("""
                        <div class="feature-card">
                            <h2>Format Analysis</h2>
                        """, unsafe_allow_html=True)

                        st.metric("Format Score",
                                  f"{int(analysis.get('format_score', 0))}%")
                        st.metric("Section Score",
                                  f"{int(analysis.get('section_score', 0))}%")

                        st.markdown("</div>", unsafe_allow_html=True)

                        # Suggestions Card with improved UI
                        st.markdown("""
                        <div class="feature-card">
                            <h2>📋 Resume Improvement Suggestions</h2>
                        """, unsafe_allow_html=True)

                            # Contact Section
                        if analysis.get('contact_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>📞 Contact Information</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'contact_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # Summary Section
                        if analysis.get('summary_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>📝 Professional Summary</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'summary_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # Skills Section
                        if analysis.get(
                            'skills_suggestions') or analysis['keyword_match']['missing_skills']:
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>🎯 Skills</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'skills_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                if analysis['keyword_match']['missing_skills']:
                                    st.markdown(
    "<li style='margin-bottom: 8px;'>✓ Consider adding these relevant skills:</li>",
     unsafe_allow_html=True)
                                    for skill in analysis['keyword_match']['missing_skills']:
                                        st.markdown(
    f"<li style='margin-left: 20px; margin-bottom: 4px;'>• {skill}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # Experience Section
                        if analysis.get('experience_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>💼 Work Experience</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'experience_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # Education Section
                        if analysis.get('education_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>🎓 Education</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'education_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # General Formatting Suggestions
                        if analysis.get('format_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>📄 Formatting</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'format_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)

                        # Course Recommendations
                    st.markdown("""
                        <div class="feature-card">
                            <h2>📚 Recommended Courses</h2>
                        """, unsafe_allow_html=True)

                        # Get courses based on role and category
                    courses = get_courses_for_role(selected_role)
                    if not courses:
                            category = get_category_for_role(selected_role)
                            courses = COURSES_BY_CATEGORY.get(
                                category, {}).get(selected_role, [])

                        # Display courses in a grid
                    cols = st.columns(2)
                    for i, course in enumerate(
                        courses[:6]):  # Show top 6 courses
                            with cols[i % 2]:
                                st.markdown(f"""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h4>{course[0]}</h4>
                                    <a href='{course[1]}' target='_blank'>View Course</a>
                                </div>
                                """, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                        # Learning Resources
                    st.markdown("""
                        <div class="feature-card">
                            <h2>📺 Helpful Videos</h2>
                        """, unsafe_allow_html=True)

                    tab1, tab2 = st.tabs(["Resume Tips", "Interview Tips"])

                    with tab1:
                            # Resume Videos
                            for category, videos in RESUME_VIDEOS.items():
                                st.subheader(category)
                                cols = st.columns(2)
                                for i, video in enumerate(videos):
                                    with cols[i % 2]:
                                        st.video(video[1])

                    with tab2:
                            # Interview Videos
                            for category, videos in INTERVIEW_VIDEOS.items():
                                st.subheader(category)
                                cols = st.columns(2)
                                for i, video in enumerate(videos):
                                    with cols[i % 2]:
                                        st.video(video[1])

                    st.markdown("</div>", unsafe_allow_html=True)

        with analyzer_tabs[1]:
            st.markdown("""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>AI-Powered Resume Analysis</h3>
                <p>Get detailed insights from advanced AI models that analyze your resume and provide personalized recommendations.</p>
                <p><strong>Upload your resume to get AI-powered analysis and recommendations.</strong></p>
            </div>
            """, unsafe_allow_html=True)

            # AI Model Selection
            ai_model = st.selectbox(
                "Select AI Model",
                ["Google Gemini"],
                help="Choose the AI model to analyze your resume"
            )
             
            # Add job description input option
            use_custom_job_desc = st.checkbox("Use custom job description", value=False, 
                                             help="Enable this to provide a specific job description for more targeted analysis")
            
            custom_job_description = ""
            if use_custom_job_desc:
                custom_job_description = st.text_area(
                    "Paste the job description here",
                    height=200,
                    placeholder="Paste the full job description from the company here for more targeted analysis...",
                    help="Providing the actual job description will help the AI analyze your resume specifically for this position"
                )
                
                st.markdown("""
                <div style='background-color: #2e7d32; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                    <p><i class="fas fa-lightbulb"></i> <strong>Pro Tip:</strong> Including the actual job description significantly improves the accuracy of the analysis and provides more relevant recommendations tailored to the specific position.</p>
                </div>
                """, unsafe_allow_html=True)
             
                    



            # Job Role Selection for AI Analysis
            categories = list(self.job_roles.keys())
            selected_category = st.selectbox(
    "Job Category", categories, key="ai_category")

            roles = list(self.job_roles[selected_category].keys())
            selected_role = st.selectbox("Specific Role", roles, key="ai_role")

            role_info = self.job_roles[selected_category][selected_role]

            # Display role information
            st.markdown(f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>{selected_role}</h3>
                <p>{role_info['description']}</p>
                <h4>Required Skills:</h4>
                <p>{', '.join(role_info['required_skills'])}</p>
            </div>
            """, unsafe_allow_html=True)

            # File Upload for AI Analysis
            uploaded_file = st.file_uploader(
    "Upload your resume", type=[
        'pdf', 'docx'], key="ai_file")

            if not uploaded_file:
            # Display empty state with a prominent upload button
                st.markdown(
                self.render_empty_state(
            "fas fa-robot",
                        "Upload your resume to get AI-powered analysis and recommendations"
        ),
        unsafe_allow_html=True
    )
            else:
                # Add a prominent analyze button
                analyze_ai = st.button("🤖 Analyze with AI",
                                type="primary",
                                use_container_width=True,
                                key="analyze_ai_button")

                if analyze_ai:
                    with st.spinner(f"Analyzing your resume with {ai_model}..."):
                        # Get file content
                        text = ""
                        try:
                            if uploaded_file.type == "application/pdf":
                                text = self.analyzer.extract_text_from_pdf(
                                    uploaded_file)
                            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                text = self.analyzer.extract_text_from_docx(
                                    uploaded_file)
                            else:
                                text = uploaded_file.getvalue().decode()
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                            st.stop()

                        # Analyze with AI
                        try:
                            # Show a loading animation
                            with st.spinner("🧠 AI is analyzing your resume..."):
                                progress_bar = st.progress(0)
                                
                                # Get the selected model
                                selected_model = "Google Gemini"
                                
                                # Update progress
                                progress_bar.progress(10)
                                
                                # Extract text from the resume
                                analyzer = AIResumeAnalyzer()
                                if uploaded_file.type == "application/pdf":
                                    resume_text = analyzer.extract_text_from_pdf(
                                        uploaded_file)
                                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                    resume_text = analyzer.extract_text_from_docx(
                                        uploaded_file)
                                else:
                                    # For text files or other formats
                                    resume_text = uploaded_file.getvalue().decode('utf-8')
                                
                                # Initialize the AI analyzer (moved after text extraction)
                                progress_bar.progress(30)
                                
                                # Get the job role
                                job_role = selected_role if selected_role else "Not specified"
                                
                                # Update progress
                                progress_bar.progress(50)
                                
                                # Analyze the resume with Google Gemini
                                if use_custom_job_desc and custom_job_description:
                                    # Use custom job description for analysis
                                    analysis_result = analyzer.analyze_resume_with_gemini(
                                        resume_text, job_role=job_role, job_description=custom_job_description)
                                    # Show that custom job description was used
                                    st.session_state['used_custom_job_desc'] = True
                                else:
                                    # Use standard role-based analysis
                                    analysis_result = analyzer.analyze_resume_with_gemini(
                                        resume_text, job_role=job_role)
                                    st.session_state['used_custom_job_desc'] = False

                                
                                # Update progress
                                progress_bar.progress(80)
                                
                                # Save the analysis to the database
                                if analysis_result and "error" not in analysis_result:
                                    # Extract the resume score
                                    resume_score = analysis_result.get(
                                        "resume_score", 0)
                                    
                                    # Save to database
                                    save_ai_analysis_data(
                                        None,  # No user_id needed
                                        {
                                            "model_used": selected_model,
                                            "resume_score": resume_score,
                                            "job_role": job_role
                                        }
                                    )
                                # show snowflake effect
                                st.snow()

                                # Complete the progress
                                progress_bar.progress(100)
                                
                                # Display the analysis result
                                if analysis_result and "error" not in analysis_result:
                                    st.success("✅ Analysis complete!")
                                    
                                    # Extract data from the analysis
                                    full_response = analysis_result.get(
                                        "analysis", "")
                                    resume_score = analysis_result.get(
                                        "resume_score", 0)
                                    ats_score = analysis_result.get(
                                        "ats_score", 0)
                                    model_used = analysis_result.get(
                                        "model_used", selected_model)
                                    
                                    # Store the full response in session state for download
                                    st.session_state['full_analysis'] = full_response
                                    
                                    # Display the analysis in a nice format
                                    st.markdown("## Full Analysis Report")
                                    
                                    # Get current date
                                    from datetime import datetime
                                    current_date = datetime.now().strftime("%B %d, %Y")
                                    
                                    # Create a modern styled header for the report
                                    st.markdown(f"""
                                    <div style="background-color: #262730; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                        <h2 style="color: #ffffff; margin-bottom: 10px;">AI Resume Analysis Report</h2>
                                        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                                            <div style="flex: 1; min-width: 200px;">
                                                <p style="color: #ffffff;"><strong>Job Role:</strong> {job_role if job_role else "Not specified"}</p>
                                                <p style="color: #ffffff;"><strong>Analysis Date:</strong> {current_date}</p>                                                                                                                                        </div>
                                            <div style="flex: 1; min-width: 200px;">
                                                <p style="color: #ffffff;"><strong>AI Model:</strong> {model_used}</p>
                                                <p style="color: #ffffff;"><strong>Overall Score:</strong> {resume_score}/100 - {"Excellent" if resume_score >= 80 else "Good" if resume_score >= 60 else "Needs Improvement"}</p>
                                                {f'<p style="color: #4CAF50;"><strong>✓ Custom Job Description Used</strong></p>' if st.session_state.get('used_custom_job_desc', False) else ''}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Add gauge charts for scores
                                    import plotly.graph_objects as go
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        # Resume Score Gauge
                                        fig1 = go.Figure(go.Indicator(
                                            mode="gauge+number",
                                            value=resume_score,
                                            domain={'x': [0, 1], 'y': [0, 1]},
                                            title={'text': "Resume Score", 'font': {'size': 16}},
                                            gauge={
                                                'axis': {'range': [0, 100], 'tickwidth': 1},
                                                'bar': {'color': "#4CAF50" if resume_score >= 80 else "#FFA500" if resume_score >= 60 else "#FF4444"},
                                                'bgcolor': "white",
                                                'borderwidth': 2,
                                                'bordercolor': "gray",
                                                'steps': [
                                                    {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.2)'},
                                                    {'range': [40, 60], 'color': 'rgba(255, 165, 0, 0.2)'},
                                                    {'range': [60, 80], 'color': 'rgba(255, 214, 0, 0.2)'},
                                                    {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.2)'}
                                                ],
                                                'threshold': {
                                                    'line': {'color': "red", 'width': 4},
                                                    'thickness': 0.75,
                                                    'value': 60
                                                }
                                            }
                                        ))
                                        
                                        fig1.update_layout(
                                            height=250,
                                            margin=dict(l=20, r=20, t=50, b=20),
                                        )
                                        
                                        st.plotly_chart(fig1, use_container_width=True)
                                        
                                        status = "Excellent" if resume_score >= 80 else "Good" if resume_score >= 60 else "Needs Improvement"
                                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{status}</div>", unsafe_allow_html=True)
                                    
                                    with col2:
                                        # ATS Score Gauge
                                        fig2 = go.Figure(go.Indicator(
                                            mode="gauge+number",
                                            value=ats_score,
                                            domain={'x': [0, 1], 'y': [0, 1]},
                                            title={'text': "ATS Optimization Score", 'font': {'size': 16}},
                                            gauge={
                                                'axis': {'range': [0, 100], 'tickwidth': 1},
                                                'bar': {'color': "#4CAF50" if ats_score >= 80 else "#FFA500" if ats_score >= 60 else "#FF4444"},
                                                'bgcolor': "white",
                                                'borderwidth': 2,
                                                'bordercolor': "gray",
                                                'steps': [
                                                    {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.2)'},
                                                    {'range': [40, 60], 'color': 'rgba(255, 165, 0, 0.2)'},
                                                    {'range': [60, 80], 'color': 'rgba(255, 214, 0, 0.2)'},
                                                    {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.2)'}
                                                ],
                                                'threshold': {
                                                    'line': {'color': "red", 'width': 4},
                                                    'thickness': 0.75,
                                                    'value': 60
                                                }
                                            }
                                        ))
                                        
                                        fig2.update_layout(
                                            height=250,
                                            margin=dict(l=20, r=20, t=50, b=20),
                                        )
                                        
                                        st.plotly_chart(fig2, use_container_width=True)
                                        
                                        status = "Excellent" if ats_score >= 80 else "Good" if ats_score >= 60 else "Needs Improvement"
                                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{status}</div>", unsafe_allow_html=True)

                                    # Add Job Description Match Score if custom job description was used
                                    if st.session_state.get('used_custom_job_desc', False) and custom_job_description:
                                        # Extract job match score from analysis result or calculate it
                                        job_match_score = analysis_result.get("job_match_score", 0)
                                        if not job_match_score and "job_match" in analysis_result:
                                            job_match_score = analysis_result["job_match"].get("score", 0)
                                        
                                        # If we have a job match score, display it
                                        if job_match_score:
                                            st.markdown("""
                                            <h3 style="background: linear-gradient(90deg, #4d7c0f, #84cc16); color: white; padding: 10px; border-radius: 5px; margin-top: 20px;">
                                                <i class="fas fa-handshake"></i> Job Description Match Analysis
                                            </h3>
                                            """, unsafe_allow_html=True)
                                            
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                # Job Match Score Gauge
                                                fig3 = go.Figure(go.Indicator(
                                                    mode="gauge+number",
                                                    value=job_match_score,
                                                    domain={'x': [0, 1], 'y': [0, 1]},
                                                    title={'text': "Job Match Score", 'font': {'size': 16}},
                                                    gauge={
                                                        'axis': {'range': [0, 100], 'tickwidth': 1},
                                                        'bar': {'color': "#4CAF50" if job_match_score >= 80 else "#FFA500" if job_match_score >= 60 else "#FF4444"},
                                                        'bgcolor': "white",
                                                        'borderwidth': 2,
                                                        'bordercolor': "gray",
                                                        'steps': [
                                                            {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.2)'},
                                                            {'range': [40, 60], 'color': 'rgba(255, 165, 0, 0.2)'},
                                                            {'range': [60, 80], 'color': 'rgba(255, 214, 0, 0.2)'},
                                                            {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.2)'}
                                                        ],
                                                        'threshold': {
                                                            'line': {'color': "red", 'width': 4},
                                                            'thickness': 0.75,
                                                            'value': 60
                                                        }
                                                    }
                                                ))
                                                
                                                fig3.update_layout(
                                                    height=250,
                                                    margin=dict(l=20, r=20, t=50, b=20),
                                                )
                                                
                                                st.plotly_chart(fig3, use_container_width=True)
                                                
                                                match_status = "Excellent Match" if job_match_score >= 80 else "Good Match" if job_match_score >= 60 else "Low Match"
                                                st.markdown(f"<div style='text-align: center; font-weight: bold;'>{match_status}</div>", unsafe_allow_html=True)
                                            
                                            with col2:
                                                st.markdown("""
                                                <div style="background-color: #262730; padding: 20px; border-radius: 10px; height: 100%;">
                                                    <h4 style="color: #ffffff; margin-bottom: 15px;">What This Means</h4>
                                                    <p style="color: #ffffff;">This score represents how well your resume matches the specific job description you provided.</p>
                                                    <ul style="color: #ffffff; padding-left: 20px;">
                                                        <li><strong>80-100:</strong> Excellent match - your resume is highly aligned with this job</li>
                                                        <li><strong>60-79:</strong> Good match - your resume matches many requirements</li>
                                                        <li><strong>Below 60:</strong> Consider tailoring your resume more specifically to this job</li>
                                                    </ul>
                                                </div>
                                                """, unsafe_allow_html=True)
                                    

                                    # Format the full response with better styling
                                    formatted_analysis = full_response
                                    
                                    # Replace section headers with styled headers
                                    section_styles = {
                                        "## Overall Assessment": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-chart-line"></i> Overall Assessment
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Professional Profile Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #047857, #10b981); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-user-tie"></i> Professional Profile Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Skills Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #4f46e5, #818cf8); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-tools"></i> Skills Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Experience Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #9f1239, #e11d48); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-briefcase"></i> Experience Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Education Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #854d0e, #eab308); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-graduation-cap"></i> Education Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Key Strengths": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #166534, #22c55e); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-check-circle"></i> Key Strengths
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Areas for Improvement": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #9f1239, #fb7185); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-exclamation-circle"></i> Areas for Improvement
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## ATS Optimization Assessment": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #0e7490, #06b6d4); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-robot"></i> ATS Optimization Assessment
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Recommended Courses": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #5b21b6, #8b5cf6); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-book"></i> Recommended Courses
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Resume Score": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #0369a1, #0ea5e9); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-star"></i> Resume Score
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Role Alignment Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #7c2d12, #ea580c); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-bullseye"></i> Role Alignment Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Job Match Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #4d7c0f, #84cc16); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-handshake"></i> Job Match Analysis
                                            </h3>
                                            <div class="section-content">""",
                                    }
                                    
                                    # Apply the styling to each section
                                    for section, style in section_styles.items():
                                        if section in formatted_analysis:
                                            formatted_analysis = formatted_analysis.replace(
                                                section, style)
                                            # Add closing div tags
                                            next_section = False
                                            for next_sec in section_styles.keys():
                                                if next_sec != section and next_sec in formatted_analysis.split(style)[1]:
                                                    split_text = formatted_analysis.split(style)[1].split(next_sec)
                                                    formatted_analysis = formatted_analysis.split(style)[0] + style + split_text[0] + "</div></div>" + next_sec + "".join(split_text[1:])
                                                    next_section = True
                                                    break
                                            if not next_section:
                                                formatted_analysis = formatted_analysis + "</div></div>"
                                    
                                    # Remove any extra closing div tags that might have been added
                                    formatted_analysis = formatted_analysis.replace("</div></div></div></div>", "</div></div>")
                                    
                                    # Ensure we don't have any orphaned closing tags at the end
                                    if formatted_analysis.endswith("</div>"):
                                        # Count opening and closing div tags
                                        open_tags = formatted_analysis.count("<div")
                                        close_tags = formatted_analysis.count("</div>")
                                        
                                        # If we have more closing than opening tags, remove the extras
                                        if close_tags > open_tags:
                                            excess = close_tags - open_tags
                                            formatted_analysis = formatted_analysis[:-6 * excess]
                                    
                                    # Clean up any visible HTML tags that might appear in the text
                                    formatted_analysis = formatted_analysis.replace("&lt;/div&gt;", "")
                                    formatted_analysis = formatted_analysis.replace("&lt;div&gt;", "")
                                    formatted_analysis = formatted_analysis.replace("<div>", "<div>")  # Ensure proper opening
                                    formatted_analysis = formatted_analysis.replace("</div>", "</div>")  # Ensure proper closing
                                    
                                    # Add CSS for the report
                                    st.markdown("""
                                    <style>
                                        .report-section {
                                            margin-bottom: 25px;
                                            border: 1px solid #4B4B4B;
                                            border-radius: 8px;
                                            overflow: hidden;
                                        }
                                        .section-content {
                                            padding: 15px;
                                            background-color: #262730;
                                            color: #ffffff;
                                        }
                                        .report-section h3 {
                                            margin-top: 0;
                                            font-weight: 600;
                                        }
                                        .report-section ul {
                                            padding-left: 20px;
                                        }
                                        .report-section p {
                                            color: #ffffff;
                                            margin-bottom: 10px;
                                        }
                                        .report-section li {
                                            color: #ffffff;
                                            margin-bottom: 5px;
                                        }
                                    </style>
                                    """, unsafe_allow_html=True)

                                    # Display the formatted analysis
                                    st.markdown(f"""
                                    <div style="background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4B4B4B; color: #ffffff;">
                                        {formatted_analysis}
                                    </div>
                                    """, unsafe_allow_html=True)

                                    # Create a PDF report
                                    pdf_buffer = self.ai_analyzer.generate_pdf_report(
                                        analysis_result={
                                            "score": resume_score,
                                            "ats_score": ats_score,
                                            "model_used": model_used,
                                            "full_response": full_response,
                                            "strengths": analysis_result.get("strengths", []),
                                            "weaknesses": analysis_result.get("weaknesses", []),
                                            "used_custom_job_desc": st.session_state.get('used_custom_job_desc', False),
                                            "custom_job_description": custom_job_description if st.session_state.get('used_custom_job_desc', False) else ""
                                        },
                                        candidate_name=st.session_state.get(
                                            'candidate_name', 'Candidate'),
                                        job_role=selected_role
                                    )

                                    # PDF download button
                                    if pdf_buffer:
                                        st.download_button(
                                            label="📊 Download PDF Report",
                                            data=pdf_buffer,
                                            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                            mime="application/pdf",
                                            use_container_width=True,
                                            on_click=lambda: st.balloons()
                                        )
                                    else:
                                        st.error("PDF generation failed. Please try again later.")
                                else:
                                    st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
                        except Exception as ai_error:
                            st.error(f"Error during AI analysis: {str(ai_error)}")
                            import traceback as tb
                            st.code(tb.format_exc())

      

    def render_home(self):
        apply_modern_styles()
        
        # Hero Section
        hero_section(
            "Smart Resume AI",
            "Transform your career with AI-powered resume analysis and building. Get personalized insights and create professional resumes that stand out."
        )
        
        # Features Section
        st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
        
        feature_card(
            "fas fa-robot",
            "AI-Powered Analysis",
            "Get instant feedback on your resume with advanced AI analysis that identifies strengths and areas for improvement."
        )
        
        feature_card(
            "fas fa-magic",
            "Smart Resume Builder",
            "Create professional resumes with our intelligent builder that suggests optimal content and formatting."
        )
        
        feature_card(
            "fas fa-chart-line",
            "Career Insights",
            "Access detailed analytics and personalized recommendations to enhance your career prospects."
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
      

        # Call-to-Action with Streamlit navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Get Started", key="get_started_btn", 
                        help="Click to start analyzing your resume",
                        type="primary",
                        use_container_width=True):
                cleaned_name = "🔍 RESUME ANALYZER".lower().replace(" ", "_").replace("🔍", "").strip()
                st.session_state.page = cleaned_name
                st.rerun()

    def render_job_search(self):
        """Render the job search page"""
        render_job_search()

       


    def render_feedback_page(self):
        """Render the feedback page"""
        apply_modern_styles()
        
        # Page Header
        page_header(
            "Feedback & Suggestions",
            "Help us improve by sharing your thoughts"
        )
        
       



    def main(self):
        """Main application entry point"""
        self.apply_global_styles()
        
        # Admin login/logout in sidebar
        with st.sidebar:
            st_lottie(self.load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_xyadoh9h.json"), height=200, key="sidebar_animation")
            st.title("Smart Resume AI")
            st.markdown("---")
            
            # Navigation buttons
            for page_name in self.pages.keys():
                if st.button(page_name, use_container_width=True):
                    cleaned_name = page_name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").replace("📊", "").replace("🎯", "").replace("💬", "").replace("ℹ️", "").strip()
                    st.session_state.page = cleaned_name
                    st.rerun()

          

        
        

        # Force home page on first load
        if 'initial_load' not in st.session_state:
            st.session_state.initial_load = True
            st.session_state.page = 'home'
            st.rerun()
        
        # Get current page and render it
        current_page = st.session_state.get('page', 'home')
        
        # Create a mapping of cleaned page names to original names
        page_mapping = {name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").replace("📊", "").replace("🎯", "").replace("💬", "").replace("ℹ️", "").strip(): name 
                       for name in self.pages.keys()}
        
        # Render the appropriate page
        if current_page in page_mapping:
            self.pages[page_mapping[current_page]]()
        else:
            # Default to home page if invalid page
            self.render_home()
    
        # Add footer to every page
        self.add_footer()

if __name__ == "__main__":
    app = ResumeApp()
    app.main()