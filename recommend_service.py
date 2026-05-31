# /services/recommend_service.py

import pickle
import pandas as pd
from datetime import datetime

# 프로젝트의 다른 모듈 import
# 이 경로는 프로젝트 구조에 따라 달라질 수 있습니다.
from dao import BoardDAO, UserDAO # 인기 게시물, 최근 활동 조회를 위해
from models import Recommend_Board_DTO
from DBManager import DBManager

# 학습된 모델 아티팩트 파일 경로
ARTIFACTS_PATH = "model_artifacts.pkl" # train_als_model.py에서 저장한 경로와 동일해야 함

class RecommendationService:
    _instance = None
    
    # 싱글턴 패턴: 이 클래스의 인스턴스가 단 하나만 생성되도록 보장
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RecommendationService, cls).__new__(cls)
            cls._instance._load_artifacts()
        return cls._instance

    def _load_artifacts(self):
        """서버 시작 시 아티팩트를 로드합니다. (최종 수정안)"""
        # 1. Fallback 데이터(인기 게시물)를 먼저 로드
        print(f"[{datetime.now()}] 추천 서비스 초기화 시작...")
        try:
            self.board_dao = BoardDAO()
            self.popular_items = self.board_dao.get_list(order_key="like_count desc", limit=20)
            print("  - 콜드 스타트용 인기 게시물 로드 완료.")
        except Exception as e:
            print(f"오류: 인기 게시물 로드 실패. >> {e}")
            self.popular_items = []

        # 2. 모델 관련 속성 초기화
        self.model = None
        self.sparse_user_item = None
        self.user_map = {}
        self.item_inv_map = {}
        self.timestamp = "N/A"

        # 3. 모델 아티팩트 로드 시도
        try:
            print("  - 추천 모델 아티팩트 로딩 시도...")
            with open(ARTIFACTS_PATH, 'rb') as f:
                artifacts = pickle.load(f)
            
            # ★★★★★ 중요: pkl 파일에 저장된 맵을 직접 사용합니다. ★★★★★
            self.model = artifacts['model']
            self.sparse_user_item = artifacts['sparse_user_item']
            self.user_map = artifacts['user_map']
            self.item_inv_map = artifacts['item_inv_map']
            self.timestamp = artifacts.get('timestamp', 'N/A')

            print(f"  - 모델 로딩 완료 (학습 시점: {self.timestamp})")
            print(f"  - 로드된 사용자 수: {len(self.user_map)}, 아이템 수: {len(self.item_inv_map)}")

        except FileNotFoundError:
            print(f"  - 정보: 모델 아티팩트 파일({ARTIFACTS_PATH})을 찾을 수 없습니다.")
        except Exception as e:
            print(f"  - 경고: 모델 아티팩트 로딩 중 예외 발생. >> {e}")

    def _get_recommended_board_ids(self, user_no) -> list:
        """
        [내부 메소드] 주어진 사용자의 전체 추천 게시물 ID 목록을 점수와 함께 생성합니다.
        """
        # ★★★★★ 중요 수정 포인트 1 ★★★★★
        # 이 메소드 자체에서도 콜드 스타트 사용자인지 확인합니다.
        if self.model is None or user_no not in self.user_map:
            # 모델이 없거나, 학습 시점에 없었던 새로운 사용자라면 빈 리스트를 반환합니다.
            return [] 

        user_cat = self.user_map[user_no]
        user_interactions = self.sparse_user_item[user_cat]
        
        num_total_items = self.sparse_user_item.shape[1]
        
        # IndexError를 원천 방지하기 위한 최종 방어선
        # user_cat이 모델이 아는 사용자 수 범위를 벗어나는지 확인합니다.
        num_users_in_model = self.model.user_factors.shape[0]
        if user_cat >= num_users_in_model:
            print(f"경고: user_cat({user_cat})이 모델의 사용자 수({num_users_in_model}) 범위를 벗어납니다. user_no: {user_no}")
            return []
        
        recommended_cats, scores = self.model.recommend(
            userid=user_cat,
            user_items=user_interactions,
            N=num_total_items,
            filter_already_liked_items=True
        )

        recommendations = []
        for item_cat, score in zip(recommended_cats, scores):
            board_no = self.item_inv_map.get(item_cat)
            if board_no:
                recommendations.append({'board_no': board_no, 'score': score})
        
        return recommendations

    def get_recommendations(self, user_no, offset=0, limit=10, current_user_no=None) -> tuple:
        """
        주어진 사용자 번호에 대해 페이징된 추천 목록을 반환합니다.
        """
        # ★★★★★ 중요 수정 포인트 2 ★★★★★
        # 여기서 콜드 스타트 여부를 명확히 판단하고, 그에 따라 분기합니다.

        # 1. 모델이 없거나, user_no가 학습된 유저 목록에 없는 경우 -> 콜드 스타트!
        if self.model is None or user_no not in self.user_map:
            print(f"콜드 스타트 사용자 감지 (user_no: {user_no}). 인기 게시물 목록을 반환합니다.")
            # ★★★★★ 중요 수정 포인트 ★★★★★
            # Board_DTO를 Recommend_Board_DTO로 변환하고 score를 채워줍니다.
            popular_items_paginated = self.popular_items[offset : offset + limit]
            # asdict를 사용해 DTO를 딕셔너리로 변환하고 score 추가 후 다시 DTO로 만듭니다.
            from dataclasses import asdict
            recommend_dto_list = []
            for board_dto in popular_items_paginated:
                board_dict = asdict(board_dto)
                board_dict['score'] = 0.0 # 콜드 스타트 아이템은 점수를 0으로 설정
                recommend_dto_list.append(Recommend_Board_DTO(**board_dict))

            has_next = len(self.popular_items) > offset + limit
            return (recommend_dto_list, has_next)

        # 2. 기존 사용자(Warm Start)의 경우, 개인화 추천 로직 수행
        all_recs_with_scores = self._get_recommended_board_ids(user_no)
        
        if not all_recs_with_scores:
            print(f"개인화 추천 결과가 없습니다 (user_no: {user_no}). 인기 게시물 목록을 반환합니다.")
            # 여기도 동일하게 DTO 변환 및 score 추가
            from dataclasses import asdict
            popular_items_paginated = self.popular_items[offset : offset + limit]
            recommend_dto_list = []
            for board_dto in popular_items_paginated:
                board_dict = asdict(board_dto)
                board_dict['score'] = 0.0
                recommend_dto_list.append(Recommend_Board_DTO(**board_dict))

            has_next = len(self.popular_items) > offset + limit
            return (recommend_dto_list, has_next)

        # 3. 페이징 처리 및 상세 정보 조회
        paginated_recs = all_recs_with_scores[offset : offset + limit]
        has_next = len(all_recs_with_scores) > offset + limit
        
        final_recommendations = self._get_board_details_with_scores(paginated_recs, current_user_no)
        
        return (final_recommendations, has_next)

    def _get_board_details_with_scores(self, recs_with_scores, current_user_no) -> list[Recommend_Board_DTO]:
        """
        추천된 board_no 목록과 점수를 받아, DB에서 상세 정보를 조회하고 최종 DTO로 만듭니다.
        """
        
        board_nos = [rec['board_no'] for rec in recs_with_scores]
        if not board_nos:
            return []
            
        score_map = {rec['board_no']: rec['score'] for rec in recs_with_scores}

        # BoardDAO의 get_list와 유사한 쿼리를 사용하여 상세 정보 조회
        with DBManager() as db:
            # IN 절의 파라미터 개수에 맞춰 %s를 동적으로 생성
            placeholders = ','.join(['%s'] * len(board_nos))
            
            sql  = "SELECT b.board_no, b.board_title, b.board_note, date(b.board_write_date) as board_write_date, u.user_no, u.user_id, u.user_pf_img, "
            sql += "IFNULL(GROUP_CONCAT(t.tag_name SEPARATOR ', '), '') AS tag_names, "
            sql += "COUNT(DISTINCT lk.user_no) AS like_count, "
            if current_user_no:
                sql += "IF(SUM(CASE WHEN lk.user_no = %s THEN 1 ELSE 0 END) > 0, 1, 0) AS user_has_liked "
            else:
                sql += "0 AS user_has_liked "
            sql += "FROM board b "
            sql += "JOIN user u ON b.user_no = u.user_no "
            sql += "LEFT JOIN like_info lk ON b.board_no = lk.board_no "
            sql += "LEFT JOIN board_tag bt ON b.board_no = bt.board_no "
            sql += "LEFT JOIN tag t ON bt.tag_no = t.tag_no "
            sql += f"WHERE b.board_no IN ({placeholders}) " # IN 절 사용
            sql += "GROUP BY b.board_no "
            
            params = list(board_nos)
            if current_user_no:
                params.insert(0, current_user_no)
            
            detailed_boards_dict = db.getAll(sql, tuple(params))
            
            # 점수 추가 및 DTO 변환
            dto_list = []
            for board_dict in detailed_boards_dict:
                board_no = board_dict['board_no']
                board_dict['score'] = score_map.get(board_no, 0.0)
                dto_list.append(Recommend_Board_DTO(**board_dict))
                
            # 원래 추천 점수 순서대로 정렬
            dto_list.sort(key=lambda x: x.score, reverse=True)
            return dto_list

# 애플리케이션 시작 시 추천 서비스 인스턴스를 미리 생성 (싱글턴)
rec_service = RecommendationService()