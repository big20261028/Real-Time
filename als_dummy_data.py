import pandas as pd
import numpy as np
from tqdm import tqdm # 진행 상황을 보여주기 위한 라이브러리 (pip install tqdm)
from DBManager import DBManager
# ==============================================================================
# 가짜 데이터 생성 설정
# ==============================================================================
CONFIG = {
    'USER_IDS': list(range(11, 111)),
    'PROBABILITIES': {
        'SUBSCRIBE': 0.7,      # 자신의 주력 카테고리를 구독할 확률
        'LIKE_PREFERRED': 0.5, # 자신의 주력 카테고리 게시물을 좋아할 확률
        'LIKE_OTHER': 0.02     # 다른 카테고리 게시물을 좋아할 확률 (노이즈)
    }
}


def clear_interaction_data(db_manager):
    """
    기존에 생성된 상호작용 데이터(subscribe, like_info)만 삭제합니다.
    """
    print("--- 기존 상호작용 데이터 삭제 시작 ---")
    cursor = db_manager.get_cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    tables_to_clear = ['subscribe', 'like_info'] # board, categorie 제외
    for table in tables_to_clear:
        cursor.execute(f"TRUNCATE TABLE {table};")
        print(f"테이블 '{table}' 초기화 완료.")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    print("--- 기존 상호작용 데이터 삭제 완료 ---\n")


def define_user_groups(parent_categories):
    """
    DB에서 읽어온 부모 카테고리를 기반으로 사용자 그룹을 정의합니다.
    """
    # 사용자 ID를 4개의 그룹으로 나눔
    user_chunks = np.array_split(CONFIG['USER_IDS'], 4)
    
    # 부모 카테고리 이름과 사용자 그룹을 매핑
    groups = {
        parent_categories[0]['categorie_name']: list(user_chunks[0]), # PC RPG 유저
        parent_categories[1]['categorie_name']: list(user_chunks[1]), # PC 액션/FPS/스포츠 유저
        parent_categories[2]['categorie_name']: list(user_chunks[2]), # 카드/MOBA/전략 유저
        parent_categories[3]['categorie_name']: list(user_chunks[3]), # 모바일 유저
    }
    print("--- 사용자 그룹 정의 완료 ---")
    for name, users in groups.items():
        print(f"'{name}' 그룹: {len(users)}명 (user_no {users[0]} ~ {users[-1]})")
    print("")
    return groups


def generate_subscriptions(db_manager, user_groups, all_categories_df):
    """subscribe 테이블에 데이터 생성"""
    print("--- 구독 정보 생성 시작 ---")
    cursor = db_manager.get_cursor()
    subscriptions_to_insert = []
    
    parent_cat_df = all_categories_df[all_categories_df['categorie_level'] == 1]
    
    for parent_cat_name, user_list in user_groups.items():
        # 선호하는 부모 카테고리의 ID 찾기
        parent_cat_info = parent_cat_df[parent_cat_df['categorie_name'] == parent_cat_name]
        if parent_cat_info.empty:
            continue
        parent_cat_no = parent_cat_info.iloc[0]['categorie_no']

        # 해당 부모 카테고리에 속한 자식 카테고리 ID 목록
        child_category_ids = all_categories_df[all_categories_df['categorie_parent_no'] == parent_cat_no]['categorie_no'].tolist()

        for user_no in user_list:
            for cat_no in child_category_ids:
                if np.random.rand() < CONFIG['PROBABILITIES']['SUBSCRIBE']:
                    subscriptions_to_insert.append((cat_no, user_no))
    
    sql = "INSERT INTO subscribe (categorie_no, user_no) VALUES (%s, %s)"
    cursor.executemany(sql, subscriptions_to_insert)
    print(f"{len(subscriptions_to_insert)}개의 구독 정보 생성 완료.")
    print("--- 구독 정보 생성 완료 ---\n")


