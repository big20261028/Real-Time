from flask import Blueprint, request, jsonify, session
from tools import AI_Tools
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dao import BoardDAO, UserDAO, CategorieDAO, FiltersDAO
from dataclasses import asdict

api = Blueprint("api", __name__, template_folder='templates')

ALLOWED_ORDER_KEYS = ['like_count desc', 'board_no desc', 'board_no']

# 메인페이지 무한스크롤
@api.route("/posts.do", methods=["GET"])
def get_posts():
    # 1. 클라이언트가 요청한 파라미터 가져오기
    try:
        page = int(request.args.get('page', 1)) 
        limit = 10 
        offset = (page - 1) * limit
    except ValueError:
        return jsonify({'status': 'error', 'message': '페이지 번호가 올바르지 않습니다.'}), 400

    order_key = request.args.get('order_key', ALLOWED_ORDER_KEYS[0])
    if order_key not in ALLOWED_ORDER_KEYS:
        order_key = ALLOWED_ORDER_KEYS[0]

    # 2. DAO를 통해 데이터 조회
    try:
        current_user_no = session.get('user_data', {}).get('user_no')
        board_dao = BoardDAO()
        
        # DAO의 get_list를 offset과 limit을 사용하여 호출
        board_list = board_dao.get_list(
            order_key=order_key, 
            limit=limit,
            offset=offset,
            current_user_no=current_user_no
        )

        # 3. DTO 객체를 JSON으로 변환 가능한 딕셔너리로 변환
        from dataclasses import asdict
        posts_data = [asdict(post) for post in board_list]
        
        # 날짜 객체는 문자열로 변환
        for post in posts_data:
            post['board_write_date'] = post['board_write_date'].strftime('%Y-%m-%d')
            # Board_DTO의 property 'tags'도 함께 보내주면 편리합니다.
            post['tags'] = [tag.strip() for tag in post['tag_names'].split(',') if tag.strip()]


        # 4. 성공 응답 반환
        return jsonify({
            'status': 'success',
            'posts': posts_data,
            'has_next': len(posts_data) == limit 
        }), 200

    except Exception as e:
        print(f"API Error in get_posts: {e}")
        return jsonify({'status': 'error', 'message': '서버 처리 중 오류가 발생했습니다.'}), 500

# 추천 페이지 무한스크롤 API
@api.route("/recommendations.do", methods=["GET"])
def get_recommendations_api():
    # 1. 로그인 확인
    if 'user_data' not in session:
        return jsonify({'status': 'error', 'message': '로그인이 필요합니다.'}), 401

    # 2. 클라이언트가 요청한 파라미터 가져오기
    try:
        page = int(request.args.get('page', 1))
        limit = 10
        offset = (page - 1) * limit
    except ValueError:
        return jsonify({'status': 'error', 'message': '페이지 번호가 올바르지 않습니다.'}), 400

    # 3. 추천 서비스를 통해 데이터 조회
    try:
        user_no = session['user_data']['user_no']
        user_dao = UserDAO()
        
        # 수정된 서비스 메소드 호출
        board_list = user_dao.user_recommend(
            user_no=user_no,
            offset=offset,
            limit=limit,
            current_user_no=user_no
        )
        
        # 3. DTO 객체를 JSON으로 변환 가능한 딕셔너리로 변환
        # dataclasses.asdict를 사용하면 편리합니다.
        from dataclasses import asdict
        posts_data = [asdict(post) for post in board_list]
        
        # 날짜 객체는 문자열로 변환해줘야 JSON으로 직렬화 가능
        for post in posts_data:
            post['board_write_date'] = post['board_write_date'].strftime('%Y-%m-%d')
            # Board_DTO의 property 'tags'도 함께 보내주면 편리합니다.
            post['tags'] = [tag.strip() for tag in post['tag_names'].split(',') if tag.strip()]

        # 5. 성공 응답 반환
        return jsonify({
            'status': 'success',
            'posts': posts_data,
            'has_next': len(posts_data) == limit
        }), 200

    except Exception as e:
        print(f"API Error in get_recommendations_api: {e}")
        return jsonify({'status': 'error', 'message': '서버 처리 중 오류가 발생했습니다.'}), 500
    
