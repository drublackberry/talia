from flask import Blueprint, render_template, flash, redirect, url_for, request, Response, stream_with_context, abort, current_app
import json
import threading
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
        candidate = Candidate.query.filter_by(linkedin_url=research_form.linkedin_url.data).first()
        if candidate is None:
            candidate = Candidate(linkedin_url=research_form.linkedin_url.data)
            db.session.add(candidate)
        
        if candidate not in project.candidates:
            project.candidates.append(candidate)

        research = Research(
            candidate=candidate,
            project=project,
            user=current_user,
            prompt=project.prompts.first(),
            status='Pending'
        )
        db.session.add(research)
        db.session.commit()

        # Run research in a background thread
        project_prompt = project.prompts.first().text if project.prompts.first() else ""
        thread = threading.Thread(target=background_research, args=(current_app._get_current_object(), research.id, research_form.linkedin_url.data, project_prompt, current_user.settings.research_model))
        thread.start()

        flash('Research has been started in the background. The page will update once it is complete.', 'info')
        return redirect(url_for('main.project', project_id=project.id))

    if request.method == 'GET':
        prompt = project.prompts.first()
        if prompt:
            prompt_form.text.data = prompt.text

    researches = Research.query.filter_by(project_id=project.id).order_by(Research.overall_score.desc()).all()
    return render_template('project.html', title=project.name, project=project, research_form=research_form, prompt_form=prompt_form, researches=researches)

@bp.route('/research/<int:research_id>')
@login_required
def research_detail(research_id):
    research = Research.query.get_or_404(research_id)
    if research.project.creator != current_user:
        abort(403)
    return render_template('research_detail.html', title='Research Details', research=research)

def background_research(app, research_id, linkedin_url, project_prompt, research_model):
    with app.app_context():
        app.logger.info(f"[Thread-{research_id}] Starting background research for {linkedin_url}")
        research = Research.query.get(research_id)
        if not research:
            app.logger.warning(f"[Thread-{research_id}] Research with ID {research_id} not found.")
            return

        research.status = 'In Progress'
        db.session.commit()
        app.logger.info(f"[Thread-{research_id}] Status set to 'In Progress'.")

        try:
            app.logger.info(f"[Thread-{research_id}] Calling Perplexity API with model {research_model}.")
            research_result = get_profile_from_linkedin_url(
                linkedin_url=linkedin_url,
                project_prompt=project_prompt,
                research_model=research_model
            )
            app.logger.info(f"[Thread-{research_id}] Received response from Perplexity API.")
            
            if research_result.strip().startswith('```json'):
                cleaned_response = research_result.strip()[7:-3].strip()
            else:
                cleaned_response = research_result

            try:
                app.logger.info(f"[Thread-{research_id}] Parsing JSON response.")
                data = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                app.logger.error(f"[Thread-{research_id}] Failed to decode JSON from API response: {e}")
                app.logger.error(f"[Thread-{research_id}] Raw response received: {research_result}")
                raise
            
            if research.candidate:
                research.candidate.name = data.get('candidate_name')

            research.summary = data.get('summary')
            research.full_report = data.get('full_report')
            research.overall_score = data.get('overall_score')
            research.status = 'Completed'
            app.logger.info(f"[Thread-{research_id}] Research completed successfully.")

        except Exception as e:
            app.logger.error(f"[Thread-{research_id}] An error occurred during research: {e}", exc_info=True)
            research.status = 'Failed'
            research.summary = f"An error occurred during research: {e}"
        
        finally:
            db.session.commit()
            app.logger.info(f"[Thread-{research_id}] Final status '{research.status}' committed to database.")

@bp.route('/delete_candidate/<int:candidate_id>', methods=['POST'])
@login_required
def delete_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    project_id = request.form.get('project_id')
    if not project_id:
        flash('Project ID is missing.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Authorization check: ensure the user has rights to delete from this project
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        abort(403)

    db.session.delete(candidate)
    db.session.commit()
    flash('Candidate and all associated research have been deleted.', 'success')
    return redirect(url_for('main.project', project_id=project_id))


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
