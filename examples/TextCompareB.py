# 텍스트1과 텍스트2간의 유사도 측정을 위한 모듈 (RoBERTa 모델 사용)
# 작성자 : 정정훈, 백인기
# 작성일 : 2025.05.28

"""
필수 라이브러리 설치
pip install transformers torch scikit-learn numpy
"""
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

class TextCompare :
    def __init__(self, model_name="klue/roberta-base") :  # 기본 모델 설정
        # RoBERTa 모델 및 토크나이저 로드
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()  # 추론 모드로 설정 (gradient 계산 X)

        # 필요에 따라 GPU 사용
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        print(f"Using device: {self.device}")  # 어떤 장치 사용하는지 확인

        # 형태소 분석기 제거 (RoBERTa 사용으로 불필요)
        # self.okt = Okt()
        pass
    
    # 문장에서 한글만 추출하기
    def GetHangul(self,text) :
        pattern = re.compile('[ㄱ-ㅎ가-힣]+')
        matches = pattern.findall(text)
        # 단어마다 띄어쓰기 추가하여 한글 추출
        matches = " ".join(matches)
        return matches

    # 텍스트 전처리 (RoBERTa 사용에 맞게 수정)
    def PreProcess(self, text) :
        # 문장에서 한글만 추출하기
        text = self.GetHangul(text)
        print("한글만 추출한 결과...")
        print(text)
        print("=" * 40)

        # 불용어 처리 제거 (RoBERTa 모델이 문맥을 고려하므로 불필요)
        # stop_words = ['의', '가', '이', '은', '는', '에', '들', '과', '를', '으로', '로', '에서', '게', '에게', '와', '도', '고', '다', '있다', '하다', '되다', '이다', '있다']
        # word_tokens = self.okt.morphs(text)
        # result = []
        # for w in word_tokens:
        #     if w not in stop_words:
        #         result.append(w)
        # print("문장에서 토큰을 추출한 결과...")
        # print(result)
        # print("=" * 40)

        # 형태소 분석기 제거
        # return " ".join(result)
        return text  # RoBERTa 입력에 맞게 전처리된 텍스트 그대로 반환


    # 텍스트 인코딩 함수 (RoBERTa 사용)
    def encode_text(self, text):
        # 토큰화 및 패딩, truncation
        encoded_input = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt')
        encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()} # 데이터를 GPU로 옮기기

        # 모델에 입력
        with torch.no_grad():
            model_output = self.model(**encoded_input)

        # 문장 임베딩 추출 (CLS 토큰의 hidden state 사용)
        embeddings = model_output.last_hidden_state[:, 0, :]  # (batch_size, hidden_size)
        return embeddings

    # 문장A와 문장B의 유사도를 측정한다.
    def Compare(self,textA, textB) : 
        # 문장에서 토큰을 추출한다.
        docA = self.PreProcess(textA)
        docB = self.PreProcess(textB)
        docs = [docA, docB]
        print("두개의 문장에서 전처리한 결과...")
        print(docs)
        print("=" * 40)

        # RoBERTa 임베딩 생성
        embeddings = [self.encode_text(doc) for doc in docs]

        # numpy 배열로 변환 및 합치기
        embeddings_np = [embedding.cpu().numpy() for embedding in embeddings]  # GPU -> CPU -> NumPy
        embeddings_matrix = np.vstack(embeddings_np)

        # 코사인 유사도 계산
        similar = cosine_similarity(embeddings_matrix)

        # 두 문서간의 실제 유사도 구하기
        similar = similar[0][1]
        #print(similar)        
        return similar

# 모델 생성 시 모델 이름 지정 가능
# 혹은 다른 모델 이름 사용, "roberta-base" 등
t = TextCompare(model_name="klue/roberta-base") 

textA = "저는 오늘 맛있는 점심을 먹었습니다. 날씨가 아주 좋네요."
textB = "오늘 날씨가 좋아서 기분이 좋습니다. 맛있는 음식을 먹고 싶네요."
textC = "저는 책을 읽는 것을 좋아합니다. 특히 소설을 즐겨 읽습니다."
textD = "소설은 저에게 큰 즐거움을 줍니다. 책을 많이 읽으려고 노력합니다."
s = t.Compare(textA, textB)
print(f"'{textA}' and '{textB}' 유사도: {s:.4f}")

s = t.Compare(textC, textD)
print(f"'{textC}' and '{textD}' 유사도: {s:.4f}")

s = t.Compare(textA, textD)
print(f"'{textA}' and '{textD}' 유사도: {s:.4f}")

