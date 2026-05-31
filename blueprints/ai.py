from flask import Blueprint, render_template, request, flash, redirect
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

ai = Blueprint("ai", __name__, template_folder='templates')

from tools import TextCompare,SVN

@ai.route('/score_info.do')
def score_info():
    board_no = request.args.get('from_board_no')
    to_board_no = request.args.get('to_board_no')
    score    = request.args.get('score')
    if board_no is None or score is None:
        flash("잘못된 접근입니다.",'error')
        return redirect("/index.do")
    # 1. 그래프 생성 함수를 호출하여 Base64 이미지 데이터를 받습니다.
    text_compare = TextCompare()
    graph_image = text_compare.generate_similarity_graph_base64(board_no)
    board_dto = text_compare.board_data(board_no)

    return render_template("/ai/score_info.html", 
                           image_data=graph_image, 
                           board_dto=board_dto, 
                           score=score, 
                           board_no=to_board_no
                           )

@ai.route('/score_info_rec.do')
def score_info_rec():
    # 1. 쿼리 파라미터에서 정보 가져오기
    # 어떤 사용자가 로그인했는지 세션 등에서 user_no를 가져와야 합니다.
    # 여기서는 예시로 쿼리 파라미터로 받는다고 가정합니다.
    user_no = request.args.get('user_no', type=int) 
    board_no = request.args.get('board_no', type=int)
    score    = request.args.get('score')

    if user_no is None or board_no is None or score is None:
        flash("사용자 정보 또는 게시글 정보가 없습니다.", 'error')
        return redirect("/index.do")

    # 2. SVN(SVD) 모델 인스턴스 생성 및 그래프 생성
    svn_model = SVN()
    model_file_path = "recommand.pkl" # 실제 모델 파일 경로
    
    # 새로운 함수 호출
    graph_image = svn_model.generate_score_breakdown_graph(user_no, board_no, model_file_path, score)

    # 3. 템플릿에 데이터 전달
    # 게시글 자체의 정보도 필요하다면 DAO를 통해 가져옵니다.
    text_compare = TextCompare()
    board_dto = text_compare.board_data(board_no)

    if graph_image is None:
        flash("점수 분석 그래프를 생성하는 데 실패했습니다.", "warning")

    return render_template(
        "/ai/score_info_rec.html", 
        image_data=graph_image, 
        board_dto=board_dto,
        user_no=user_no,
        score=score,
        board_no=board_no
    )

