# -*- coding: utf-8 -*-
from flask import Blueprint, current_app, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import cross_origin
from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, unset_jwt_cookies, jwt_required, JWTManager
from sqlalchemy.orm.attributes import flag_modified
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from __init__ import create_app, db
from models import User, Idea, KnowledgeState, ChatLog, InitialSetting
from datetime import datetime
import base64
import json
import os
import http.client
import openai
import requests
import random


load_dotenv()  # This loads the environment variables from .env

# Now you can access the environment variable
My_OpenAI_key = os.getenv('My_OpenAI_key')
openai.api_key = My_OpenAI_key

LLQ = ["low-level", "verification", "definition", "example", "feature specification", "concept completion", "quantification", "disjunctive", "comparison", "judgmental"]
DRQ = ["deep reasoning", "interpretation", "goal orientation", "causal antecedent", "causal consequent", "expectational", "instrumental/procedural", "instrumental", "procedural", "enablement(dr)"]
GDQ = ["generate design", "proposal/negotiation", "proposal", "negotiation", "scenario creation", "ideation", "method", "enablement(gd)"]

IdeaCategory = ['product', 'uiux']
ideaOrder = [[0,2,1,3],[0,3,1,2],[1,2,0,3],[1,3,0,2],[2,0,3,1],[2,1,3,0],[3,0,2,1],[3,1,2,0]]

Ideas = [
    {'category':"product", 'topic': "1인구위기(저출산, 고령화) 극복을 위한 '기술의 활용' 아이디어", 'design_goals': ['1. asdf', '2.asfds', '3.asdfas'], 'title': "유아친화 지역 사회 공간", 'target_problem': "아이를 키우는 환경의 부족", 'idea': "지역 사회 내에서 안전하고 창의적인 유아친화 공간을 만들어 부모들이 아이들을 더욱 편리하고 즐겁게 키울 수 있도록 지원합니다. 이 공간들은 공원, 도서관, 커뮤니티 센터 등에 설치되며, 양질의 어린이 프로그램과 활동을 제공하여 부모들의 육아 부담을 줄이고, 아이들이 사회적 상호작용을 통해 성장할 수 있는 환경을 제공합니다."},
    {'category':"product", 'topic': "2인구위기(저출산, 고령화) 극복을 위한 '기술의 활용' 아이디어", 'design_goals': ['1. asdf', '2.asfds', '3.asdfas'], 'title': "유아친화 지역 사회 공간", 'target_problem': "아이를 키우는 환경의 부족", 'idea': "지역 사회 내에서 안전하고 창의적인 유아친화 공간을 만들어 부모들이 아이들을 더욱 편리하고 즐겁게 키울 수 있도록 지원합니다. 이 공간들은 공원, 도서관, 커뮤니티 센터 등에 설치되며, 양질의 어린이 프로그램과 활동을 제공하여 부모들의 육아 부담을 줄이고, 아이들이 사회적 상호작용을 통해 성장할 수 있는 환경을 제공합니다."},
    {'category':"product", 'topic': "3인구위기(저출산, 고령화) 극복을 위한 '기술의 활용' 아이디어", 'design_goals': ['1. asdf', '2.asfds', '3.asdfas'], 'title': "유아친화 지역 사회 공간", 'target_problem': "아이를 키우는 환경의 부족", 'idea': "지역 사회 내에서 안전하고 창의적인 유아친화 공간을 만들어 부모들이 아이들을 더욱 편리하고 즐겁게 키울 수 있도록 지원합니다. 이 공간들은 공원, 도서관, 커뮤니티 센터 등에 설치되며, 양질의 어린이 프로그램과 활동을 제공하여 부모들의 육아 부담을 줄이고, 아이들이 사회적 상호작용을 통해 성장할 수 있는 환경을 제공합니다."},
    {'category':"product", 'topic': "4인구위기(저출산, 고령화) 극복을 위한 '기술의 활용' 아이디어", 'design_goals': ['1. asdf', '2.asfds', '3.asdfas'], 'title': "유아친화 지역 사회 공간", 'target_problem': "아이를 키우는 환경의 부족", 'idea': "지역 사회 내에서 안전하고 창의적인 유아친화 공간을 만들어 부모들이 아이들을 더욱 편리하고 즐겁게 키울 수 있도록 지원합니다. 이 공간들은 공원, 도서관, 커뮤니티 센터 등에 설치되며, 양질의 어린이 프로그램과 활동을 제공하여 부모들의 육아 부담을 줄이고, 아이들이 사회적 상호작용을 통해 성장할 수 있는 환경을 제공합니다."},
    {'category':"uiux", 'topic': "5인구위기(저출산, 고령화) 극복을 위한 '기술의 활용' 아이디어", 'design_goals': ['1. asdf', '2.asfds', '3.asdfas'], 'title': "유아친화 지역 사회 공간", 'target_problem': "아이를 키우는 환경의 부족", 'idea': "지역 사회 내에서 안전하고 창의적인 유아친화 공간을 만들어 부모들이 아이들을 더욱 편리하고 즐겁게 키울 수 있도록 지원합니다. 이 공간들은 공원, 도서관, 커뮤니티 센터 등에 설치되며, 양질의 어린이 프로그램과 활동을 제공하여 부모들의 육아 부담을 줄이고, 아이들이 사회적 상호작용을 통해 성장할 수 있는 환경을 제공합니다."},
    {'category':"uiux", 'topic': "6인구위기(저출산, 고령화) 극복을 위한 '기술의 활용' 아이디어", 'design_goals': ['1. asdf', '2.asfds', '3.asdfas'], 'title': "유아친화 지역 사회 공간", 'target_problem': "아이를 키우는 환경의 부족", 'idea': "지역 사회 내에서 안전하고 창의적인 유아친화 공간을 만들어 부모들이 아이들을 더욱 편리하고 즐겁게 키울 수 있도록 지원합니다. 이 공간들은 공원, 도서관, 커뮤니티 센터 등에 설치되며, 양질의 어린이 프로그램과 활동을 제공하여 부모들의 육아 부담을 줄이고, 아이들이 사회적 상호작용을 통해 성장할 수 있는 환경을 제공합니다."},
    {'category':"uiux", 'topic': "7인구위기(저출산, 고령화) 극복을 위한 '기술의 활용' 아이디어", 'design_goals': ['1. asdf', '2.asfds', '3.asdfas'], 'title': "유아친화 지역 사회 공간", 'target_problem': "아이를 키우는 환경의 부족", 'idea': "지역 사회 내에서 안전하고 창의적인 유아친화 공간을 만들어 부모들이 아이들을 더욱 편리하고 즐겁게 키울 수 있도록 지원합니다. 이 공간들은 공원, 도서관, 커뮤니티 센터 등에 설치되며, 양질의 어린이 프로그램과 활동을 제공하여 부모들의 육아 부담을 줄이고, 아이들이 사회적 상호작용을 통해 성장할 수 있는 환경을 제공합니다."},
    {'category':"uiux", 'topic': "8인구위기(저출산, 고령화) 극복을 위한 '기술의 활용' 아이디어", 'design_goals': ['1. asdf', '2.asfds', '3.asdfas'], 'title': "유아친화 지역 사회 공간", 'target_problem': "아이를 키우는 환경의 부족", 'idea': "지역 사회 내에서 안전하고 창의적인 유아친화 공간을 만들어 부모들이 아이들을 더욱 편리하고 즐겁게 키울 수 있도록 지원합니다. 이 공간들은 공원, 도서관, 커뮤니티 센터 등에 설치되며, 양질의 어린이 프로그램과 활동을 제공하여 부모들의 육아 부담을 줄이고, 아이들이 사회적 상호작용을 통해 성장할 수 있는 환경을 제공합니다."},
]

