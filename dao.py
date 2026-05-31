from DBManager import DBManager
# 위에서 정의한 DTO 클래스를 import
from models import Board_DTO, Modify_board, User, Categorie_DTO, Subscribe_DTO, My_Board_DTO, Similar_Board_DTO

# BoardDAO =========================================================================================================================
class BoardDAO:
    def __init__(self):
        # DAO가 생성될 때 DBManager를 인스턴스화 할 수 있습니다.
        pass

    def get_list(self, order_key="like_count desc", limit=10, offset=0, current_user_no=None) -> list[Board_DTO]:
        """
        게시물 목록을 상세 정보와 함께 조회합니다.
        결과를 BoardDetails 객체의 리스트로 반환합니다.
        """
        try:
            with DBManager() as db:
                sql  = "SELECT b.board_no, b.board_title, b.board_note, date(b.board_write_date) as board_write_date, u.user_no, u.user_id, u.user_pf_img, "
                sql += "IFNULL(GROUP_CONCAT(t.tag_name SEPARATOR ', '), '') AS tag_names, "  # NULL일 경우 빈 문자열 반환
                sql += "COUNT(DISTINCT lk.user_no) AS like_count, "
                if current_user_no:
                    sql += "IF(SUM(CASE WHEN lk.user_no = %s THEN 1 ELSE 0 END) > 0, 1, 0) AS user_has_liked "
                else:
                    # 로그인하지 않은 경우 무조건 0 (False)
                    sql += "0 AS user_has_liked "
                sql += "FROM board b "
                sql += "JOIN user u ON b.user_no = u.user_no "
                sql += "LEFT JOIN like_info lk ON b.board_no = lk.board_no "
                sql += "LEFT JOIN board_tag bt ON b.board_no = bt.board_no "
                sql += "LEFT JOIN tag t ON bt.tag_no = t.tag_no "
                sql += "Where b.board_delete_flag = 'N' "
                sql += "GROUP BY b.board_no " # 집계함수 때문에 그룹핑 기준 간소화
                sql += f"ORDER BY {order_key} LIMIT %s, %s"
                
                if current_user_no:
                    params = (current_user_no, offset, limit)
                else:
                    params = (offset, limit)
    
                list_of_dicts = db.getAll(sql,params)
                board_list = [Board_DTO(**data) for data in list_of_dicts]
                return board_list
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return []
    
    def select_categorie_parent_list(self):
        '''
        카테고리 대분류를 조회합니다.
        '''
        try:
            with DBManager() as db:
                sql = "Select categorie_no,categorie_name from categorie where categorie_level = 1"
                categorie_parent_list = db.getAll(sql)
                if categorie_parent_list == None: 
                    print("카테고리 번호 목록 조회 실패")
                return categorie_parent_list
           
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
    
    def select_categorie_child_list(self,categorie_parent_no):
        '''
        카테고리 소분류를 조회합니다.
        '''
        try:
            with DBManager() as db:
                sql = "Select categorie_no,categorie_name from categorie where categorie_parent_no = %s"
                params = (categorie_parent_no)
                categorie_child_list = db.getAll(sql,params)
                if categorie_child_list == None: 
                    print("카테고리 자손 번호 목록 조회 실패")
                return categorie_child_list
                
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
    
    def write(self, board_title, board_note, categorie_no, user_no, tag_names):  
        """
        작성한 게시글 데이터를 DB에 저장합니다.
        새로 등록된 게시글과 기존 게시글의 유사도를 측정하여 상위 10개를 DB에 저장합니다.
        (DBManager 헬퍼 함수를 활용하여 최적화된 버전)
        """
        try:
            # with 블록은 트랜잭션 범위를 정의하는 역할만 합니다.
            with DBManager() as db:
                # --- 1. 게시글 데이터 등록 ---
                sql_board = "INSERT INTO board (board_title, board_note, categorie_no, user_no) VALUES (%s, %s, %s, %s)"
                db.runSQL(sql_board, (board_title, board_note, categorie_no, user_no))
        
                # --- 2. 방금 삽입된 board_no 가져오기 ---
                # 'AS'를 사용하면 getOne의 결과 딕셔너리가 깔끔해집니다.
                result = db.getOne("SELECT LAST_INSERT_ID() AS id")
                if not result:  # 조회 실패 시 예외 발생
                    print("board_no 조회 실패 (LAST_INSERT_ID)")
                    raise Exception("Failed to get last insert ID for board.")  
                
                board_no = result['id']
        
                # --- 3. 태그 데이터 처리 ---
                if tag_names:   # [ '태그01', '태그02', ..... ]
                    for tag_name in tag_names:
                        # 3-1. 기존 태그 확인
                        sql_select_tag = "SELECT tag_no FROM tag WHERE tag_name = %s"
                        tag_result = db.getOne(sql_select_tag, (tag_name,))
                        
                        tag_no = None
                        if tag_result:
                            tag_no = tag_result['tag_no']
                        else:
                            # 3-2. 새 태그 등록
                            sql_insert_tag = "INSERT INTO tag (tag_name) VALUES (%s)"
                            db.runSQL(sql_insert_tag, (tag_name,))
                            
                            # 새 태그 ID 가져오기
                            new_tag_result = db.getOne("SELECT LAST_INSERT_ID() AS id")
                            if not new_tag_result:
                                raise Exception(f"Failed to get last insert ID for new tag: {tag_name}")
                            tag_no = new_tag_result['id']
                        
                        # 3-3. 관계 등록
                        # 혹시 모를 중복 삽입을 방지하기 위해 'INSERT IGNORE'를 사용
                        # 오류 발생 시, ignore 삭제 후 재시도
                        sql_board_tag = "INSERT IGNORE INTO board_tag (board_no, tag_no) VALUES (%s, %s)"
                        db.runSQL(sql_board_tag, (board_no, tag_no))
                        
            print('게시물 및 태그 등록 처리 완료')
            '''
            등록된 게시물과 기존 게시물의 유사도 측정
            측정값 상위 10개 게시물을 similar_board 테이블에 추가
            '''
            if not self.similar_board(from_board_no=board_no, from_board_title=board_title, from_board_note=board_note, user_no=user_no):
                print('유사 게시물 처리 실패')
            
            
            return True
        
        except Exception as e:
            # 예외가 발생하면 with 블록이 종료되면서 자동으로 rollback 됩니다.
            print(f"DAO 작업 중 오류 발생: {e}")
            return False
        
    def modify(self, board_title, board_note, categorie_no, board_no, tag_names, user_no):
        """
        수정한 게시글 데이터를 DB에 업데이트합니다.
        이전에 등록했던 유사한 게시글 데이터를 삭제합니다.
        수정된 게시글과 기존 게시글의 유사도를 측정하여 상위 10개를 DB에 저장합니다.
        """
        try:
            with DBManager() as db:
                # board 데이터 수정
                sql  = "Update board set board_title = %s, board_note = %s, categorie_no = %s "
                sql += "Where board_no = %s"
                params = (board_title, board_note, categorie_no, board_no)
                if db.runSQL(sql,params) != 1: 
                    print("board 데이터 Update 실패 or 변경사항 없음")
                
                # 기존 board_tag 데이터 삭제
                sql = "Delete from board_tag where board_no = %s"
                params = (board_no)
                if db.runSQL(sql,params) != 1: 
                    print("board_tag 데이터 Delete 실패 or 데이터 없음")
            
                if tag_names:   # [ '태그01', '태그02', ..... ]
                    for tag_name in tag_names:
                        # 3-1. 기존 태그 확인
                        sql_select_tag = "SELECT tag_no FROM tag WHERE tag_name = %s"
                        tag_result = db.getOne(sql_select_tag, (tag_name,))
                        
                        tag_no = None
                        if tag_result:
                            tag_no = tag_result['tag_no']
                        else:
                            # 3-2. 새 태그 등록
                            sql_insert_tag = "INSERT INTO tag (tag_name) VALUES (%s)"
                            db.runSQL(sql_insert_tag, (tag_name,))
                            
                            # 새 태그 ID 가져오기
                            new_tag_result = db.getOne("SELECT LAST_INSERT_ID() AS id")
                            if not new_tag_result:
                                raise Exception(f"Failed to get last insert ID for new tag: {tag_name}")
                            tag_no = new_tag_result['id']
                        
                        # 3-3. 관계 등록
                        # 혹시 모를 중복 삽입을 방지하기 위해 'INSERT IGNORE'를 사용
                        # 오류 발생 시, ignore 삭제 후 재시도
                        sql_board_tag = "INSERT IGNORE INTO board_tag (board_no, tag_no) VALUES (%s, %s)"
                        db.runSQL(sql_board_tag, (board_no, tag_no))
            
            '''
            게시글 유사도 측정, 측정값 상위 10개 저장 로직 구현 필요
            '''
            if not self.similar_board(from_board_no=board_no, from_board_title=board_title, from_board_note=board_note, user_no=user_no):
                print('유사 게시물 처리 실패')
            # 정상흐름 종료 리턴값 True
            return True
    
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return False
    
    def similar_board(self,from_board_no, from_board_title, from_board_note, user_no):
        '''
        파라메타의 기존 유사 게시글 데이터 삭제 후 재등록
        파라메타의 가장 중요도 높은 키워드로 게시글 검색
        상위 10개 유사 게시물 추출 및 db 저장
        '''
        try:
            with DBManager() as db:
                # 기존 유사글 데이터 삭제
                sql = "Delete from similar_board where from_board_no = %s"
                params = (from_board_no,)
                if db.runSQL(sql,params) != 1: 
                    print("similar_board 데이터 Delete 실패 or 데이터 없음")
                    
                # 기존 게시글 데이터 받아오기
                # 새 게시글의 키워드 분석하여 가장 중요도 높은 키워드로 검색
                from_text = from_board_title + " " + from_board_note
                from tools import AI_Tools, TextCompare
                ai_tools = AI_Tools()
                rec_tags = ai_tools.extract_co_occurrence_keywords(text=from_text,
                                                                   num_keywords=5, 
                                                                   window_size=5)
                keyword = ''
                if len(rec_tags) > 1 :
                    keyword =  rec_tags[0][0]
                
                sql  = "SELECT board_no, board_title, board_note "
                sql += "FROM board "
                sql += "Where board_delete_flag = 'N' and user_no != %s "
                sql += "and (board_title LIKE %s OR board_note LIKE %s) "
                
                search_keyword = f"%{keyword}%"
                params = (user_no,search_keyword,search_keyword)
                
                list_of_dicts = db.getAll(sql,params)
                
                for item in list_of_dicts:
                    to_text = item['board_title'] + " " + item['board_note']
                    text_compare = TextCompare()
                    similar_score = text_compare.Compare(from_text, to_text)
                    item['score'] = float(similar_score)
                
                sorted_similar_boards = sorted(list_of_dicts, key=lambda x: x['score'], reverse=True)
                
                # 상위 10개의 유사 게시글 추출
                similar_boards = sorted_similar_boards[:10]
                
                # similar_board 테이블에 저장
                for item in similar_boards:   
                    sql =  "Insert into similar_board (from_board_no, to_board_no, score) "
                    sql += "values (%s, %s, %s)"
                    params = (from_board_no, item['board_no'], item['score'])
                    db.runSQL(sql,params)
                return True
                
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return False
    
    def select_one_board(self,board_no):
        '''
        게시물 1개의 데이터를 조회합니다.
        '''
        try:
            with DBManager() as db:
                sql  = "SELECT b.board_no, b.user_no, b.board_title, b.board_note, b.categorie_no, c.categorie_parent_no, "
                sql += "IFNULL(GROUP_CONCAT(t.tag_name SEPARATOR ', '), '') AS tag_names "  # NULL일 경우 빈 문자열 반환
                sql += "FROM board b "
                sql += "LEFT JOIN board_tag bt ON b.board_no = bt.board_no "
                sql += "LEFT JOIN tag t ON bt.tag_no = t.tag_no "
                sql += "JOIN categorie c on b.categorie_no = c.categorie_no "
                sql += "WHERE b.board_delete_flag = 'N' and b.board_no = %s "
                sql += "GROUP BY b.board_no "
                
                params = (board_no,)
                
                board_dict_data = db.getOne(sql,params)
                if not board_dict_data:
                    return None
                
                return Modify_board(**board_dict_data)
       
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
        
    def is_your_board(self,user_no,board_no):
        '''
        사용자가 작성한 게시물인지 확인합니다.
        '''
        try:
            with DBManager() as db:
                sql = "Select count(*) as count from board where user_no = %s and board_no = %s"
                params = (user_no,board_no)
                
                result = db.getOne(sql,params)
                
                if result['count'] != 1:
                    return False
                
                return True
                
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return False
    
    def delete(self,board_no):
        '''
        게시물 데이터의 board_delete_flag 값을 Y로 수정, board_delete_date에 처리 날짜 등록
        '''
        try:
            with DBManager() as db:
                sql  = "Update board set board_delete_flag = 'Y', board_delete_date = now() where board_no = %s"
                params = (board_no)
                if db.runSQL(sql,params) != 1: 
                    print("board 데이터 Delete 처리 실패")
                    return False
                sql = "Delete from similar_board where from_board_no = %s"
                db.runSQL(sql,params)
                return True
    
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None

    def toggle_like(self, user_no, board_no):
        """
        Google 제미니 작성
        사용자가 특정 게시물에 대한 '좋아요' 상태를 토글합니다.
        이미 좋아요를 눌렀으면 취소하고, 아니면 추가합니다.
        
        :return: 작업 결과와 새로운 좋아요 수를 담은 딕셔너리
                 {'status': 'success', 'action': 'liked'|'unliked', 'count': new_like_count}
                 또는 에러 발생 시 {'status': 'error', 'message': ...}
        """
        try:
            with DBManager() as db:
                # 1. 사용자가 이미 좋아요를 눌렀는지 확인
                sql_check = "SELECT COUNT(*) as count FROM like_info WHERE user_no = %s AND board_no = %s"
                check_result = db.getOne(sql_check, (user_no, board_no))
                
                action = ''
                # 2. 결과에 따라 좋아요 추가 또는 삭제
                if check_result['count'] > 0:
                    # 이미 좋아요 상태 -> 좋아요 취소 (DELETE)
                    sql_delete = "DELETE FROM like_info WHERE user_no = %s AND board_no = %s"
                    db.runSQL(sql_delete, (user_no, board_no))
                    action = 'unliked'
                else:
                    # 좋아요 상태 아님 -> 좋아요 추가 (INSERT)
                    sql_insert = "INSERT INTO like_info (user_no, board_no) VALUES (%s, %s)"
                    db.runSQL(sql_insert, (user_no, board_no))
                    action = 'liked'
                
                # 3. 최신 좋아요 수 조회
                sql_count = "SELECT COUNT(*) as count FROM like_info WHERE board_no = %s"
                count_result = db.getOne(sql_count, (board_no,))
                new_like_count = count_result['count']
                
                return {'status': 'success', 'action': action, 'count': new_like_count}

        except Exception as e:
            print(f"DAO (toggle_like) 작업 중 오류 발생: {e}")
            return {'status': 'error', 'message': '데이터베이스 처리 중 오류가 발생했습니다.'}


