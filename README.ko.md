# AI 허니팟 컬렉션

`ai-honeypot-collection`은 자동화된 보안 정찰과 AI 지원 보안 정찰을 연구하기
위한 안전하고 관측 가능한 HTTP 디코이 모음입니다. 각 서비스는 스캐너가
우선적으로 탐색하는 경로를 무해한 형태로 제공하고, 요청 메타데이터를 JSONL로
기록하며, 명백하게 합성된 데이터만 반환합니다.

이 저장소는 방어 목적의 연구 인프라입니다. 익스플로잇 전달, 자격 증명 검증,
명령 실행, C2 작업 지시 또는 실제 비밀 정보는 포함하지 않습니다.

## 🌐 언어

- [English](README.md)
- [한국어](README.ko.md)

## AI 중심 허니팟이 필요한 이유

현대의 보안 에이전트는 모델 기반 계획 수립 기능을 브라우저, 셸, 기존 스캐너와
결합합니다. 기반 도구는 여전히 `/.env`, `/actuator`, `/graphql`, 클라우드
메타데이터 경로와 같은 익숙한 자산을 열거하지만, 에이전트는 응답에 따라 다음
행동을 조정하고, 유망한 분기를 다시 방문하거나, 자연어 지시를 따를 수 있습니다.

한국 환경에서도 기업·공공기관의 한국어 웹 서비스, 국내 클라우드 운영 환경,
한국어 파일명과 관리 페이지가 자동 스캔의 대상이 될 수 있습니다. 한국어
디코이는 이러한 현지화된 탐색 행동을 관측하는 데 도움을 주지만, 언어나 요청
형태만으로 공격자의 국적·소재지·의도를 단정해서는 안 됩니다.

어떤 HTTP 요청도 LLM이 생성했다는 사실을 증명할 수 없습니다. 따라서 이
프로젝트는 다음을 구분합니다.

- 알려진 스캐너 User-Agent와 짧은 시간 동안의 다양한 경로 접근 같은
  **자동화 증거**
- 무해한 지시 카나리를 따르는 행동 같은 **에이전트형 증거**
- 외부 증거 없이는 의도적으로 결론 내리지 않는 **귀속**

이 모델의 근거와 한계는 [연구 검토 문서(영문)](docs/ai-tools-research.md)를
참고하세요.

## 카테고리

| 카테고리 | 목적 | 기본 포트 |
| --- | --- | ---: |
| [`web-scanner-trap`](categories/web-scanner-trap/README.ko.md) | API, Spring Actuator, WordPress, Git, 환경 파일, API 문서 및 한국어 경로 디코이 | `8080` |
| [`credential-honey`](categories/credential-honey/README.ko.md) | 명백히 가짜인 환경 파일, 클라우드 자격 증명, SSH 키 및 한국어 설정 파일 | `8081` |
| [`token-drain-maze`](categories/token-drain-maze/README.ko.md) | AI 봇의 토큰을 고갈시키는 가짜 취약점의 끝없는 미로 | `8081` |
| [`c2-decoy`](categories/c2-decoy/README.ko.md) | C2 지문 식별 연구를 위한 비활성 HTTP 응답 형태 | `8082` |
| [`graphql-trap`](categories/graphql-trap/README.ko.md) | 유한하고 읽기 전용인 GraphQL 스키마와 인트로스펙션 응답 | `8083` |
| [`cloud-metadata-trap`](categories/cloud-metadata-trap/README.ko.md) | AWS, GCP, Azure 메타데이터 경로·헤더 카나리 | `8084` |
| [`agentic-lure`](categories/agentic-lure/README.ko.md) | 한국어를 포함한 무해한 자연어 지시 이행 카나리 | `8085` |
| [`mcp-server-trap`](categories/mcp-server-trap/README.md) | 비활성 MCP 발견, 도구, 리소스, 프롬프트 픽스처 | `8086` |
| [`a2a-agent-trap`](categories/a2a-agent-trap/README.md) | 고정된 Agent Card, 메시지, 작업 프로토콜 픽스처 | `8087` |
| [`vector-store-trap`](categories/vector-store-trap/README.md) | 읽기 전용 벡터 저장소 열거 및 결정론적 랭킹 픽스처 | `8088` |
| [`rag-pipeline-trap`](categories/rag-pipeline-trap/README.md) | 드라이런 수집, 검색, 재순위화, 작업 픽스처 | `8089` |
| [`model-registry-trap`](categories/model-registry-trap/README.md) | MLflow, Ollama, OCI 모델 메타데이터 픽스처 | `8090` |
| [`llm-gateway-trap`](categories/llm-gateway-trap/README.md) | 고정된 OpenAI·Ollama 호환 게이트웨이 응답 | `8091` |
| [`browser-workflow-trap`](categories/browser-workflow-trap/README.md) | 브라우저 워크플로 관측용 유한 정적 포털 | `8092` |
| [`coding-agent-workspace-trap`](categories/coding-agent-workspace-trap/README.md) | 합성 에이전트 지시문, 매니페스트, 소스 코드, 테스트 파일 | `8093` |
| [`reverse-jailbreak-trap`](categories/reverse-jailbreak-trap/README.md) | 에이전트 행동과 맹목적 크롤링을 구분하기 위한 합성 안전 인터록 중단 프롬프트 | `8094` |
| [`ai-fingerprint`](categories/ai-fingerprint/README.ko.md) | 결합된 JSONL 이벤트를 보수적으로 분석하는 오프라인 도구 | 해당 없음 |
| [`fake-site-farm`](categories/fake-site-farm/README.ko.md) | 모든 배포 가능 카테고리의 스캐너 탐지용 미끼를 결합한 정교한 정적 회사 사이트 | 해당 없음 |

