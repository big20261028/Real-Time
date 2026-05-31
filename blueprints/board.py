from flask import Blueprint, render_template, redirect, request, session, flash, jsonify, url_for
from dao import BoardDAO
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

board = Blueprint("board", __name__, template_folder='templates')

@board.route('/write.do')
def write():
    categorie_no = request.args.get('categorie_no')
    categorie_parent_no = request.args.get('categorie_parent_no')
    
    if 'user_data' not in session:
        flash('로그인이 필요한 서비스입니다.', "error")
        return redirect(url_for('index'))
    return render_template("/board/write.html",categorie_no=categorie_no, categorie_parent_no=categorie_parent_no)

@board.route('/parent_categorie.do')
def parent_cateogorie():
    board_dao = BoardDAO()
    categorie_parent_no_list = board_dao.select_categorie_parent_list()
    
    return jsonify(categorie_parent_no_list)

@board.route('/child_categorie.do')
def child_categorie():
    categorie_parent_no = request.args.get('categorie_parent_no')
    
    board_dao = BoardDAO()
    categorie_child_no_list = board_dao.select_categorie_child_list(categorie_parent_no)
    
    return jsonify(categorie_child_no_list)

@board.route('/writeok.do', methods=['POST'])
def writeok():
    if 'user_data' not in session:
        flash('로그인이 필요한 서비스입니다.', "error")
        return redirect(url_for('index'))
    
    user_no = session['user_data']['user_no']
    
    board_title  = request.form.get('board_title')
    board_note   = request.form.get('board_note')
    categorie_no = request.form.get('categorie_no')
    tags         = request.form.get('tags')
        
    tag_names = []
    if tags:
        try:
            # JSON 문자열을 Python 리스트/딕셔너리로 변환
            tags_list = json.loads(tags)
            # 각 딕셔너리에서 'value' 값만 추출
            tag_names = [tag['value'] for tag in tags_list]
        except (json.JSONDecodeError, TypeError):
            # 비정상적인 데이터가 올 경우 예외 처리
            tag_names = []
    
    board_dao = BoardDAO()
    if not board_dao.write(board_title, board_note, categorie_no, user_no, tag_names):
        flash('게시글 등록을 실패했습니다.', 'error')
        return redirect(url_for('index'))
    flash('게시글 등록에 성공했습니다.', 'success')
    return redirect('/user/myboard.do')

@board.route('/modify.do', methods=['GET'])
def modify():
    if 'user_data' not in session:
        flash('로그인이 필요한 서비스입니다.', "error")
        return redirect(url_for('index'))
    
    board_no = request.args.get('board_no')
    
    if not board_no:
        flash('잘못된 접근입니다.', 'error')
        return redirect(url_for('index'))
    
    board_dao = BoardDAO()
    modify_board = board_dao.select_one_board(board_no)
    
    if not modify_board:
        flash('존재하지 않는 게시글입니다.', 'error')
        return redirect(url_for('index'))
    
    if modify_board.user_no != session['user_data']['user_no']:
        flash('작성자만 수정할 수 있습니다.', 'error')
        return redirect(request.referrer or url_for('index'))
    
    tag_names_str = modify_board.tag_names # 'tag1, tag2' 또는 ''
    tag_list = []
    if tag_names_str:
        tag_list = tag_names_str.split(', ')
        
    tags_for_tagify = [{"value": name} for name in tag_list]
    tags_json = json.dumps(tags_for_tagify, ensure_ascii=False)
    
    return render_template("/board/modify.html",
                           modify_board=modify_board, 
                           tags_json=tags_json)

@board.route('/modifyok.do',methods=['POST'])
def modifyok():
    if 'user_data' not in session:
        flash('로그인이 필요한 서비스입니다.', "error")
        return redirect(url_for('index'))
    
    user_no  = session['user_data']['user_no']
    board_no = request.form.get('board_no')
    
    board_dao = BoardDAO()
    if not board_dao.is_your_board(user_no, board_no):
        flash('작성자만 수정할 수 있습니다.','error')
        return redirect(url_for('index'))
    
    board_title  = request.form.get('board_title')
    board_note   = request.form.get('board_note')
    categorie_no = request.form.get('categorie_no')
    tags         = request.form.get('tags')
    
    tag_names = []
    if tags:
        try:
            # JSON 문자열을 Python 리스트/딕셔너리로 변환
            tags_list = json.loads(tags)
            # 각 딕셔너리에서 'value' 값만 추출
            tag_names = [tag['value'] for tag in tags_list]
        except (json.JSONDecodeError, TypeError):
            # 비정상적인 데이터가 올 경우 예외 처리
            tag_names = []
    
    
    if not board_dao.modify(board_title, board_note, categorie_no, board_no, tag_names, user_no):
        flash('게시글 등록을 실패했습니다.', 'error')
        return redirect(url_for('index'))
    flash('게시글 등록에 성공했습니다.', 'success')
    return redirect('/user/myboard.do')

@board.route('/delete.do', methods=['GET'])
def delete():
    if 'user_data' not in session:
        flash('로그인이 필요한 서비스입니다.', "error")
        return redirect(url_for('index'))
    
    board_no     = request.args.get('board_no')
    user_no      = request.args.get('user_no')
    
    if user_no != str(session['user_data']['user_no']):
        flash('잘못된 접근입니다.','error')
        return redirect(url_for('index'))
    
    board_dao = BoardDAO()
    if not board_dao.delete(board_no):
        flash('게시글 삭제를 실패했습니다.', 'error')
        return redirect(url_for('index'))
    flash('게시글 삭제를 성공했습니다.', 'success')
    return redirect(request.referrer or url_for('index'))


    
    
    

