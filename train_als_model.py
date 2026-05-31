# train_als_model.py (최종 완성본)

import pandas as pd
from scipy.sparse import csr_matrix
import implicit
import pickle
from datetime import datetime
from DBManager import DBManager # DBManager.py가 같은 경로에 있다고 가정

# 모델 학습 파라미터
ALS_PARAMS = {
    'factors': 64,
    'regularization': 0.01,
    'iterations': 50,
    'random_state': 42
}
ARTIFACTS_PATH = "./model_artifacts.pkl"

def load_data_all(db_manager):
    sql = """
        select user_no,board_no,sum(score) as score
        from
        (
        SELECT user_no, board_no,1.0 as score
        FROM like_info
        union
        SELECT s.user_no, b.board_no,0.5 as score
        FROM subscribe s JOIN board b ON s.categorie_no = b.categorie_no
        ) x
        group by user_no,board_no;    
    """
    df = db_manager.getAll_df(sql)
    df.to_csv("data.csv",encoding="euc-kr")
    
def load_interaction_data(db_manager):
    """DB에서 좋아요 및 구독 데이터를 로드합니다."""
    print("1. DB에서 상호작용 데이터 로드 중...")
    sql_likes = "SELECT user_no, board_no FROM like_info"
    likes_df = db_manager.getAll_df(sql_likes)
    if not likes_df.empty:
        likes_df['score'] = 1.0
    
    sql_subs = """
        SELECT s.user_no, b.board_no
        FROM subscribe s JOIN board b ON s.categorie_no = b.categorie_no
    """
    subs_df = db_manager.getAll_df(sql_subs)
    if not subs_df.empty:
        subs_df['score'] = 0.5
    
    print(f"  - 좋아요: {len(likes_df)}건, 구독(확장): {len(subs_df)}건 로드 완료.")
    return likes_df, subs_df

def preprocess_and_train(likes_df, subs_df):
    # 이 함수는 이전 답변의 최종안과 동일합니다. 수정할 필요 없습니다.
    print("\n2. 데이터 전처리, 모델 학습 및 아티팩트 생성 시작...")
    interaction_df = pd.concat([likes_df, subs_df])
    if interaction_df.empty:
        raise ValueError("학습할 상호작용 데이터가 없습니다.")
    interaction_df = interaction_df.groupby(['user_no', 'board_no'])['score'].max().reset_index()
    
    interaction_df['user_id_cat'] = interaction_df['user_no'].astype("category").cat.codes
    interaction_df['item_id_cat'] = interaction_df['board_no'].astype("category").cat.codes
    
    num_users = len(interaction_df['user_id_cat'].unique())
    num_items = len(interaction_df['item_id_cat'].unique())
    
    sparse_user_item = csr_matrix(
        (interaction_df['score'].astype(float),
         (interaction_df['user_id_cat'], interaction_df['item_id_cat'])),
        shape=(num_users, num_items)
    )
    sparse_item_user = sparse_user_item.T.tocsr()
    
    print("  - ALS 모델 학습 시작...")
    model = implicit.als.AlternatingLeastSquares(**ALS_PARAMS)
    model.fit(sparse_item_user, show_progress=True)
    print("  - 모델 학습 완료.")
    
    return model, interaction_df, sparse_user_item

def save_artifacts(model, interaction_df, sparse_user_item):
    """결과물을 파일로 저장합니다."""
    print(f"\n3. 학습 결과물({ARTIFACTS_PATH}) 저장 중...")

    # ★★★★★ 가장 확실한 최종 수정 ★★★★★
    # drop_duplicates()를 사용하여 user_no와 user_id_cat의 유니크한 쌍을 보장합니다.
    user_map_df = interaction_df[['user_no', 'user_id_cat']].drop_duplicates()
    item_map_df = interaction_df[['board_no', 'item_id_cat']].drop_duplicates()
    
    user_map = dict(zip(user_map_df.user_no, user_map_df.user_id_cat))
    item_inv_map = dict(zip(item_map_df.item_id_cat, item_map_df.board_no))
    
    print(f"  - 최종 맵 생성 완료: {len(user_map)}명의 사용자, {len(item_inv_map)}개의 아이템")
    
    artifacts = {
        'model': model,
        'user_map': user_map,
        'item_inv_map': item_inv_map,
        'sparse_user_item': sparse_user_item,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(ARTIFACTS_PATH, 'wb') as f:
        pickle.dump(artifacts, f)
    print("  - 저장 완료.")


def main():
    print("="*50)
    print(f"ALS 모델 학습 스크립트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    try:
        with DBManager() as db:
            load_data_all(db)
            likes_df, subs_df = load_interaction_data(db)
            model, interaction_df, sparse_user_item = preprocess_and_train(likes_df, subs_df)
            save_artifacts(model, interaction_df, sparse_user_item)

        print("\n학습 및 저장 프로세스가 성공적으로 완료되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: 스크립트 실행 중단. >> {e}")

if __name__ == '__main__':
    main()