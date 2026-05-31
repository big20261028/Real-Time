drop database if exists ateamSNS;
create database ateamSNS;
use ateamSNS;
-- ======================================= 유저 테이블 ================================================
create table user(
	user_no int primary key auto_increment comment '사용자 번호',
	user_id varchar(50) not null unique comment '사용자 아이디',
	user_pw varchar(100) not null comment '사용자 비밀번호'
    user_join_date datetime default now() comment '사용자 가입일'
);

-- ======================================= 카테고리 테이블 ================================================
-- 카테고리 정보 테이블 통합
create table categorie(
	categorie_no int primary key auto_increment comment '카테고리 번호',
	categorie_name varchar(100) not null unique comment '카테고리 이름',
	categorie_level tinyint unsigned not null comment '카테고리 깊이',
	categorie_info varchar(200) not null comment '카테고리 소개글',
	categorie_bg_img_path varchar(200) comment '카테고리 배경 이미지 물리명',
	categorie_bg_img_name varchar(200) comment '카테고리 배경 이미지 논리명',
	categorie_pf_img_path varchar(200) comment '카테고리 프로필 이미지 물리명',
	categorie_pf_img_name varchar(200) comment '카테고리 프로필 이미지 논리명',
	categorie_parent_no int comment '카테고리 부모 번호',
	
	CONSTRAINT fk_parent_category
        FOREIGN KEY (categorie_parent_no)
        REFERENCES categorie (categorie_no)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- ======================================= 게시판 테이블 ================================================
create table board(
	board_no int primary key auto_increment comment '게시물 번호',
	board_title varchar(100) not null comment '게시물 제목',
	board_write_date datetime default now() comment '게시물 작성일자',
    board_modify_date datetime comment '게시물 수정일자',
    board_delete_date datetime comment '게시물 삭제일자',
	board_note text not null comment '게시물 내용',
	user_no int comment '사용자 번호',
	categorie_no int comment '카테고리 번호',
	
	foreign key (user_no) references user (user_no),
	foreign key (categorie_no) references categorie (categorie_no)
);

-- ======================================= 태그 테이블 ================================================
create table tag(
	tag_no int primary key auto_increment comment '태그 번호',
	tag_name varchar(100) not null unique comment '태그 이름'
);

-- ======================================= 게시물 태그 테이블 ================================================
create table board_tag(
	board_no int comment '게시물 번호',
	tag_no int comment '태그 번호',
	PRIMARY KEY (board_no, tag_no),
	
	foreign key (board_no) references board (board_no),
	foreign key (tag_no) references tag (tag_no)
);

-- ======================================= 추천 정보 테이블 ================================================
create table recommend(
	board_no int comment '게시물 번호',
	user_no int comment '사용자 번호',
	PRIMARY KEY (board_no, user_no),
	
	foreign key (board_no) references board (board_no),
	foreign key (user_no) references user (user_no)
);

-- ======================================= 구독 정보 테이블 ================================================
create table subscribe(
	categorie_no int comment '카테고리 번호',
	user_no int comment '사용자 번호',
	PRIMARY KEY (categorie_no, user_no),
	
	foreign key (categorie_no) references categorie (categorie_no),
	foreign key (user_no) references user (user_no)
);

-- ======================================= TF-IDF 정보 테이블 ================================================
CREATE TABLE board_tfidf_vectors (
    board_no INT PRIMARY KEY COMMENT '게시물 번호',
    tfidf_vector JSON NOT NULL COMMENT '제목, 작성자, 내용, 카테고리, 태그를 조합한 TF-IDF 벡터',
    
    FOREIGN KEY (board_no) REFERENCES board(board_no) ON DELETE CASCADE
);

-- ======================================= 단어 모음 정보 테이블 ================================================
CREATE TABLE terms (
    term_id INT PRIMARY KEY AUTO_INCREMENT comment '단어 아이디',
    term_name VARCHAR(255) NOT NULL UNIQUE comment '실제 단어'
);

-- ======================================= 사용자-게시물 상호작용 정보 테이블 ================================================
CREATE TABLE user_board_interaction (
    interaction_no BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '사용자-게시물 상호작용 번호',
    user_no INT NOT NULL COMMENT '사용자 번호',
    board_no INT NOT NULL COMMENT '게시물 번호',
    interaction_type VARCHAR(50) NOT NULL COMMENT '상호작용 타입 (read, comment, share 등)',
    interaction_timestamp DATETIME DEFAULT NOW() COMMENT '상호작용 일시',

    FOREIGN KEY (user_no) REFERENCES user(user_no) ON DELETE CASCADE,
    FOREIGN KEY (board_no) REFERENCES board(board_no) ON DELETE CASCADE
);

-- ==================================================================================================
-- =======================================최초 데이터 등록================================================




















