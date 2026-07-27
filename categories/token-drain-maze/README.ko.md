# 토큰 드레인 메이즈

토큰 드레인 메이즈는 자동화된 재귀 탐색 행동을 관찰하기 위한 합성 FastAPI
허니팟입니다. 다음 일곱 가지 트랩 전략을 유한하고 비활성인 응답으로
구현합니다.

1. **히드라 패턴(Hydra Pattern)** — 일반 경로마다 합성 하위 경로 세 개를
   제공하며, 설정된 최대 깊이에서 확장을 멈춥니다.
2. **변이 응답(Mutating Response)** — 같은 세션이 같은 경로를 반복 요청하면
   서로 다른 예시 취약점을 반환합니다.
3. **로직 루프(Logic Loop)** — `/config.json`, `/internal/db-config`,
   `/secrets/database`가 두 개의 JSON 참조와 한 번의 리디렉션으로 서로를
   가리킵니다.
4. **토큰 집약 페이로드(Token-Intensive Payload)** — 경로에 `dump`, `backup`,
   `export`가 포함되면 10 KiB 크기의 의사 base64 디코이 페이로드를
   반환합니다.
5. **프롬프트 인젝션 트랩(Prompt Injection Trap)** — HTML 경로나 `html`,
   `page` 쿼리 매개변수가 있는 요청에 합성 숨김 지시문을 넣습니다.
6. **프로토콜 타핏(Protocol Tarpit)** — `slow` 또는 `tarpit` 쿼리 매개변수가
   있는 요청을 의도적으로 지연해 스트리밍합니다.
7. **신뢰도 퍼널(Credibility Funnel)** — API, 백업, 키, 비밀 파일처럼 보이는
   다섯 경로가 명시적으로 가짜인 유한 체인을 구성합니다.

비밀처럼 보이는 모든 값은 `EXAMPLE`로 시작합니다. 이 서비스는 호스트의
자격 증명을 읽거나, 제출된 내용을 실행하거나, 실제 백엔드를 노출하지
않습니다. `/healthz`를 제외한 요청은 공통 개인정보 보호형 추적기를 통해
`/data/events.jsonl`과 표준 출력에 기록됩니다.

## 실행

이 디렉터리에서 다음 명령을 실행합니다.

```bash
docker compose up --detach --build
curl http://127.0.0.1:8081/
curl http://127.0.0.1:8081/config.json
curl http://127.0.0.1:8081/api/v1/users
docker compose logs --follow
```

기본 바인딩 주소는 `127.0.0.1:8081`입니다. `MAZE_MAX_DEPTH`,
`MAZE_TARPIT_MIN_MS`, `MAZE_TARPIT_MAX_MS`로 메이즈 깊이와 타핏 지연 범위를
설정할 수 있습니다. 공개 배포는 격리된 역방향 프록시 뒤에 두고, 본인이
소유하거나 명시적으로 허가받은 주소 공간에서만 운영하세요.

## 모든 전략 검증

저장소 루트에서 새 이미지를 빌드하고 실행합니다.

```bash
docker compose -f categories/token-drain-maze/docker-compose.yml build --no-cache
docker compose -f categories/token-drain-maze/docker-compose.yml up --detach
```

진입 경로, 일곱 가지 트랩 전략, 헬스체크를 모두 실행합니다.

```bash
curl -s http://127.0.0.1:8081/api/v1/users
curl -s http://127.0.0.1:8081/admin/config
curl -s http://127.0.0.1:8081/secrets/aws.json
curl -s http://127.0.0.1:8081/config.json
curl -s http://127.0.0.1:8081/.env
curl -s http://127.0.0.1:8081/.env
curl -s http://127.0.0.1:8081/backup/dump | wc -c
timeout 5 curl -s 'http://127.0.0.1:8081/api/v1/users?slow=true' | wc -c
curl -s 'http://127.0.0.1:8081/page.html?html=true' | head -5
curl -s http://127.0.0.1:8081/healthz
```

응답에는 유한한 신뢰도 체인, 히드라 하위 경로 세 개, 명시적으로 가짜인
종단 비밀 응답, 로직 루프의 다음 참조가 나타나야 합니다. `/.env`를 반복
요청하면 변이 데이터가 달라져야 합니다. 덤프 응답은 10,000바이트보다 커야
하며, 무작위 지연이 적용되는 타핏은 `timeout` 종료 전까지 일부 본문만
반환하거나 0바이트를 반환할 수 있습니다. HTML 응답에는
`EXAMPLE AI instruction` 주석이 포함되어야 하고, 헬스체크는
`{"status":"ok"}`를 반환해야 합니다.

검증 후 컨테이너를 중지하고 제거합니다.

```bash
docker compose -f categories/token-drain-maze/docker-compose.yml down
```

## 안전과 해석

트랩에서 생성된 신호만으로 방문자가 악의적이거나 AI 기반이라고 단정할 수
없습니다. 재귀 요청, 반복 접근, 느린 스트림 처리는 일반 스캐너나 테스트
클라이언트에서도 발생할 수 있습니다. 원본 주소와 요청 메타데이터를 잠재적인
개인정보로 취급하고, 배포 전에 로그 접근 제한과 보존 정책을 정하세요.
