# 파일명: image_downloader.py

import os
import requests
import pymysql
from urllib.parse import urlparse

# --- 스크립트 설정 (사용자 환경에 맞게 수정) ---

# 1. 이미지를 저장할 로컬 폴더 경로
#    (웹 서버가 접근할 수 있는 static 경로로 지정하는 것이 일반적입니다.)
IMAGE_SAVE_PATH = 'static/img/category_icons'

# 2. 데이터베이스 연결 정보
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'ezen',
    'db': 'ateamSNS',
    'charset': 'utf8',
    'cursorclass': pymysql.cursors.DictCursor # 결과를 딕셔너리로 받기
}

# --- 메인 로직 ---

def download_and_update_images():
    """DB에서 이미지 URL을 가져와 로컬에 다운로드하고, DB를 업데이트합니다."""
    
    # 1. 로컬 저장 폴더가 없으면 생성
    try:
        os.makedirs(IMAGE_SAVE_PATH, exist_ok=True)
        print(f"이미지 저장 폴더: '{IMAGE_SAVE_PATH}'")
    except OSError as e:
        print(f"오류: 폴더 생성에 실패했습니다. '{IMAGE_SAVE_PATH}'. {e}")
        return

    connection = None
    try:
        # 2. 데이터베이스 연결
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("데이터베이스에 성공적으로 연결되었습니다.")

        # 3. 처리할 대상 선정: 이미지 이름이 http로 시작하는 모든 레코드
        select_sql = "SELECT categorie_no, categorie_pf_img_name FROM categorie WHERE categorie_pf_img_name LIKE 'http%'"
        cursor.execute(select_sql)
        image_list = cursor.fetchall()

        if not image_list:
            print("모든 이미지가 이미 로컬에 저장되어 있습니다. 새로 다운로드할 이미지가 없습니다.")
            return

        print(f"총 {len(image_list)}개의 이미지를 다운로드합니다...")
        
        # 4. 각 이미지를 순회하며 다운로드 및 업데이트
        for item in image_list:
            category_no = item['categorie_no']
            image_url = item['categorie_pf_img_name']

            print(f"\n처리 중 (ID: {category_no})... URL: {image_url}")

            try:
                # 4-a. 이미지 다운로드 요청 (stream=True로 메모리 효율성 향상)
                response = requests.get(image_url, stream=True, timeout=10)
                response.raise_for_status() # 200 OK가 아니면 예외 발생

                # 4-b. 파일 확장자 추출
                path = urlparse(image_url).path
                ext = os.path.splitext(path)[1]
                if not ext: # 확장자가 없는 경우 .jpg를 기본값으로 사용
                    ext = '.jpg'
                
                # 4-c. 새 파일명 및 전체 저장 경로 생성
                new_filename = f"{category_no}{ext}"
                full_save_path = os.path.join(IMAGE_SAVE_PATH, new_filename)

                # 4-d. 파일 저장 (binary write mode)
                with open(full_save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"  [성공] 파일 저장 완료: {full_save_path}")

                # 4-e. DB 업데이트
                update_sql = "UPDATE categorie SET categorie_pf_img_name = %s WHERE categorie_no = %s"
                cursor.execute(update_sql, (new_filename, category_no))
                print(f"  [성공] DB 업데이트: categorie_pf_img_name -> '{new_filename}'")

            except requests.exceptions.RequestException as e:
                print(f"  [오류] 이미지 다운로드 실패 (ID: {category_no}): {e}")
            except Exception as e:
                print(f"  [오류] 파일 처리 중 알 수 없는 문제 발생 (ID: {category_no}): {e}")

        # 5. 모든 변경사항을 DB에 최종 커밋
        connection.commit()
        print("\n모든 작업이 완료되었으며, 변경사항이 데이터베이스에 저장되었습니다.")

    except pymysql.Error as e:
        print(f"데이터베이스 오류 발생: {e}")
        if connection:
            connection.rollback() # 오류 발생 시 롤백
    except Exception as e:
        print(f"알 수 없는 오류 발생: {e}")
    finally:
        if connection:
            connection.close()
            print("데이터베이스 연결을 닫았습니다.")

# ===================================================================
# 스크립트 실행
# ===================================================================
if __name__ == "__main__":
    download_and_update_images()