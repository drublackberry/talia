from flask import Blueprint, render_template, flash, redirect, url_for, request, Response, stream_with_context, abort, current_app
import json
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Candidate, Research, Project, Prompt
from app.forms import LoginForm, RegistrationForm, ResearchForm, ProjectForm, SettingsForm, EditPromptForm
from app.services import get_profile_from_linkedin_url

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
        # Create the project and the initial prompt together
        project = Project(name=form.name.data, creator=current_user)
        db.session.add(project)
        # Create an initial prompt for the project
        prompt_text = form.master_prompt.data
        if not current_user.settings.advanced_mode:
            prompt_text += f" {current_app.config['APPEND_PROMPT']}"
        initial_prompt = Prompt(text=prompt_text, project=project)
        db.session.add(initial_prompt)
        db.session.commit()
        flash('Your project has been created!')
        return redirect(url_for('main.dashboard'))
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).all()
    return render_template('dashboard.html', title='Dashboard', form=form, projects=projects)

@bp.route('/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def project(project_id):
    project = Project.query.get_or_404(project_id)
    research_form = ResearchForm()
    prompt_form = EditPromptForm()

    if prompt_form.submit_prompt.data and prompt_form.validate():
        prompt_text = prompt_form.text.data
        if not current_user.settings.advanced_mode:
            prompt_text += f" {current_app.config['APPEND_PROMPT']}"
        new_prompt = Prompt(text=prompt_text, project_id=project.id)
        db.session.add(new_prompt)
        db.session.commit()
        flash('Master prompt has been updated.')
        return redirect(url_for('main.project', project_id=project.id))

    if research_form.submit_research.data and research_form.validate():
        latest_prompt = project.prompts.first()
        if not latest_prompt:
            flash('Cannot perform research without a master prompt.', 'danger')
            return redirect(url_for('main.project', project_id=project.id))

        candidate = Candidate.query.filter_by(linkedin_url=research_form.linkedin_url.data).first()
        if candidate is None:
            candidate = Candidate(linkedin_url=research_form.linkedin_url.data)
            db.session.add(candidate)
            project.candidates.append(candidate)

        try:
            # Create a placeholder research object
            new_research = Research(
                prompt_id=latest_prompt.id,
                full_research="Processing...",
                candidate_id=candidate.id,
                user_id=current_user.id,
                project_id=project.id
            )
            db.session.add(new_research)
            db.session.commit()
            flash('Research has started. Results will stream in below as they become available.', 'info')
            # Redirect to a page that will display the streaming content
            return redirect(url_for('main.research_stream', research_id=new_research.id))

        except Exception as e:
            flash(f'An error occurred while creating the research record: {e}', 'danger')
            return redirect(url_for('main.project', project_id=project.id))

    if request.method == 'GET':
        prompt_form.text.data = project.master_prompt

    researches = Research.query.filter_by(project_id=project.id).order_by(Research.overall_score.desc()).all()
    return render_template('project.html', title=project.name, project=project, research_form=research_form, prompt_form=prompt_form, researches=researches)

@bp.route('/research/<int:research_id>')
@login_required
def research_detail(research_id):
    research = Research.query.get_or_404(research_id)
    if research.project.creator != current_user:
        abort(403)
    return render_template('research_detail.html', title='Research Details', research=research)

@bp.route('/research_stream/<int:research_id>')
@login_required
def research_stream(research_id):
    research = Research.query.get_or_404(research_id)
    return render_template('research_stream.html', title='Research in Progress', research=research)

@bp.route('/stream/<int:research_id>')
@login_required
def stream(research_id):
    research = Research.query.get_or_404(research_id)

    def generate():
        full_response = ""
        try:
            for chunk in get_profile_from_linkedin_url(research.candidate.linkedin_url, research_model=current_user.settings.research_model):
                yield f"data: {chunk.model_dump_json()}\n\n"
                if chunk.choices and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content

            research.full_research = full_response
            db.session.commit()
        except Exception as e:
            error_message = f"An error occurred: {e}"
            research.full_research = error_message
            db.session.commit()
            error_payload = {"error": error_message}
            yield f"data: {json.dumps(error_payload)}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        current_user.settings.theme = 'dark' if form.dark_theme.data else 'light'
        current_user.settings.advanced_mode = form.advanced_mode.data
        current_user.settings.research_model = form.research_model.data
        db.session.commit()
        flash('Your settings have been updated.')
        return redirect(url_for('main.settings'))
    elif request.method == 'GET':
        form.dark_theme.data = current_user.settings.theme == 'dark'
        form.advanced_mode.data = current_user.settings.advanced_mode
        form.research_model.data = current_user.settings.research_model
    return render_template('settings.html', title='Settings', form=form)

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