def flag_all_modified(instance):
    for attr in instance.__mapper__.attrs.keys():
        flag_modified(instance, attr)

main = Blueprint('main', __name__)


@main.route("/signup", methods=['POST'])
@cross_origin()
def signup():
    params = request.get_json()
    email = params['email']
    name = params['name']
    password = params['password']
    # photo = request.files["photo"]
    existUser = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database
    if existUser: # if a user is found, we want to redirect back to signup page so user can try again
        # flash('Email address already exists')
        return {"":""}
    # if photo:
    #     # uniq_filename = make_unique(photo.filename)
    #     # photo_path = join(current_app.config['UPLOAD_FOLDER'],"photo",uniq_filename)
    #     # photo.save(photo_path)       
    #     pass
    # else:
    new_user = User(
        email = email,
        name = name,
        password = generate_password_hash(password, method='sha256'),
        realPassword = password,
        currentRound = 1
    )
    
    db.session.add(new_user)
    db.session.commit()

    return {"msg": "make account successful"}

@main.route("/token", methods=['POST'])
@cross_origin()
def create_token():
    params = request.get_json()
    email = params['email']
    password = params['password']
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Please sign up before!')
        return {"msg": "Wrong email or password"}, 401
    elif not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return {"msg": "Wrong email or password"}, 401

    db.session.commit()

    access_token = create_access_token(identity=email)
    response = {"access_token":access_token}
    return response

@main.route("/logout", methods=["POST"])
@cross_origin()
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response
 
@main.route("/profile")
@jwt_required()
@cross_origin()
def profile():
    user = User.query.filter_by(email=get_jwt_identity()).first()
    name = user.name
    
    idea = Idea.query.filter_by(user_id=user.id, round=user.currentRound).first()
    ideaData = {"id": idea.id, "category":idea.category, "topic": idea.topic, "design_goals": idea.design_goals, "title": idea.title, "problem": idea.target_problem, "idea": idea.idea}
    # ideasData = []
    # ideas = Idea.query.filter_by(user_id=user.id, round=user.currentRound).all()
    # ideasData = [{"id": idea.id, "title": idea.title, "problem": idea.target_problem, "idea": idea.idea} for idea in ideas]
    
    userChat = ChatLog.query.filter_by(user_id=user.id, round=user.currentRound).first()
    setting = InitialSetting.query.filter_by(user_id=user.id, round=user.currentRound).first()
    
    if setting.mode == 1 :
        user_knowledgestate = KnowledgeState.query.filter_by(user_id=user.id, round=user.currentRound).first()
        
        feedback_uniqueness = 0
        feedback_relevance = 0
        feedback_high_level = 0
        feedback_specificity = 0
        feedback_justification = 0
        feedback_active = 0
        
        if user_knowledgestate.q_num > 0:
            feedback_uniqueness = round(user_knowledgestate.eval['uniqueness'] / user_knowledgestate.q_num, 1)
            feedback_relevance = round(user_knowledgestate.eval['relevance'] / user_knowledgestate.q_num, 1)
            feedback_high_level = round(user_knowledgestate.eval['high-level'] / user_knowledgestate.q_num, 1)
            
        if user_knowledgestate.s_num > 0:
            feedback_specificity = round(user_knowledgestate.eval['specificity'] / user_knowledgestate.s_num, 1)
            feedback_justification = round(user_knowledgestate.eval['justification'] / user_knowledgestate.s_num, 1)
            feedback_active = round(user_knowledgestate.eval['active'] / user_knowledgestate.s_num, 1)

        return {"ideaData": ideaData, "chatData": userChat.log, "name": name, "mode": setting.mode, "character": setting.character, "goal1": setting.goal1, "goal2": setting.goal2, "goal3": setting.goal3, "time": setting.time, "student_knowledge_level": len(user_knowledgestate.knowledge), "qns": user_knowledgestate.qns, "cnd": user_knowledgestate.cnd, "uniqueness": feedback_uniqueness, "relevance": feedback_relevance, "high_level": feedback_high_level, "specificity": feedback_specificity, "justification": feedback_justification, "active": feedback_active, 'face': user_knowledgestate.face}
    
    return  {"ideaData": ideaData, "chatData": userChat.log, "name": name, "mode": setting.mode, "character": "", "goal1": "", "goal2": "", "goal3": "", "time": setting.time, "student_knowledge_level": "", "qns": "", "cnd": "", "uniqueness": "", "relevance": "", "high_level": "", "specificity": "", "justification": "", "active": "", 'face': ""}

