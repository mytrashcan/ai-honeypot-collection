# C2 디코이

이 서비스는 의심되는 C2 인프라를 분류하는 탐색을 연구하기 위한 비활성 HTTP
응답 형태 디코이입니다.

- 일반 GET 요청에는 정적 HTML
- 이미지 확장자에는 1픽셀 GIF
- `.woff`와 `.woff2` 경로에는 유효하지 않은 `EXAMPLE` 글꼴 마커
- POST 요청에는 본문 없는 `204 No Content`

Cobalt Strike, Sliver 또는 다른 C2 프로토콜을 구현하지 않습니다. 핸드셰이크,
작업 지시, 암호화, 메시지 디코딩, 페이로드 스테이징, 리디렉터, 콜백 기능은
없습니다.

## 배포

```bash
docker compose up --detach --build
curl -i http://127.0.0.1:8082/example.woff
docker compose logs --follow
```

기본 바인딩은 `127.0.0.1:8082`입니다.

## 생성되는 신호

상태 확인을 제외한 모든 디코이 요청에 `c2_like_probe`가 기록되며, 글꼴
확장자를 요청하면 `sliver_stager_shape_probe`가 추가됩니다. 응답에는
`X-Decoy-Safety: NO-TASKING-NO-PAYLOADS` 헤더가 포함됩니다. JSONL 이벤트는
요청 메타데이터와 제한된 본문 다이제스트만 보존합니다.

## 윤리와 안전

실제 악성 프로파일을 복제하거나 방문자에게 명령·페이로드를 전달하지 마세요.
TLS와 네트워크 흐름 지문은 별도의 허가된 인프라에서 수집해야 합니다. 관측된
응답 형태 탐색만으로 특정 공격 도구, 운영자 또는 악의적 의도를 단정하지 말고,
허가받은 격리 환경에서만 사용하세요.
