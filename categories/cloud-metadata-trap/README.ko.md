# 클라우드 메타데이터 트랩

이 서비스는 다음 클라우드 인스턴스 메타데이터 프로토콜 형태를 인식합니다.

- AWS IMDS: `/latest/api/token`, `/latest/meta-data/...`
- GCP: `/computeMetadata/v1/...`와 `Metadata-Flavor: Google`
- Azure: `/metadata/instance...`와 `Metadata: true`

응답에는 유효하지 않은 `EXAMPLE` ID와 자격 증명만 포함됩니다.

## 배포

```bash
docker compose up --detach --build
curl -H 'Metadata-Flavor: Google' \
  http://127.0.0.1:8084/computeMetadata/v1/project/project-id
docker compose logs --follow
```

기본 바인딩은 `127.0.0.1:8084`입니다.

## 생성되는 신호

공급자별 경로 접근에는 각각 `aws_metadata`, `gcp_metadata`,
`azure_metadata`가 기록됩니다. 역할 자격 증명이나 토큰 형태를 요청하면
`cloud_credential_probe`도 추가됩니다. GCP와 Azure 경로는 요구되는 프로토콜
헤더의 존재를 응답 상태로 구분하지만 헤더 값은 로그에 저장하지 않습니다.

## 윤리와 안전

이 서비스를 실제 링크 로컬 메타데이터 주소 `169.254.169.254`에 바인딩하거나
운영 호스트의 경로를 변경해서는 안 됩니다. 실제 클라우드 인스턴스 ID 또는 IAM
역할을 부여하지 마세요. SSRF 라우팅 테스트는 완전히 격리된 실습 환경에서만
수행하고, 허가받지 않은 시스템을 대상으로 요청을 유도하지 마세요.
