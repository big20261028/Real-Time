from flask import Blueprint, render_template, redirect, request, flash, url_for, session
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dao import CategorieDAO

categorie = Blueprint("categorie", __name__, template_folder='templates')

ALLOWED_ORDER_KEYS = ['subscribe_count desc', 'categorie_no desc', 'categorie_no']
ALLOWED_ORDER_KEYS_BOARD = ['like_count desc', 'board_no desc', 'board_no']

@categorie.route('/categorie_list.do', methods=['GET'])
def categorie_list():
    categorie_parent_no = request.args.get('categorie_parent_no')
    
    if categorie_parent_no == None or categorie_parent_no == '':
        flash('잘못된 접근입니다.','error')
        return redirect(url_for('index'))
    
    # 게시물 정렬 기준, 기본값 : 구독자 많은 순
    order_key = request.args.get("order_key", ALLOWED_ORDER_KEYS[0])
    if order_key not in ALLOWED_ORDER_KEYS:
        print(f"경고: 허용되지 않은 order_key 값 시도됨 -> {order_key}")
        order_key = ALLOWED_ORDER_KEYS[0]
    
    current_user_no = session.get('user_data', {}).get('user_no')
    
    categorie_dao = CategorieDAO()
    
    categorie_data = categorie_dao.categorie_list(categorie_parent_no, order_key, current_user_no=current_user_no)
    
    return render_template("/categorie/categorie_list.html", categorie_data=categorie_data, order_key=order_key, categorie_parent_no=categorie_parent_no)

@categorie.route('/categorie_page.do', methods=['GET'])
def categorie_page():
    categorie_no = request.args.get('categorie_no')
    
    if categorie_no == None or categorie_no == '':
        flash('잘못된 접근입니다.','error')
        return redirect(url_for('index'))
    
    # 게시물 정렬 기준, 기본값 : 최신순
    order_key = request.args.get("order_key", ALLOWED_ORDER_KEYS_BOARD[1])
    if order_key not in ALLOWED_ORDER_KEYS_BOARD:
        print(f"경고: 허용되지 않은 order_key 값 시도됨 -> {order_key}")
        order_key = ALLOWED_ORDER_KEYS_BOARD[1]
        
    current_user_no = session.get('user_data', {}).get('user_no')
    
    categorie_dao = CategorieDAO()
    result = categorie_dao.categorie_page(categorie_no,order_key,current_user_no=current_user_no)
    
    return render_template("/categorie/categorie_page.html", result=result, order_key=order_key)