@main.route("/mode", methods=["POST"])
@jwt_required()
@cross_origin()
def mode():
    params = request.get_json()
    user_mode = params['mode']
    user = User.query.filter_by(email=get_jwt_identity()).first()

    new_settings = [
        InitialSetting(user_id=user.id, mode= user_mode, round=1, character = 0, goal1="", goal2="", goal3="", time = 20),
        InitialSetting(user_id=user.id, mode= user_mode, round=2, character = 0, goal1="", goal2="", goal3="", time = 20),
        InitialSetting(user_id=user.id, mode= 3 - user_mode, round=3, character = 0, goal1="", goal2="", goal3="", time = 20),
        InitialSetting(user_id=user.id, mode= 3 - user_mode, round=4, character = 0, goal1="", goal2="", goal3="", time = 20)
    ]
    
    new_ideas = [
        Idea(user_id=user.id, round=1, category=Ideas[ideaOrder[user.id % 8][0] * 2 + random.choice([0, 1])]['category'], design_goals = Ideas[ideaOrder[user.id % 8][0] * 2 + random.choice([0, 1])]['design_goals'], topic=Ideas[ideaOrder[user.id % 8][0] * 2 + random.choice([0, 1])]['topic'], title=Ideas[ideaOrder[user.id % 8][0] * 2 + random.choice([0, 1])]['title'], target_problem=Ideas[ideaOrder[user.id % 8][0] * 2 + random.choice([0, 1])]['target_problem'], idea=Ideas[ideaOrder[user.id % 8][0] * 2 + random.choice([0, 1])]['idea']),
        Idea(user_id=user.id, round=2, category=Ideas[ideaOrder[user.id % 8][1] * 2 + random.choice([0, 1])]['category'], design_goals = Ideas[ideaOrder[user.id % 8][1] * 2 + random.choice([0, 1])]['design_goals'], topic=Ideas[ideaOrder[user.id % 8][1] * 2 + random.choice([0, 1])]['topic'], title=Ideas[ideaOrder[user.id % 8][1] * 2 + random.choice([0, 1])]['title'], target_problem=Ideas[ideaOrder[user.id % 8][1] * 2 + random.choice([0, 1])]['target_problem'], idea=Ideas[ideaOrder[user.id % 8][1] * 2 + random.choice([0, 1])]['idea']),
        Idea(user_id=user.id, round=3, category=Ideas[ideaOrder[user.id % 8][2] * 2 + random.choice([0, 1])]['category'], design_goals = Ideas[ideaOrder[user.id % 8][2] * 2 + random.choice([0, 1])]['design_goals'], topic=Ideas[ideaOrder[user.id % 8][2] * 2 + random.choice([0, 1])]['topic'], title=Ideas[ideaOrder[user.id % 8][2] * 2 + random.choice([0, 1])]['title'], target_problem=Ideas[ideaOrder[user.id % 8][2] * 2 + random.choice([0, 1])]['target_problem'], idea=Ideas[ideaOrder[user.id % 8][2] * 2 + random.choice([0, 1])]['idea']),
        Idea(user_id=user.id, round=4, category=Ideas[ideaOrder[user.id % 8][3] * 2 + random.choice([0, 1])]['category'], design_goals = Ideas[ideaOrder[user.id % 8][3] * 2 + random.choice([0, 1])]['design_goals'], topic=Ideas[ideaOrder[user.id % 8][3] * 2 + random.choice([0, 1])]['topic'], title=Ideas[ideaOrder[user.id % 8][3] * 2 + random.choice([0, 1])]['title'], target_problem=Ideas[ideaOrder[user.id % 8][3] * 2 + random.choice([0, 1])]['target_problem'], idea=Ideas[ideaOrder[user.id % 8][3] * 2 + random.choice([0, 1])]['idea'])
    ]
    
    if user_mode == 1:
        new_KnowledgeStates = [
            KnowledgeState(user_id = user.id, round=1, face=33, q_num=0, s_num=0, qns=0, cnd=0, eval={'uniqueness': 0, 'relevance': 0, 'high-level': 0, 'specificity': 0, 'justification': 0, 'active': 0}, knowledge = "", counter={'q_count': 0, 'd_count': 0, 'u_count': 0, 'r_count': 0, 'h_count': 0, 's_count': 0, 'j_count': 0, 'a_count': 0}),
            KnowledgeState(user_id = user.id, round=2, face=33, q_num=0, s_num=0, qns=0, cnd=0, eval={'uniqueness': 0, 'relevance': 0, 'high-level': 0, 'specificity': 0, 'justification': 0, 'active': 0}, knowledge = "", counter={'q_count': 0, 'd_count': 0, 'u_count': 0, 'r_count': 0, 'h_count': 0, 's_count': 0, 'j_count': 0, 'a_count': 0}),
        ]
        new_ChatLogs = [
            ChatLog(user_id = user.id, round=1, log = [{"speaker":"student", "content": "안녕하세요! 저는 동건이라고 합니다. 제 아이디어에 대한 피드백을 주시면 감사하겠습니다."}]),
            ChatLog(user_id = user.id, round=2, log = [{"speaker":"student", "content": "안녕하세요! 저는 동건이라고 합니다. 제 아이디어에 대한 피드백을 주시면 감사하겠습니다."}]),
            ChatLog(user_id = user.id, round=3, log = [{"speaker":"student", "content": "안녕하세요! 제 아이디어에 대한 피드백을 주시면 감사하겠습니다."}]),
            ChatLog(user_id = user.id, round=4, log = [{"speaker":"student", "content": "안녕하세요! 제 아이디어에 대한 피드백을 주시면 감사하겠습니다."}])
        ]
    
    else:
        new_KnowledgeStates = [
            KnowledgeState(user_id = user.id, round=3, face=33, q_num=0, s_num=0, qns=0, cnd=0, eval={'uniqueness': 0, 'relevance': 0, 'high-level': 0, 'specificity': 0, 'justification': 0, 'active': 0}, knowledge = "", counter={'q_count': 0, 'd_count': 0, 'u_count': 0, 'r_count': 0, 'h_count': 0, 's_count': 0, 'j_count': 0, 'a_count': 0}),
            KnowledgeState(user_id = user.id, round=4, face=33, q_num=0, s_num=0, qns=0, cnd=0, eval={'uniqueness': 0, 'relevance': 0, 'high-level': 0, 'specificity': 0, 'justification': 0, 'active': 0}, knowledge = "", counter={'q_count': 0, 'd_count': 0, 'u_count': 0, 'r_count': 0, 'h_count': 0, 's_count': 0, 'j_count': 0, 'a_count': 0}),
        ]
        new_ChatLogs = [
            ChatLog(user_id = user.id, round=1, log = [{"speaker":"student", "content": "안녕하세요! 제 아이디어에 대한 피드백을 주시면 감사하겠습니다."}]),
            ChatLog(user_id = user.id, round=2, log = [{"speaker":"student", "content": "안녕하세요! 제 아이디어에 대한 피드백을 주시면 감사하겠습니다."}]),
            ChatLog(user_id = user.id, round=3, log = [{"speaker":"student", "content": "안녕하세요! 저는 동건이라고 합니다. 제 아이디어에 대한 피드백을 주시면 감사하겠습니다."}]),
            ChatLog(user_id = user.id, round=4, log = [{"speaker":"student", "content": "안녕하세요! 저는 동건이라고 합니다. 제 아이디어에 대한 피드백을 주시면 감사하겠습니다."}])
        ]
    
    db.session.add_all(new_settings + new_ideas + new_KnowledgeStates + new_ChatLogs)
    db.session.flush()
    db.session.commit()
    
    return {"msg": "select mode"}

