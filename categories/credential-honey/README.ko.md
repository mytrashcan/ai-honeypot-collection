# 자격 증명 허니

이 서비스는 자격 증명 수집기가 찾는 파일 이름의 조회를 기록합니다.

- `/.env`, `/.env.production`, `/config/.env`
- `/config.json`, `/credentials.json`
- 한국어 파일명 `/.환경`, `/설정.json`, `/설정/.환경`, `/설정/설정.json`,
  `/자격증명.json`
- `/.aws/credentials`
- `/.ssh/id_rsa`

모든 값은 의도적으로 유효하지 않으며 눈에 띄게 `EXAMPLE` 접두사를 사용합니다.
어떤 공급자에도 요청하지 않고 토큰을 검증하지 않으며, 사용 가능한 키 자료를
포함하지 않습니다.

## 배포

```bash
./deploy.sh
curl http://127.0.0.1:8081/.env
curl http://127.0.0.1:8081/%EC%84%A4%EC%A0%95.json
docker compose logs --follow
```

`deploy.sh`는 빌드 전에 합성 추적 마커를 확인합니다. 로컬 Compose 프로젝트만
시작하며 기존 웹 루트로 파일을 복사하지 않습니다. 기본 바인딩은
`127.0.0.1:8081`입니다.

## 생성되는 신호

환경 파일에는 `credential_file_probe`와 `environment_file_probe`, JSON
설정 파일에는 `credential_file_probe`와 `cloud_credential_probe`, SSH 키
경로에는 `ssh_key_probe`가 추가됩니다. 한국어 파일명에는
`korean_localized_probe`도 추가됩니다. 공통 요청 메타데이터는 JSONL과 표준
출력에 기록되며 제출된 본문과 민감한 헤더 값은 저장하지 않습니다.

## 윤리와 안전

실제 자격 증명을 디코이에 넣거나 운영 시스템의 비밀 저장소, 홈 디렉터리,
클라우드 IAM 역할에 연결하지 마세요. 방문자가 제출한 값을 검증하거나 다른
서비스에 재사용해서도 안 됩니다. 허가받은 환경에서만 운영하고, 접근 로그의
보존 기간과 접근 권한을 최소화하세요.
