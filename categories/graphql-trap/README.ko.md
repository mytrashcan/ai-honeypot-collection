# GraphQL 트랩

이 서비스는 `/graphql`에서 GET 또는 JSON POST 요청을 받고 인트로스펙션 시도를
기록한 뒤 작은 합성 스키마를 반환합니다. `__schema`, `__type`, `users`,
`serviceStatus`를 인식하고 mutation은 거부합니다.

구현은 의도적으로 유한합니다. 범용 GraphQL 실행 엔진, 데이터베이스, 임의
resolver, 파일 접근 또는 외부 네트워크 호출은 없습니다. `apiKey` 필드는
유효하지 않은 `EXAMPLE` 마커만 포함합니다.

## 배포

```bash
docker compose up --detach --build
curl -s http://127.0.0.1:8083/graphql \
  -H 'Content-Type: application/json' \
  --data '{"query":"query { __schema { queryType { name } } }"}'
docker compose logs --follow
```

기본 바인딩은 `127.0.0.1:8083`입니다.

## 생성되는 신호

스키마·타입 조회에는 `graphql_introspection`, `users` 조회에는
`graphql_data_probe`, mutation 시도에는 `graphql_mutation_attempt`가
추가됩니다. 쿼리 본문 자체는 저장하지 않고 최대 64 KiB의 크기와 SHA-256
다이제스트만 기록합니다.

## 윤리와 안전

실제 사용자 데이터나 API 키를 반환하지 말고 운영 GraphQL 백엔드 또는
데이터베이스에 연결하지 마세요. 인트로스펙션은 정상적인 개발 도구도 수행할 수
있으므로 탐지 신호를 악의나 AI 사용의 증거로 취급해서는 안 됩니다. 명시적으로
허가된 격리 환경에서만 배포하세요.