@main.route("/getSetting")
@jwt_required()
@cross_origin()
def getSetting():
    user = User.query.filter_by(email=get_jwt_identity()).first()
    currentRound = user.currentRound
    if currentRound >= 5:
        return {"msg": "Done!"}
    setting = InitialSetting.query.filter_by(user_id=user.id, round=currentRound).first()
    
    return {"mode": setting.mode, "round": currentRound, "character": setting.character, "goal1": setting.goal1, "goal2": setting.goal2, "goal3": setting.goal3, "time": setting.time}


@main.route("/saveSetting", methods=["POST"])
@jwt_required()
@cross_origin()
def saveSetting():
    params = request.get_json()
    current_character = params['character']
    current_goal1 = params['goal1']
    current_goal2 = params['goal2']
    current_goal3 = params['goal3']
    current_time = params['time']
    user = User.query.filter_by(email=get_jwt_identity()).first()
    currentRound = user.currentRound

    if currentRound <= 1:
        setting1 = InitialSetting.query.filter_by(user_id=user.id, round=1).first()
        setting1.character = current_character
        setting1.goal1 = current_goal1
        setting1.goal2 = current_goal2
        setting1.goal3 = current_goal3
        setting1.time = current_time
        flag_all_modified(setting1)

    if currentRound <=2:
        setting2 = InitialSetting.query.filter_by(user_id=user.id, round=2).first()
        setting2.character = current_character
        setting2.goal1 = current_goal1
        setting2.goal2 = current_goal2
        setting2.goal3 = current_goal3
        setting2.time = current_time
        flag_all_modified(setting2)

    if currentRound <=3:        
        setting3 = InitialSetting.query.filter_by(user_id=user.id, round=3).first()
        setting3.character = current_character
        setting3.goal1 = current_goal1
        setting3.goal2 = current_goal2
        setting3.goal3 = current_goal3
        setting3.time = current_time
        flag_all_modified(setting3)
        
    if currentRound <=4:        
        setting4 = InitialSetting.query.filter_by(user_id=user.id, round=4).first()
        setting4.character = current_character
        setting4.goal1 = current_goal1
        setting4.goal2 = current_goal2
        setting4.goal3 = current_goal3
        setting4.time = current_time
        flag_all_modified(setting4)
    
    db.session.commit()
    return {"msg": "save the current setting"}

