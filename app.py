from flask import Flask,render_template, redirect, request, session, jsonify
from blueprints.user import user
from blueprints.ai import ai
from blueprints.board import board
from blueprints.categorie import categorie
from blueprints.filters import filters
from blueprints.api import api

from dao import BoardDAO,CategorieDAO,UserDAO
import os

app = Flask(__name__)
app.register_blueprint(user, url_prefix='/user')
app.register_blueprint(ai, url_prefix='/ai')
app.register_blueprint(board, url_prefix='/board')
app.register_blueprint(categorie, url_prefix='/categorie')
app.register_blueprint(filters, url_prefix='/filters')
app.register_blueprint(api, url_prefix='/api')


app.config['SECRET_KEY'] = os.urandom(24)

ALLOWED_ORDER_KEYS = ['like_count desc', 'board_no desc', 'board_no']

@app.route("/") 
def main():
    return redirect("/index.do")

# index ===========================================================
@app.route("/index.do", methods=["GET"])
def index():
    # 게시물 정렬 기준, 기본값 : 인기순
    order_key = request.args.get("order_key", ALLOWED_ORDER_KEYS[0])
    if order_key not in ALLOWED_ORDER_KEYS:
        print(f"경고: 허용되지 않은 order_key 값 시도됨 -> {order_key}")
        order_key = ALLOWED_ORDER_KEYS[0]
        
    current_user_no = session.get('user_data', {}).get('user_no')
    
    board_dao = BoardDAO()
    
    board_list = board_dao.get_list(order_key=order_key, current_user_no=current_user_no)
    
    if board_list is None:
        return "error page"
    
    return render_template("index.html", board_list=board_list, order_key=order_key)

# subscribe / like ==================================================
@app.route("/like.do", methods=["POST"])
def toggle_like():
    # 1. 로그인 상태 확인 (401: 권한 없음)
    if 'user_data' not in session:
        return jsonify({'status': 'error', 'message': '로그인이 필요합니다.'}), 401

    # 2. 프론트엔드에서 보낸 데이터 확인 (400: 잘못된 요청)
    board_no_str = request.form.get('board_no')
    
    if not board_no_str:
        return jsonify({'status': 'error', 'message': '게시물 번호(board_no)가 필요합니다.'}), 400

    # 3. DAO를 통해 좋아요 처리 (500: 서버 내부 에러)
    try:
        user_no = session['user_data']['user_no']
        board_no = int(board_no_str)
        
        board_dao = BoardDAO()
        result = board_dao.toggle_like(user_no, board_no)
        
        # 4. 처리 결과 반환
        if result['status'] == 'success':
            return jsonify(result), 200 # 성공
        else:
            return jsonify(result), 500 # DAO 내부 에러

    except ValueError:
        return jsonify({'status': 'error', 'message': '게시물 번호가 올바른 형식이 아닙니다.'}), 400
    except Exception as e:
        print(f"Error in toggle_like: {e}")
        return jsonify({'status': 'error', 'message': '서버 처리 중 오류가 발생했습니다.'}), 500

@app.route("/subscribe.do", methods=["POST"])
def toggle_subscribe():
    # 1. 로그인 상태 확인 (개선: 401 상태 코드 반환)
    if 'user_data' not in session:
        return jsonify({'status': 'error', 'message': '로그인이 필요합니다.'}), 401 # Unauthorized

    # 2. 프론트엔드에서 보낸 데이터 확인 (개선: 400 상태 코드 반환)
    categorie_no_str = request.form.get('categorie_no')

    if not categorie_no_str:
        return jsonify({'status': 'error', 'message': '카테고리 번호(categorie_no)가 필요합니다.'}), 400 # Bad Request

    # 3. DAO를 통해 구독 처리 (개선: 500 상태 코드 및 ValueError 처리)
    try:
        user_no = session['user_data']['user_no']
        categorie_no = int(categorie_no_str)  # 안전을 위해 정수형으로 변환
        
        categorie_dao = CategorieDAO()
        result = categorie_dao.toggle_subscribe(user_no, categorie_no)
        
        # 3-1. 세션에 등록된 로그인 유저 구독 데이터 갱신
        user_dao = UserDAO()
        sub_categorie_list = user_dao.sub_categorie(user_no)
        
        session['sub_categorie_list'] = sub_categorie_list
        session['sub_categorie_no_list'] = [dto.categorie_no for dto in sub_categorie_list]
        
        # 4. 처리 결과 반환
        if result['status'] == 'success':
            return jsonify(result), 200 # OK
        else:
            # DAO 내부에서 에러가 발생한 경우
            return jsonify(result), 500 # Internal Server Error

    except ValueError:
        # categorie_no가 숫자가 아닐 경우의 에러 처리
        return jsonify({'status': 'error', 'message': '카테고리 번호가 올바른 형식이 아닙니다.'}), 400
    except Exception as e:
        print(f"Error in toggle_subscribe: {e}")
        return jsonify({'status': 'error', 'message': '서버 처리 중 오류가 발생했습니다.'}), 500


# main 함수
if __name__ == "__main__":
    app.run()
    #app.run(host='0.0.0.0', port=5000)
