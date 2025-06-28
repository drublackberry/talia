from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Candidate, Research, Project
from app.forms import LoginForm, RegistrationForm, ResearchForm, ProjectForm
import requests # We'll use this to simulate the LLM call

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html', title='Welcome')

@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(name=form.name.data, master_prompt=form.master_prompt.data, creator=current_user)
        db.session.add(project)
        db.session.commit()
        flash('Your project has been created!')
        return redirect(url_for('main.dashboard'))
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).all()
    return render_template('dashboard.html', title='Dashboard', form=form, projects=projects)

@bp.route('/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ResearchForm()
    if form.validate_on_submit():
        candidate = Candidate.query.filter_by(linkedin_url=form.linkedin_url.data).first()
        if candidate is None:
            candidate = Candidate(linkedin_url=form.linkedin_url.data)
            db.session.add(candidate)
            # Add candidate to project
            project.candidates.append(candidate)

        # Use project's master prompt for the research
        research_prompt = project.master_prompt

        # Mock LLM research
        # In a real application, you would pass research_prompt to an LLM
        mock_result = f"This is a mock research result for {form.linkedin_url.data}."

        research = Research(
            content=mock_result,
            candidate=candidate,
            user_id=current_user.id,
            project_id=project.id
        )
        db.session.add(research)
        db.session.commit()
        flash('Research has been completed and saved!')
        return redirect(url_for('main.project', project_id=project.id))

    researches = Research.query.filter_by(project_id=project.id).order_by(Research.created_at.desc()).all()
    return render_template('project.html', title=project.name, project=project, form=form, researches=researches)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.dashboard'))
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)
