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

| 카테고리 | 한국어 문서 | 역할 |
| --- | --- | --- |
| 웹 스캐너 트랩 | [문서](../categories/web-scanner-trap/README.ko.md) | 고가치 웹 경로와 한국어 관리 경로 디코이 |
| 자격 증명 허니 | [문서](../categories/credential-honey/README.ko.md) | 합성 자격 증명 파일과 한국어 설정 파일 |
| C2 디코이 | [문서](../categories/c2-decoy/README.ko.md) | 안전한 C2 유사 HTTP 응답 형태 |
| GraphQL 트랩 | [문서](../categories/graphql-trap/README.ko.md) | 유한한 읽기 전용 GraphQL 응답 |
| 클라우드 메타데이터 트랩 | [문서](../categories/cloud-metadata-trap/README.ko.md) | AWS·GCP·Azure 프로토콜 카나리 |
| 에이전트형 루어 | [문서](../categories/agentic-lure/README.ko.md) | 영어·한국어 자연어 지시 카나리 |
| AI 지문 분석기 | [문서](../categories/ai-fingerprint/README.ko.md) | JSONL 이벤트의 보수적 오프라인 분석 |

## 운영 전 확인

모든 서비스는 기본적으로 루프백에 바인딩되지만, 공개 배포에는 별도의 승인,
네트워크 격리, 외부 통신 차단, 개인정보 최소 수집, 접근 제어 및 보존 정책이
필요합니다. 규칙 일치는 자동화나 에이전트형 행동의 연구 신호일 뿐 악의, 국적,
특정 AI 모델 사용을 증명하지 않습니다.
