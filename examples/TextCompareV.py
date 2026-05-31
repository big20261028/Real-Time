# 텍스트1과 텍스트2간의 유사도 측정을 위한 모듈 (한글 형태소 분석기 버전)
# 작성자 : 정정훈, 백인기
# 작성일 : 2025.05.28

"""
필수 라이브러리 설치
pip install numpy scikit-learn nltk
pip install konlpy
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from konlpy.tag import Okt
# 정규식 연산 라이브러리
import re 

class TextCompare :
    def __init__(self) :
        # 한글 형태소 분석기 모듈 탑재
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
        # 불용어 (예: 조사, 접속사 등) 필요에 따라 추가하면 됨
        stop_words = ['의', '가', '이', '은', '는', '에', '들', '과', '를', '으로', '로', '에서', '게', '에게', '와', '도', '고', '다', '있다', '하다', '되다', '이다', '있다']

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
        # 필요에 따라 ngram_range=(1, 2) 등 파라미터 조정한다.
        vectorizer   = TfidfVectorizer()  
        tfidf_matrix = vectorizer.fit_transform(docs)
        #print(tfidf_matrix)
        
        # 두 문장간의 코사인 유사도를 계산한다.
        # 계산 결과는 아래와 같이 출력된다.
        #[[1.         0.23577034]
        #[0.23577034 1.        ]]
        #즉, 아래와 같은 매트릭스 형태 유사도로 출력됨
        #           문서1        문서2
        # 문서1       1         0.23577034  
        # 문서2    0.23577034      1
        similar = cosine_similarity(tfidf_matrix)
        #print(similar)
        
        # 두 문서간의 실제 유사도 구하기
        similar = similar[0][1]
        #print(similar)        
        return similar

t = TextCompare()
textA = "저는 오늘 맛있는 점심을 먹었습니다. 날씨가 아주 좋네요."
textB = "오늘 날씨가 좋아서 기분이 좋습니다. 맛있는 음식을 먹고 싶네요."
textC = "저는 책을 읽는 것을 좋아합니다. 특히 소설을 즐겨 읽습니다."
textD = "소설은 저에게 큰 즐거움을 줍니다. 책을 많이 읽으려고 노력합니다."
s = t.Compare(textA, textB)
print(s)

s = t.Compare(textC, textD)
print(s)

s = t.Compare(textA, textD)
print(s)
print(type(s))






