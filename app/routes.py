from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Candidate, Research
from app.forms import LoginForm, RegistrationForm, ResearchForm
import requests # We'll use this to simulate the LLM call

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = ResearchForm()
    if form.validate_on_submit():
        # Mock LLM research
        # In a real app, you would call the LLM API here
        mock_result = f"This is a mock research result for {form.linkedin_url.data} based on the prompt: '{form.prompt.data}'"
        
        # Check if candidate exists, or create a new one
        candidate = Candidate.query.filter_by(linkedin_url=form.linkedin_url.data).first()
        if candidate is None:
            candidate = Candidate(linkedin_url=form.linkedin_url.data)
            db.session.add(candidate)
        
        # Create and save the research record
        research = Research(
            prompt=form.prompt.data,
            result=mock_result,
            candidate=candidate,
            user_id=current_user.id
        )
        db.session.add(research)
        db.session.commit()
        
        flash('Research has been completed and saved!')
        return redirect(url_for('main.index'))
    
    researches = Research.query.filter_by(user_id=current_user.id).order_by(Research.id.desc()).all()
    return render_template('index.html', title='Home', form=form, researches=researches)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