# UserDAO =========================================================================================================================
class UserDAO:
    def __init__(self):
        pass
    
    def join(self, user_id, user_pw, user_pf_img):
        try:
            with DBManager() as db:
                sql = "INSERT INTO user (user_id, user_pw, user_pf_img) VALUES (%s, MD5(%s), %s)"
                params = (user_id, user_pw, user_pf_img)
                db.runSQL(sql,params)
                return True
            
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return False
            
    def login(self, user_id, user_pw):
        try:
            with DBManager() as db:
                sql = "SELECT * FROM user WHERE user_id = %s AND user_pw = MD5(%s)"
                params = (user_id, user_pw)
                
                user_dict = db.getOne(sql,params)
                if user_dict: return User(**user_dict) # 위치 인자 언패킹
                                
                return None

        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
    
    def sub_categorie(self,user_no):
        try:
            with DBManager() as db:
                sql  = "Select c.categorie_no, c.categorie_name, sb.user_no "
                sql += "from categorie c "
                sql += "Left Join subscribe sb On c.categorie_no = sb.categorie_no "
                sql += "where sb.user_no = %s "
                params = (user_no)
                sub_categorie_list = db.getAll(sql,params)
                return [Subscribe_DTO(**data) for data in sub_categorie_list]
                
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
    
    def myboard(self, user_no, order_key="board_no desc", limit=10, offset=0) -> list[Board_DTO]:
        """
        로그인한 사용자의 게시물 목록을 상세 정보와 함께 조회합니다.
        각 게시물 번호로 similar_board을 조회하고 가장 점수가 높은 6개를 얻습니다.
        """
        try:
            with DBManager() as db:
                sql  = "SELECT b.board_no, b.board_title, b.board_note, date(b.board_write_date) as board_write_date, u.user_no, u.user_id, u.user_pf_img, "
                sql += "IFNULL(GROUP_CONCAT(t.tag_name SEPARATOR ', '), '') AS tag_names, "  # NULL일 경우 빈 문자열 반환
                sql += "COUNT(DISTINCT lk.user_no) AS like_count, "
                sql += "IF(SUM(CASE WHEN lk.user_no = %s THEN 1 ELSE 0 END) > 0, 1, 0) AS user_has_liked "
                sql += "FROM board b "
                sql += "JOIN user u ON b.user_no = u.user_no "
                sql += "LEFT JOIN like_info lk ON b.board_no = lk.board_no "
                sql += "LEFT JOIN board_tag bt ON b.board_no = bt.board_no "
                sql += "LEFT JOIN tag t ON bt.tag_no = t.tag_no "
                sql += "WHERE b.board_delete_flag = 'N' and b.user_no = %s "
                sql += "GROUP BY b.board_no "
                sql += f"ORDER BY {order_key} LIMIT %s, %s"
                
                params = (user_no, user_no, offset, limit)
                
                # 사용자 작성글 조회
                list_of_dicts = db.getAll(sql,params)
                
                # 유사글 조회
                for item in list_of_dicts:
                    sql = "Select to_board_no from similar_board where from_board_no = %s order by score desc"
                    params = (item['board_no'],)
                    similar_no_datas = db.getAll(sql,params)
                    similar_board_list = []
                    # 조회한 유사글 번호들을 반복문으로 조회 후 list에 append
                    for data in similar_no_datas:
                        similar_board_no = data['to_board_no']
                        sql  = "SELECT b.board_no, b.board_title, b.board_note, date(b.board_write_date) as board_write_date, "
                        sql += "u.user_no, u.user_id, u.user_pf_img "
                        sql += "FROM board b "
                        sql += "JOIN user u ON b.user_no = u.user_no "
                        sql += "WHERE b.board_no = %s "
                        params = (similar_board_no,)
                        result = db.getOne(sql,params)
                        
                        sql = "SELECT ROUND(score, 2) AS score from similar_board where from_board_no = %s and to_board_no = %s"
                        params = (item['board_no'],similar_board_no)
                        result.update(db.getOne(sql,params))
                        # 완성된 dict를 similar_Board_DTO로 변환
                        similar_Board_DTO = Similar_Board_DTO(**result)
                        # 리스트에 DTO 등록
                        similar_board_list.append(similar_Board_DTO)
                    # 완성된 DTO 리스트를 item에 'similar_board_list'를 키로 저장
                    item['similar_board_list'] = similar_board_list
                        
                
                board_list = [My_Board_DTO(**data) for data in list_of_dicts]
                
                '''
                유사 게시글 조회 및 최상위 6개 게시글 데이터 조회
                데이터를 1개 객체로 묶어서 return 필요
                '''
                
                return board_list
    
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
    
    
    
    def userpage(self, user_no, board_no='', order_key="board_no desc", limit=10, offset=0, current_user_no=None) -> list[Board_DTO]:
        '''
        사용자의 정보와 사용자가 작성한 글들을 조회합니다.
        게시물 번호가 파라메터로 넘어올 경우 해당 게시물을 최상단에 출력합니다.
        userpage_data[0] => 유저 정보
        userpage_data[1] => 파라메타 게시글 정보
        userpage_data[2] => 유저 작성글 정보 리스트
        '''
        try:
            with DBManager() as db:
                userpage_data = []
                # 1. user 데이터 조회
                # 작성한 게시글이 없을 때에도 유효한 페이지 데이터를 출력하기 위해
                sql = "SELECT * FROM user WHERE user_no = %s"
                params = (user_no)
                
                user_dict = db.getOne(sql,params)
                if user_dict is None: return None
                
                userdata = User(**user_dict) # 위치 인자 언패킹
                userpage_data.append(userdata) # userpage_data[0] = User() 객체
                
                # 2. board_no 조회
                # board_no 파라메타가 없을 경우 None
                # board_no 파라메타가 있을 경우 Board_DTO() 객체 
                if board_no != '' and board_no != None:
                    sql  = "SELECT b.board_no, b.board_title, b.board_note, date(b.board_write_date) as board_write_date, u.user_no, u.user_id, u.user_pf_img, "
                    sql += "IFNULL(GROUP_CONCAT(t.tag_name SEPARATOR ', '), '') AS tag_names, "  # NULL일 경우 빈 문자열 반환
                    sql += "COUNT(DISTINCT lk.user_no) AS like_count, "
                    if current_user_no:
                        sql += "IF(SUM(CASE WHEN lk.user_no = %s THEN 1 ELSE 0 END) > 0, 1, 0) AS user_has_liked "
                    else:
                        # 로그인하지 않은 경우 무조건 0 (False)
                        sql += "0 AS user_has_liked "
                    sql += "FROM board b "
                    sql += "JOIN user u ON b.user_no = u.user_no "
                    sql += "LEFT JOIN like_info lk ON b.board_no = lk.board_no "
                    sql += "LEFT JOIN board_tag bt ON b.board_no = bt.board_no "
                    sql += "LEFT JOIN tag t ON bt.tag_no = t.tag_no "
                    sql += "WHERE b.board_delete_flag = 'N' and b.user_no = %s and b.board_no = %s "
                    sql += "GROUP BY b.board_no "
                    
                    if current_user_no:
                        params = (current_user_no, user_no, board_no)
                    else:
                        params = (user_no, board_no)
                        
                    board_of_dict = db.getOne(sql,params)
                    
                    search_board = Board_DTO(**board_of_dict)
                    
                    userpage_data.append(search_board) # userpage_data[1] = Board_DTO() 객체
                else:
                    userpage_data.append(None) # userpage_data[1] = None  board_no 파라메타 없을때
                    
                # 3. user 작성 게시글 조회
                # Board_DTO() 객체를 list로 묶은 데이터 
                board_list = self.user_board(user_no,order_key,limit,offset,current_user_no)
                
                userpage_data.append(board_list) # userpage_data[2] = [Board_DTO(),....] 객체 리스트
                
                return userpage_data
                
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
    
    def user_board(self,user_no,order_key="board_no desc", limit=10, offset=0, current_user_no=None):
        '''
        user_no 사용자가 작성한 게시글을 조회합니다.
        '''
        try:
            with DBManager() as db:
                sql  = "SELECT b.board_no, b.board_title, b.board_note, date(b.board_write_date) as board_write_date, u.user_no, u.user_id, u.user_pf_img, "
                sql += "IFNULL(GROUP_CONCAT(t.tag_name SEPARATOR ', '), '') AS tag_names, "  # NULL일 경우 빈 문자열 반환
                sql += "COUNT(DISTINCT lk.user_no) AS like_count, "
                if current_user_no:
                    sql += "IF(SUM(CASE WHEN lk.user_no = %s THEN 1 ELSE 0 END) > 0, 1, 0) AS user_has_liked "
                else:
                    # 로그인하지 않은 경우 무조건 0 (False)
                    sql += "0 AS user_has_liked "
                sql += "FROM board b "
                sql += "JOIN user u ON b.user_no = u.user_no "
                sql += "LEFT JOIN like_info lk ON b.board_no = lk.board_no "
                sql += "LEFT JOIN board_tag bt ON b.board_no = bt.board_no "
                sql += "LEFT JOIN tag t ON bt.tag_no = t.tag_no "
                sql += "WHERE b.board_delete_flag = 'N' and b.user_no = %s "
                sql += "GROUP BY b.board_no "
                sql += f"ORDER BY {order_key} LIMIT %s, %s"
                
                if current_user_no:
                    params = (current_user_no, user_no, offset, limit)
                else:
                    params = (user_no, offset, limit)
    
                list_of_dicts = db.getAll(sql,params)
                board_list = [Board_DTO(**data) for data in list_of_dicts]
                
                return board_list
                
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
        
    def user_recommend(self,user_no, current_user_no, limit=10, offset=0):
        '''
        user_no 사용자의 활동 데이터로 게시물 선호도를 조회합니다.
        '''
        try:
            start_n = offset*10
            end_n   = start_n + limit
            board_no_list = []
            score_list = []
            
            from tools import SVN
            svn = SVN()
            model_file = "recommand.pkl"
            
            trainset, algo, all_boards = svn.LoadModel(model_file) 
            if algo is None :
                with DBManager() as db:    
                    df = svn.LoadData(db)
                    if df is None: return None
                    trainset, algo, all_boards = svn.TrainData(df,model_file)
    
            print("=" * 40)
            recommendations = svn.GetRecommnad(trainset, algo, all_boards, user_no, start_n, end_n)
            if recommendations != None :
                for board_id, estimated_score in recommendations:
                    # 예측된 점수(estimated_score)도 0.5 ~ 1.5 범위 근처의 값으로 나옵니다.
                    board_no_list.append(board_id)
                    score_list.append(estimated_score)
                    print(f"게시물 번호: {board_id}, 예상 평점: {estimated_score:.4f}")
                    
            with DBManager() as db:
                # IN 절의 파라미터 개수에 맞춰 %s를 동적으로 생성
                placeholders = ','.join(['%s'] * len(board_no_list))
                
                sql  = "SELECT b.board_no, b.board_title, b.board_note, date(b.board_write_date) as board_write_date, u.user_no, u.user_id, u.user_pf_img, "
                sql += "IFNULL(GROUP_CONCAT(t.tag_name SEPARATOR ', '), '') AS tag_names, "
                sql += "COUNT(DISTINCT lk.user_no) AS like_count, "
                if current_user_no:
                    sql += "IF(SUM(CASE WHEN lk.user_no = %s THEN 1 ELSE 0 END) > 0, 1, 0) AS user_has_liked "
                else:
                    sql += "0 AS user_has_liked "
                sql += "FROM board b "
                sql += "JOIN user u ON b.user_no = u.user_no "
                sql += "LEFT JOIN like_info lk ON b.board_no = lk.board_no "
                sql += "LEFT JOIN board_tag bt ON b.board_no = bt.board_no "
                sql += "LEFT JOIN tag t ON bt.tag_no = t.tag_no "
                sql += f"WHERE b.board_delete_flag = 'N' and b.board_no IN ({placeholders}) " # IN 절 사용
                sql += "GROUP BY b.board_no "
                
                params = list(board_no_list)
                if current_user_no:
                    params.insert(0, current_user_no)
                
                detailed_boards_dict = db.getAll(sql, tuple(params))
                # 점수 추가 및 DTO 변환
                dto_list = []
                for idx, board_dict in enumerate(detailed_boards_dict):
                    board_dict['score'] = score_list[idx]
                    from models import Recommend_Board_DTO
                    dto_list.append(Recommend_Board_DTO(**board_dict))
                    
                # 원래 추천 점수 순서대로 정렬
                dto_list.sort(key=lambda x: x.score, reverse=True)
                return dto_list
            
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
    
