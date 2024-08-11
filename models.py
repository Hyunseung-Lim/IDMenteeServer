from flask_login import UserMixin
from __init__ import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    realPassword = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    num = db.Column(db.Integer)
    currentRound = db.Column(db.Integer)

class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    round = db.Column(db.Integer)
    category = db.Column(db.String(10))
    topic = db.Column(db.String(10))
    design_goals = db.Column(db.JSON)
    title = db.Column(db.String(1000))
    target_problem = db.Column(db.String(1000))
    idea = db.Column(db.String(1000))

# class Note(db.Model):
#     id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     content = db.Column(db.String(100))
#     position = db.Column(db.JSON)

class InitialSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    mode = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    round = db.Column(db.Integer)
    character = db.Column(db.Integer)
    goal1 = db.Column(db.String(1000))
    goal2 = db.Column(db.String(1000))
    goal3 = db.Column(db.String(1000))
    time = db.Column(db.Integer)

class KnowledgeState(db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    round = db.Column(db.Integer)
    face = db.Column(db.Integer)
    # opportunity = db.Column(db.String(1000))
    # consideration = db.Column(db.String(1000))
    q_num = db.Column(db.Integer)
    s_num = db.Column(db.Integer)
    c_num = db.Column(db.Integer)
    d_num = db.Column(db.Integer)
    # qns = db.Column(db.Integer) # question and statemnet
    # cnd = db.Column(db.Integer) # divergent and convergent
    eval = db.Column(db.JSON)
    knowledge = db.Column(db.String(3000))
    actionPlan = db.Column(db.String(3000))
    counter = db.Column(db.JSON)
 
class ChatLog(db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    round = db.Column(db.Integer)
    log = db.Column(db.JSON)

class UserLog(db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    round = db.Column(db.Integer)
    timestamp = db.Column(db.String(100))
    tag = db.Column(db.String(100))
    data = db.Column(db.JSON)

# class Log(db.Model):
#     id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     input = db.Column(db.String(1000))
#     output = db.Column(db.String(1000))
#     isStereo = db.Column(db.String(100))
#     initalTarget = db.Column(db.String(100))
#     targets = db.Column(db.JSON)
#     relation = db.Column(db.String(100))
#     familiar = db.Column(db.String(100))
#     degree = db.Column(db.String(100))
#     context = db.Column(db.String(100))
#     isWordIssue = db.Column(db.String(100))
#     words = db.Column(db.JSON)
#     ambiguous = db.Column(db.String(1000))

# class Activity(db.Model):
#     id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     time = db.Column(db.String(100))
#     log_id = db.Column(db.String(100))
#     state = db.Column(db.String(100))
#     note = db.Column(db.String(100))

# class Post(db.Model):
#     id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
#     post_num = db.Column(db.Integer)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     user = db.relationship('User', backref=db.backref('user', lazy=True))
#     post_image = db.Column(db.String(1000))
#     post_text = db.Column(db.JSON)