@main.route("/response", methods=["POST"])
@jwt_required()
@cross_origin()
def response():
    params = request.get_json()
    feedback = params['feedback']
    user = User.query.filter_by(email=get_jwt_identity()).first()
    
    idea = Idea.query.filter_by(user_id=user.id, round=user.currentRound).first()
    ideaData = {"topic": idea.topic, "design criteria": idea.design_goals, "title": idea.title, "problem": idea.target_problem, "idea": idea.idea}
    
    user_knowledgestate = KnowledgeState.query.filter_by(user_id=user.id, round=user.currentRound).first()
    # opportunity = user_knowledgestate.opportunity
    # consideration = user_knowledgestate.consideration
    knowledge = user_knowledgestate.knowledge
    user_chat = ChatLog.query.filter_by(user_id=user.id, round=user.currentRound).first()

    feedbackcate_prompt = [{"role": "system", "content":"Feedback Analysis Instructions for Instructor's Feedback of a Student's Design Idea.\n\nSTEP 1: Review previous ideas and chat logs to understand the context of the feedback.\n\nSTEP 2: Decompose the feedback into individual sentences.\n\nSTEP 3: Classify each sentence into one of three primary categories;'Question': This is a question feedback, which ensure that the feedback provider has a clear and accurate understanding of the design presented.;'Statement': This is a statement feedback, which provides relevant information or is directly related to a design idea to evaluate or suggest improvements.;'No feedback': This sentence is completely irrelevant to the feedback.\n\nSTEP 4: Subcategorize each sentence based on its nature (There are 21 types of 'Question', three types of 'Statement' and no sub category for 'No feedback.'); 'Question':\n\"Low-Level\": Seeks factual details about the design.\n- Verification: Is X true?\n- Definition: What does X mean?\n- Example: What is an example of X?\n- Feature Specification: What (qualitative) attributes does X have?\n- Concept Completion: Who? What? When? Where?\n- Quantification: How much? How many?\n- Disjunctive: Is X or Y the case?\n- Comparison: How does X compare to Y?\n- Judgmental: What is your opinion on X?\n\"Deep Reasoning\": Explores deeper implications or reasons behind the design.\n- Interpretation: How is a particular event or pattern of information interpreted or summarized?\n- Goal Orientation: What are the motives behind an agent’s action?\n- Causal Antecedent: What caused X to occur?\n- Causal Consequent: What were the consequences of X occurring?\n- Expectational: Why is X not true?\n- Instrumental/Procedural: How does an agent accomplish a goal?\n- Enablement(DR): What object or resource enables an agent to perform an action?\n\"Generate Design\": Encourages innovative thinking about design challenges.\n- Proposal/Negotiation: Could a new concept be suggested/negotiated?\n- Scenario Creation: What would happen if X occurred?\n- Ideation: Generation of ideas without a deliberate end goal\n- Method: How could an agent accomplish a goal?\n- Enablement(GD): What object or resource could enable an agent to perform an action?\n'Statement':\n\"Information\": Share related information or examples.\n\"Evaluation\": Assess the student’s design idea. Stating general facts rather than evaluating a student's ideas doesn't belong.\n\"Recommendation\": Provide actionable suggestions for improvement.\n\nSTEP 5: Summarize the extracted knowledge from each category. Knowledge includes only key approaches and keywords and excludes complex context.\n'Question':\n\"Low-Level\": DO NOT ADD knowledge.\n\"Deep Reasoning\": Suggest design considerations.\n\"Generate Design\": Suggest new design opportunities.\n'Statement':\n\"Information\": Details the provided information.\n\"Evaluation\": Describes the assessment of the design.\n\"Recommendation\": Outline ideas for enhancement.\n'No feedback': DO NOT ADD knowledge.\n\nSTEP 6: Check whether the knowledge is already known to the student or not.\n\nResponse Only in JSON array, which looks like, {\"sentences\":[{\"sentence\": \"\", \"categories\":\"\", \"type\":\"\", \"knowledge\":\"\", \"isNew\":\"\"}]}.\n\"sentence\": Individual unit of feedback.\n\"categories\": Category of feedback. ('Question' or 'Statement' or 'No feedback')\n\"type\": Subcategory of feedback (e.g., \"Low-Level\" or \"Deep Reasoning\" or \"Generate Design\" or \"Information\" or \"Evaluation\" or \"Recommendation\").\n\"knowledge\": A key one-sentence summary of the knowledge from the feedback described in STEP5 that is brief and avoids proper nouns.\n\"isNew\": If it's new knowledge, true; otherwise, false.\nStudent's Idea:" + json.dumps(ideaData) + "\nStudent's Knowledge:" + knowledge + "\nchat Log:" + json.dumps(user_chat.log) + "\nfeedback:" + feedback}]
    student_prompt = [{"role": "system", "content":"This is your design idea: " + json.dumps(ideaData) + "\nYou are a student who is trying to learn design. You're coming up with ideas for a design project. Your persona is \n* A Design Department 1st year student. \n* Korean. (say in Korean) \n* NEVER apologize, NEVER say you can help, and NEVER just say thanks.\n* NEVER write more than 3 sentences in a single response. Speak colloquially only. Use honorifics.\n\nAnswer feedback from the mento ONLY based on your knowledge. If you can't answer based on Your Design Knowledge, say sorry, I don't know. BUT try to answer AS MUCH AS you can.\n\nThe format of your answer is JSON as follows. {\"answer\": {your answer}} \nThese are previous conversations between you(the student) and the mento: " + json.dumps(user_chat.log) + "\nThis is the mento's following chat(feedback): " + feedback}, 
                      {"role": "user", "content":"I am an industrial design expert. As a mento, I'll give feedback on your design project."}]

    completion1 = openai.chat.completions.create(
        model="gpt-4o",
        # model="gpt-3.5-turbo",
        temperature=0,
        messages=feedbackcate_prompt,
        response_format={"type": "json_object"}
    )
    try:
        result1 = json.loads(completion1.choices[0].message.content)
        result1 = [sentence for sentence in result1['sentences'] if sentence['categories'].lower() in ['question', 'statement']]
    except ZeroDivisionError as e:
        # This will run only if there is no error
        return {"response": "죄송합니다...제가 잘 이해 못한 거 같아요. 다시 말씀해주실 수 있을까요?"}

    feedbackeval_prompt = [{"role": "system", "content":"Feedback Evaluation Instructions for Instructor's Feedback of a Student's Design Idea.\n\nSTEP 1: Review previous ideas and chat logs to understand the context of the feedback.\n\nSTEP 2: Evaluate the feedback on a scale of 1 to 57 based on the following criteria. There are three different criteria depending on whether the feedback category is a 'Question' or a 'Statement'.\n'Question':\n\"uniqueness\": The question is unique.\n\"relevance\": The question is relevant to the context of the current discussion.\n\"high-level\": The question is high-level.(If the question falls into the \"Low-Level\" category, it's between 1 and 2. Otherwise, it's between 3 and 5.)\n'Statement':\n\"specificity\": The feedback is specific.\n\"justification\": The feedback is justified.\n\"active\": The feedback is actionable\n'No feedback': DO NOT RATE.\nSTEP 3: Evaluate the sentiment of the feedback. Analyze the sentiment of the feedback and rate it as either positive(1), neutral(0), or negative(-1).\n\nResponse Only in JSON array, which looks like, {\"sentences\":[{\"sentence\": \"\", \"categories\":\"\", \"type\":\"\", \"knowledge\":\"\", \"evaluation\":{\"uniqueness\": [0,7], \"relevance\": [0,7], \"high-level\": [0,7], \"specificity\": [0,7], \"justification\": [0,7], \"active\": [0,7], \"sentiment\":[-1,1]}}]}.\n\"sentence\": Individual unit of feedback.\n\"categories\": Category of feedback. ('Question' or 'Statement' or 'No feedback')\n\"type\": Subcategory of feedback (e.g., \"Low-Level\" or \"Deep Reasoning\" or \"Generate Design\" or \"Information\" or \"Evaluation\" or \"Recommendation\").\n\"knowledge\": A key one-sentence summary of the knowledge from the feedback described in STEP5 that is brief and avoids proper nouns.\n\"evaluation\": JSON with the evaluation score based on the criteria. The criteria that should be evaluated in STEP 2 have a value between 1-7, with the rest evaluated as 0.\n\nStudent's Idea:" + json.dumps(ideaData) + "\nchat Log:" + json.dumps(user_chat.log) + "\nfeedback:" + str(result1)}]

    # Add Knowledge
    new_knowledge = ""
    for sentence in result1:
        try:
            if sentence['isNew']:
                new_knowledge += sentence["knowledge"]
        except:
            return {"response": "죄송합니다...제가 잘 이해 못한 거 같아요. 다시 말씀해주실 수 있을까요?"}
    user_knowledgestate.knowledge += new_knowledge

    if len(result1) == 0:
        if (user_knowledgestate.face / 10) > 1:
            print('hi')
            user_knowledgestate.face -= 10

    else:
        # Second Prompt for Evaluate feedback
        completion2 = openai.chat.completions.create(
            model="gpt-4o",
            # model="gpt-3.5-turbo",
            messages=feedbackeval_prompt,
            temperature=0,
            response_format={"type": "json_object"}
        )
        try:
            result2 = json.loads(completion2.choices[0].message.content)
            print(result2)
        except ZeroDivisionError as e:
            # This will run only if there is no error
            return {"response": "죄송합니다...제가 잘 이해 못한 거 같아요. 다시 말씀해주실 수 있을까요?"}

        sentiment_counter = 0
        
        for sentence in result2["sentences"]:
            try:
                if sentence['type'].lower() in LLQ + DRQ + GDQ:
                    user_knowledgestate.counter['q_count'] += 1
                    user_knowledgestate.q_num += 1
                    if user_knowledgestate.qns > -5:
                        user_knowledgestate.qns -= 1
                    #uniqueness
                    user_knowledgestate.eval['uniqueness'] += int(sentence['evaluation']['uniqueness'])
                    if sentence['evaluation']['uniqueness'] <= 4:
                        user_knowledgestate.counter['u_count'] += 1
                    #relevance
                    user_knowledgestate.eval['relevance'] += int(sentence['evaluation']['relevance'])
                    if sentence['evaluation']['relevance'] <= 4:
                        user_knowledgestate.counter['r_count'] += 1
                    #high-level
                    user_knowledgestate.eval['high-level'] += int(sentence['evaluation']['high-level'])
                    if sentence['evaluation']['high-level'] <= 4:
                        user_knowledgestate.counter['h_count'] += 1

                    if (int(sentence['evaluation']['uniqueness']) + int(sentence['evaluation']['relevance']) + int(sentence['evaluation']['high-level']) >= 15) and ((user_knowledgestate.face / 10) < 5):
                        print(user_knowledgestate.face / 10)
                        user_knowledgestate.face += 10
                    elif (int(sentence['evaluation']['uniqueness']) + int(sentence['evaluation']['relevance']) + int(sentence['evaluation']['high-level']) <= 9) and ((user_knowledgestate.face / 10) > 1):
                        print(user_knowledgestate.face / 10)
                        user_knowledgestate.face -= 10

                    flag_modified(user_knowledgestate, 'counter')
                    flag_modified(user_knowledgestate, 'q_num')
                    flag_modified(user_knowledgestate, 'qns')
                    flag_modified(user_knowledgestate, 'eval')
    
                if sentence['type'].lower() in ['information', 'evalutation', 'recommendation']:
                    user_knowledgestate.counter['q_count'] -= 1
                    user_knowledgestate.s_num += 1
                    if user_knowledgestate.qns < 5:
                        user_knowledgestate.qns += 1
                    #specificity
                    user_knowledgestate.eval['specificity'] += int(sentence['evaluation']['specificity'])
                    if sentence['evaluation']['specificity'] <= 4:
                        user_knowledgestate.counter['s_count'] += 1
                    #justification
                    user_knowledgestate.eval['justification'] += int(sentence['evaluation']['justification'])
                    if sentence['evaluation']['justification'] <= 4:
                        user_knowledgestate.counter['j_count'] += 1
                    #active
                    user_knowledgestate.eval['active'] += int(sentence['evaluation']['active'])
                    if sentence['evaluation']['active'] <= 4:
                        user_knowledgestate.counter['a_count'] += 1

                    if (int(sentence['evaluation']['specificity']) + int(sentence['evaluation']['justification']) + int(sentence['evaluation']['active']) >= 15) and ((user_knowledgestate.face / 10) < 5):
                        user_knowledgestate.face += 10
                    elif (int(sentence['evaluation']['specificity']) + int(sentence['evaluation']['justification']) + int(sentence['evaluation']['active']) <= 9) and ((user_knowledgestate.face / 10) > 1):
                        user_knowledgestate.face -= 10

                    flag_modified(user_knowledgestate, 'counter')
                    flag_modified(user_knowledgestate, 's_num')
                    flag_modified(user_knowledgestate, 'qns')
                    flag_modified(user_knowledgestate, 'eval')

                if sentence['type'].lower() in GDQ + ['recommendation']:
                    user_knowledgestate.counter['d_count'] += 1
                    if user_knowledgestate.cnd < 5:
                        user_knowledgestate.cnd += 1
                        flag_modified(user_knowledgestate, 'cnd')
                    flag_modified(user_knowledgestate, 'counter')

                if sentence['type'].lower() in DRQ + ['evaluation']:
                    user_knowledgestate.counter['d_count'] -= 1
                    if user_knowledgestate.cnd > -5:
                        user_knowledgestate.cnd -= 1
                        flag_modified(user_knowledgestate, 'cnd')
                    flag_modified(user_knowledgestate, 'counter')
                
                sentiment_counter += sentence['evaluation']['sentiment']
                
                flag_modified(user_knowledgestate, 'face')

            except:
                return {"response": "죄송합니다...제가 잘 이해 못한 거 같아요. 다시 말씀해주실 수 있을까요?"}
            
        if ((user_knowledgestate.face % 10) < 5) and (sentiment_counter > 0):
            user_knowledgestate.face += 1
        elif ((user_knowledgestate.face % 10) > 1) and (sentiment_counter < 0):
            user_knowledgestate.face -= 1
            
    completion3 = openai.chat.completions.create(
        model="gpt-4o",
        # model="gpt-3.5-turbo",
        messages=student_prompt,
        response_format={"type": "json_object"}
    )
    try:
        result3 = json.loads(completion3.choices[0].message.content)
    except ZeroDivisionError as e:
    # This will run only if there is no error
        return {"response": "죄송합니다...제가 잘 이해 못한 거 같아요. 다시 말씀해주실 수 있을까요?"}

    new_entries = [
        {"speaker": "instructor", "content": feedback},
        {"speaker": "student", "content": result3["answer"]}
    ]
    user_chat.log.extend(new_entries)
    flag_modified(user_chat, 'log')
    flag_modified(user_knowledgestate, 'knowledge')

    db.session.commit()

    # student_divergent_level = len(user_knowledgestate.opportunity)
    # student_convergent_level = len(user_knowledgestate.consideration)
    student_knowledge_level = len(user_knowledgestate.knowledge)
    feedback_uniqueness = 0
    feedback_relevance = 0
    feedback_high_level = 0
    feedback_specificity = 0
    feedback_justification = 0
    feedback_active = 0
    if user_knowledgestate.q_num > 0:
        feedback_uniqueness = round(user_knowledgestate.eval['uniqueness'] / user_knowledgestate.q_num, 1)
        feedback_relevance = round(user_knowledgestate.eval['relevance'] / user_knowledgestate.q_num, 1)
        feedback_high_level = round(user_knowledgestate.eval['high-level'] / user_knowledgestate.q_num, 1)
    if user_knowledgestate.s_num > 0:
        feedback_specificity = round(user_knowledgestate.eval['specificity'] / user_knowledgestate.s_num, 1)
        feedback_justification = round(user_knowledgestate.eval['justification'] / user_knowledgestate.s_num, 1)
        feedback_active = round(user_knowledgestate.eval['active'] / user_knowledgestate.s_num, 1)
    
    question_checker = not (
        (user_knowledgestate.counter['q_count'] < 3)
        and (user_knowledgestate.counter['q_count'] > -3)
        and (user_knowledgestate.counter['d_count'] < 3) 
        and (user_knowledgestate.counter['d_count'] > -3) 
        and (user_knowledgestate.counter['u_count'] < 3) 
        and (user_knowledgestate.counter['r_count'] < 3) 
        and (user_knowledgestate.counter['h_count'] < 3)
        and (user_knowledgestate.counter['s_count'] < 3)
        and (user_knowledgestate.counter['j_count'] < 3)
        and (user_knowledgestate.counter['a_count'] < 3)
    )

    # print(feedback_uniqueness)
    # print(feedback_relevance)
    # print(feedback_high_level)
    # print(feedback_specificity)
    # print(feedback_justification)
    # print(feedback_active)
    # print(user_knowledgestate.qns)

    # print("opportunity: ", user_knowledgestate.opportunity)
    # print("consideration: ", user_knowledgestate.consideration)
    # print(question_checker)
    # print(user_knowledgestate.face)
    # print("knowledge: ", user_knowledgestate.knowledge)

    return {"response": result3["answer"], "student_knowledge_level": student_knowledge_level, "qns": user_knowledgestate.qns, "cnd": user_knowledgestate.cnd, "uniqueness": feedback_uniqueness, "relevance": feedback_relevance, "high_level": feedback_high_level, "specificity": feedback_specificity, "justification": feedback_justification, "active": feedback_active, "questionChecker": question_checker, "face": user_knowledgestate.face}

