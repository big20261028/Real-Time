#pip install scikit-surprise pandas
import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
import pickle
from DBManager import DBManager

# 데이터 준비
def LoadData(db_manager):
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
    
    print("--- 원본 데이터 (Pandas DataFrame) ---")
    print(df.head())
    print("=" * 40)
    return df

# 데이터 학습
def TrainData(df,model_file) :
    # Reader 객체의 rating_scale을 실제 데이터의 점수 범위인 (0.5, 1.5)로 설정합니다.
    # 이 설정을 통해 surprise 라이브러리가 점수의 스케일을 올바르게 이해하고 모델을 학습합니다.
    reader = Reader(rating_scale=(0.5, 1.5))    
    
    # Pandas DataFrame에서 surprise 데이터셋으로 로드
    surprise_data = Dataset.load_from_df(df[['user_no', 'board_no', 'score']], reader)
    
    # 전체 데이터를 학습용으로 사용
    trainset = surprise_data.build_full_trainset()
    
    # SVD (Singular Value Decomposition) 알고리즘 사용
    # 하이퍼파라미터는 데이터 특성에 따라 튜닝할 수 있습니다.
    algo = SVD(n_factors=50, n_epochs=20, random_state=42)
    
    # 모델 학습
    algo.fit(trainset)
    
    print("--- 모델 학습 완료 ---")
    print("알고리즘: SVD")
    print(f"평점 범위: {reader.rating_scale}")
    print("=" * 40)
    
    all_boards = df["board_no"].unique()
    
    with open(model_file,"wb") as f :
        data = (trainset, algo,all_boards)
        pickle.dump(algo,f)   
        print(f"모델파일 {model_file}로 저장완료...")
    
    return trainset, algo, all_boards

# 학습데이터 로드
def LoadModel(model_file) :
    trainset   = None
    algo       = None
    all_boards = None
    try :
        with open(model_file,"rb") as f :
            trainset, algo, all_boards = pickle.load(f)
    except:
        print(f"모델파일 {model_file} 로딩 오류...")
    return trainset, algo, all_boards

# 특정 사용자를 위한 추천 목록 생성 함수
def GetRecommnad(trainset, algo, all_boards, user_id, top_n=10):
    try :
        # 사용자가 이미 평가한 게시물 목록 가져오기 (내부 ID -> 원본 ID 변환)
        # surprise 내부 ID 체계를 다루기 위한 변환 과정입니다.
        # to_inner_uid: user_no -> surprise 내부 user id
        # ur: 사용자의 평가 기록
        # to_raw_iid: surprise 내부 item id -> board_no
        rated_boards_inner_ids = [item_id for (item_id, rating) in trainset.ur[trainset.to_inner_uid(user_id)]]
        rated_boards_raw_ids = [trainset.to_raw_iid(inner_id) for inner_id in rated_boards_inner_ids]
        
        # 사용자가 아직 평가하지 않은 게시물 목록
        unrated_boards = [board for board in all_boards if board not in rated_boards_raw_ids]
        
        # 평가하지 않은 게시물에 대해 예상 평점 예측
        predictions = [algo.predict(user_id, board_id) for board_id in unrated_boards]
        
        # 예상 평점이 높은 순으로 정렬
        # pred.est 는 'estimated rating'의 약자로, 예측된 평점 값을 의미합니다.
        predictions.sort(key=lambda x: x.est, reverse=True)
        
        # 상위 N개의 추천 결과 반환
        top_recommendations = [(pred.iid, pred.est) for pred in predictions[:top_n]]
        
        return top_recommendations
    except :
        return None
    
model_file = "recommand.pkl"
trainset, algo, all_boards = LoadModel(model_file) 
if algo is None :
    with DBManager() as db:    
        df = LoadData(db)
        trainset, algo, all_boards = TrainData(df,model_file)

print("=" * 40)
user_id = 11
recommendations = GetRecommnad(trainset, algo, all_boards, user_id, 10)
if recommendations != None :
    for board_id, estimated_score in recommendations:
        # 예측된 점수(estimated_score)도 0.5 ~ 1.5 범위 근처의 값으로 나옵니다.
        print(f"게시물 번호: {board_id}, 예상 평점: {estimated_score:.4f}")

print("=" * 40)
user_id = 20
recommendations = GetRecommnad(trainset, algo, all_boards, user_id, 10)
if recommendations != None :
    for board_id, estimated_score in recommendations:
        # 예측된 점수(estimated_score)도 0.5 ~ 1.5 범위 근처의 값으로 나옵니다.
        print(f"게시물 번호: {board_id}, 예상 평점: {estimated_score:.4f}")

print("=" * 40)
user_id = 1
recommendations = GetRecommnad(trainset, algo, all_boards, user_id, 10)
if recommendations != None :
    for board_id, estimated_score in recommendations:
        # 예측된 점수(estimated_score)도 0.5 ~ 1.5 범위 근처의 값으로 나옵니다.
        print(f"게시물 번호: {board_id}, 예상 평점: {estimated_score:.4f}")




