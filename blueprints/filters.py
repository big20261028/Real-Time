from flask import Blueprint, render_template, request, flash, url_for, redirect
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dao import FiltersDAO


filters = Blueprint("filters", __name__, template_folder='templates')

ALLOWED_ORDER_KEYS_BOARD = ['like_count desc', 'board_no desc', 'board_no']

@filters.route('/search.do')
def search():
    keyword = request.args.get('keyword')
    search_filter = request.args.get('search_filter')
    
    # 키워드 미 입력 시 페이지 접근불가능
    if keyword == None or keyword == '':
        flash('잘못된 접근입니다.','error')
        return redirect(url_for('index'))
    
    # 기본 검색 기준 : 전체 검색
    if search_filter == None or search_filter == '':
        search_filter = '1'
    
    # 게시물 정렬 기준, 기본값 : 최신순
    order_key = request.args.get("order_key", ALLOWED_ORDER_KEYS_BOARD[1])
    if order_key not in ALLOWED_ORDER_KEYS_BOARD:
        print(f"경고: 허용되지 않은 order_key 값 시도됨 -> {order_key}")
        order_key = ALLOWED_ORDER_KEYS_BOARD[1]
    
    filter_dao = FiltersDAO()
    
    result = filter_dao.search(keyword, search_filter, order_key)
    
    if result is False:
        flash("검색 중 오류가 발생했습니다.", "error")
        return redirect(url_for('index'))
        
    
    return render_template("/filter/search.html", 
                           keyword=keyword,
                           result=result, 
                           order_key=order_key, 
                           search_filter=search_filter)

@filters.route('/tagboard.do')
def tagboard():
    tag = request.args.get('tag')
    if tag == None or tag == '':
        flash('잘못된 접근입니다.','error')
        return redirect(url_for('index'))
    
    return redirect(url_for('filters.search', keyword=tag, search_filter='5'))