def generate_likes(db_manager, user_groups, all_categories_df, all_boards_df):
    """like_info 테이블에 데이터 생성"""
    print("--- 좋아요 정보 생성 시작 ---")
    cursor = db_manager.get_cursor()
    likes_to_insert = []
    
    parent_cat_df = all_categories_df[all_categories_df['categorie_level'] == 1]
    
    # 게시물이 어떤 부모 카테고리에 속하는지 미리 계산
    board_with_parent_cat = pd.merge(all_boards_df, all_categories_df[['categorie_no', 'categorie_parent_no']], on='categorie_no')

    for parent_cat_name, user_list in tqdm(user_groups.items(), desc="사용자 그룹별 좋아요 생성"):
        parent_cat_info = parent_cat_df[parent_cat_df['categorie_name'] == parent_cat_name]
        if parent_cat_info.empty:
            continue
        parent_cat_no = parent_cat_info.iloc[0]['categorie_no']
        
        # 선호/비선호 게시물 목록 분리
        preferred_boards = board_with_parent_cat[board_with_parent_cat['categorie_parent_no'] == parent_cat_no]['board_no'].tolist()
        other_boards = board_with_parent_cat[board_with_parent_cat['categorie_parent_no'] != parent_cat_no]['board_no'].tolist()

        for user_no in user_list:
            # 선호 카테고리 게시물에 좋아요
            for board_no in preferred_boards:
                if np.random.rand() < CONFIG['PROBABILITIES']['LIKE_PREFERRED']:
                    likes_to_insert.append((board_no, user_no))
            # 비선호 카테고리 게시물에 좋아요 (노이즈)
            for board_no in other_boards:
                if np.random.rand() < CONFIG['PROBABILITIES']['LIKE_OTHER']:
                    likes_to_insert.append((board_no, user_no))

    print("\nDB에 좋아요 정보 삽입 중...")
    sql = "INSERT IGNORE INTO like_info (board_no, user_no) VALUES (%s, %s)"
    
    # 대량 데이터 삽입 시, 여러번 나눠서 실행 (메모리 관리 및 타임아웃 방지)
    chunk_size = 50000
    for i in tqdm(range(0, len(likes_to_insert), chunk_size), desc="DB 삽입"):
        chunk = likes_to_insert[i:i + chunk_size]
        cursor.executemany(sql, chunk)

    print(f"총 {len(likes_to_insert)}개의 좋아요 상호작용 생성 완료.")
    print("--- 좋아요 정보 생성 완료 ---\n")


def main():
    """메인 실행 함수"""
    try:
        with DBManager() as db:
            # 1. 기존 상호작용 데이터 초기화
            clear_interaction_data(db)
            
            # 2. DB에서 필요한 원본 데이터 로드
            print("--- DB에서 원본 데이터 로드 중 ---")
            all_categories_df = db.getAll_df("SELECT categorie_no, categorie_name, categorie_level, categorie_parent_no FROM categorie")
            all_boards_df = db.getAll_df("SELECT board_no, categorie_no FROM board WHERE board_delete_flag = 'N'")
            print(f"로드된 카테고리 수: {len(all_categories_df)}, 로드된 게시물 수: {len(all_boards_df)}\n")

            if all_categories_df.empty or all_boards_df.empty:
                print("오류: 카테고리 또는 게시물 데이터가 DB에 없습니다. 스크립트를 종료합니다.")
                return

            # 3. 사용자 그룹 정의
            parent_categories = all_categories_df[all_categories_df['categorie_level'] == 1].to_dict('records')
            user_groups = define_user_groups(parent_categories)
            
            # 4. 구독 정보 생성
            generate_subscriptions(db, user_groups, all_categories_df)
            
            # 5. 좋아요 정보 생성
            generate_likes(db, user_groups, all_categories_df, all_boards_df)

    except Exception as e:
        print(f"스크립트 실행 중 오류 발생: {e}")

if __name__ == '__main__':
    main()