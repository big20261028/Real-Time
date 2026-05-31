drop database if exists ateamSNS;
create database ateamSNS;
use ateamSNS;
-- ======================================= 유저 테이블 ================================================
create table user(
	user_no int primary key auto_increment comment '사용자 번호',
	user_id varchar(50) not null unique comment '사용자 아이디',
	user_pw varchar(100) not null comment '사용자 비밀번호'
);

-- ======================================= 카테고리 테이블 ================================================
create table categorie(
	categorie_no int primary key auto_increment comment '카테고리 번호',
	categorie_name varchar(100) not null unique comment '카테고리 이름',
	categorie_level tinyint unsigned not null comment '카테고리 깊이',
	categorie_parent_no int comment '카테고리 부모 번호',
	
	CONSTRAINT fk_parent_category
        FOREIGN KEY (categorie_parent_no)
        REFERENCES categorie (categorie_no)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- ======================================= 카테고리 정보 테이블 ================================================
create table categorie_info(
	categorie_no int primary key comment '카테고리 번호',
	categorie_info varchar(200) not null comment '카테고리 소개글',
	categorie_bg_img_path varchar(200) comment '카테고리 배경 이미지 물리명',
	categorie_bg_img_name varchar(200) comment '카테고리 배경 이미지 논리명',
	categorie_pf_img_path varchar(200) comment '카테고리 프로필 이미지 물리명',
	categorie_pf_img_name varchar(200) comment '카테고리 프로필 이미지 논리명',
	
	foreign key (categorie_no) references categorie (categorie_no)

);

-- ======================================= 게시판 테이블 ================================================
create table board(
	board_no int primary key auto_increment comment '게시물 번호',
	board_title varchar(100) not null comment '게시물 제목',
	board_wdate datetime default now() comment '게시물 작성일자',
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
CREATE TABLE tfidf_vectors (
    board_no INT NOT NULL comment '게시물 번호',
    term_id INT NOT NULL comment '단어 아이디',
    tfidf_value DOUBLE NOT NULL comment 'tf-idf 값',
    PRIMARY KEY (board_no, term_id), -- 복합 기본 키
    FOREIGN KEY (board_no) REFERENCES board(board_no) ON DELETE CASCADE,
    FOREIGN KEY (term_id) REFERENCES terms(term_id) ON DELETE CASCADE -- 아래 terms 테이블 참조
);

-- `tfidf_vectors` 테이블을 조금 더 명확하게 수정
CREATE TABLE board_tfidf_vectors (
    board_no INT PRIMARY KEY COMMENT '게시물 번호',
    -- 조합된 텍스트의 TF-IDF 벡터 (JSON 형태로 저장)
    -- numpy 배열 tf-idf 백터를 list로 변환 -> list를 json으로 변환 후 db에 등록
    tfidf_vector JSON NOT NULL COMMENT '제목, 작성자, 내용, 카테고리, 태그를 조합한 TF-IDF 벡터',
    
    FOREIGN KEY (board_no) REFERENCES board(board_no) ON DELETE CASCADE
);

-- ======================================= 단어 모음 정보 테이블 ================================================
CREATE TABLE terms (
    term_id INT PRIMARY KEY AUTO_INCREMENT comment '단어 아이디',
    term_name VARCHAR(255) NOT NULL UNIQUE comment '실제 단어' -- 예: '스마트폰', '카메라'
);

-- ======================================= 게시물 유사도 정보 테이블 ================================================
-- 데이터가 많아져서 병목현상이 발생할 때 도입 고려
CREATE TABLE board_similarities (
    board_id_1 INT NOT NULL comment '비교할 게시물 번호',
    board_id_2 INT NOT NULL comment '비교당할 게시물 번호',
    similarity_score DOUBLE NOT NULL comment '유사도 점수(넘파이 배열)',
    PRIMARY KEY (board_id_1, board_id_2),
    FOREIGN KEY (board_id_1) REFERENCES board(board_no) ON DELETE CASCADE,
    FOREIGN KEY (board_id_2) REFERENCES board(board_no) ON DELETE CASCADE
);

-- ======================================= 사용자-게시물 상호작용 정보 테이블 ================================================
CREATE TABLE user_board_interaction (
    interaction_no BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '사용자-게시물 상호작용 번호',
    user_no INT NOT NULL COMMENT '사용자 번호',
    board_no INT NOT NULL COMMENT '게시물 번호',
    interaction_type VARCHAR(50) NOT NULL COMMENT '상호작용 타입 (read, like, comment, share 등)',
    interaction_timestamp DATETIME DEFAULT NOW() COMMENT '상호작용 일시',

    FOREIGN KEY (user_no) REFERENCES user(user_no) ON DELETE CASCADE,
    FOREIGN KEY (board_no) REFERENCES board(board_no) ON DELETE CASCADE
    UNIQUE (user_no, board_no, interaction_type) -- 특정 상호작용은 한 번만 허용할 경우
);

-- ======================================= 사용자-카테고리 상호작용 정보 테이블 ================================================
-- subscribe 테이블 통합
CREATE TABLE user_categorie_interaction (
    interaction_no BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '사용자-카테고리 상호작용 번호',
    user_no INT NOT NULL COMMENT '사용자 번호',
    categorie_no INT NOT NULL COMMENT '카테고리 번호',
    interaction_type VARCHAR(50) NOT NULL COMMENT '상호작용 타입 (subscribe, visit, read_articles_in_category 등)',
    interaction_timestamp DATETIME DEFAULT NOW() COMMENT '상호작용 일시',

    FOREIGN KEY (user_no) REFERENCES user(user_no) ON DELETE CASCADE,
    FOREIGN KEY (categorie_no) REFERENCES categorie(categorie_no) ON DELETE CASCADE
    UNIQUE (user_no, categorie_no, interaction_type) -- 특정 타입의 상호작용은 한 번만 허용
);

-- ======================================= 추천 캐시 정보 테이블 ================================================
-- 사용법 재학습 필요
CREATE TABLE user_recommendations_cache (
    user_no INT NOT NULL,
    recommended_item_id INT NOT NULL,
    item_type VARCHAR(20) NOT NULL COMMENT 'board 또는 categorie',
    score DOUBLE NOT NULL,
    ranked_order INT NOT NULL,
    generated_at DATETIME DEFAULT NOW(),

    PRIMARY KEY (user_no, item_type, ranked_order), -- 사용자별, 아이템 타입별 순위로 PK
    FOREIGN KEY (user_no) REFERENCES user(user_no) ON DELETE CASCADE
    -- recommended_item_id는 item_type에 따라 board 또는 categorie를 참조. 직접 FK 설정은 어려움.
    -- 애플리케이션 레벨에서 유효성 검사 필요.
);
-- ==================================================================================================
-- =======================================최초 데이터 등록================================================




















