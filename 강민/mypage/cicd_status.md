# CI/CD 적용 상태

기준일: 2026-05-15

## 완료

- GitHub Actions CI workflow 추가
  - 파일: `.github/workflows/ci.yml`
  - PR 생성/수정 시 마이페이지, 데이터 스크립트, 문서 체크 실행
  - `main`, `mypage`, `Crawling`, `강민` 브랜치 push 시 실행
  - 수동 실행(`workflow_dispatch`) 가능

- 마이페이지 프론트/목업 API 체크 추가
  - 필수 파일 존재 확인
  - `강민/mypage/app.js` 문법 검사
  - `mypage_mock_server.js` 문법 검사
  - 목업 서버 실행 후 `/api/mypage/summary`, `/orders`, `/wishlist` smoke test

- 데이터 크롤링/DB 스크립트 체크 추가
  - 무신사/29CM 크롤러 Python 문법 검사
  - CSV 정제 스크립트 문법 검사
  - DB import/benchmark 스크립트 문법 검사
  - 존재하는 CSV의 공통 스키마 컬럼 검증

- 필수 문서 체크 추가
  - 기능명세서 검토
  - ERD 초안
  - 아키텍처 v1 초안
  - Task 및 CI/CD 기준 문서
  - PostgreSQL/MySQL 벤치마크 README

- GitHub Pages 배포 workflow 추가
  - 파일: `.github/workflows/deploy-mypage.yml`
  - `main` 브랜치에 마이페이지 변경이 merge되면 정적 프리뷰 배포
  - 수동 실행 가능

## 아직 팀 확인 필요

- GitHub Pages 사용 여부와 repository Pages 설정
- upstream PR 대상 브랜치가 `main`인지 각자 이름 브랜치인지
- CI 통과를 merge 필수 조건으로 branch protection에 등록할지 여부
- 실제 백엔드/프론트 통합 후 lint, test, build 명령어 확정

## 현재 결론

CI/CD 설계 초안은 문서에서 실제 GitHub Actions workflow로 옮겨졌다.
다만 GitHub Pages 배포는 저장소 설정에서 Pages 사용이 켜져 있어야 실제 배포 URL이 생성된다.
