from DBManager import DBManager
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# 크롤링 =======================================================================================================================================
class Categorie_crawling:
    '''
    DB 카테고리 테이블의 데이터를 크롤링하는 클래스
    '''
    def __init__(self):
        pass

    def categorie_db_to_csv(self,save_file_name):
        '''
        DB에 저장된 카테고리 정보를 csv파일로 저장합니다.
        :param save_file_name: 저장될 csv파일의 이름
        :return: True  : 성공
        :return: False : 실패
        '''
        try:
            with DBManager() as db:
                sql = "select * from categorie"
    
                df = db.getAll_df(sql)
                print(df)
                
                df.to_csv(save_file_name, index=False, encoding='utf-8-sig')
                return True
        
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return False
        
    def categorie_csv_to_db(self,read_file_name):
        '''
        csv파일을 읽어온 뒤 DB에 저장합니다.
        :param read_file_name: 읽어올 csv파일의 이름
        :return: True  : 성공
        :return: False : 실패
        '''
        # 전역변수
        df = None
        
        # --- 1. CSV 파일 읽기 및 데이터 전처리 ---
        try:
            df = pd.read_csv(read_file_name)
            
            # DB에 NULL로 넣어야 할 컬럼들의 데이터 타입을 'object'로 변경
            df['categorie_parent_no'] = df['categorie_parent_no'].astype('object')
            df['categorie_pf_img_name'] = df['categorie_pf_img_name'].astype('object')
            df['inven_board_url'] = df['inven_board_url'].astype('object')
    
            # NaN 값을 Python의 None으로 변환
            df = df.where(pd.notna(df), None)
            # print(df.info())
            print("CSV 파일 로드 및 전처리 완료.")
    
        except:
            print("오류: CSV 파일 처리 중, 에러 발생")
            return False
        
        # --- 2. DB에 데이터 등록 ---
        try:
            with DBManager() as db:
                # INSERT
                sql = """
                    INSERT INTO categorie 
                    (categorie_no, categorie_name, categorie_level, categorie_info, 
                     categorie_pf_img_name, categorie_parent_no, inven_board_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                # DataFrame을 순회하며 DB에 삽입
                for index, row in df.iterrows():
                    # SQL 템플릿에 전달할 값들을 튜플로 만듦 (순서 중요!)
                    params = (
                        row['categorie_no'],
                        row['categorie_name'],
                        row['categorie_level'],
                        row['categorie_info'],
                        row['categorie_pf_img_name'],
                        row['categorie_parent_no'],
                        row['inven_board_url']
                    )
                    # 안전하게 SQL 실행
                    if db.runSQL(sql, params) != 1:
                        print(f'{index}번째 행 입력 실패')
                
                print("모든 데이터 삽입 처리가 완료 되었습니다.")
        
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return False
            
    #AI 검토 코드
    def categorie_board_url_AI(self):
        """
        카테고리별 자유 게시판 URL을 추출하여 DB에 업데이트합니다.
        :return: True  : 성공
        :return: False : 실패
        """
        
        driver = None  # finally 블록에서 사용하기 위해 미리 선언
        try:
            print('카테고리 id 추출 시작')
            driver = webdriver.Chrome()
            
            base_url = 'https://www.inven.co.kr'
            # 시작 URL을 base_url과 분리하여 관리
            start_page_url = urljoin(base_url, '/webzine/zone/gamer/')
            
            driver.get(start_page_url)
            
            # '전체게임' 버튼 클릭
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "body > header > div.header-nav > div > div > button"))
            )
            button.click()
            
            # 장르 메뉴가 나타날 때까지 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "genre"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            # 변수명 수정: all_links -> categorie_links
            categorie_links = soup.select('#genre ul a')
            update_count = 0
            
            # keywords로 <a>태그 
            keywords = ['자유 게시판', '통합 게시판',  '질문과 답변', '전체 게시판']
            
            # 수정 1: 변수명 중복 방지 (link -> categorie_link)
            for categorie_link in categorie_links:
                categorie_name = categorie_link.get_text(strip=True)
                categorie_relative_url = categorie_link.get('href')
                
                if '전체' in categorie_name or not categorie_relative_url:
                    continue
                    
                print(f"\n[카테고리] {categorie_name}")
                
                # 수정 2: 상대 경로를 절대 경로로 변환
                categorie_full_url = urljoin(base_url, categorie_relative_url)
                
                # User-Agent는 실제 존재하는 버전으로 수정하는 것이 좋음
                head = { "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36" }
                
                try:
                    result = requests.get(url=categorie_full_url, headers=head)
                    result.raise_for_status()  # HTTP 오류 발생 시 예외를 일으킴
                    html = result.text
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    board_link_all = soup.find_all('a') # 카테고리 페이지의 모든 <a>태그 
                    board_link_tag = None
                    key_name = ""
                    # 모든 <a>태그의 text 안에 keywords 중 하나라도 있다면 board_link_tag에 <a>태그 객체 저장
                    for link in board_link_all :
                        for key in keywords :
                            if key in link.text :
                                print(link.text)
                                print("=" * 40)
                                board_link_tag = link
                                key_name = key
                                break
                        if board_link_tag is not None :
                            break
    
                    
                    free_board_url = None
                    if board_link_tag:
                        # 수정 2-1: 게시판 링크도 절대 경로로 변환
                        free_board_url = urljoin(base_url, board_link_tag.get('href'))
    
                    if free_board_url:
                        print(f"[성공] {categorie_name} {key_name} URL 추출 완료: {free_board_url}")
                        
                        # --- DB 작업 시작 ---
                        try:
                            with DBManager() as db:
                                sql = "UPDATE categorie SET inven_board_url = %s WHERE categorie_name = %s"
                                params = (free_board_url, categorie_name)
                                if db.runSQL(sql,params) != 1:
                                    print(f'{categorie_name} 게시판 링크 등록 실패')
                                update_count += 1     
                        except Exception as e:
                            print(f"DAO 작업 중 오류 발생: {e}")
                            return False
                        
                    else:
                        print(f"[실패] {categorie_name} 자유게시판 URL을 찾을 수 없습니다.")
                        
                except requests.exceptions.RequestException as e:
                    print(f"[실패] {categorie_name} 페이지({categorie_full_url}) 요청 실패: {e}")
                
            print(f"\n총 {update_count}개의 카테고리 정보가 업데이트되었습니다.")
                
        except Exception as e:
            print(f'[실패] 전체 작업 중 에러 발생: {e}')
            
        finally:
            if driver:
                driver.quit()
                print("\n웹 드라이버를 종료했습니다.")

# AI 활용 ===========================================================================================================================
import itertools
from konlpy.tag import Okt
import networkx as nx

class AI_Tools:
    def __init__(self):
        pass
    
    
    def extract_co_occurrence_keywords(self, text, num_keywords=10, window_size=5):
        """
        주어진 텍스트에서 동시 출현 빈도와 TextRank를 이용해 키워드를 추출합니다.
        :param text          : 분석할 텍스트 (문자열)
        :param num_keywords  : 추출할 키워드의 수 (정수)
        :param window_size   : 동시 출현을 확인할 윈도우 크기 (정수)
        :return: [ (키워드, 중요도 점수), .... ] 튜플의 리스트
        """
        # Okt 형태소 분석기 인스턴스 생성
        okt = Okt()
    
        # 명사만 추출하고, 한 글자 단어는 제외 => 리스트
        tagged_words = okt.pos(text, stem=True)
        nouns = [word for word, tag in tagged_words if tag == 'Noun' and len(word) > 1]
        
        # 단어가 최소 window_size보다 작으면 그대로 반환
        if len(nouns) < window_size:
            return []
    
        # 동시 출현 빈도를 저장할 그래프 생성
        graph = nx.Graph()
    
        # 윈도우를 슬라이딩하며 동시 출현 단어쌍을 그래프에 추가
        for i in range(len(nouns) - window_size + 1):
            window = nouns[i:i + window_size]
            for w1, w2 in itertools.combinations(window, 2):
                if w1 != w2: # 같은 단어끼리는 연결하지 않음
                    if graph.has_edge(w1, w2):
                        graph[w1][w2]['weight'] += 1
                    else:
                        graph.add_edge(w1, w2, weight=1)
    
        # PageRank 알고리즘을 사용해 각 단어의 중요도 계산
        try:
            pagerank_scores = nx.pagerank(graph, weight='weight')
        except nx.NetworkXError:
            # 그래프에 노드가 없거나 연결이 없는 경우 예외 처리
            return []
    
        # 중요도(PageRank 점수)가 높은 순서대로 키워드 정렬
        sorted_keywords = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 상위 N개의 키워드 추출
        keywords = sorted_keywords[:num_keywords]
    
        return keywords

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# 정규식 연산 라이브러리
import re 

import io
import base64
import matplotlib.pyplot as plt
from matplotlib import rc
import platform

# --- Matplotlib 한글 폰트 설정 (기존 코드와 동일) ---
if platform.system() == 'Windows':
    rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':
    rc('font', family='AppleGothic')
else:
    rc('font', family='NanumGothic')
plt.rcParams['axes.unicode_minus'] = False

class TextCompare :
    def __init__(self) :
        self.okt = Okt()
        pass
    
    # 문장에서 한글만 추출하기
    def GetHangul(self,text) :
        pattern = re.compile('[ㄱ-ㅎ가-힣]+') 
        matches = pattern.findall(text)
        # 단어마다 띄어쓰기 추가하여 한글 추출
        matches = " ".join(matches)
        return matches

    # 텍스트 전처리 
    def PreProcess(self,text) :
        # 문장에서 한글만 추출하기
        text = self.GetHangul(text)
        print("한글만 추출한 결과...")
        print(text)
        print("=" * 40)
        
        #  불용어 처리
        stop_words = ['의', '가', '이', '은', '는', '에', '들', '과', '를', '으로', 
                      '로', '에서', '게', '에게', '와', '도', '고', '다', '있다', 
                      '하다', '되다', '이다', '있다']

        # 한글 형태소 분석기를 이용한 토큰화(모든 품사 추출)
        word_tokens = self.okt.morphs(text)

        # 불용어 제거
        result = []
        for w in word_tokens:
            if w not in stop_words:
                result.append(w)
        print("문장에서 토큰을 추출한 결과...")
        print(result)
        print("=" * 40)
        return " ".join(result)

    # 문장A와 문장B의 유사도를 측정한다.
    def Compare(self,textA, textB) : 
        # 문장에서 토큰을 추출한다.
        docA = self.PreProcess(textA)
        docB = self.PreProcess(textB)
        docs = [docA, docB]
        print("두개의 문장에서 토큰을 추출한 결과...")
        print(docs)
        print("=" * 40)
        
        # TF-IDF 벡터화한다.
        vectorizer   = TfidfVectorizer()  
        tfidf_matrix = vectorizer.fit_transform(docs)
        #print(tfidf_matrix)
        similar = cosine_similarity(tfidf_matrix)
        #print(similar)
        
        # 두 문서간의 실제 유사도 구하기
        similar = similar[0][1]
        #print(similar)        
        return similar
    
    # --- ★★★ 웹용으로 새로 수정한 시각화 함수 ★★★ ---
    def generate_similarity_graph_base64(self,board_no):
        """
        유사도를 분석하고 그래프를 Base64 인코딩된 이미지 문자열로 반환합니다.
        
        Args:
            base_text (str): 기준 문장.
            comparison_texts (list of str): 비교 문장 리스트.

        Returns:
            str: PNG 이미지의 Base64 인코딩된 문자열.
        """
        base_text = ''
        comparison_texts = []
        
        try:
            with DBManager() as db:
                sql = 'select board_note from board where board_no = %s'
                params = (board_no,)
                base_text = db.getOne(sql,params)['board_note']
                
                sql = '''
                    SELECT
                        b.board_no,
                        b.board_title,
                        b.board_note
                    FROM
                        similar_board sb
                    INNER JOIN
                        board b ON sb.to_board_no = b.board_no
                    WHERE
                        sb.from_board_no = %s;
                '''
                comparison_texts = db.getAll(sql,params)
                
                
                
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return False
        
        comparer = TextCompare()
        scores = []
        labels = []

        for dict_data in comparison_texts:
            labels.append(str(dict_data['board_no']))
            text = dict_data['board_title'] + ' ' + dict_data['board_note']
            score = comparer.Compare(base_text, text)
            scores.append(score)
        
        print('-'*40)
        print(scores)
        print('-'*40)
        print(comparison_texts)
        print('-'*40)
        print(labels)
        print('-'*40)
        
        # Matplotlib 그래프 그리기
        plt.figure(figsize=(12, 7))
        bars = plt.bar(labels, scores, color='skyblue')
        plt.title('기준 문장과 비교 문장 간의 코사인 유사도', fontsize=16)
        plt.xlabel('비교 대상', fontsize=12)
        plt.ylabel('유사도 (Cosine Similarity)', fontsize=12)
        plt.ylim(0, 1.1)

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.3f}', va='bottom', ha='center', fontsize=10)
        
        # 1. 그래프를 메모리 내의 바이트 버퍼에 저장
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        
        # 2. 버퍼의 내용을 Base64로 인코딩
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # 3. 버퍼와 그래프 객체를 닫아 메모리 확보
        buf.close()
        plt.close()
        
        # 4. Base64 문자열 반환
        return image_base64
    
    def board_data(self,board_no):
        try:
            with DBManager() as db:
                # board_no 데이터 
                sql  = "SELECT b.board_no, b.board_title, b.board_note, date(b.board_write_date) as board_write_date, u.user_no, u.user_id, u.user_pf_img, "
                sql += "IFNULL(GROUP_CONCAT(t.tag_name SEPARATOR ', '), '') AS tag_names, "  # NULL일 경우 빈 문자열 반환
                sql += "COUNT(DISTINCT lk.user_no) AS like_count, "
                sql += "0 AS user_has_liked "
                sql += "FROM board b "
                sql += "JOIN user u ON b.user_no = u.user_no "
                sql += "LEFT JOIN like_info lk ON b.board_no = lk.board_no "
                sql += "LEFT JOIN board_tag bt ON b.board_no = bt.board_no "
                sql += "LEFT JOIN tag t ON bt.tag_no = t.tag_no "
                sql += "WHERE b.board_delete_flag = 'N' and b.board_no = %s "
                sql += "GROUP BY b.board_no "
                params = (board_no,)
                board_of_dict = db.getOne(sql,params)
                
                from models import Board_DTO
                
                search_board = Board_DTO(**board_of_dict)
                return search_board
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return False
        
        
from surprise import Dataset, Reader, SVD
import pickle
from dao import BoardDAO

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc
import platform

class SVN:
    def __init__(self):
        try:
            self.board_dao = BoardDAO()
            self.popular_items = self.board_dao.get_list(order_key="like_count desc", limit=20)
            print("  - 콜드 스타트용 인기 게시물 로드 완료.")
        except Exception as e:
            print(f"오류: 인기 게시물 로드 실패. >> {e}")
            self.popular_items = []
    
    # 데이터 준비
    def LoadData(self,db_manager):
        sql = """
            select user_no,board_no,sum(score) as score from
            ( SELECT user_no, board_no,1.0 as score FROM like_info
            union
            SELECT s.user_no, b.board_no,0.5 as score FROM subscribe s JOIN board b ON s.categorie_no = b.categorie_no
            ) x group by user_no,board_no;    
        """
        df = db_manager.getAll_df(sql)
        
        print("--- 원본 데이터 (Pandas DataFrame) ---")
        print(df.head())
        print("=" * 40)
        return df

    # 데이터 학습
    def TrainData(self,df,model_file) :
        # Reader 객체의 rating_scale을 실제 데이터의 점수 범위인 (0.5, 1.5)로 설정합니다.
        reader = Reader(rating_scale=(0.5, 1.5))    
        surprise_data = Dataset.load_from_df(df[['user_no', 'board_no', 'score']], reader)
        # 전체 데이터를 학습용으로 사용
        trainset = surprise_data.build_full_trainset()
        # SVD (Singular Value Decomposition) 알고리즘 사용
        algo = SVD(n_factors=50, n_epochs=20, random_state=42)
        algo.fit(trainset)
        
        print("--- 모델 학습 완료 ---")
        print("알고리즘: SVD")
        print(f"평점 범위: {reader.rating_scale}")
        print("=" * 40)
        
        all_boards = df["board_no"].unique()
        
        with open(model_file,"wb") as f :
            data = (trainset, algo,all_boards)
            pickle.dump(data,f)   
            print(f"모델파일 {model_file}로 저장완료...")
        
        return trainset, algo, all_boards

    # 학습데이터 로드
    def LoadModel(self,model_file) :
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
    def GetRecommnad(self,trainset, algo, all_boards, user_no, start_n=0, end_n=10):
        try :
            # 사용자가 이미 평가한 게시물 목록 가져오기 (내부 ID -> 원본 ID 변환)
            rated_boards_inner_ids = [item_id for (item_id, rating) in trainset.ur[trainset.to_inner_uid(user_no)]]
            rated_boards_raw_ids = [trainset.to_raw_iid(inner_id) for inner_id in rated_boards_inner_ids]
            
            # 사용자가 아직 평가하지 않은 게시물 목록
            unrated_boards = [board for board in all_boards if board not in rated_boards_raw_ids]
            
            # 평가하지 않은 게시물에 대해 예상 평점 예측
            predictions = [algo.predict(user_no, board_id) for board_id in unrated_boards]
            
            # 예상 평점이 높은 순으로 정렬
            # pred.est 는 'estimated rating'의 약자로, 예측된 평점 값을 의미합니다.
            predictions.sort(key=lambda x: x.est, reverse=True)
            
            # 상위 N개의 추천 결과 반환
            top_recommendations = [(pred.iid, pred.est) for pred in predictions[start_n:end_n]]
            
            return top_recommendations
        except :
            return None
    
    # ★★★ 새로 추가된 점수 분석 및 시각화 함수 ★★★
    def generate_score_breakdown_graph(self, user_no, board_no, model_file,score):
        """
        특정 사용자와 게시물에 대한 SVD 예측 점수를 구성 요소별로 분해하여
        Matplotlib 그래프(Base64)로 생성합니다.
    
        Args:
            user_no (int): 사용자 번호
            board_no (int): 게시글 번호
            model_file (str): 학습된 모델 파일 경로
    
        Returns:
            str or None: 그래프 이미지의 Base64 인코딩 문자열 또는 실패 시 None
        """
        
    
        try:
            # 1. 학습된 모델과 trainset 로드
            trainset, algo, all_boards = self.LoadModel(model_file)
            if algo is None:
                print("그래프 생성: 모델 파일 로딩 실패. 재학습을 시작합니다.")
                with DBManager() as db:
                    df = self.LoadData(db)
                    if df is None or df.empty:
                        print("재학습 데이터가 없어 그래프를 생성할 수 없습니다.")
                        return None
                    # 재학습 실행
                    trainset, algo, all_boards = self.TrainData(df, model_file)
             
            # 2. 예측 점수와 상세 내역 가져오기
            # verbose=True를 해야 .details 딕셔너리에 분해된 값이 채워집니다.
            prediction = algo.predict(uid=user_no, iid=board_no, verbose=True)
    
            # 사용자가나 아이템이 trainset에 없는 경우, 예측이 불가능합니다.
            if prediction.details.get('was_impossible', False):
                reason = prediction.details.get('reason', '알 수 없는 이유')
                print(f"예측 불가: {reason}. 그래프를 생성할 수 없습니다.")
                return None
    
            # 3. 점수 구성 요소 추출
            # SVD 공식: r_ui = μ + b_u + b_i + q_i^T * p_u
            global_mean = trainset.global_mean
            
            # 내부 ID를 통해 bias와 factor 벡터에 접근해야 합니다.
            inner_user_id = algo.trainset.to_inner_uid(user_no)
            inner_item_id = algo.trainset.to_inner_iid(board_no)
    
            user_bias = algo.bu[inner_user_id]
            item_bias = algo.bi[inner_item_id]
            
            # 잠재 요인 벡터의 내적(dot product) 계산
            user_factors = algo.pu[inner_user_id]
            item_factors = algo.qi[inner_item_id]
            dot_product = np.dot(user_factors, item_factors)
    
            # 4. 그래프 데이터 준비
            labels = ['전체 평균 점수\n(Baseline)', '사용자 성향 점수\n(User Bias)', 
                      '게시글 특징 점수\n(Item Bias)', '잠재 요인 점수\n(Interaction)']
            values = [global_mean, user_bias, item_bias, dot_product]
            colors = ['gray', 'cornflowerblue', 'salmon', 'mediumseagreen']
    
            # 5. Matplotlib으로 그래프 그리기
            plt.figure(figsize=(10, 7))
            bars = plt.bar(labels, values, color=colors)
    
            plt.axhline(0, color='black', linewidth=0.8, linestyle='--') # 0점 기준선
            
            # 각 막대 위에 값 표시
            for bar in bars:
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:+.3f}', 
                         va='bottom' if yval >= 0 else 'top', ha='center', fontsize=10)
    
            plt.title(f'게시글 #{board_no} 추천 점수 상세 분석 (For User #{user_no})', fontsize=16)
            plt.ylabel('점수 기여도', fontsize=12)
            plt.xticks(rotation=10, ha='center')
    
            # 최종 예측 점수를 그래프에 텍스트로 추가
            total_score_text = f'최종 예측 점수: {score}'
            plt.text(0.95, 0.95, total_score_text, transform=plt.gca().transAxes,
                     fontsize=14, fontweight='bold', va='top', ha='right',
                     bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5))
            
            plt.tight_layout()
    
            # 6. 그래프를 Base64 문자열로 변환
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            buf.close()
            plt.close()
    
            return image_base64
    
        except Exception as e:
            print(f"그래프 생성 중 오류 발생: {e}")
            return None