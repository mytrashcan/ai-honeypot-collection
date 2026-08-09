# AI 허니팟 컬렉션 한국어 문서

안전하고 관측 가능한 HTTP 디코이를 사용해 자동화 및 AI 지원 보안 정찰을
연구하기 위한 한국어 문서 모음입니다.

## 시작하기

- [프로젝트 README](../README.ko.md): 목적, 연구 모델, 빠른 시작, 로깅과
  안전 원칙
- [배포 가이드(영문)](deployment-guide.md): 로컬·공개 배포 경계, 이벤트
  저장, 사고 대응
- [연구 검토 문서(영문)](ai-tools-research.md): AI 지원 스캔 신호의 근거와
  한계
- [English documentation](../README.md)

## 카테고리

| 카테고리 | 문서 | 역할 |
| --- | --- | --- |
| 웹 스캐너 트랩 | [문서](../categories/web-scanner-trap/README.ko.md) | 고가치 웹 경로와 한국어 관리 경로 디코이 |
| 자격 증명 허니 | [문서](../categories/credential-honey/README.ko.md) | 합성 자격 증명 파일과 한국어 설정 파일 |
| GraphQL 트랩 | [문서](../categories/graphql-trap/README.ko.md) | 유한한 읽기 전용 GraphQL 응답 |
| 클라우드 메타데이터 트랩 | [문서](../categories/cloud-metadata-trap/README.ko.md) | AWS·GCP·Azure 프로토콜 카나리 |
| 에이전트형 루어 | [문서](../categories/agentic-lure/README.ko.md) | 영어·한국어 자연어 지시 카나리 |
| MCP 서버 트랩 | [영문](../categories/mcp-server-trap/README.md) | 비활성 도구·리소스·프롬프트 프로토콜 픽스처 |
| A2A 에이전트 트랩 | [영문](../categories/a2a-agent-trap/README.md) | 고정된 에이전트 카드·메시지·작업 픽스처 |
| 벡터 저장소 트랩 | [영문](../categories/vector-store-trap/README.md) | 읽기 전용 열거 및 결정론적 검색 결과 |
| 모델 레지스트리 트랩 | [영문](../categories/model-registry-trap/README.md) | 모델 메타데이터·매니페스트 탐색 디코이 |
| LLM 게이트웨이 트랩 | [영문](../categories/llm-gateway-trap/README.md) | 고정 응답만 제공하는 추론 API 형태 디코이 |
| 코딩 에이전트 작업공간 트랩 | [영문](../categories/coding-agent-workspace-trap/README.md) | 합성 지시문·소스·테스트 후속 탐색 |
| 패키지 레지스트리 트랩 | [영문](../categories/registry-trap/README.md) | 비활성 패키지·컨테이너 레지스트리 표면 |
| Git 원격 저장소 트랩 | [영문](../categories/git-remote-trap/README.md) | 복제·시크릿 파일 후속 접근 신호 |
| OAuth/SSO 트랩 | [영문](../categories/oauth-sso-trap/README.md) | 인증·디바이스 코드·토큰 교환 시도 |
| 아카이브 크랙 트랩 | [영문](../categories/archive-crack-trap/README.md) | 레거시 암호화·알려진 평문·암호 시도 루어 |
| 세션 쿠키 트랩 | [영문](../categories/session-cookie-trap/README.md) | CBC 형태 쿠키 변조·관리자 후속 접근 신호 |
| 링크 미리보기·검색 트랩 | [영문](../categories/link-preview-search-trap/README.md) | 외부 요청 없는 SSRF·블라인드 SQLi 형태 루어 |
| 비밀 금고 트랩 | [영문](../categories/secrets-vault-trap/README.md) | 상태 없는 복구 추측·부분 진행 응답 |
| 스크립트 드롭 트랩 | [영문](../categories/script-drop-trap/README.md) | 부작용 없는 스크립트 다운로드·실행 형태 제출 |
| AI 지문 분석기 | [문서](../categories/ai-fingerprint/README.ko.md) | JSONL 이벤트의 보수적 오프라인 분석 |

## 운영 전 확인

모든 서비스는 기본적으로 루프백에 바인딩되지만, 공개 배포에는 별도의 승인,
네트워크 격리, 외부 통신 차단, 개인정보 최소 수집, 접근 제어 및 보존 정책이
필요합니다. 규칙 일치는 자동화나 에이전트형 행동의 연구 신호일 뿐 악의, 국적,
특정 AI 모델 사용을 증명하지 않습니다.
