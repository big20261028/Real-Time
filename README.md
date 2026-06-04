# Real-Time

사용자 활동 데이터와 유사도 분석을 활용한 AI 추천 커뮤니티 웹 서비스입니다.  
게시글 데이터를 수집·정제하고, 사용자 활동 데이터를 기반으로 추천 태그, 유사 게시글, 사용자별 추천 게시글을 제공하도록 구현했습니다.

## 프로젝트 개요

Real-Time은 사용자 활동 데이터를 기반으로 개인화 추천 기능을 제공하는 커뮤니티 서비스입니다.  
게시글 데이터 수집, 전처리, DB 저장, 추천 로직 적용, 화면 출력까지 이어지는 데이터 기반 서비스 흐름을 구현했습니다.

## 주요 기능

- 게시글 데이터 수집 및 전처리
- 사용자 활동 데이터 점수화
- 추천 태그 생성
- 유사 게시글 추천
- 사용자별 추천 게시글 제공
- 추천 결과 DB 저장 및 화면 출력
- Ajax 기반 무한 스크롤

## 기술 스택

### Backend / DB
- Python
- Flask
- MySQL
- PyMySQL

### AI / Data
- Selenium
- BeautifulSoup
- Okt
- scikit-learn
- TF-IDF
- Cosine Similarity
- SVD

### Frontend
- HTML
- CSS
- JavaScript
- Ajax

### Tool
- Anaconda
- Spyder

## 담당 역할

- 1인 프로젝트로 서비스 설계, DB 설계, 화면 구현 전반 담당
- Selenium, BeautifulSoup 기반 게시글 데이터 수집
- 결측치, 이상치, 사용 불가 URL 제거 등 데이터 정제
- 사용자 활동 데이터 점수화
- TF-IDF, Cosine Similarity, SVD 기반 추천 로직 구현
- 추천 결과 DB 저장 및 화면 연동

## 배운 점

데이터 수집부터 전처리, DB 저장, 추천 로직, 화면 출력까지 이어지는 데이터 기반 서비스 흐름을 경험했습니다.  
이 과정에서 서버 기능의 완성도는 코드뿐 아니라 데이터 품질과 DB 구조에도 영향을 받는다는 점을 배웠습니다.