# CategorieDAO =========================================================================================================================
class CategorieDAO:
    def __init__(self):
        pass
    
    def categorie_list(self,categorie_parent_no, order_key="subscribe_count desc", offset=0, limit=10, current_user_no=None):
        '''
        매개변수의 하위 카테고리 조회 데이터와 매개변수의 카테고리 이름을 리턴합니다.
        하위 카테고리 리스트 = categorie_data[0]
        매개변수 카테고리 이름 = categorie_data[1]
        '''
        try:
            with DBManager() as db:
                sql  = "Select c.categorie_no, c.categorie_name, c.categorie_info, c.categorie_pf_img_name, c.categorie_parent_no, "
                sql += "Count(DISTINCT sb.user_no) AS subscribe_count, "
                if current_user_no:
                    sql += "IF(SUM(CASE WHEN sb.user_no = %s THEN 1 ELSE 0 END) > 0, 1, 0) AS user_has_sub "
                else:
                    # 로그인하지 않은 경우 무조건 0 (False)
                    sql += "0 AS user_has_sub "
                sql += "From categorie c "
                sql += "Left Join subscribe sb On c.categorie_no = sb.categorie_no "
                sql += "Where c.categorie_parent_no = %s "
                sql += "GROUP BY c.categorie_no "
                
                if current_user_no:
                    params = (current_user_no, categorie_parent_no)
                else:
                    params = (categorie_parent_no)
                
                list_of_dicts = db.getAll(sql,params)
                categorie_dto_list = [Categorie_DTO(**data) for data in list_of_dicts]
                
                categorie_data = []
                categorie_data.append(categorie_dto_list)
                
                sql = "Select categorie_name from categorie where categorie_no = %s "
                params = (categorie_parent_no)
                categorie_parent_name = db.getOne(sql,params)
                categorie_data.append(categorie_parent_name)
                
                return categorie_data
        
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
    
    def categorie_page(self,categorie_no, order_key="like_count desc", offset=0, limit=10, current_user_no=None):
        '''
        categorie_no의 카테고리 정보와 게시글을 조회합니다.
        result[0] = 카테고리 정보
        result[1] = 카데고리 게시글 리스트
        '''
        try:
            with DBManager() as db:
                sql  = "Select c.categorie_no, c.categorie_name, c.categorie_info, c.categorie_pf_img_name, c.categorie_parent_no, "
                sql += "Count(DISTINCT sb.user_no) AS subscribe_count, "
                if current_user_no:
                    sql += "IF(SUM(CASE WHEN sb.user_no = %s THEN 1 ELSE 0 END) > 0, 1, 0) AS user_has_sub "
                else:
                    # 로그인하지 않은 경우 무조건 0 (False)
                    sql += "0 AS user_has_sub "
                sql += "From categorie c "
                sql += "Left Join subscribe sb On c.categorie_no = sb.categorie_no "
                sql += "Where c.categorie_no = %s "
                sql += "GROUP BY c.categorie_no"
                
                if current_user_no:
                    params = (current_user_no, categorie_no)
                else:
                    params = (categorie_no,)
                    
                categorie_data = db.getOne(sql,params)
                categorie_dto = Categorie_DTO(**categorie_data)
                
                result = []
                result.append(categorie_dto)
                
                board_dto_list = self.categorie_board(categorie_no, 
                                                      order_key, 
                                                      offset, 
                                                      limit, 
                                                      current_user_no)
                
                result.append(board_dto_list)
                return result
                
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
        
    def categorie_board(self, categorie_no, order_key="like_count desc", offset=0, limit=10, current_user_no=None):
        '''
        카테고리의 게시글을 조회합니다
        '''
        try:
            with DBManager() as db:
                sql  = "SELECT b.board_no, b.board_title, b.board_note, date(b.board_write_date) as board_write_date, u.user_no, u.user_id, u.user_pf_img, "
                sql += "IFNULL(GROUP_CONCAT(t.tag_name SEPARATOR ', '), '') AS tag_names, "  # NULL일 경우 빈 문자열 반환
                sql += "COUNT(DISTINCT lk.user_no) AS like_count, "
                if current_user_no:
                    sql += "IF(SUM(CASE WHEN lk.user_no = %s THEN 1 ELSE 0 END) > 0, 1, 0) AS user_has_liked "
                else:
                    # 로그인하지 않은 경우 무조건 0 (False)
                    sql += "0 AS user_has_liked "
                sql += "FROM board b "
                sql += "JOIN user u ON b.user_no = u.user_no "
                sql += "LEFT JOIN like_info lk ON b.board_no = lk.board_no "
                sql += "LEFT JOIN board_tag bt ON b.board_no = bt.board_no "
                sql += "LEFT JOIN tag t ON bt.tag_no = t.tag_no "
                sql += "WHERE b.board_delete_flag = 'N' and b.categorie_no = %s "
                sql += "GROUP BY b.board_no "
                sql += f"ORDER BY {order_key} LIMIT %s, %s"
                
                if current_user_no:
                    params = (current_user_no, categorie_no, offset, limit)
                else:
                    params = (categorie_no, offset, limit)
                
                board_list_of_dicts = db.getAll(sql,params)
                board_dto_list = [Board_DTO(**data) for data in board_list_of_dicts]
                
                return board_dto_list
                
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return None
        
    def toggle_subscribe(self, user_no, categorie_no):
       """
       Google 제미니 작성
       사용자가 특정 카테고리에 대한 '구독' 상태를 토글합니다.
       이미 구독 중이면 취소하고, 아니면 추가합니다.
       
       :return: 작업 결과와 새로운 구독자 수를 담은 딕셔너리
                {'status': 'success', 'action': 'subscribed'|'unsubscribed', 'count': new_subscribe_count}
                또는 에러 발생 시 {'status': 'error', 'message': ...}
       """
       try:
           with DBManager() as db:
               # 1. 사용자가 이미 구독했는지 확인
               sql_check = "SELECT COUNT(*) as count FROM subscribe WHERE user_no = %s AND categorie_no = %s"
               check_result = db.getOne(sql_check, (user_no, categorie_no))
               
               action = ''
               # 2. 결과에 따라 구독 추가 또는 삭제
               if check_result['count'] > 0:
                   # 이미 구독 상태 -> 구독 취소 (DELETE)
                   sql_delete = "DELETE FROM subscribe WHERE user_no = %s AND categorie_no = %s"
                   db.runSQL(sql_delete, (user_no, categorie_no))
                   action = 'unsubscribed'
               else:
                   # 구독 상태 아님 -> 구독 추가 (INSERT)
                   sql_insert = "INSERT INTO subscribe (user_no, categorie_no) VALUES (%s, %s)"
                   db.runSQL(sql_insert, (user_no, categorie_no))
                   action = 'subscribed'
               
               # 3. 최신 구독자 수 조회
               sql_count = "SELECT COUNT(*) as count FROM subscribe WHERE categorie_no = %s"
               count_result = db.getOne(sql_count, (categorie_no,))
               new_subscribe_count = count_result['count']
               
               return {'status': 'success', 'action': action, 'count': new_subscribe_count}
    
       except Exception as e:
           print(f"DAO (toggle_subscribe) 작업 중 오류 발생: {e}")
           return {'status': 'error', 'message': '데이터베이스 처리 중 오류가 발생했습니다.'}
    
    