> **참고:** `credential-honey`와 `token-drain-maze`는 모두 기본적으로
> `8081` 포트를 사용합니다. 두 서비스를 동시에 실행하기 전에 한 서비스의
> 호스트 포트를 변경하세요.

배포 가능한 마지막 두 카테고리는 연구 결과를 바탕으로 추가되었습니다. 클라우드
메타데이터 탐색에는 제공자별 프로토콜 신호가 있으며, 프롬프트를 따르는 행동은
고정된 단어 목록 기반 스캐너보다 에이전트에 더 특화된 몇 안 되는 관측 항목 중
하나입니다.

## 벤치마크

다음 추정치는 `token-drain-maze`가 AI 봇의 자원을 얼마나 낭비시킬 수 있는지
보여 줍니다. 비용은 GPT-4o 또는 Claude Sonnet의 입력 토큰 100만 개당 약
$3-15인 요금을 기준으로 하며, 실제 사용량은 모델, 에이전트 행동, 요청 제한에
따라 달라집니다.

| 지표 | 추정치 | 참고 |
| --- | --- | --- |
| **응답 크기** | 엔드포인트당 약 500-2000자 | 요청당 125-500토큰 |
| **히드라 엔드포인트 폭증** | 3^n개 경로 (n=1..20) | 깊이 20에서 이론상 약 34.9억 개 경로, 실제 봇은 일반적으로 50-200회 요청으로 제한 |
| **단일 봇 세션 비용** | 시간당 $0.50-5.00 | 약 1,000회 요청의 입력 및 출력 토큰 기준 |
| **토큰 집약형 페이로드** | 요청당 10KB = 약 2,500토큰 | AI가 Base64 blob의 디코딩 및 분석을 시도 |
| **타핏 시간 낭비** | 청크당 0.5-3초 | 봇 연결을 열린 상태로 유지해 소켓 및 타임아웃 예산 소모 |
| **변이형 탐색** | 경로당 최대 10개의 취약점 | 봇이 같은 경로를 여러 번 다시 분석 |

## 빠른 시작

각 허니팟은 독립적으로 배포할 수 있습니다. Docker Compose는 기본적으로
루프백 주소에 바인딩합니다.

```bash
cd categories/web-scanner-trap
docker compose up --detach --build
curl http://127.0.0.1:8080/.env
docker compose logs --follow
```

