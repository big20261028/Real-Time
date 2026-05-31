from dataclasses import dataclass
from datetime import date

@dataclass
class User:
    user_no: int
    user_id: str
    user_pw: str
    user_join_date: date
    user_pf_img: int

@dataclass
class Tag:
    tag_no: int
    tag_name: str

@dataclass
class Categorie:
    categorie_no: int
    cateogirie_name: str
    categorie_levle: int
    categorie_intro: str
    categorie_pf_img_path: str
    categorie_parent_id: int
    
@dataclass
class Board:
    board_no: int
    user_no: int
    categorie_no: int
    board_title: str
    board_write_date: date
    board_modify: date
    board_delete_date: date
    board_delete_flag: str
    board_note: str
    
@dataclass
class Subcribe:
    user_no: int
    categorie_no: int
    
@dataclass
class Like_Info:
    user_no: int
    categorie_no: int
    
@dataclass
class Board_Tag:
    board_no: int
    tag_no: int
    
@dataclass
class Recommend_Board:
    user_no: int
    board_no: int
    score: int
    
@dataclass
class Similar_Board:
    from_board_no: int
    to_board_no: int
    score: int

# 여러 테이블을 JOIN한 결과를 담을 DTO(Data Transfer Object) 클래스 ===========================================
@dataclass
class Board_DTO:
    board_no: int
    board_title: str
    board_note: str
    board_write_date: date
    user_no: int
    user_id: str
    user_pf_img: str
    tag_names: str  # "태그1, 태그2" 형태의 문자열
    like_count: int
    user_has_liked: bool

    # tag_names를 리스트로 변환해주는 프로퍼티를 추가하면 템플릿에서 사용하기 편리합니다.
    @property
    def tags(self) -> list[str]: # -> list[str] 은 타입힌트, 삭제해도 정상작동함
        if self.tag_names:
            return [tag.strip() for tag in self.tag_names.split(',')]
        return []

@dataclass
class Similar_Board_DTO:
    board_no: int
    board_title: str
    board_note: str
    board_write_date: date
    user_no: int
    user_id: str
    user_pf_img: str
    score: float
    
@dataclass
class Recommend_Board_DTO:
    board_no: int
    board_title: str
    board_note: str
    board_write_date: date
    user_no: int
    user_id: str
    user_pf_img: str
    tag_names: str  
    like_count: int
    user_has_liked: bool
    score : float

    # tag_names를 리스트로 변환해주는 프로퍼티를 추가하면 템플릿에서 사용하기 편리합니다.
    @property
    def tags(self) -> list[str]: # -> list[str] 은 타입힌트, 삭제해도 정상작동함
        if self.tag_names:
            return [tag.strip() for tag in self.tag_names.split(',')]
        return []
    
@dataclass
class My_Board_DTO:
    board_no: int
    board_title: str
    board_note: str
    board_write_date: date
    user_no: int
    user_id: str
    user_pf_img: str
    tag_names: str  # "태그1, 태그2" 형태의 문자열
    like_count: int
    user_has_liked: bool
    # 유사 게시글 변수 추가
    similar_board_list: list[Similar_Board_DTO]

    # tag_names를 리스트로 변환해주는 프로퍼티를 추가하면 템플릿에서 사용하기 편리합니다.
    @property
    def tags(self) -> list[str]: # -> list[str] 은 타입힌트, 삭제해도 정상작동함
        if self.tag_names:
            return [tag.strip() for tag in self.tag_names.split(',')]
        return []


    

@dataclass
class Modify_board:
    board_no: int
    user_no: int
    board_title: str
    board_note: str
    categorie_no: int
    tag_names: str
    categorie_parent_no: int
    
@dataclass
class Categorie_DTO:
    categorie_no: int
    categorie_name: str
    categorie_info: str
    categorie_pf_img_name: str
    categorie_parent_no: int
    subscribe_count: int
    user_has_sub: bool
    
@dataclass
class Subscribe_DTO:
    user_no: int
    categorie_no: int
    categorie_name: str
    