# 마이페이지 무한스크롤
@api.route('/my_posts.do', methods=['GET'])
def get_my_posts():
    # 1. 로그인 상태 확인 (API는 JSON으로 응답)
    if 'user_data' not in session:
        return jsonify({'status': 'error', 'message': '로그인이 필요합니다.'}), 401

    # 2. 클라이언트 요청 파라미터 가져오기
    try:
        page = int(request.args.get('page', 1))
        limit = 10
        offset = (page - 1) * limit
    except ValueError:
        return jsonify({'status': 'error', 'message': '페이지 번호가 올바르지 않습니다.'}), 400
        
    order_key = request.args.get('order_key', ALLOWED_ORDER_KEYS[1])
    if order_key not in ALLOWED_ORDER_KEYS:
        order_key = ALLOWED_ORDER_KEYS[1]

    # 3. DAO를 통해 데이터 조회
    try:
        user_no = session['user_data']['user_no']
        user_dao = UserDAO()
        board_list = user_dao.myboard(
            user_no=user_no,
            order_key=order_key,
            limit=limit,
            offset=offset
        )

        # 4. 조회 결과를 JSON으로 변환
        posts_data = [asdict(post) for post in board_list]
        for post in posts_data:
            post['board_write_date'] = post['board_write_date'].strftime('%Y-%m-%d')
            post['tags'] = [tag.strip() for tag in post['tag_names'].split(',') if tag.strip()]

        # 5. 성공 응답 반환
        return jsonify({
            'status': 'success',
            'posts': posts_data,
            'has_next': len(posts_data) == limit
        }), 200

    except Exception as e:
        print(f"API Error in get_my_posts: {e}")
        return jsonify({'status': 'error', 'message': '서버 처리 중 오류가 발생했습니다.'}), 500
    
# 카테고리 페이지 무한스크롤
@api.route('/categorie_posts.do',methods=['GET'])
def get_categorie_posts():
    # 2. 클라이언트 요청 파라미터 가져오기
    try:
        categorie_no = int(request.args.get('categorie_no'))
        page = int(request.args.get('page', 1))
        limit = 10
        offset = (page - 1) * limit
    except ValueError:
        return jsonify({'status': 'error', 'message': '카테고리 또는 페이지 번호가 올바르지 않습니다.'}), 400
        
    order_key = request.args.get('order_key', ALLOWED_ORDER_KEYS[1])
    if order_key not in ALLOWED_ORDER_KEYS:
        order_key = ALLOWED_ORDER_KEYS[1]

    # 3. DAO를 통해 데이터 조회
    #  def categorie_board(self, categorie_no, order_key="like_count desc", offset=0, limit=10, current_user_no=None):
    try:
        current_user_no = session.get('user_data', {}).get('user_no')
        categorie_dao = CategorieDAO()
        board_list = categorie_dao.categorie_board(
            categorie_no = categorie_no,
            order_key = order_key,
            limit = limit,
            offset = offset,
            current_user_no = current_user_no
        )

        # 4. 조회 결과를 JSON으로 변환
        posts_data = [asdict(post) for post in board_list]
        for post in posts_data:
            post['board_write_date'] = post['board_write_date'].strftime('%Y-%m-%d')
            post['tags'] = [tag.strip() for tag in post['tag_names'].split(',') if tag.strip()]

        # 5. 성공 응답 반환
        return jsonify({
            'status': 'success',
            'posts': posts_data,
            'has_next': len(posts_data) == limit
        }), 200

    except Exception as e:
        print(f"API Error in get_my_posts: {e}")
        return jsonify({'status': 'error', 'message': '서버 처리 중 오류가 발생했습니다.'}), 500
    