@main.route("/baselineresponse", methods=["POST"])
@jwt_required()
@cross_origin()
def baselineresponse():
    params = request.get_json()
    feedback = params['feedback']
    user = User.query.filter_by(email=get_jwt_identity()).first()
    
    idea = Idea.query.filter_by(user_id=user.id, round=user.currentRound).first()
    ideaData = {"topic": idea.topic, "design criteria": idea.design_goals, "title": idea.title, "problem": idea.target_problem, "idea": idea.idea}

    user_chat = ChatLog.query.filter_by(user_id=user.id, round=user.currentRound).first()

    prompt = [{"role": "system","content":"This is your design ideas: " + json.dumps(ideaData) +  "\nAnswer feedback from the user.\nThe format of your answer is JSON as follows. {\"answer\": {your answer}} \nThis is previous conversations: " + json.dumps(user_chat.log) + "\nThis is the following chat(feedback): " + feedback }]
            
    completion = openai.chat.completions.create(
        model="gpt-4o",
        # model="gpt-3.5-turbo",
        messages=prompt,
        response_format={"type": "json_object"}
    )
    try:
        result3 = json.loads(completion.choices[0].message.content)
    except ZeroDivisionError as e:
    # This will run only if there is no error
        return {"response": "죄송합니다...제가 잘 이해 못한 거 같아요. 다시 말씀해주실 수 있을까요?"}

    new_entries = [
        {"speaker": "instructor", "content": feedback},
        {"speaker": "student", "content": result3["answer"]}
    ]
    user_chat.log.extend(new_entries)
    flag_modified(user_chat, 'log')

    db.session.commit()


    return {"response": result3["answer"]}


