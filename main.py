# -*- coding: utf-8 -*-
from flask import Blueprint, current_app, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import cross_origin
from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, unset_jwt_cookies, jwt_required, JWTManager
from sqlalchemy.orm.attributes import flag_modified
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from __init__ import create_app, db
from models import User, Idea, KnowledgeState, ChatLog, InitialSetting, UserLog
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

ideaOrder = [[4,0,2],[5,2,0],[2,1,4],[3,4,1],[0,3,5],[1,5,3],[4,0,3],[2,1,5],[5,2,1],[0,3,4],[3,4,0],[1,5,2],[4,0,2],[5,2,0],[2,1,4],[3,4,1],[0,3,5],[1,5,3],[4,0,3],[2,1,5],[5,2,1],[0,3,4],[3,4,0],[1,5,2]]

Ideas = [
    {'topic': "반려동물을 위한 서비스", 'title': "Petit - 책임감 있는 반려동물 입양 플랫폼", 'target_problem': "최근 반려동물을 입양한 후에 돌볼 능력이나 책임감이 부족해 유기동물로 전락하는 사례가 많다. 실제로 반려동물을 돌보는 과정에서 예상치 못한 비용과 시간 소모, 그리고 건강 관리 소홀로 인해 동물의 건강이 나빠져 돌봄을 포기하게 되는 것이 주요 원인이다. 이러한 문제를 완화하기 위해서는 입양 과정에서 충분한 교육과 입양 준비 절차를 지원하고, 입양 후에도 지속적인 지원이 필요하다.", 'idea': "Petit은 입양 전 교육과 평가, 입양 후 지원 시스템, 적합성 테스트, 정기적 체크인 및 평가를 통해 입양자들이 충분한 지식과 책임감을 갖추도록 돕는다. 먼저, 입양 희망자는 동물의 기본적인 돌봄 지식, 건강 관리, 훈련 방법 등을 배우는 온라인 교육 프로그램을 이수해야 한다. 교육을 마친 후에는 퀴즈나 평가를 통해 이해도를 확인하고 일정 점수 이상을 받아야만 입양 절차를 진행할 수 있다. 이후 전문 상담사와의 인터뷰를 통해 입양 희망자의 생활 환경, 시간적 여유, 경제적 능력 등을 평가하고, 필요하다면 가정방문 평가를 통해 반려동물이 생활하게 될 환경을 직접 확인한다. 입양이 확정되면, 입양자는 동물의 건강 상태와 필요한 돌봄 사항 등을 명시한 계약서를 작성하게 된다. 가상 입양 체험을 통해 입양 희망자는 실제로 반려동물을 돌보는 것이 어떤 것인지 시뮬레이션해볼 수 있으며, 기본적인 반려동물 훈련 프로그램에 참여하여 실제로 동물을 다루는 능력을 평가받을 수 있다. 정기 방문을 통해 입양 후 일정 기간마다 동물의 상태를 확인하고, 입양자가 책임감 있게 돌보고 있는지 평가하며, 입양자는 정기적으로 반려동물의 상태를 온라인으로 보고할 수 있어 문제가 발생하면 신속하게 대처할 수 있다."},
    {'topic': "반려동물을 위한 서비스", 'title': "(반려동물 번역기) 반려동물 목소리를 자연어로 번역하는 서비스", 'target_problem': "반려동물은 자연어(사람 말)를 하지못하기에 ex) 아플때 아프다 못하고 결국 주인이 반려동물 대신해서 결정을 내림.", 'idea': "왜 LLM은 되는데 Large Dog Language Model (LDLM)은 안될까? 반려동물의 목소리 데이터를 잘 축적해서 동물 전문가를 통한 Dataset 검증을 받고 이를 supervised learning 기반 model을 만들고 ex 강아지 목줄에 달면 짖을때마다 무슨 말을 하는지 알 수 있으면 재미있지 않을까?\n해당 아이디어는 다음과 같다. 우선 강아지가 짖는 상황(목소리)을 녹음한다. 강아지의 피치나, Duration, 톤 등에 대한 데이터 셋 자체가 지금은 조금 부족한 느낌이기 때문에 우선 이러한 데이터를 수집한다. 이러한 데이터를 동물 전문가를 통해 labeling을 시켜서 강아지 언어 데이터 셋을 만든다. (예를들어, 강아지: 왈, 의미: 밥줘). 여러 상황에 따른 강아지의 반응 데이터가 수집이 된다면 이를 활용해 번역기를 만들수 있지 않을까? 이 과정에서 아무래도 Labeling이 된 데이터셋이라면 Supervised learning을 통해 model을 만들고 이를 기반으로 Prediction을 할 수 있을것 같다. (정확도 부분에 대해서는 사실 전혀 모르겠다… 그렇지만 재미요소나 마켓팅 비즈니스 요소로는 재미있는 시도라고 생각이 드는것같다)  강아지가 평상시 목줄을 착용하기때문에 웨어러블 느낌의 작은 센서가 목줄에 달려있어 강아지가 짖으면 이가 자동으로 번역되어 스피커를 통해 나오거나 앱을 통해 사용자에게 전달되는 interaction flow를 상상하긴했음."},
    {'topic': "탄소중립을 위한 서비스", 'title': "기숙사 탄소배출을 줄이자", 'target_problem': "아파트에 거주하는 경우, 전기세 부담 때문에 더운 날씨에도 에어컨 사용을 자제하고, 방이 시원해지면 바로 꺼버리는 경우가 많음. 반면, 학교 강의실, 연구실, 기숙사 등 전기세를 직접 부담하지 않는 공간에서는 전기세에 대한 걱정 없이 에어컨을 최저 온도로 켜두는 경우가 많음. 특히, 기숙사에서는 외출 시에도 돌아올 때 시원함을 위해 하루 종일 에어컨을 켜놓는 경우가 있음. 학교 측에서는 이러한 과도한 에어컨 사용을 막기 위해 하루 세 번, 정해진 시간에 에어컨을 자동으로 제어하지만, 여전히 몇 시간 동안 빈 방에 에어컨이 켜져 있는 경우가 발생함.", 'idea': "학생증을 사용해 기숙사에 출입하는 시스템을 활용하여, 외출 시 에어컨이 켜져 있다면 자동으로 꺼지게 하는 시스템을 도입함. 이를 통해 에어컨이 불필요하게 작동되는 시간을 줄이고, 전력 낭비를 방지할 수 있음. 또한, 학생증을 통해 외출 시 불이 켜져 있다면 불도 자동으로 꺼지게하는 시스템을 함께 도입하면 더 많은 탄소 배출을 줄일 수 있을 것."},
    {'topic': "탄소중립을 위한 서비스", 'title': "저탄소 교통 이용을 장려하는 지도 서비스", 'target_problem': "많은 사람들이 저탄소의 중요성을 인지하고 저탄소 교통 (버스, 지하철) 를 타려고 노력하고 있습니다. 하지만, 저탄소 교통을 타기 위해 기다리는 귀찮음, 많은 사람들과 함께 타다보니 이에서 불쾌감과 짜증이 발생합니다. 이러한 부정적인 경험들이 점점 쌓이고 쌓여 저탄소 교통의 이용은 줄어들고, 개인 교통 (자동차, 오토바이) 의 이용이 점점 늘어나게 됩니다.", 'idea': "해당 목적지로 향하기 위해 저탄소 교통을 탔을 때 발생하는 탄소량과 개인 교통을 탔을 때 발생하는 탄소량을 직접 비교한다면, 저탄소 교통의 친환경성을 더욱 강조할 수 있을 것입니다. 현재 지도 서비스의 대중교통 탭에서는, 해당 목적지로 가기 위해서 타야하는 버스/지하철의 경로, 소요시간, 이용요금의 정보가 나타납니다. 이 정보 외에도 ‘저탄소 교통을 탐으로써 절약한 탄소량’의 정보를 보여준다면, 사람들에게 저탄소 교통 이용을 장려할 수 있을 것입니다."},
    {'topic': "아동 보호를 위한 서비스", 'title': "Safeview - 아동 안전 콘텐츠 필터링 익스텐션", 'target_problem': "현대 가정에서 유튜브, 넷플릭스와 같은 스트리밍 서비스를 통해 다양한 콘텐츠를 시청하는 것은 일상적이다. 그러나 이러한 플랫폼에는 성인용 콘텐츠도 많이 포함되어 있어 아이들이 이를 무방비 상태로 접할 위험이 있다. 부모들이 이러한 콘텐츠를 완벽하게 관리하기 어렵고, 아이들에게 부적절한 콘텐츠가 노출될 경우 심리적, 정서적 문제를 일으킬 수 있다. 따라서, 아이들이 안전하게 콘텐츠를 소비할 수 있도록 돕는 효과적인 필터링 도구가 필요하다.", 'idea': "Safeview는 부모들이 사용하는 브라우저에 설치할 수 있는 익스텐션으로, 유튜브, 넷플릭스 등 다양한 스트리밍 플랫폼에서 아이들이 보기에 적합한 콘텐츠만 노출되도록 필터링하는 기능을 제공한다. Safeview는 AI 기반의 콘텐츠 분석 기술을 통해 실시간으로 영상의 내용을 분석하고, 부적절한 콘텐츠를 감지하여 자동으로 차단한다. 부모는 익스텐션을 통해 아이들에게 적합한 연령대와 콘텐츠 유형을 설정할 수 있으며, 이를 기반으로 필터링이 적용된다. 예를 들어, 부모가 7세 이하의 아이에게 적합한 콘텐츠만 노출되도록 설정하면, 그 외의 콘텐츠는 자동으로 차단된다."},
    {'topic': "아동 보호를 위한 서비스", 'title': "아동의 안전을 위한 웨어러블 기기", 'target_problem': "아동 보호 서비스는 아동 학대, 방치를 방지하고, 아동의 안전을 지원하기 위해 존재합니다. 그러나 아동 학대와 방치는 주로 실내에서 이뤄지기 때문에, 주변인들이 아동의 상태를 인지하고 대처하기 어렵습니다. 즉, 아동 보호 서비스는 공간적인 제약이 있습니다. 아동 학대나 방치 상황을 빠르게 인지하고 대응하기 위해서는 아동의 상태를 어디서나 인지할 수 있도록 데이터를 수집할 필요가 있습니다.", 'idea': "일반 팔찌처럼 생긴 아동 안전 웨어러블 기기는 GPS 추적 기능, 마이크, 심박수 모니터링, 그리고 응급 호출 버튼이 있습니다. GPS와 마이크, 심박수를 통해 아동이 처한 상황의 데이터를 실시간으로 수집할 수 있습니다. 따라서, 만약 아동이 위험한 상황에 처했을 때 즉시 아동의 상태를 확인하고 적절한 대응을 취할 수 있을 것입니다. 또한, 아동이 스스로 신고를 할 수 있는 상황이라면, 아동이 직접 응급 호출 버튼을 눌러 도움을 요청할 수도 있습니다."},
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
    num = int(params['num'])
    password = params['password']

    existUser = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database
    if existUser: # if a user is found, we want to redirect back to signup page so user can try again
        # flash('Email address already exists')
        return {"":""}

    new_user = User(
        email = email,
        name = name,
        num = num,
        password = generate_password_hash(password, method='sha256'),
        realPassword = password,
        currentRound = 1
    )
    db.session.add(new_user)
    db.session.commit()

    #if num is 1-12, user_mode is 1; if num is 13-24, user_mode is 2 
    user_mode = 2
    if ((num - 1) % 24) < 12:
        user_mode = 1
    
    new_settings = [
        InitialSetting(user_id=new_user.id, mode= 1, round=1, character = 0, goal1="", goal2="", goal3="", time = 5),
        InitialSetting(user_id=new_user.id, mode= user_mode, round=2, character = 0, goal1="", goal2="", goal3="", time = 20),
        InitialSetting(user_id=new_user.id, mode= 3 - user_mode, round=3, character = 0, goal1="", goal2="", goal3="", time = 20)
    ]

    new_ideas = [
        Idea(user_id=new_user.id, round=1, topic=Ideas[ideaOrder[num - 1][0]]['topic'], title=Ideas[ideaOrder[num - 1][0]]['title'], target_problem=Ideas[ideaOrder[num - 1][0]]['target_problem'], idea=Ideas[ideaOrder[num - 1][0]]['idea']),
        Idea(user_id=new_user.id, round=2, topic=Ideas[ideaOrder[num - 1][1]]['topic'], title=Ideas[ideaOrder[num - 1][1]]['title'], target_problem=Ideas[ideaOrder[num - 1][1]]['target_problem'], idea=Ideas[ideaOrder[num - 1][1]]['idea']),
        Idea(user_id=new_user.id, round=3, topic=Ideas[ideaOrder[num - 1][2]]['topic'], title=Ideas[ideaOrder[num - 1][2]]['title'], target_problem=Ideas[ideaOrder[num - 1][2]]['target_problem'], idea=Ideas[ideaOrder[num - 1][2]]['idea']),
    ]
    
    new_KnowledgeStates = [
        KnowledgeState(user_id = new_user.id, round=1, face=33, q_num=0, s_num=0, c_num=0, d_num=0, eval={'timely': 0, 'relevance': 0, 'high-level': 0, 'specificity': 0, 'justification': 0, 'active': 0}, knowledge = "", actionPlan = "", counter={'q_count': 0, 'd_count': 0, 'u_count': 0, 'r_count': 0, 'h_count': 0, 's_count': 0, 'j_count': 0, 'a_count': 0}),
        KnowledgeState(user_id = new_user.id, round=2, face=33, q_num=0, s_num=0, c_num=0, d_num=0, eval={'timely': 0, 'relevance': 0, 'high-level': 0, 'specificity': 0, 'justification': 0, 'active': 0}, knowledge = "", actionPlan = "", counter={'q_count': 0, 'd_count': 0, 'u_count': 0, 'r_count': 0, 'h_count': 0, 's_count': 0, 'j_count': 0, 'a_count': 0}),
        KnowledgeState(user_id = new_user.id, round=3, face=33, q_num=0, s_num=0, c_num=0, d_num=0, eval={'timely': 0, 'relevance': 0, 'high-level': 0, 'specificity': 0, 'justification': 0, 'active': 0}, knowledge = "", actionPlan = "", counter={'q_count': 0, 'd_count': 0, 'u_count': 0, 'r_count': 0, 'h_count': 0, 's_count': 0, 'j_count': 0, 'a_count': 0})
    ]
    new_ChatLogs = [
        ChatLog(user_id = new_user.id, round=1, log = [{"speaker":"student", "content": "안녕하세요! 저는 동건이라고 합니다. 제 아이디어에 대한 피드백을 주시면 감사하겠습니다."}]),
        ChatLog(user_id = new_user.id, round=2, log = [{"speaker":"student", "content": "안녕하세요! 저는 동건이라고 합니다. 제 아이디어에 대한 피드백을 주시면 감사하겠습니다."}]),
        ChatLog(user_id = new_user.id, round=3, log = [{"speaker":"student", "content": "안녕하세요! 저는 동건이라고 합니다. 제 아이디어에 대한 피드백을 주시면 감사하겠습니다."}])
    ]
    
    db.session.add_all(new_settings + new_ideas + new_KnowledgeStates + new_ChatLogs)
    db.session.flush()
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
    ideaData = {"id": idea.id, "topic": idea.topic, "title": idea.title, "problem": idea.target_problem, "idea": idea.idea}
    userChat = ChatLog.query.filter_by(user_id=user.id, round=user.currentRound).first()
    setting = InitialSetting.query.filter_by(user_id=user.id, round=user.currentRound).first()
    user_knowledgestate = KnowledgeState.query.filter_by(user_id=user.id, round=user.currentRound).first()

    ########Collect Log#######
    timestamp = datetime.fromtimestamp(datetime.now().timestamp())
    userlog = UserLog(user_id = user.id, round=user.currentRound, timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S'), tag="start", data="")
    db.session.add(userlog)
    db.session.commit()
    ##########################
    
    if setting.mode == 1 :        
        feedback_timely = 0
        feedback_relevance = 0
        feedback_high_level = 0
        feedback_specificity = 0
        feedback_justification = 0
        feedback_active = 0
        
        if user_knowledgestate.q_num > 0:
            feedback_timely = round(user_knowledgestate.eval['timely'] / user_knowledgestate.q_num, 1)
            feedback_relevance = round(user_knowledgestate.eval['relevance'] / user_knowledgestate.q_num, 1)
            feedback_high_level = round(user_knowledgestate.eval['high-level'] / user_knowledgestate.q_num, 1)
            
        if user_knowledgestate.s_num > 0:
            feedback_specificity = round(user_knowledgestate.eval['specificity'] / user_knowledgestate.s_num, 1)
            feedback_justification = round(user_knowledgestate.eval['justification'] / user_knowledgestate.s_num, 1)
            feedback_active = round(user_knowledgestate.eval['active'] / user_knowledgestate.s_num, 1)

        qns = 50
        if user_knowledgestate.q_num + user_knowledgestate.s_num > 0:
            qns = user_knowledgestate.q_num * 100 / (user_knowledgestate.q_num + user_knowledgestate.s_num)
        
        cnd = 50
        if user_knowledgestate.c_num + user_knowledgestate.d_num > 0:
            qns = user_knowledgestate.c_num * 100 / (user_knowledgestate.c_num + user_knowledgestate.d_num)

        return {"ideaData": ideaData, "chatData": userChat.log, "name": name, "mode": setting.mode, "character": setting.character, "goal1": setting.goal1, "goal2": setting.goal2, "goal3": setting.goal3, "time": setting.time, "student_knowledge_level": len(user_knowledgestate.knowledge), "qns": qns, "cnd": cnd, "timely": feedback_timely, "relevance": feedback_relevance, "high_level": feedback_high_level, "specificity": feedback_specificity, "justification": feedback_justification, "active": feedback_active, 'face': user_knowledgestate.face, 'knowledge': user_knowledgestate.knowledge, 'actionPlan': user_knowledgestate.actionPlan}
    
    return {"ideaData": ideaData, "chatData": userChat.log, "name": name, "mode": setting.mode, "character": "", "goal1": "", "goal2": "", "goal3": "", "time": setting.time, "student_knowledge_level": "", "qns": "", "cnd": "", "timely": "", "relevance": "", "high_level": "", "specificity": "", "justification": "", "active": "", 'face': "", 'actionPlan': user_knowledgestate.actionPlan}

@main.route("/getSetting")
@jwt_required()
@cross_origin()
def getSetting():
    user = User.query.filter_by(email=get_jwt_identity()).first()
    currentRound = user.currentRound
    if currentRound >= 4:
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
        flag_all_modified(setting2)

    if currentRound <=3:        
        setting3 = InitialSetting.query.filter_by(user_id=user.id, round=3).first()
        setting3.character = current_character
        setting3.goal1 = current_goal1
        setting3.goal2 = current_goal2
        setting3.goal3 = current_goal3
        flag_all_modified(setting3)
    
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
    knowledge = user_knowledgestate.knowledge
    user_chat = ChatLog.query.filter_by(user_id=user.id, round=user.currentRound).first()
    
    formatted_chat = ''.join([f'you: {x["content"]}\n' if x["speaker"] == "student" else f'mentor: {x["content"]}\n' for x in user_chat.log])
    formatted_knowledge = knowledge.replace(".", ".\n")

    categorization_prompt = [
        {
            "role": "system",
            "content": f"""Your task is to categorize the feedback provided by the mentor about the student's design idea. The studens is a 1st year Design Department student, and the mentor is an industrial design expert.

This is student's current design idea:
* Topic: {ideaData['topic']}
* Title: {ideaData['title']}
* Problem: {ideaData['problem']}
* Idea: {ideaData['idea']}

These are previous conversations between the student and the mentor about student's design idea:
{formatted_chat}

After the conversation, the mentor provided feedback to the student. This is the feedback that need to be categorized: {feedback}

Follow the steps below to complete the task.

STEP 1: Review student's current design idea and chat logs to understand the context of the feedback.

STEP 2: Decompose the feedback into individual sentences.

STEP 3: Classify each sentence into one of three primary categories;
'Question': This is a question feedback, which ensure that the feedback provider has a clear and accurate understanding of the design presented.
'Statement': This is a statement feedback, which provides relevant information or is directly related to a design idea to evaluate or suggest improvements.
'No feedback': This sentence is completely irrelevant to the feedback.

STEP 4: Subcategorize each sentence based on its nature (There are 21 types of 'Question', three types of 'Statement' and no sub category for 'No feedback.');
'Question':
"Low-Level": Seeks factual details about the design.
- Verification: Is X true?
- Definition: What does X mean?
- Example: What is an example of X?
- Feature Specification: What (qualitative) attributes does X have?
- Concept Completion: Who? What? When? Where?
- Quantification: How much? How many?
- Disjunctive: Is X or Y the case?
- Comparison: How does X compare to Y?
- Judgmental: What is your opinion on X?
"Deep Reasoning": Explores deeper implications or reasons behind the design.
- Interpretation: How is a particular event or pattern of information interpreted or summarized?
- Goal Orientation: What are the motives behind an agent’s action?
- Causal Antecedent: What caused X to occur?
- Causal Consequent: What were the consequences of X occurring?
- Expectational: Why is X not true?
- Instrumental/Procedural: How does an agent accomplish a goal?
- Enablement(DR): What object or resource enables an agent to perform an action?
"Generate Design": Encourages innovative thinking about design challenges.
- Proposal/Negotiation: Could a new concept be suggested/negotiated?
- Scenario Creation: What would happen if X occurred?
- Ideation: Generation of ideas without a deliberate end goal
- Method: How could an agent accomplish a goal?
- Enablement(GD): What object or resource could enable an agent to perform an action?

'Statement':
"Information": Share related information or examples.
"Evaluation": Assess the student’s design idea. Stating general facts rather than evaluating a student's ideas doesn't belong.
"Recommendation": Provide actionable suggestions for improvement.

Response Only in JSON array, which looks like, {{"sentences":[{{"sentence": "", "categories":"", "type":""}}]}}.
"sentence": Individual unit of feedback.
"categories": Category of feedback. ('Question' or 'Statement' or 'No feedback')
"type": Subcategory of feedback. ("Low-Level" or "Deep Reasoning" or "Generate Design" or "Information" or "Evaluation" or "Recommendation").
"""
}]
    completion1 = openai.chat.completions.create(
        model="gpt-4o",
        # model="gpt-3.5-turbo",
        temperature=0,
        messages=categorization_prompt,
        response_format={"type": "json_object"}
    )
    try:
        result1 = json.loads(completion1.choices[0].message.content)
        result1 = [sentence for sentence in result1['sentences'] if sentence['categories'].lower() in ['question', 'statement']]
        print(result1)
    except ZeroDivisionError as e:
        # This will run only if there is no error
        return {"response": "죄송합니다...제가 잘 이해 못한 거 같아요. 다시 말씀해주실 수 있을까요?"}

    # Add Knowledge
    knowledge_prompt = [
        {
            "role": "system",
            "content": f"""Your task is to extract the knowledge that was accumulated by the student during the conversation with the mentor about the student's design idea.

This is student's current design idea:
* Topic: {ideaData['topic']}
* Title: {ideaData['title']}
* Problem: {ideaData['problem']}
* Idea: {ideaData['idea']}

These are previous conversations between the student and the mentor about student's design idea:
{formatted_chat}

This is student's current design knowledge accumulated by the conversation with the mentor:
{formatted_knowledge}

Now, you will be given the feedback that the mentor provided to the student after the conversation, and the type of that feedback. The format of the input is as follows:
{{"sentence": "", "categories":"", "type":""}}

First, don't interpret the sentence literally, but contextualize it from previous conversations to understand what is being said.

Next, extract the knowledge that the student can derive from the feedback.
The knowledge should be a one-line sentence, and is highly relevant to the given instructor's feedback, but could be applied to any design idea or context. It should not include specific details related to the current design idea.
You can infer some intentions behind the feedback to build the knowledge, but avoid generating too irrelevant or too specific knowledge.

Then, based on the knowledge, generate one-line action plan that the student should take based on the feedback. The action plan should be about the actions that the student should take to improve the current design idea based on the knowledge extracted from the feedback.
"Deep Reasoning": Suggest design considerations from the feedback.
"Generate Design": Suggest new design opportunities from the feedback.
"Information": Details the information provided in the feedback.
"Evaluation": Describes the assessment of the design idea.
"Recommendation": Outline ideas for enhancement based on the feedback.

Lastly, convert the extracted knowledge into the form of a student talking to himself. This should be a one-line Korean sentence. This should be not rephrasing the given feedback, but more about the process of translating the given feedback into his own knowledge. End with an exclamation point if the thought is surprising, a question mark if it conflicts with your knowledge or common sense, and a period otherwise.

The response should be in JSON array format, which looks like, {{"knowledge": "", "action_plan": "", "thinking": ""}}.
"""
}]

    new_knowledge = []
    new_actionPlan = []
    new_thinking = []
    for sentence in result1:
        if sentence['categories'].lower() == 'no feedback' or sentence['categories'].lower() == 'low-level':
            continue
        getKowledge = openai.chat.completions.create(
            model="gpt-4o",
            # model="gpt-3.5-turbo",
            messages=knowledge_prompt + [{"role": "assistant", "content": json.dumps(sentence)}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        try:
            knowledge = json.loads(getKowledge.choices[0].message.content)
            print(knowledge)
            new_knowledge.append(knowledge["knowledge"])
            new_actionPlan.append(knowledge["action_plan"])
            new_thinking.append(knowledge["thinking"])
        except:
            return {"response": "죄송합니다...제가 잘 이해 못한 거 같아요. 다시 말씀해주실 수 있을까요?"}

    if (user_knowledgestate.knowledge != ""):
        user_knowledgestate.knowledge += ", "
    user_knowledgestate.knowledge += ", ".join(new_knowledge)
    if (user_knowledgestate.actionPlan != ""):
        user_knowledgestate.actionPlan += ", "
    user_knowledgestate.actionPlan += ", ".join(new_actionPlan)
    new_thinking = " ".join(new_thinking)

    if len(result1) == 0:
        if (user_knowledgestate.face / 10) > 2:
            user_knowledgestate.face -= 10
    else:
        feedbackeval_prompt = [{"role": "system", "content": f"""
Feedback Evaluation Instructions for Instructor's Feedback of a Student's Design Idea.

STEP 1: Review previous ideas and chat logs to understand the context of the feedback.

STEP 2: Evaluate the feedback on a scale of 1 to 57 based on the following criteria. There are three different criteria depending on whether the feedback category is a 'Question' or a 'Statement'.
'Question':
"timely": This feedback(question) was provided at the appropriate time.
"relevance": The feedback(question) is relevant to achieving the design goals.The design goals are; Inovation: how innovative the idea is, Elaboration: how sophisticated the idea is, Usability: how easy the idea is to use, Value: how valuable the idea is to use, and Social Responsibility: how socially responsible the idea is.
"high-level": The feedback(question) is high-level.(If the question falls into the "Low-Level" category, it's between 1 and 2. Otherwise, it's between 3 and 5.)
'Statement':
"specificity": The feedback is specific.
"justification": The feedback is justified.
"active": The feedback is actionable.
'No feedback': DO NOT RATE.

STEP 3: Evaluate the sentiment of the feedback. Analyze the sentiment of the feedback and rate it as either positive(1), neutral(0), or negative(-1).

Response Only in JSON array, which looks like, 
{{"sentences":[{{"sentence": "", "categories":"", "type":"", "knowledge":"", "evaluation":{{"uniqueness": [0,7], "relevance": [0,7], "high-level": [0,7], "specificity": [0,7], "justification": [0,7], "active": [0,7], "sentiment":[-1,1]}}}}]}}.
"sentence": Individual unit of feedback.
"categories": Category of feedback. ('Question' or 'Statement' or 'No feedback')
"type": Subcategory of feedback (e.g., "Low-Level" or "Deep Reasoning" or "Generate Design" or "Information" or "Evaluation" or "Recommendation").
"knowledge": A key one-sentence summary of the knowledge from the feedback described in STEP5 that is brief and avoids proper nouns.
"evaluation": JSON with the evaluation score based on the criteria. The criteria that should be evaluated in STEP 2 have a value between 1-7, with the rest evaluated as 0.

This is student's current design idea:
* Topic: {ideaData['topic']}
* Title: {ideaData['title']}
* Problem: {ideaData['problem']}
* Idea: {ideaData['idea']}

These are previous conversations between the student and the mentor about student's design idea:
{formatted_chat}

This is the feedback that the student received from the mentor: {result1}
"""}]
                                                                
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
                    #timely
                    user_knowledgestate.eval['timely'] += int(sentence['evaluation']['timely'])
                    if sentence['evaluation']['timely'] <= 4:
                        user_knowledgestate.counter['u_count'] += 1
                    #relevance
                    user_knowledgestate.eval['relevance'] += int(sentence['evaluation']['relevance'])
                    if sentence['evaluation']['relevance'] <= 4:
                        user_knowledgestate.counter['r_count'] += 1
                    #high-level
                    user_knowledgestate.eval['high-level'] += int(sentence['evaluation']['high-level'])
                    if sentence['evaluation']['high-level'] <= 4:
                        user_knowledgestate.counter['h_count'] += 1

                    if (int(sentence['evaluation']['timely']) + int(sentence['evaluation']['relevance']) + int(sentence['evaluation']['high-level']) >= 16) and ((user_knowledgestate.face / 10) < 5):
                        user_knowledgestate.face += 10
                    elif (int(sentence['evaluation']['timely']) + int(sentence['evaluation']['relevance']) + int(sentence['evaluation']['high-level']) <= 9) and ((user_knowledgestate.face / 10) > 2):
                        user_knowledgestate.face -= 10

                    flag_modified(user_knowledgestate, 'counter')
                    flag_modified(user_knowledgestate, 'q_num')
                    flag_modified(user_knowledgestate, 'eval')
    
                if sentence['type'].lower() in ['information', 'evaluation', 'recommendation']:
                    user_knowledgestate.counter['q_count'] -= 1
                    user_knowledgestate.s_num += 1
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

                    if int(sentence['evaluation']['specificity']) + int(sentence['evaluation']['justification']) + int(sentence['evaluation']['active']) >= 14:
                        if (user_knowledgestate.face / 10) < 5:
                            user_knowledgestate.face += 10
                    if int(sentence['evaluation']['specificity']) + int(sentence['evaluation']['justification']) + int(sentence['evaluation']['active']) <= 8:
                        if (user_knowledgestate.face / 10) > 2:
                            user_knowledgestate.face -= 10

                    flag_modified(user_knowledgestate, 'counter')
                    flag_modified(user_knowledgestate, 's_num')
                    flag_modified(user_knowledgestate, 'eval')

                if sentence['type'].lower() in GDQ + ['recommendation']:
                    user_knowledgestate.counter['d_count'] += 1
                    user_knowledgestate.d_num += 1

                    flag_modified(user_knowledgestate, 'd_num')
                    flag_modified(user_knowledgestate, 'counter')

                if sentence['type'].lower() in DRQ + ['evaluation']:
                    user_knowledgestate.counter['d_count'] -= 1
                    user_knowledgestate.c_num += 1

                    flag_modified(user_knowledgestate, 'c_num')
                    flag_modified(user_knowledgestate, 'counter')
                
                sentiment_counter += sentence['evaluation']['sentiment']
                
                flag_modified(user_knowledgestate, 'face')

            except:
                return {"response": "죄송합니다...제가 잘 이해 못한 거 같아요. 다시 말씀해주실 수 있을까요?"}
            
        if ((user_knowledgestate.face % 10) < 5) and (sentiment_counter > 0):
            user_knowledgestate.face += 1
        elif ((user_knowledgestate.face % 10) > 2) and (sentiment_counter < 0):
            user_knowledgestate.face -= 1
            
    student_prompt = [{"role": "system", "content":"This is your design idea: " + json.dumps(ideaData, ensure_ascii=False) + "\nYou are a student who is trying to learn design. You're coming up with ideas for a design project. Your persona is \n* A Design Department 1st year student. \n* Korean. (say in Korean) \n* NEVER apologize, NEVER say you can help, and NEVER just say thanks.\n* NEVER write more than 3 sentences in a single response. Speak colloquially only. Use honorifics.\n\nAnswer feedback from the mentor ONLY based on your knowledge. If you can't answer based on Your Design Knowledge, say sorry, I don't know. BUT try to answer AS MUCH AS you can.\n\nThe format of your answer is JSON as follows. {\"answer\": {your answer}} \nThese are previous conversations between you(the student) and the mentor: " + json.dumps(user_chat.log, ensure_ascii=False) + "\nThis is the mentor's following chat(feedback): " + feedback}, 
                      {"role": "user", "content":"I am an industrial design expert. As a mentor, I'll give feedback on your design project."}]
    completion3 = openai.chat.completions.create(
        model="gpt-4o",
        # model="gpt-3.5-turbo",
        messages=student_prompt,
        response_format={"type": "json_object"}
    )
    try:
        result3 = json.loads(completion3.choices[0].message.content)
        print(result3)
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

    
    ########Collect Log#######
    timestamp = datetime.fromtimestamp(datetime.now().timestamp())
    userlog = UserLog(user_id = user.id, round=user.currentRound, timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S'), tag="user_feedaback", data=json.dumps({"user_input": feedback, "category": result1, "new_knowledge": new_knowledge, "new_actionPlan": new_actionPlan, "new_thinking": new_thinking, "evaluation": result2, "response": result3}, ensure_ascii=False))
    db.session.add(userlog)
    db.session.commit()
    ##########################


    db.session.commit()

    student_knowledge_level = len(user_knowledgestate.knowledge)
    feedback_timely = 0
    feedback_relevance = 0
    feedback_high_level = 0
    feedback_specificity = 0
    feedback_justification = 0
    feedback_active = 0
    if user_knowledgestate.q_num > 0:
        feedback_timely = round(user_knowledgestate.eval['timely'] / user_knowledgestate.q_num, 1)
        feedback_relevance = round(user_knowledgestate.eval['relevance'] / user_knowledgestate.q_num, 1)
        feedback_high_level = round(user_knowledgestate.eval['high-level'] / user_knowledgestate.q_num, 1)
    if user_knowledgestate.s_num > 0:
        feedback_specificity = round(user_knowledgestate.eval['specificity'] / user_knowledgestate.s_num, 1)
        feedback_justification = round(user_knowledgestate.eval['justification'] / user_knowledgestate.s_num, 1)
        feedback_active = round(user_knowledgestate.eval['active'] / user_knowledgestate.s_num, 1)
    
    question_checker = not (
        (user_knowledgestate.counter['q_count'] < 4)
        and (user_knowledgestate.counter['q_count'] > -4)
        and (user_knowledgestate.counter['d_count'] < 4) 
        and (user_knowledgestate.counter['d_count'] > -4) 
        and (user_knowledgestate.counter['u_count'] < 4) 
        and (user_knowledgestate.counter['r_count'] < 4) 
        and (user_knowledgestate.counter['h_count'] < 4)
        and (user_knowledgestate.counter['s_count'] < 4)
        and (user_knowledgestate.counter['j_count'] < 4)
        and (user_knowledgestate.counter['a_count'] < 4)
    )

    # print(feedback_timely)
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

    qns = 50
    if user_knowledgestate.q_num + user_knowledgestate.s_num > 0:
        qns = user_knowledgestate.q_num * 100 / (user_knowledgestate.q_num + user_knowledgestate.s_num)
    
    cnd = 50
    if user_knowledgestate.c_num + user_knowledgestate.d_num > 0:
        cnd = user_knowledgestate.c_num * 100 / (user_knowledgestate.c_num + user_knowledgestate.d_num)

    return {"response": result3["answer"], "student_knowledge_level": student_knowledge_level, "qns": qns, "cnd": cnd, "timely": feedback_timely, "relevance": feedback_relevance, "high_level": feedback_high_level, "specificity": feedback_specificity, "justification": feedback_justification, "active": feedback_active, "questionChecker": question_checker, "face": user_knowledgestate.face, "knowledge": user_knowledgestate.knowledge, "actionPlan": user_knowledgestate.actionPlan, "thinking": new_thinking}

# @main.route("/baselineresponse", methods=["POST"])
# @jwt_required()
# @cross_origin()
# def baselineresponse():
#     params = request.get_json()
#     feedback = params['feedback']
#     user = User.query.filter_by(email=get_jwt_identity()).first()
    
#     idea = Idea.query.filter_by(user_id=user.id, round=user.currentRound).first()
#     ideaData = {"topic": idea.topic, "design criteria": idea.design_goals, "title": idea.title, "problem": idea.target_problem, "idea": idea.idea}

#     user_chat = ChatLog.query.filter_by(user_id=user.id, round=user.currentRound).first()
#     formatted_chat = ''.join([f'you: {x["content"]}\n' if x["speaker"] == "student" else f'mentor: {x["content"]}\n' for x in user_chat.log])


#     prompt = [
#         {
#             "role": "system",
#             "content": f"""
# Your task is to respond to the feedback provided by the mentor about the student's design idea. The studens is a 1st year Design Department student, and the mentor is an industrial design expert.

# This is student's current design idea:
# * Topic: {ideaData['topic']}
# * Title: {ideaData['title']}
# * Problem: {ideaData['problem']}
# * Idea: {ideaData['idea']}

# These are previous conversations between the student and the mentor about student's design idea:
# {formatted_chat}

# This is the feedback that the student received from the mentor after the conversation: {feedback}

# Response Only in JSON array, which looks like, {{"answer": "your answer"}}
#             """
#         }
#     ]
            
#     completion = openai.chat.completions.create(
#         model="gpt-4o",
#         # model="gpt-3.5-turbo",
#         messages=prompt,
#         response_format={"type": "json_object"}
#     )
#     try:
#         result3 = json.loads(completion.choices[0].message.content)
#     except ZeroDivisionError as e:
#     # This will run only if there is no error
#         return {"response": "죄송합니다...제가 잘 이해 못한 거 같아요. 다시 말씀해주실 수 있을까요?"}

#     new_entries = [
#         {"speaker": "instructor", "content": feedback},
#         {"speaker": "student", "content": result3["answer"]}
#     ]
#     user_chat.log.extend(new_entries)
#     flag_modified(user_chat, 'log')

#     db.session.commit()
#     return {"response": result3["answer"]}


@main.route("/askQuestion")
@jwt_required()
@cross_origin()
def askQuestion():
    user = User.query.filter_by(email=get_jwt_identity()).first()
    user_knowledgestate = KnowledgeState.query.filter_by(user_id=user.id, round=user.currentRound).first()
    knowledge = user_knowledgestate.knowledge
    user_chat = ChatLog.query.filter_by(user_id=user.id, round=user.currentRound).first()
    idea = Idea.query.filter_by(user_id=user.id, round=user.currentRound).first()
    ideaData = {"topic": idea.topic, "design criteria": idea.design_goals, "title": idea.title, "problem": idea.target_problem, "idea": idea.idea}

    instruction = ""

    # print(user_knowledgestate.counter)
    if user_knowledgestate.counter['q_count'] >= 4:
        instruction = "Ask for the reviewer's own opinion or advice on the previous reviewer's question."
    elif user_knowledgestate.counter['q_count'] <= -4:
        instruction = "Ask what I need to think about to respond to the feedback."
    elif user_knowledgestate.counter['d_count'] >= 4:
        instruction = "Ask questions to synthesize what we've discussed so far."
    elif user_knowledgestate.counter['d_count'] <= -4:
        instruction = "Ask questions to expand on what we've discussed so far."
    elif user_knowledgestate.counter['r_count'] >= 4:
        instruction = "Ask questions that are relevant to what we're discussing."
    elif user_knowledgestate.counter['h_count'] >= 4:
        instruction = "Ask questions that elicit feedback that lead to higher-level thinking."
    elif user_knowledgestate.counter['s_count'] >= 4:
        instruction = "Ask questions that elicit specific feedback."
    elif user_knowledgestate.counter['j_count'] >= 4:
        instruction = "Ask questions that elicit justification."
    elif user_knowledgestate.counter['a_count'] >= 4:
        instruction = "Ask questions that elicit actionable feedback."
    elif user_knowledgestate.counter['u_count'] >= 4:
        instruction = "Ask questions to get feedback you hadn't considered."

    user_knowledgestate.counter = {'q_count': 0, 'd_count': 0, 'u_count': 0, 'r_count': 0, 'h_count': 0, 's_count': 0, 'j_count': 0, 'a_count': 0}
    
    formatted_chat = ''.join([f'you: {x["content"]}\n' if x["speaker"] == "student" else f'mentor: {x["content"]}\n' for x in user_chat.log])
    formatted_knowledge = knowledge.replace(".", ".\n")
    question_prompt = [
        {
            "role": "system",
            "content": f"""You are a student who is trying to learn design. You're coming up with ideas for a design project. Your persona is:
* a Design Department 1st year student.
* Korean. (say in Korean)
* Speak colloquially only. Use honorifics.

This is your current design idea:
* Topic: {ideaData['topic']}
* Title: {ideaData['title']}
* Problem: {ideaData['problem']}
* Idea: {ideaData['idea']}

These are previous conversations between you (the student) and the mentor about your design idea:
{formatted_chat}

This is your current design knowledge accumulated by the conversation with your mentor:
{formatted_knowledge}

Now, you need to ask questions to get more feedback from your mentor. {instruction} You should not ask for direct answers to your design idea, but you need to ask some questions that can elicit feedback on it.

Your question can be one of the following types:
* Critique: Directly ask for feedback on your design. Your question should not be asking for general feedback but rather focusing on a specific aspect of your design.
* Improve: Ask a question about how to improve your design. Your question should not be asking for a solution but rather a direction or actions that you need to do.
* Share: Ask your mentor about their experience or knowledge of the current topic.

Your question should help you find knowledge not in your current design knowledge, but you need to know how to answer the last mentor's question. Keep your questions concise, no more than one sentence.

The format of your question is JSON as follows:
{{"question": "your question"}}
        """
        },
        {"role": "user", "content": "I am an industrial design expert. As a mentor, I'll give feedback on your design project."},
    ]

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

    # print(result)

    user_chat.log.append({"speaker": "student", "content": result["question"]})
    flag_modified(user_chat, 'log')
    flag_modified(user_knowledgestate, 'counter')
    db.session.commit()

    ########Collect Log#######
    timestamp = datetime.fromtimestamp(datetime.now().timestamp())
    userlog = UserLog(user_id = user.id, round=user.currentRound, timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S'), tag="student_question", data=json.dumps({"question": result["question"]}, ensure_ascii=False))
    db.session.add(userlog)
    db.session.commit()
    ##########################

    return {"response": result["question"]}

@main.route("/updateIdea")
@jwt_required()
@cross_origin()
def updateIdea():
    user = User.query.filter_by(email=get_jwt_identity()).first()
    user_chat = ChatLog.query.filter_by(user_id=user.id, round=user.currentRound).first()
    user_knowledgestate = KnowledgeState.query.filter_by(user_id=user.id, round=user.currentRound).first()
    idea = Idea.query.filter_by(user_id=user.id, round=user.currentRound).first()
    
    if (user_knowledgestate.actionPlan == ""):
        return {"response": "No action plan to update the idea."}
    
    ideaData = {"topic": idea.topic, "design criteria": idea.design_goals, "title": idea.title, "problem": idea.target_problem, "idea": idea.idea}
    formatted_chat = ''.join([f'you: {x["content"]}\n' if x["speaker"] == "student" else f'mentor: {x["content"]}\n' for x in user_chat.log])
    formatted_actionPlan = ""
    for action in user_knowledgestate.actionPlan.split(", "):
        formatted_actionPlan += f"* {action}\n"
    
    ideaUpdatePrompt = [{
        "role": "system",
        "content": f"""
You are a student who is trying to improve your design ideas for a design project. Your persona is:
* a Design Department 1st year student.
* Korean. (say in Korean)

This is your current design idea:
* Topic: {ideaData['topic']}
* Title: {ideaData['title']}
* Problem: {ideaData['problem']}
* Idea: {ideaData['idea']}        

Now you have to improve this idea based on your conversation with your instructor, who is an industrial design expert.
These are previous conversations between you (the student) and the mentor about your design idea:
{formatted_chat}

Based on your conversation with the mentor, you made a list of action plans to improve your design idea. You need to update your design idea based on these action plans.
{formatted_actionPlan}

All content must be written in Korean. Ideas are a maximum of 3000 characters.

Response Only in JSON array, which looks like, {{'title': "", 'target_problem': "", 'idea': ""}}
        """
    }]
    
    completion1 = openai.chat.completions.create(
        model="gpt-4-turbo",
        # model="gpt-3.5-turbo",
        messages=ideaUpdatePrompt,
        response_format={"type": "json_object"}
    )
    try:
        result = json.loads(completion1.choices[0].message.content)
    except ZeroDivisionError as e:
        # This will run only if there is no error
        return {"response": "error"}
    
    try:
        user_knowledgestate.actionPlan = ""
        idea.title = result['title']
        idea.problem = result['target_problem']
        idea.idea = result['idea']

        flag_modified(idea, 'title')
        flag_modified(idea, 'target_problem')
        flag_modified(idea, 'idea')
        db.session.commit()

        ########Collect Log#######
        timestamp = datetime.fromtimestamp(datetime.now().timestamp())
        userlog = UserLog(user_id = user.id, round=user.currentRound, timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S'), tag="update_idea", data=json.dumps({"title": result['title'], "problem": result['target_problem'], "idea": result['idea']}, ensure_ascii=False))
        db.session.add(userlog)
        db.session.commit()
        ##########################

    except ZeroDivisionError as e:
        return {"response": "error"}
    
    ideaData = {"topic": idea.topic, "design criteria": idea.design_goals, "title": result['title'], "problem": result['target_problem'], "idea": result['idea']}

    return {"ideaData": ideaData}

# When the user finishes that round, move them to the next round.
@main.route("/nextRound")
@jwt_required()
@cross_origin()
def nextRound():
    user = User.query.filter_by(email=get_jwt_identity()).first()

    ########Collect Log#######
    timestamp = datetime.fromtimestamp(datetime.now().timestamp())
    userlog = UserLog(user_id = user.id, round=user.currentRound, timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S'), tag="finish", data="")
    db.session.add(userlog)
    db.session.commit()
    ##########################

    user.currentRound += 1
    flag_modified(user, 'currentRound')
    db.session.commit()

    return {"msg":"Next Round!"}

# get log data
@main.route("/getLogData", methods=["POST"])
@cross_origin()
def getLogData():
    params = request.get_json()
    userNum = int(params['userNum'])
    user_id = User.query.filter_by(num=userNum).first().id
    logs = UserLog.query.filter_by(user_id=user_id).all()

    logData = []
    for log in logs:
        logData.append({"user_id": log.user_id, "timestamp": log.timestamp, "tag": log.tag, "data": log.data})

    return {"logData": logData}



app = create_app()
if __name__ == '__main__':
    db.create_all(app=create_app())
    app.run(host='0.0.0.0', port=5000, debug=True)