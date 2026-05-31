# 테스트용 모듈
from DBManager import DBManager

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix # 희소 행렬을 위해 필요
import implicit # implicit 라이브러리
from surprise import SVD, Dataset, Reader
from collections import defaultdict


def test_data_insert():
    try:
        with DBManager() as db:
            sql = "Insert into user (user_id, user_pw, user_pf_img) Values (%s, md5(%s), %s) "
            
            for n in range(1,101):
                user_id = 'test_id%02d' % n
                user_pw = '1234'
                user_pf_img = 0
                # print(user_id,user_pw,user_pf_img)
                params = (user_id, user_pw, user_pf_img)
                if db.runSQL(sql,params) != 1:
                    print(f'{n}번째 유저 데이터 등록 실패')
                return True
            
    except Exception as e:
        print(f"작업 중 오류 발생: {e}")
        return False
        
def to_csv(table, save_file_name):
    try:
        with DBManager() as db:
            sql = f"Select * from {table}"
            df = db.getAll_df(sql)
            print(df)
            
            #df.to_csv(save_file_name, index=False, encoding='utf-8-sig')
            return True
            
            
    except Exception as e:
        print(f"작업 중 오류 발생: {e}")
        return False


def svn_test():
    # 1. 의미 있는 가짜 데이터 생성
    
    # 설정
    n_users = 100
    n_items = 100
    user_groups = {'PC RPG 유저': range(0, 25), 'PC 액션/FPS/스포츠 유저': range(25, 50), '카드/MOBA/전략 유저': range(50, 75), '모바일 유저':range(75,100)}
    # DB에 등록된 카테고리 대분류
    # 소분류 66개 대신 대분류 사용
    item_categories = {'PC RPG': range(0, 25), 'PC 액션/FPS/스포츠': range(25, 50), '카드/MOBA/전략': range(50, 75), '모바일':range(75,100)}
    
    data = []
    
    for user_id in range(n_users):
        for item_id in range(n_items):
            like_prob = 0.1  # 기본 '좋아요' 확률 (노이즈)
    
            # 사용자 그룹과 아이템 카테고리에 따라 확률 조정
            if user_id in user_groups['PC RPG 유저'] and item_id in item_categories['PC RPG']:
                like_prob = 0.8
            elif user_id in user_groups['PC 액션/FPS/스포츠 유저'] and item_id in item_categories['PC 액션/FPS/스포츠']:
                like_prob = 0.8
            elif user_id in user_groups['카드/MOBA/전략 유저'] and item_id in item_categories['카드/MOBA/전략']:
                like_prob = 0.8
            elif user_id in user_groups['모바일 유저'] and item_id in item_categories['모바일']:
                like_prob = 0.8
            
            # 확률에 따라 like(1) 또는 no like(0) 결정
            rating = 1 if np.random.rand() < like_prob else 0
            
            # like 데이터만 사용 (0인 데이터는 '평가 안함'으로 간주)
            if rating == 1:
                data.append({'userID': user_id, 'itemID': item_id, 'rating': rating})
    
    df = pd.DataFrame(data)
    
    print("--- 생성된 데이터 샘플 ---")
    print(df.head())
    print(f"\n총 {len(df)}개의 'like' 데이터 생성됨")
    
    
    # 2. Surprise 라이브러리를 사용한 SVD 모델 학습 및 추천
    
    # Surprise 데이터셋으로 변환
    # rating_scale을 (0, 1)로 설정해야 함
    reader = Reader(rating_scale=(0, 1)) 
    data_surprise = Dataset.load_from_df(df[['userID', 'itemID', 'rating']], reader)
    trainset = data_surprise.build_full_trainset()
    
    # SVD 모델 학습
    model = SVD(n_factors=50, n_epochs=20, random_state=42)
    model.fit(trainset)
    
    # 3. 특정 사용자에 대한 추천 목록 생성
    target_user_id = 5  # 예시 사용자 (sports_fan 그룹)
    print(f"\n--- 사용자 ID {target_user_id} (PC RPG 유저)에 대한 추천 생성 ---")
    
    # 이 사용자가 아직 'like'하지 않은 게시물 목록
    liked_items = df[df['userID'] == target_user_id]['itemID'].tolist()
    all_items = set(range(n_items))
    unseen_items = list(all_items - set(liked_items))
    
    # 보지 않은 아이템에 대해 예측 점수 계산
    predictions = []
    for item_id in unseen_items:
        pred = model.predict(uid=target_user_id, iid=item_id)
        predictions.append(pred)
    
    # 예측 점수가 높은 순으로 정렬
    predictions.sort(key=lambda x: x.est, reverse=True)
    
    # 상위 10개 추천
    top_n_recommendations = predictions[:10]
    
    print(f"사용자 {target_user_id}를 위한 상위 10개 추천 게시물:")
    for pred in top_n_recommendations:
        category = "Unknown"
        if pred.iid in item_categories['sports']: category = "스포츠"
        elif pred.iid in item_categories['tech']: category = "IT"
        elif pred.iid in item_categories['food']: category = "음식"
        
        print(f"게시물 ID: {pred.iid:3d} (카테고리: {category}), 예측 점수: {pred.est:.4f}")


