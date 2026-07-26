# AI 지문 분석기

`analyzer.py`는 허니팟이 생성한 JSONL 이벤트를 점수화하는 오프라인
분석기입니다. 의도적으로 보수적으로 동작합니다.

- 알려진 스캐너 User-Agent와 빠른 경로 다양성은 자동화 신호입니다.
- GraphQL 및 클라우드 메타데이터 신호는 프로토콜 인식형 탐색의 신뢰도를
  높입니다.
- 자연어 카나리를 따르는 행동은 더 강한 에이전트형 신호로 취급합니다.
- 어떤 규칙도 트래픽을 특정 업체나 모델에 귀속하지 않습니다.

규칙 파일은 YAML 1.2에서 유효한 JSON 문법을 사용하므로 Python 표준
라이브러리로 파싱할 수 있습니다.

## 실행

이 카테고리는 서버를 배포하지 않습니다. 신뢰할 수 있는 분석 호스트로 내보낸
이벤트 파일을 복사한 뒤 실행하세요.

```bash
python3 analyzer.py ../../events.jsonl
python3 analyzer.py --json web.jsonl graphql.jsonl agentic.jsonl
```

## 생성되는 결과

원본 IP별로 `score`, `verdict`, `event_count`, `matched_rules`를 출력합니다.
판정은 `insufficient-evidence`, `automation-suspected`,
`agentic-automation-suspected` 중 하나입니다. 분석기는 새 네트워크 요청을
보내거나 캡처된 값의 유효성을 검사하지 않습니다.

## 윤리와 안전

점수는 수동 검토를 위한 휴리스틱 단서입니다. 스캐너를 사용하는 사람, 스크립트
크롤러, NAT, 프록시, 위조 가능한 헤더가 분류를 혼동시킬 수 있습니다. 점수만으로
개인·조직·국가·도구·AI 모델에 책임을 귀속하거나 대응 공격을 수행하지 마세요.
원본 IP와 분석 결과의 접근 권한 및 보존 기간을 제한하세요.
