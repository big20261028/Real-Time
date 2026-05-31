# 한글문장에서 단어의 동시 출현(Co-occurrence) 빈도를 이용해 주제어를 추출하는 방식
# 으로 주제어를 추출하는 모듈
"""
pip install networkx
"""
import itertools
from konlpy.tag import Okt
import networkx as nx

def extract_co_occurrence_keywords(text, num_keywords=10, window_size=5):
    """
    주어진 텍스트에서 동시 출현 빈도와 TextRank를 이용해 키워드를 추출합니다.
    :param text: 분석할 텍스트 (문자열)
    :param num_keywords: 추출할 키워드의 수 (정수)
    :param window_size: 동시 출현을 확인할 윈도우 크기 (정수)
    :return: (키워드, 중요도 점수) 튜플의 리스트
    """
    # Okt 형태소 분석기 인스턴스 생성
    okt = Okt()

    # 명사만 추출하고, 한 글자 단어는 제외
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
        # 윈도우 내 모든 단어 쌍에 대해 엣지(연결) 추가
        # itertools.combinations는 윈도우 내 모든 조합을 구해줌
        for w1, w2 in itertools.combinations(window, 2):
            if w1 != w2: # 같은 단어끼리는 연결하지 않음
                if graph.has_edge(w1, w2):
                    graph[w1][w2]['weight'] += 1
                else:
                    graph.add_edge(w1, w2, weight=1)

    # PageRank 알고리즘을 사용해 각 단어의 중요도 계산
    # weight='weight'는 우리가 부여한 동시 출현 빈도를 가중치로 사용하겠다는 의미
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

# --- 예제 실행 ---
if __name__ == "__main__":
    # 분석할 샘플 텍스트
    sample_text = """
    인공지능(AI) 기술이 빠르게 발전하면서, 딥러닝과 머신러닝은 이제 우리 생활 깊숙이 자리 잡았습니다. 
    특히 자연어 처리(NLP) 분야에서 인공지능의 활약이 두드러집니다. 
    구글, 마이크로소프트 등 글로벌 빅테크 기업들은 대규모 언어 모델(LLM) 개발에 막대한 투자를 하고 있습니다. 
    이러한 언어 모델은 챗봇 서비스, 번역, 문서 요약 등 다양한 서비스에 활용되며, 
    사용자 경험을 혁신적으로 개선하고 있습니다. 
    앞으로 인공지능 기술은 데이터 분석과 결합하여 더욱 정교한 예측 모델을 만들어낼 것으로 기대됩니다.
    """

    # 키워드 추출 함수 호출
    # window_size를 조절하여 결과의 변화를 확인해볼 수 있습니다.
    keywords = extract_co_occurrence_keywords(sample_text, num_keywords=10, window_size=5)

    # 결과 출력
    print("--- 텍스트 원문 ---")
    print(sample_text)
    print("\n--- Co-occurrence 기반 추출 키워드 (상위 10개) ---")
    for word, score in keywords:
        # 점수는 소수점 5자리까지만 표시
        print(f"{word}: {score:.5f}")