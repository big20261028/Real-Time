// 무한 스크롤 관련 전역 변수 (또는 객체로 묶기)
let currentPage;
let isLoading;
let hasNextPage;


// window.onload
$(function () {
    // 로그아웃
    $("#logoutBtn").click(function () {
        document.location = "/user/logout.do";
    });
    // 검색
    $("#searchBtn").click(function () {
        if ($("#keyword").val() == "") {
            alert("검색 키워드를 입력해주세요.");
            $("#keyword").focus();
            return;
        }
        $("#searchFrm").submit()
    });
    // 필터 셀렉트
    $('#selectForm select').on('change', function () {
      //$(this).closest('form').submit();
      $("#selectForm").submit();
    });

    // 무한 스크롤
    // 스크롤 이벤트 핸들러
    $(window).scroll(function () {
        // isLoading이 true이거나, 다음 페이지가 없거나,
        // loadMorePosts 함수가 해당 페이지에 정의되지 않았으면 실행하지 않음
        if (isLoading || !hasNextPage || typeof loadMorePosts !== 'function') {
            return;
        }

        if ($(window).scrollTop() + $(window).height() >= $(document).height() - 400) {
            // 각 페이지에 정의된 loadMorePosts 함수를 호출
            loadMorePosts();
        }
    });
});


// 태그 링크
function GoPage(tag) {
    tag = tag.replace("#", "");
    document.location = "/filters/tagboard.do?tag=" + tag;
}
// 게시글 삭제
function DoDelete(board_no, user_no) {
    if (confirm('게시글을 삭제하시겠습니까?')) {
        document.location = "/board/delete.do?board_no=" + board_no + "&user_no=" + user_no
    }
}
// 좋아요 추가,삭제
function DoLike(buttonElement, board_no) // 'buttonElement' 인자 추가
{
    $.ajax({
        url: "/like.do",
        type: 'POST',
        data: { board_no: board_no },

        success: function (data) {
            $(buttonElement).toggleClass('active');
            $("#board_like_count_" + board_no).html(data.count);
            if (data.action == 'liked') {
                // 추천 시 알람 
            }
        },

        error: function (error) {
            let errorMessage = "오류가 발생했습니다.";
            if (error.responseJSON && error.responseJSON.message) {
                errorMessage = error.responseJSON.message;
            }
            Swal.fire({
                icon: 'error', title: errorMessage,
                showConfirmButton: false, timer: 1500
            });
        }
    });
}
// 구독 추가,삭제
function DoSubscribe(event, buttonElement, categorie_no) {
    event.stopPropagation();

    $.ajax({
        url: "/subscribe.do",
        type: 'POST',
        data: { categorie_no: categorie_no },
        // 1. 진짜 성공했을 때 (HTTP 상태 코드 200)
        success: function (data) {
            // 이 블록 안에서는 data.status가 항상 'success'라고 확신할 수 있습니다.
            $(buttonElement).toggleClass('active');

            $("#categorie_sub_count_" + categorie_no).html(data.count);

            if (data.action == 'subscribed') {
                Swal.fire({
                    icon: 'success',
                    title: '구독이 완료되었습니다.',
                    showConfirmButton: false,
                    timer: 1500
                });
                $("#categorie_sub_status_" + categorie_no).html('구독 중');
            } else if (data.action == 'unsubscribed') {
                Swal.fire({
                    icon: 'success',
                    title: '구독이 취소되었습니다.',
                    showConfirmButton: false,
                    timer: 1500
                });
                $("#categorie_sub_status_" + categorie_no).html('구독하기');
            }
            // 성공 시 구독자 수 업데이트
            $("#categorie_sub_count_" + categorie_no).html(data.count)
        },
        // 2. 실패했을 때 (HTTP 상태 코드 4xx, 5xx)
        error: function (error) {
            let errorMessage = "오류가 발생했습니다.";
            if (error.responseJSON && error.responseJSON.message) {
                errorMessage = error.responseJSON.message;
            }
            Swal.fire({
                icon: 'error', title: errorMessage,
                showConfirmButton: false, timer: 1500
            });
        }
    });
}