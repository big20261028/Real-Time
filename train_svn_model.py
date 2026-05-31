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
              
def main():
    model_file = "recommand.pkl"
    trainset, algo, all_boards = LoadModel(model_file) 
    if algo is None :
        with DBManager() as db:    
            df = LoadData(db)
            trainset, algo, all_boards = TrainData(df,model_file)

if __name__ == '__main__':
    main()