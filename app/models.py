from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    projects = db.relationship('Project', backref='creator', lazy='dynamic')
    researches = db.relationship('Research', backref='user', lazy='dynamic')
    _settings = db.relationship('UserSettings', back_populates='user', uselist=False, cascade="all, delete-orphan")

    @property
    def settings(self):
        if self._settings is None:
            self._settings = UserSettings()
        return self._settings

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# Association table for the many-to-many relationship between Project and Candidate
project_candidates = db.Table('project_candidates',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('candidate_id', db.Integer, db.ForeignKey('candidate.id'), primary_key=True)
)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    researches = db.relationship('Research', backref='project', lazy='dynamic')
    candidates = db.relationship(
        'Candidate',
        secondary=project_candidates,
        backref=db.backref('projects', lazy='dynamic'),
        lazy='dynamic'
    )
    prompts = db.relationship('Prompt', backref='project', lazy='dynamic', order_by=lambda: Prompt.created_at.desc(), cascade="all, delete-orphan")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def master_prompt(self):
        latest_prompt = self.prompts.first()
        return latest_prompt.text if latest_prompt else "No prompt set."

    def __repr__(self):
        return f'<Project {self.name}>'

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    linkedin_url = db.Column(db.String(256), index=True, unique=True)
    researches = db.relationship('Research', backref='candidate', lazy='dynamic', cascade="all, delete-orphan")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Candidate {self.linkedin_url}>'

class Research(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    prompt_id = db.Column(db.Integer, db.ForeignKey('prompt.id'))
    prompt = db.relationship('Prompt', backref='researches')
    overall_score = db.Column(db.Integer)
    summary = db.Column(db.Text)
    full_report = db.Column(db.Text)
    full_research = db.Column(db.Text)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Research {self.id}>'

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    theme = db.Column(db.String(10), nullable=False, default='light')
    advanced_mode = db.Column(db.Boolean, nullable=False, default=False)
    research_model = db.Column(db.String(50), nullable=False, default='sonar-deep-research')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    user = db.relationship('User', back_populates='_settings')

    def __repr__(self):
        return f'<UserSettings for User {self.user_id}>'

class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Prompt {self.id} for Project {self.project_id}>'
