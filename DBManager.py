import pymysql
import pandas as pd

class DBManager:
    def __init__(self, host='127.0.0.1', user='root', password='ezen', db='ateamSNS', charset='utf8'):
        self.conn = None
        self.cursor = None
        self.conn_info = {
            'host': host,
            'user': user,
            'password': password,
            'db': db,
            'charset': charset,
            'cursorclass': pymysql.cursors.DictCursor  # 생성 시 커서 타입을 지정
        }

    def __enter__(self):
        self.conn = pymysql.connect(**self.conn_info)
        self.cursor = self.conn.cursor() # DictCursor가 기본으로 생성됨
        print("DB 연결 성공 (with)")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:  # 예외가 발생했다면
            self.conn.rollback()
            print(f"예외 발생으로 롤백: {exc_val}")
        else: # 예외 없이 정상 종료 시
            self.conn.commit()

        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("DB 연결 해제 (with)")

    def get_cursor(self):
        """__enter__에서 생성된 공유 커서를 반환합니다."""
        if not self.cursor:
            raise Exception("Cursor is not available. Use within a 'with' block.")
        return self.cursor # self.cursor를 직접 반환

    # INSERT, UPDATE, DELETE 쿼리 실행 (이름을 더 명확하게)
    def runSQL(self, sql, params=None):
        """
        데이터를 변경하는 쿼리(INSERT, UPDATE, DELETE)를 실행합니다.
        성공 시 영향을 받은 행의 수를 반환합니다.
        """
        return self.cursor.execute(sql, params)

    # 모든 결과 조회 (DataFrame)
    def getAll_df(self, sql, params=None):
        """
        SELECT 쿼리를 실행하고, 모든 결과를 pandas DataFrame으로 반환합니다.
        """
        self.cursor.execute(sql, params)
        result = self.cursor.fetchall() # DictCursor 덕분에 딕셔너리의 리스트로 반환됨
        return pd.DataFrame(result)

    # 하나의 결과만 조회 (단일 딕셔너리)
    def getOne(self, sql, params=None):
        """
        SELECT 쿼리를 실행하고, 첫 번째 결과만 딕셔너리로 반환합니다.
        결과가 없으면 None을 반환합니다.
        """
        self.cursor.execute(sql, params)
        return self.cursor.fetchone() # 첫 번째 행만 가져옴

    # 모든 결과 조회 (딕셔너리의 리스트)
    def getAll(self, sql, params=None):
        """
        SELECT 쿼리를 실행하고, 모든 결과를 딕셔너리의 리스트로 반환합니다.
        """
        #print(f"getALL:sql:{sql}")
        #print(f"getALL:params:{params}")
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()