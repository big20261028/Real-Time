drop database if exists ateamSNS;
create database ateamSNS;
use ateamSNS;
-- ======================================= 유저 테이블 ================================================
-- 사용자 프로필 이미지 : 0, 1, 2 중 한가지 선택
create table user(
	user_no int primary key auto_increment comment '사용자 번호',
	user_id varchar(50) not null unique comment '사용자 아이디',
	user_pw varchar(100) not null comment '사용자 비밀번호',
	user_join_date datetime default now() comment '사용자 가입일',
	user_pf_img int comment '사용자 프로필 이미지'
);

-- ======================================= 카테고리 테이블 ================================================
-- 카테고리 정보 테이블 통합
create table categorie(
	categorie_no int primary key auto_increment comment '카테고리 번호',
	categorie_name varchar(100) not null unique comment '카테고리 이름',
	categorie_level tinyint unsigned not null comment '카테고리 레벨',
	categorie_info varchar(200) not null comment '카테고리 소개글',
	categorie_pf_img_name varchar(200) comment '카테고리 프로필 이미지',
	categorie_parent_no int comment '카테고리 부모 번호',
	
	CONSTRAINT fk_parent_category
        FOREIGN KEY (categorie_parent_no)
        REFERENCES categorie (categorie_no)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- ======================================= 게시판 테이블 ================================================
create table board(
	board_no int primary key auto_increment comment '게시글 번호',
	board_title varchar(100) not null comment '게시글 제목',
	board_write_date datetime default now() comment '게시글 작성일자',
	board_modify_date datetime comment '게시글 수정일자',
	board_delete_date datetime comment '게시글 삭제일자',
	board_delete_flag varchar(1) comment '게시글 삭제 여부',
	board_note text not null comment '게시글 내용',
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

-- ======================================= 게시글 태그 테이블 ================================================
create table board_tag(
	board_no int comment '게시글 번호',
	tag_no int comment '태그 번호',
	PRIMARY KEY (board_no, tag_no),
	
	foreign key (board_no) references board (board_no),
	foreign key (tag_no) references tag (tag_no)
);

-- ======================================= 좋아요 정보 테이블 ================================================
create table like(
	board_no int comment '게시글 번호',
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

-- ======================================= 유사 게시글 테이블 ================================================
CREATE TABLE similar_board (
	from_board_no int comment '새 게시글 번호',
	to_board_no int comment '기존 게시글 번호',
	score int not null comment '점수',
	PRIMARY KEY (from_board_no, to_board_no),

	foreign key (from_board_no) references board (board_no),
	foreign key (to_board_no) references board (board_no)
);

-- ======================================= 유사 게시글 테이블 ================================================
create table recommend_board (
	user_no int comment '사용자 번호',
	board_no int comment '게시글 번호',
	score int not null comment '점수',
	PRIMARY KEY (user_no, board_no),

	foreign key (user_no) references user (user_no),
	foreign key (board_no) references board (board_no)
)



-- ==================================================================================================
-- =======================================최초 데이터 등록================================================




















