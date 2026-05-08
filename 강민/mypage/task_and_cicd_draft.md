# 강민 마이페이지 Task 및 CI/CD 기준 초안

담당자: 강민  
담당 기능: 마이페이지  
기준일: 2026-05-07

## 주차별 Task

| 주차 | 작업 | 산출물 | 상태 |
|---|---|---|---|
| 1주차 | 마이페이지 1차 기능명세서 검토 | `feature_spec_review.md` | 완료 |
| 1주차 | 마이페이지 ERD 초안 작성 | `erd_draft.md` | 완료 |
| 1주차 | 마이페이지 v1 아키텍처 초안 작성 | `architecture_v1_draft.md` | 완료 |
| 1주차 | 마이페이지 정적 프론트 mock 구현 | `index.html`, `styles.css`, `app.js` | 완료 |
| 2주차 | 백엔드 API 명세 확정 | API request/response 문서 | 예정 |
| 2주차 | 마이페이지 API 구현 | Controller/Service/Repository | 예정 |
| 2주차 | 프론트 API 연동 | mock 제거, fetch 연동 | 예정 |
| 3주차 | 인증/인가 검증 | 본인 데이터 접근 테스트 | 예정 |
| 3주차 | 통합 테스트 및 PR | 테스트 결과, PR | 예정 |

## 강민 담당 기능 완료 기준

- 마이페이지 메인에서 사용자 요약 정보가 보인다.
- 내 정보 조회/수정이 가능하다.
- 주문 목록과 주문 상세가 연결된다.
- 찜 목록 조회와 찜 삭제가 가능하다.
- 최근 본 상품 목록이 보인다.
- 로그인하지 않은 사용자는 마이페이지 API에 접근할 수 없다.
- 다른 사용자의 주문 상세는 조회할 수 없다.

## CI/CD 설계 제안

팀 공통 GitHub Actions 기준으로 아래를 제안한다.

| 기준 | 제안 |
|---|---|
| 동작 브랜치 | `main`, 각자 담당 브랜치, PR 대상 브랜치 |
| PR 기준 | PR 생성/수정 시 build, test, lint 실행 |
| merge 기준 | GitHub Actions 통과 + 리뷰 승인 후 merge |
| 배포 조건 | `upstream main` merge 후 수동 또는 태그 기반 배포 |
| 실패 시 처리 | 실패한 job 로그 확인 후 수정 commit push |

## 마이페이지 CI 체크 항목

- 정적 프론트 파일 존재 확인
  - `강민/mypage/index.html`
  - `강민/mypage/styles.css`
  - `강민/mypage/app.js`
- JavaScript 문법 검사
  - `node --check 강민/mypage/app.js`
- 추후 앱 통합 후 추가할 항목
  - 프론트 lint
  - 백엔드 test
  - API 통합 테스트
  - 빌드 산출물 생성 확인

## GitHub Actions 동작 기준 초안

```yaml
name: mypage-check

on:
  pull_request:
    branches: [main]
  push:
    branches: [mypage, main]

jobs:
  static-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Check mypage files
        run: |
          test -f "강민/mypage/index.html"
          test -f "강민/mypage/styles.css"
          test -f "강민/mypage/app.js"
      - name: Check JavaScript syntax
        run: node --check "강민/mypage/app.js"
```

## 팀 검토 필요

- 개인 브랜치명은 `mypage`처럼 기능명 기준으로 둘지, `name/feature` 형식으로 통일할지 결정 필요
- PR 대상 브랜치를 각자 이름 브랜치로 둘지, 바로 `main`으로 둘지 팀 규칙 확인 필요
- 배포는 v1에서 수동 배포로 시작할지, main merge 자동 배포까지 할지 결정 필요

## 2026-05-07 추가 Task

- 결제 내역 조회 mock API 추가 완료
- 결제 상세 조회 mock API 추가 완료
- 마이페이지 Payments 탭 추가 완료
- 주문 상세의 결제/취소 액션 진입점 추가 완료
- CI 체크 대상에 `mypage_mock_server.js` 문법 검사를 포함해야 함