# filter =========================================================================================================================
class FiltersDAO:
    def __init__(self):
        pass
    
    def search(self, keyword, search_filter, order_key="board_no desc", offset=0, limit=10, current_user_no=None):
        try:
            with DBManager() as db:
                sql  = "SELECT b.board_no, b.board_title, b.board_note, date(b.board_write_date) as board_write_date, u.user_no, u.user_id, u.user_pf_img, "
                sql += "IFNULL(GROUP_CONCAT(t.tag_name SEPARATOR ', '), '') AS tag_names, "  # NULL일 경우 빈 문자열 반환
                sql += "COUNT(DISTINCT lk.user_no) AS like_count, "
                if current_user_no:
                    sql += "IF(SUM(CASE WHEN lk.user_no = %s THEN 1 ELSE 0 END) > 0, 1, 0) AS user_has_liked "
                else:
                    # 로그인하지 않은 경우 무조건 0 (False)
                    sql += "0 AS user_has_liked "
                sql += "FROM board b "
                sql += "JOIN user u ON b.user_no = u.user_no "
                sql += "LEFT JOIN like_info lk ON b.board_no = lk.board_no "
                sql += "LEFT JOIN board_tag bt ON b.board_no = bt.board_no "
                sql += "LEFT JOIN tag t ON bt.tag_no = t.tag_no "
                sql += "WHERE b.board_delete_flag = 'N' "
                
                search_keyword = f"%{keyword}%"
                
                where_params = []

                if search_filter == '1': # 전체 검색
                    sql += "AND (b.board_title LIKE %s OR b.board_note LIKE %s OR u.user_id LIKE %s OR t.tag_name LIKE %s) "
                    where_params.extend([search_keyword, search_keyword, search_keyword, search_keyword])
                elif search_filter == '2': # 제목
                    sql += "AND b.board_title LIKE %s "
                    where_params.append(search_keyword)
                elif search_filter == '3': # 내용
                    sql += "AND b.board_note LIKE %s "
                    where_params.append(search_keyword)
                elif search_filter == '4': # 작성자
                    sql += "AND u.user_id LIKE %s "
                    where_params.append(search_keyword)
                elif search_filter == '5': # 태그
                    sql += "AND t.tag_name LIKE %s "
                    where_params.append(search_keyword)
                
                sql += "GROUP BY b.board_no, b.board_title, b.board_note, b.board_write_date, u.user_no, u.user_id, u.user_pf_img "
                sql += f"ORDER BY {order_key} LIMIT %s, %s"
                params = tuple(where_params + [offset, limit])
                
                if current_user_no:
                    params = tuple([current_user_no] + where_params + [offset, limit])
                else:
                    params = tuple(where_params + [offset, limit])
                
                board_list_of_dicts = db.getAll(sql,params)
                board_dto_list = [Board_DTO(**data) for data in board_list_of_dicts]
                
                return board_dto_list
        
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return False    

'''
# template =========================================================================================================================
class TemplateDAO:
    def __init__(self):
        pass
    
    def template(self):
        try:
            with DBManager() as db:
                pass
        
        except Exception as e:
            print(f"DAO 작업 중 오류 발생: {e}")
            return False
'''
    
    