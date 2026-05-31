from DBManager import DBManager
from urllib.parse import urlparse, urlunparse

def insert_post_id_to_url(original_url, post_id):
    """URL의 경로(path) 끝에 게시글 ID를 추가합니다."""
    
    # 1. URL을 구성요소로 분해
    parsed_url = urlparse(original_url)
    
    # 2. 기존 경로에 게시글 ID를 추가하여 새 경로 생성
    # 예: '/board/apexlegends/5404' + '/30846'
    new_path = parsed_url.path + '/' + str(post_id)
    
    # 3. 분해된 URL 구성요소에서 path만 교체
    # _replace는 기존 튜플에서 특정 값만 바꿔 새 튜플을 만드는 편리한 기능입니다.
    new_url_parts = parsed_url._replace(path=new_path)
    
    # 4. 수정된 구성요소를 다시 합쳐 완전한 URL로 만듦
    final_url = urlunparse(new_url_parts)
    
    return final_url

db = DBManager()

if db.dbOpen("root", "ezen", "ateamSNS"):
    print("DB 연결 성공")
    try:
        sql = "select categorie_no,inven_board_url from categorie"
        total = db.openSelect(sql)
        df    = db.getAll()
        
        df = df.dropna()
        print(df)
        print(df.iloc[0])
        print("="*40)
        
        db.closeSelect()
        
        head = { "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36" }
        
        import requests
        from bs4 import BeautifulSoup
        
        url_list = df.values.tolist()
        print(url_list[0])
        
        for item in url_list:
            # 카테고리 번호
            categorie_no = item[0]
            # 크롤링 할 게시판 url
            target_board_url = item[1]
            
            print("="*40)
            print("="*40)
            print("target_board_url =>" ,target_board_url)
            print("="*40)
            print("="*40)
            # 테스트
            #target_board_url  = "https://www.inven.co.kr/board/apexlegends/5404?category=_영상"
            
            # 웹페이지 받아오기
            result = requests.get(url=str(target_board_url), headers=head)
            #print(result)
            #print("="*40)
            
            html = result.text
            #print(html)
            #print("="*40)
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 게시물 번호가 있는 모든 td > span 태그를 가져옴
            post_num_elements = soup.select(".board-list > table > tbody tr td.num > span")
            
            first_board_no = None # 시작 번호를 저장할 변수 초기화
            
            # 가져온 모든 번호 태그를 순회
            for num_span in post_num_elements:
                num_text = num_span.text.strip()
                # .isdigit() 메소드로 문자열이 숫자로만 구성되었는지 확인
                if num_text.isdigit():
                    first_board_no = int(num_text)
                    print(f"찾은 첫 게시물 번호: {first_board_no}")
                    break # 첫 번째 숫자를 찾았으면 루프 중단
            
            # for 루프가 끝난 후, 숫자로 된 게시물 번호를 찾았는지 확인
            if first_board_no is None:
                print("[!] 이 페이지에서 유효한 게시물 번호를 찾지 못했습니다. 다음 카테고리로 넘어갑니다.")
                continue # while 루프를 실행하지 않고 다음 카테고리로 이동
            
            # 수집할 데이터 갯수
            count_collect_data = 10
            '''
            data = soup.select_one(".board-list > table > tbody > tr:nth-child(6) > td.num > span")
            print("="*40)
            print("="*40)
            print("="*40)
            print(data.text)
            
            # 첫 게시물 번호
            first_board_no = data.text
            first_board_no = int(first_board_no)
            
            # 수집할 데이터 갯수
            count_collect_data = 10
            '''
            while True:
                if count_collect_data < 0 : break
                
                target_view_url = insert_post_id_to_url(target_board_url,first_board_no)
                '''
                # db의 url 주소 + /{first_board_no} 로 조회
                target_view_url = target_board_url + "/" + str(first_board_no)
                print(target_view_url)
                '''
                first_board_no -= 1
                
                result = requests.get(url=str(target_view_url), headers=head)
                html = result.text
                #print(html)
                #print("="*40)
                
                # soup 객체로 변환
                soup = BeautifulSoup(html, 'html.parser')
                
                print(type(soup))
                
                title_element = soup.select_one("#tbArticle > div.articleMain > div.articleSubject > div.articleTitle > h1")
                date_element = soup.select_one("#tbArticle div.articleDate")
                note_element = soup.select_one("#imageCollectDiv")
                #print(title_element)
                #print(date_element)
                #print(note_element)
                
                if title_element and date_element and note_element: 
            
                    board_title = title_element.text.strip()
                    board_write_date = date_element.text.strip()
                    board_note = note_element.get_text(separator="\n", strip=True)
                
                    print('board_title :',board_title)
                    print('board_wdate :',board_write_date)
                    print('board_note :',board_note)
                    print('categorie_no :',categorie_no)
                    print("="*40)
                
                    # board 테이블에 등록
                    sql = """
                        INSERT INTO board 
                        (board_title, board_write_date, board_note, categorie_no, user_no)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    params = (board_title, board_write_date, board_note, categorie_no, '1')
                    
                    db.run_sql_with_params(sql, params)
                    count_collect_data -= 1
                    print("[O] 데이터 저장 완료")
                else:
                    print("[X] 데이터 확인 불가, 다음 페이지로 스킵")
                    continue
                
            print(f"{item[0]}번 카테고리 데이터 수집 완료")
            
    except Exception as e:
        print(f"DB 작업 중 오류 발생: {e}")
    finally:
        # --- 2-3. DB 연결 종료 ---
        db.dbClose()
        print("DB 연결을 닫았습니다.")
else:
    print("DB 연결에 실패했습니다.")