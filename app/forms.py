from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, URL
from app.models import User, Project

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    master_prompt = TextAreaField('Master Prompt', validators=[DataRequired()])
    submit = SubmitField('Create Project')

class ResearchForm(FlaskForm):
    linkedin_url = StringField('Candidate LinkedIn URL', validators=[DataRequired(), URL()])
    submit_research = SubmitField('Add Candidate and Perform Research')

class SettingsForm(FlaskForm):
    dark_theme = BooleanField('Dark Mode')
    advanced_mode = BooleanField('Advanced Mode')
    research_model = SelectField('Research Model', choices=[
        ('sonar-deep-research', 'Sonar Deep Research'),
        ('sonar-pro', 'Sonar Pro')
    ])
    submit = SubmitField('Save Settings')

class EditPromptForm(FlaskForm):
    text = TextAreaField('Master Prompt', validators=[DataRequired()])
    submit_prompt = SubmitField('Update Prompt')
