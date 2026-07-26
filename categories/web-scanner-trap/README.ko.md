# 웹 스캐너 트랩

이 FastAPI 서비스는 콘텐츠 탐색 도구, 취약점 템플릿, 보안 에이전트가 자주
우선 탐색하는 경로의 비활성 버전을 제공합니다.

- `/api/v1/`, `/api/v1/users`와 한국어 경로 `/api/v1/사용자`
- `/actuator`, `/actuator/health`, `/actuator/env`
- `/graphql`
- `/.env`, `/.git/config`
- `/wp-admin`, `/wp-login.php`
- `/openapi.json`, `/swagger.json`, `/swagger-ui`, `/docs`
- 한국어 관리 경로 `/관리자`, `/관리/로그인`, `/상태`

모든 응답에는 `EXAMPLE`로 표시된 합성 데이터만 포함됩니다. 상태 확인용
`/healthz`를 제외한 요청은 `/data/events.jsonl`과 표준 출력에 기록됩니다.

## 배포

```bash
docker compose up --detach --build
curl http://127.0.0.1:8080/actuator/env
curl http://127.0.0.1:8080/%EA%B4%80%EB%A6%AC%EC%9E%90
docker compose logs --follow
```

기본 포트는 `127.0.0.1:8080`입니다. 외부에 노출하기 전에는 저장소의
[배포 가이드](../../docs/deployment-guide.md)에 따라 전용 네트워크와 역방향
프록시를 구성하세요.

## 생성되는 신호

요청한 경로에 따라 `api_version_probe`, `spring_actuator_probe`,
`credential_file_probe`, `graphql_introspection`, `source_control_probe`,
`wordpress_admin_probe`, `api_schema_probe`, `admin_panel_probe`,
`korean_localized_probe` 같은 신호가 이벤트에 추가됩니다. 공통 로거는 원본 IP,
요청 메서드와 경로, 쿼리 키 이름, 응답 상태, User-Agent, 본문 크기와
다이제스트를 기록하지만 요청 본문·쿠키·Authorization 값은 저장하지 않습니다.

## 윤리와 안전

이 서비스는 인증, 업무 로직, 파일 접근 또는 실제 익스플로잇 대상을 구현하지
않습니다. 한국어 경로 접근은 현지화된 탐색의 단서일 수 있지만 방문자의 국적,
소재지, 악의 또는 AI 사용을 증명하지 않습니다. 본인이 소유하거나 명시적으로
허가받은 주소 공간에서만 격리해 운영하고, 원본 IP를 잠재적인 개인정보로
취급하세요.