@main.route("/askQuestion")
@jwt_required()
@cross_origin()
def askQuestion():
    user = User.query.filter_by(email=get_jwt_identity()).first()
    user_knowledgestate = KnowledgeState.query.filter_by(user_id=user.id).first()
    knowledge = user_knowledgestate.knowledge
    user_chat = ChatLog.query.filter_by(user_id=user.id).first()
    idea = Idea.query.filter_by(user_id=user.id, round=user.currentRound).first()
    ideaData = {"topic": idea.topic, "design criteria": idea.design_goals, "title": idea.title, "problem": idea.target_problem, "idea": idea.idea}

    instruction = ""

    if user_knowledgestate.counter['q_count'] >= 3:
        instruction = "Ask for the reviewer's own opinion or advice on the previous reviewer's question."
    elif user_knowledgestate.counter['q_count'] <= -3:
        instruction = "Ask what I need to think about to respond to the feedback."
    elif user_knowledgestate.counter['d_count'] >= 3:
        instruction = "Ask questions to synthesize what we've discussed so far."
    elif user_knowledgestate.counter['d_count'] <= -3:
        instruction = "Ask questions to expand on what we've discussed so far."
    elif user_knowledgestate.counter['r_count'] >= 3:
        instruction = "Ask questions that are relevant to what we're discussing."
    elif user_knowledgestate.counter['h_count'] >= 3:
        instruction = "Ask questions that elicit feedback that lead to higher-level thinking."
    elif user_knowledgestate.counter['s_count'] >= 3:
        instruction = "Ask questions that elicit specific feedback."
    elif user_knowledgestate.counter['j_count'] >= 3:
        instruction = "Ask questions that elicit justification."
    elif user_knowledgestate.counter['a_count'] >= 3:
        instruction = "Ask questions that elicit actionable feedback."
    elif user_knowledgestate.counter['u_count'] >= 3:
        instruction = "Ask questions to get feedback you hadn't considered."

    user_knowledgestate.counter = {'q_count': 0, 'd_count': 0, 'u_count': 0, 'r_count': 0, 'h_count': 0, 's_count': 0, 'j_count': 0, 'a_count': 0}
    
    question_prompt = [{"role": "system","content":"This is your design idea: " + json.dumps(ideaData) + "\nYour Design Knowledge: " + knowledge + "\nYou are a student who is trying to learn design. You're coming up with ideas for a design project. Your persona is \n* a Design Department 1st year student. \n* Korean. (say in Korean) \n* Speak colloquially only. Use honorifics.\n\nAsk questions to get good feedback from your mento.The feedback meets the following conditions.\n* The question is aimed at finding knowledge that is not in my design knowledge that I need to know to answer the last mento's question.\n*" + instruction + "\n* Keep your questions concise, in one sentence.\nThe format of your question is JSON as follows. {\"question\": {your question}} \nThese are previous conversations between you(the student) and the mento: " + json.dumps(user_chat.log)}, 
                    {"role": "user", "content":"I am an industrial design expert. As a mento, I'll give feedback on your design project."}]

    completion1 = openai.chat.completions.create(
        model="gpt-4o",
        # model="gpt-3.5-turbo",
        messages=question_prompt,
        response_format={"type": "json_object"}
    )
    try:
        result = json.loads(completion1.choices[0].message.content)
    except ZeroDivisionError as e:
        # This will run only if there is no error
        return {"response": "죄송합니다...질문이 있었는데 까먹었습니다..."}

    print(result)
    user_chat.log.append({"speaker": "student", "content": result["question"]})
    flag_modified(user_chat, 'log')
    flag_modified(user_knowledgestate, 'counter')

    db.session.commit()

    return {"response": result["question"]}

@main.route("/nextRound")
@jwt_required()
@cross_origin()
def nextRound():
    user = User.query.filter_by(email=get_jwt_identity()).first()
    user.currentRound += 1

    flag_modified(user, 'currentRound')
    db.session.commit()

    return {"msg":"Next Round!"}

app = create_app()
if __name__ == '__main__':
    db.create_all(app=create_app())
    app.run(debug=True)