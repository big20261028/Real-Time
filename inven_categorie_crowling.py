# 파일명: crawler_to_dataframe.py (최종 업그레이드 버전)

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import requests # 2차 크롤링을 위해 import

# --- 2차 크롤링을 위한 헬퍼 함수 ---
def get_high_res_logo_from_channel_page(channel_url):
    """
    주어진 채널 페이지 URL로 접속하여 고해상도 로고 이미지의 src를 반환합니다.
    
    Args:
        channel_url (str): 각 게임별 채널 페이지의 전체 URL.

    Returns:
        성공 시 이미지 URL(str), 실패 시 None.
    """
    # 유효한 외부 링크가 아니면(예: 내부 파라미터 링크) 시도하지 않음
    if not channel_url or not channel_url.startswith('http'):
        return None

    try:
        # Selenium 대신 훨씬 가벼운 requests를 사용하여 2차 크롤링 속도 향상
        headers = {'User-Agent': 'Mozilla/5.0'} # 차단을 피하기 위한 User-Agent 설정
        response = requests.get(channel_url, headers=headers, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 고해상도 로고를 찾기 위한 일반적인 CSS 셀렉터 리스트 (우선순위 순)
        # 대부분의 인벤 채널 사이트들은 이 구조 중 하나를 따릅니다.
        logo_selectors = [
            'header h1 img',        # 헤더 안의 H1 태그 안의 이미지 (가장 흔함)
            '#header .logo img',    # id가 header인 요소 밑의 logo 클래스 안의 이미지
            '.main-header h1 img'   # main-header 클래스 안의 H1 태그 안의 이미지
        ]

        for selector in logo_selectors:
            logo_tag = soup.select_one(selector)
            if logo_tag and logo_tag.get('src'):
                logo_src = logo_tag.get('src')
                # 추출한 src가 완전한 URL이 되도록 보장
                full_logo_url = urljoin(channel_url, logo_src)
                print(f"  [2차 크롤링 성공] '{channel_url}' 에서 로고 발견: {full_logo_url}")
                return full_logo_url
        
        print(f"  [2차 크롤링 정보] '{channel_url}' 에서 일반적인 로고 셀렉터를 찾지 못함.")
        return None

    except requests.RequestException as e:
        print(f"  [2차 크롤링 오류] '{channel_url}' 접속 실패: {e}")
        return None

# --- 메인 크롤러 함수 ---
def crawl_and_create_dataframe():
    driver = webdriver.Chrome()
    base_url = 'https://www.inven.co.kr'
    url = urljoin(base_url, '/webzine/zone/gamer/')
    processed_data = []

    print("인벤 게이머존 2단계 크롤링을 시작합니다...")

    try:
        driver.get(url)
        # ... (Selenium으로 1차 페이지 로딩하는 부분은 동일) ...
        button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "body > header > div.header-nav > div > div > button")))
        button.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "genre")))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        category_container = soup.find('div', id='genre')

        if not category_container:
            return pd.DataFrame()

        category_rows = category_container.find_all('div', class_='row')

        for row in category_rows:
            # ... (부모 카테고리 처리 부분은 동일) ...
            parent_tag = row.find('h4')
            if not parent_tag: continue
            parent_name = parent_tag.get_text(strip=True)
            parent_dict = {
                'categorie_name': parent_name, 'categorie_level': 1, 'categorie_info': f"최상위 카테고리: {parent_name}",
                'categorie_pf_img_name': None, 'categorie_parent_no': None, 'parent_name_for_logic': None
            }
            processed_data.append(parent_dict)

            child_list_tag = row.find('ul')
            if child_list_tag:
                child_tags = child_list_tag.find_all('a')
                for child_tag in child_tags:
                    child_name = child_tag.get_text(strip=True)
                    if '전체' in child_name: continue
                    
                    # 1. 1차 정보 수집 (채널 URL, 저해상도 대체 이미지)
                    channel_page_url = urljoin(base_url, child_tag.get('href'))
                    
                    fallback_image_url = None
                    low_res_img_tag = child_tag.find('img', class_='iconimg')
                    if low_res_img_tag:
                        fallback_image_url = urljoin(base_url, low_res_img_tag.get('src'))

                    # 2. 2차 크롤링 시도
                    high_res_image_url = get_high_res_logo_from_channel_page(channel_page_url)
                    
                    # 3. 최종 이미지 결정 (고해상도가 있으면 사용, 없으면 저해상도 대체재 사용)
                    final_image_url = high_res_image_url or fallback_image_url

                    child_dict = {
                        'categorie_name': child_name, 'categorie_level': 2, 'categorie_info': f"'{parent_name}'의 하위 카테고리: {child_name}",
                        'categorie_pf_img_name': final_image_url, # 최종 결정된 이미지 URL 저장
                        'categorie_parent_no': None, 'parent_name_for_logic': parent_name
                    }
                    processed_data.append(child_dict)
        
        print(f"\n크롤링 및 데이터 가공 완료! 총 {len(processed_data)}개의 카테고리 처리됨.")
        df = pd.DataFrame(processed_data)
        return df

    finally:
        driver.quit()

# ===================================================================
# 메인 실행 부분 (이전과 동일)
# ===================================================================
if __name__ == "__main__":
    category_df = crawl_and_create_dataframe()
    if not category_df.empty:
        print("\n--- 생성된 DataFrame 미리보기 (고해상도 이미지 포함) ---")
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
            print(category_df)
        output_filename = "categories.csv"
        category_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"\nDataFrame을 '{output_filename}' 파일로 성공적으로 저장했습니다.")