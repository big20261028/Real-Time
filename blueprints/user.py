from flask import Blueprint, render_template, request, redirect, session, flash, url_for, jsonify
from dao import UserDAO
from dataclasses import asdict
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

user = Blueprint("user", __name__, template_folder='templates')

ALLOWED_ORDER_KEYS = ['like_count desc', 'board_no desc', 'board_no']

@user.route('/myboard.do', methods=["GET"])
def myboard():
    if 'user_data' not in session:
        flash('로그인이 필요한 서비스입니다.', "error")
        return redirect("/index.do")
    
    # 게시물 정렬 기준, 기본값 : 최신순
    order_key = request.args.get("order_key", ALLOWED_ORDER_KEYS[1])
    if order_key not in ALLOWED_ORDER_KEYS:
        print(f"경고: 허용되지 않은 order_key 값 시도됨 -> {order_key}")
        order_key = ALLOWED_ORDER_KEYS[1]
    
    user_no = session['user_data']['user_no']
    
    user_dao = UserDAO()
    
    board_list = user_dao.myboard(user_no=user_no,order_key=order_key)
    
    return render_template("/user/myboard.html", board_list=board_list, order_key=order_key)

@user.route('/userpage.do', methods=['GET'])
def userpage():
    user_no  = request.args.get('user_no')
    board_no = request.args.get('board_no')
    if user_no is None:
        flash("잘못된 접근입니다.",'error')
        return redirect("/index.do")
    
    # 게시물 정렬 기준, 기본값 : 최신순
    order_key = request.args.get("order_key", ALLOWED_ORDER_KEYS[1])
    if order_key not in ALLOWED_ORDER_KEYS:
        print(f"경고: 허용되지 않은 order_key 값 시도됨 -> {order_key}")
        order_key = ALLOWED_ORDER_KEYS[1]
        
    current_user_no = session.get('user_data', {}).get('user_no')
    
    user_dao = UserDAO()
    userpage_data = user_dao.userpage(user_no=user_no,board_no=board_no, current_user_no=current_user_no)
    
    if userpage_data is None:
        flash("페이지 로드 중, 오류가 발생했습니다.",'error')
        return redirect("/index.do")
    
    return render_template("/user/userpage.html",userpage_data=userpage_data, order_key=order_key)

@user.route('/recommend.do')
def recommend():
    # 1. 로그인 확인
    if 'user_data' not in session:
        flash('로그인이 필요한 서비스입니다.', "error")
        return redirect("/index.do")
    
   
    # 2. 세션에서 사용자 번호 가져오기
    user_no = session['user_data']['user_no']
    
    print(f"user_no={user_no}")
    
   
    # 3. 추천 서비스 호출하여 "첫 페이지" 데이터만 미리 가져오기
    #    - 반환된 튜플에서 첫 번째 요소(게시물 리스트)만 사용합니다.
    user_dao = UserDAO()
    board_list = user_dao.user_recommend(user_no, 
                                         offset=0, 
                                         limit=10,
                                         current_user_no=user_no)
    
    
    
    # 4. 결과를 템플릿에 전달
    return render_template(
        "/user/recommend.html", 
        board_list=board_list
    )

# login ===========================================================================================================
@user.route('/login.do')
def login():
    return render_template("/modal/login.html")

@user.route('/loginok.do',methods=['POST'])
def loginOk():
    user_id      = request.form["user_id"]  
    user_pw      = request.form["user_pw"]  
    
    user_dao = UserDAO()
    user_data = user_dao.login(user_id, user_pw)
    
    if user_data is None: 
        flash('로그인에 실패했습니다.', "error")
        return redirect(request.referrer or url_for('index'))
    
    session['user_data'] = user_data
    
    sub_categorie_list = user_dao.sub_categorie(user_data.user_no)
    
    session['sub_categorie_list'] = sub_categorie_list
    session['sub_categorie_no_list'] = [dto.categorie_no for dto in sub_categorie_list]
    
    flash('로그인을 성공했습니다.', "success")
    return redirect(request.referrer or url_for('index'))

@user.route('/logout.do')
def logout():
    # 세션 삭제
    if 'user_data' in session:
        session.clear()
        flash('로그아웃이 완료되었습니다.', "success")
        return redirect(request.referrer or url_for('index'))
    flash('잘못된 접근입니다.', "error")
    return redirect("/index.do")

# join ===========================================================================================================
@user.route('/join.do')
def join():
    return render_template("/modal/join.html")

@user.route('/joinok.do',methods=['POST'])
def joinOk():
    user_id      = request.form["user_id"]  
    user_pw      = request.form["user_pw"]  
    user_pf_img  = request.form["user_pf_img"]  
    
    user_dao = UserDAO()
    if user_dao.join(user_id, user_pw, user_pf_img): 
        flash('회원가입 성공', "success")
        return redirect(request.referrer or url_for('index'))
    flash('회원가입 실패', "error")
    return redirect(request.referrer or url_for('index'))