이벤트는 서비스의 명명된 Docker 볼륨에 있는 `/data/events.jsonl`에 추가되고
표준 출력에도 동일하게 기록됩니다. 내보낸 로그는 다음과 같이 분석합니다.

```bash
python3 categories/ai-fingerprint/analyzer.py events.jsonl
python3 categories/ai-fingerprint/analyzer.py --json events.jsonl
```

로컬 실습 환경 밖에 서비스를 노출하기 전에는
[배포 가이드(영문)](docs/deployment-guide.md)를 반드시 읽으세요. 한국어 문서
목록과 카테고리별 안내는 [한국어 문서 홈](docs/index.ko.md)에서 확인할 수
있습니다.

## 로깅 모델

상태 확인 요청을 제외한 모든 요청은 다음 항목을 기록합니다.

- UTC 타임스탬프와 무작위 이벤트 ID
- 소켓 원본 IP와 전달된 IP 헤더의 존재 여부
- 메서드, 경로, 쿼리 매개변수의 **이름**, 엔드포인트, 응답 상태
- 선택된 콘텐츠 메타데이터와 헤더의 **이름**
- 제출 본문 대신 제한된 본문 크기와 SHA-256 다이제스트
- `graphql_introspection`과 같이 안전하게 경로에서 파생된 신호

Authorization 값, 쿠키, 쿼리 값, 요청 본문은 저장하지 않습니다. 운영자는
고지, 보존 기간, 접근 제어, 대한민국의 개인정보 보호 관련 법령을 포함한 현지
법률 준수에 대한 책임이 있습니다.

## 안전 속성

- 자격 증명처럼 보이는 모든 값은 `EXAMPLE`로 시작하거나, 유효하지 않은 문법
  또는 예약된 `.invalid` 도메인을 사용합니다.
- 컨테이너는 UID/GID `10001`로 실행되고, 읽기 전용 루트 파일 시스템을
  사용하며, 모든 Linux capability를 제거하고, `no-new-privileges` 및
  메모리/PID 제한을 설정합니다.
- 운영자가 배포 설정을 의도적으로 변경하지 않는 한 포트는 `127.0.0.1`에
  바인딩됩니다.
- C2 디코이는 메시지를 디코딩하거나 페이로드를 준비하거나 작업을 지시하지
  않습니다.
- GraphQL은 유한하며 mutation을 지원하지 않습니다.
- 요청 본문은 64 KiB로 제한됩니다.

## 개발

Python 3.11 이상이 필요합니다.

```bash
ruff check .
python3 -m unittest discover -s tests -v
python3 -m compileall -q honeypot_common categories tests
for file in categories/*/docker-compose.yml; do
  docker compose -f "$file" config --quiet
done
```

FastAPI가 설치되어 있으면 서비스 스모크 테스트가 실행됩니다. 설치되어 있지
않으면 로컬에서는 건너뛰고 CI에서 실행합니다.

## 윤리적 사용

본인이 소유하거나 모니터링 권한을 명시적으로 부여받은 시스템과 주소 공간에만
배포하세요. 제3자를 사칭하거나, 불필요한 개인정보를 수집하거나, 디코이를 운영
비밀 정보에 연결하거나, 관측 결과를 방문자 공격에 사용해서는 안 됩니다.
서비스를 격리하고, 불필요한 외부 통신을 차단하고, 보존 정책을 공개하며, 원본
IP를 잠재적인 개인정보로 취급하세요.

대한민국에서 운영할 때는 개인정보 보호법, 통신 관련 법령, 조직의 내부 보안
정책과 근로자·이용자 고지 의무를 사전에 검토하세요. 수집을 최소화하고 목적과
보존 기간을 문서화하며, 법률 자문이 필요한 경우 배포 전에 받으세요.

이 저장소는 IDS, WAF, 사고 대응 프로그램 또는 법률 검토를 대체하지 않습니다.
규칙 일치는 연구 신호일 뿐 악의적 의도나 AI 작성 여부를 증명하지 않습니다.

## 라이선스

MIT