def als_test():
    # --- 이전과 동일: 의미 있는 가짜 데이터 생성 ---
    
    # 설정
    n_users = 100
    n_items = 100
    user_groups = {'PC RPG 유저': range(0, 25), 'PC 액션/FPS/스포츠 유저': range(25, 50), '카드/MOBA/전략 유저': range(50, 75), '모바일 유저':range(75,100)}
    # DB에 등록된 카테고리 대분류
    # 소분류 66개 대신 대분류 사용
    item_categories = {'PC RPG': range(0, 25), 'PC 액션/FPS/스포츠': range(25, 50), '카드/MOBA/전략': range(50, 75), '모바일':range(75,100)}
    
    data = []
    for user_id in range(n_users):
        for item_id in range(n_items):
            like_prob = 0.1
            if user_id in user_groups['PC RPG 유저'] and item_id in item_categories['PC RPG']:
                like_prob = 0.8
            elif user_id in user_groups['PC 액션/FPS/스포츠 유저'] and item_id in item_categories['PC 액션/FPS/스포츠']:
                like_prob = 0.8
            elif user_id in user_groups['카드/MOBA/전략 유저'] and item_id in item_categories['카드/MOBA/전략']:
                like_prob = 0.8
            elif user_id in user_groups['모바일 유저'] and item_id in item_categories['모바일']:
                like_prob = 0.8
            
            if np.random.rand() < like_prob:
                data.append({'userID': user_id, 'itemID': item_id, 'like': 1})
    
    df = pd.DataFrame(data)
    print("--- 생성된 데이터 샘플 ---")
    print(df.head())
    print(f"\n총 {len(df)}개의 'like' 데이터 생성됨")
    
    
    # --- 1. implicit 라이브러리를 위한 데이터 준비 ---
    # Surprise와 달리, implicit는 사용자-아이템 행렬 형태를 입력으로 받습니다.
    # DataFrame을 희소 행렬(Sparse Matrix)로 변환해야 합니다.
    
    # 사용자, 아이템 ID를 카테고리형으로 변환하여 연속적인 ID를 보장
    df['userID_cat'] = df['userID'].astype("category").cat.codes
    df['itemID_cat'] = df['itemID'].astype("category").cat.codes
    print(df)
    print('='*40)
    
    # 사용자-아이템 희소 행렬 생성 (데이터: like, 행: userID, 열: itemID)
    sparse_user_item = csr_matrix((df['like'].astype(float), 
                                   (df['userID_cat'], df['itemID_cat'])))
    
    # implicit 모델은 아이템-사용자 행렬을 기본으로 사용하므로 Transpose(.T) 해줍니다.
    sparse_item_user = sparse_user_item.T
    
    # --- 2. ALS 모델 학습 ---
    # 모델 초기화 (SVD의 하이퍼파라미터와 유사)
    # factors: 잠재 요인의 수 (SVD의 n_factors)
    # regularization: 과적합 방지를 위한 정규화 값
    # iterations: 반복 횟수 (SVD의 n_epochs)
    model = implicit.als.AlternatingLeastSquares(factors=50, 
                                                 regularization=0.01, 
                                                 iterations=20, 
                                                 random_state=42)
    
    # 모델 학습
    model.fit(sparse_item_user)
    
    # --- 3. 특정 사용자에 대한 추천 목록 생성 ---
    target_user_id = 5  # 예시 사용자 (PC RPG 유저 그룹)
    print(f"\n--- 사용자 ID {target_user_id} (스포츠 팬)에 대한 추천 생성 (ALS) ---")
    
    # 내부 카테고리 ID로 변환
    target_user_cat = df[df['userID'] == target_user_id]['userID_cat'].iloc[0]
    
    # 추천 받기 (N = 추천받을 아이템 개수)
    # user_items: 학습에 사용한 행렬을 다시 넣어주어 이미 'like'한 아이템은 제외시킴
    recommended_cat, scores = model.recommend(target_user_cat, sparse_user_item[target_user_cat], N=10)
    
    # 원래 아이템 ID로 복원
    # 카테고리 -> 원래 ID 매핑 생성
    id_to_item_cat = dict(enumerate(df['itemID'].astype("category").cat.categories))
    recommended_original_ids = [id_to_item_cat[i] for i in recommended_cat]
    
    
    print(f"사용자 {target_user_id}를 위한 상위 10개 추천 게시물:")
    for item_id, score in zip(recommended_original_ids, scores):
        category = "Unknown"
        if item_id in item_categories['PC RPG']: category = "PC RPG"
        elif item_id in item_categories['PC 액션/FPS/스포츠']: category = "PC 액션/FPS/스포츠"
        elif item_id in item_categories['카드/MOBA/전략']: category = "카드/MOBA/전략"
        elif item_id in item_categories['모바일']: category = "모바일"
        
        print(f"게시물 ID: {item_id:3d} (카테고리: {category}), 예측 점수: {score:.4f}")



        
if __name__ == "__main__":
    #test_data_insert()
    #to_csv("user", "user_board_data.csv")
    als_test()
    print('========== End Program ==========')