# 검색 페이지 무한스크롤
@api.route('/search_posts.do',methods=['GET'])
def get_search_posts():
    # 2. 클라이언트 요청 파라미터 가져오기
    # 받아야하는 파라미터 : keyword, search_filter, order_key, page
    try:
        page = int(request.args.get('page', 1))
        limit = 10
        offset = (page - 1) * limit
    except ValueError:
        return jsonify({'status': 'error', 'message': '페이지 번호가 올바르지 않습니다.'}), 400
        
    order_key = request.args.get('order_key', ALLOWED_ORDER_KEYS[1])
    if order_key not in ALLOWED_ORDER_KEYS:
        order_key = ALLOWED_ORDER_KEYS[1]
    
    keyword = request.args.get('keyword')
    search_filter = request.args.get('search_filter')
    
    if keyword == None or keyword == '':
        return jsonify({'status': 'error', 'message': '키워드가 입력되지 않았습니다.'}), 400
    
    if search_filter == None or search_filter == '':
        return jsonify({'status': 'error', 'message': '검색필터가 입력되지 않았습니다.'}), 400
    
    # 3. DAO를 통해 데이터 조회
    #  def search(self, keyword, search_filter, order_key="board_no desc", offset=0, limit=10, current_user_no=None):
    try:
        current_user_no = session.get('user_data', {}).get('user_no')
        
        filters_dao = FiltersDAO()
        board_list = filters_dao.search(
            keyword=keyword,
            search_filter=search_filter,
            order_key=order_key,
            offset=offset,
            limit=limit,
            current_user_no=current_user_no
        )

        # 4. 조회 결과를 JSON으로 변환
        posts_data = [asdict(post) for post in board_list]
        for post in posts_data:
            post['board_write_date'] = post['board_write_date'].strftime('%Y-%m-%d')
            post['tags'] = [tag.strip() for tag in post['tag_names'].split(',') if tag.strip()]

        # 5. 성공 응답 반환
        return jsonify({
            'status': 'success',
            'posts': posts_data,
            'has_next': len(posts_data) == limit
        }), 200

    except Exception as e:
        print(f"API Error in get_my_posts: {e}")
        return jsonify({'status': 'error', 'message': '서버 처리 중 오류가 발생했습니다.'}), 500

# 사용자 페이지 무한스크롤
@api.route('/user_posts.do',methods=['GET'])
def get_user_posts():
    # 2. 클라이언트 요청 파라미터 가져오기
    # 받아야하는 파라미터 : order_key, page, user_no
    try:
        user_no = int(request.args.get('user_no'))
        page = int(request.args.get('page', 1))
        limit = 10
        offset = (page - 1) * limit
    except ValueError:
        return jsonify({'status': 'error', 'message': '사용자 번호 또는 페이지 번호가 올바르지 않습니다.'}), 400
        
    order_key = request.args.get('order_key', ALLOWED_ORDER_KEYS[1])
    if order_key not in ALLOWED_ORDER_KEYS:
        order_key = ALLOWED_ORDER_KEYS[1]
    
    # 3. UserDAO를 통해 데이터 조회
    #  def user_board(self,user_no,order_key="board_no desc", limit=10, offset=0, current_user_no=None):
    try:
        current_user_no = session.get('user_data', {}).get('user_no')
        
        user_dao = UserDAO()
        board_list = user_dao.user_board(
            user_no=user_no,
            order_key=order_key,
            limit=limit,
            offset=offset,
            current_user_no=current_user_no
        )

        # 4. 조회 결과를 JSON으로 변환
        posts_data = [asdict(post) for post in board_list]
        for post in posts_data:
            post['board_write_date'] = post['board_write_date'].strftime('%Y-%m-%d')
            post['tags'] = [tag.strip() for tag in post['tag_names'].split(',') if tag.strip()]

        # 5. 성공 응답 반환
        return jsonify({
            'status': 'success',
            'posts': posts_data,
            'has_next': len(posts_data) == limit
        }), 200

    except Exception as e:
        print(f"API Error in get_my_posts: {e}")
        return jsonify({'status': 'error', 'message': '서버 처리 중 오류가 발생했습니다.'}), 500
    
# 태그 추천 알고리즘
@api.route('/rec_tag.do', methods=['POST'])
def rec_tags():
    board_title = request.form.get('board_title')
    board_note  = request.form.get('board_note')
    
    text = board_title + " " + board_note
    
    ai_tools = AI_Tools()
    rec_tags = ai_tools.extract_co_occurrence_keywords(text=text,
                                                       num_keywords=10, 
                                                       window_size=5)
    
    return jsonify({
        'status': 'success',
        'posts': rec_tags
    }), 200