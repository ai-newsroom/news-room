# Cordis AI 특별판 편집 브리프

## 주제와 중심 질문

2026년 8월 13일 공개된 active-revision preprint `A Programming Paradigm for
Spatiotemporal Composability`와 구현체 Cordis를 다룬다. DeepSeek Harness가 Cordis를
기반으로 삼은 관계를 확인하고, 앱을 작은 플러그인과 명시적 의존성, 되돌릴 수 있는
변경으로 구성하면 AI의 유지보수에 어떤 이점이 생기는지 분석한다.

중심 결론은 다음 범위로 제한한다.

> AI가 더 좁은 범위를 이해하고 시험·교체·복구하는 데 유리한 구조이지만, Cordis 자체가
> 개선안을 고르거나 스스로 학습하는 자기개선 엔진은 아니다.

## 제목과 도입부

다음과 같은 뉴스형 제목을 우선 검토한다.

> DeepSeek·베이징대 연구진, 실행 중 앱 부품을 바꾸는 ‘Cordis’ 설계 공개

첫 세 문단은 `누가 무엇을 공개했나 → 실행 중 플러그인 교체가 AI 유지보수에 왜
중요한가 → 자율 자기개선 자체는 아직 검증되지 않았다는 경계` 순서로 쓴다. 제목에
프리프린트 상태와 모든 면책 문구를 밀어 넣지 말고 summary와 한계 절에서 설명한다.

## 독자가 이해해야 할 구조

- Cordis는 단순히 플러그인 안에 플러그인을 중첩하는 구조가 아니다. 소유권과 정리 범위를
  나타내는 Context 트리, 서비스 제공자와 소비자를 잇는 의존성 그래프, 컴포넌트 생명주기,
  등록한 효과를 역순으로 회수하는 장치가 함께 작동한다.
- `temporal composability`는 부품을 제거할 때 그 부품이 만든 변경을 회수하는 능력,
  `spatial composability`는 서비스가 생기거나 사라질 때 의존 부품을 재조정하는 능력으로
  쉬운 한국어를 먼저 제시한다.
- `effect`는 컴포넌트가 환경에 만든 변경, `coeffect`는 환경에서 요구하는 서비스·조건이다.
  listener나 service를 등록하고 교체하는 구체적인 장면 뒤에 용어를 붙인다.
- LLM의 `자기회귀`, 하위 컴포넌트를 만드는 `재귀적 구성`, 에이전트가 도구를 바꾸는
  `자기변형·자기진화`를 서로 구분한다.

## AI 유지보수 관점

- AI가 거대한 앱 전체가 아니라 플러그인 하나와 명시된 계약에 집중할 수 있는가.
- 의존성 그래프로 변경 영향 범위를 좁히고 같은 인터페이스의 구현을 비교 시험할 수 있는가.
- context를 통해 등록한 listener, resource, service의 역순 회수가 rollback의 토대가 되는가.
- 현재 플러그인 트리, 서비스, 의존 관계와 lifecycle 상태를 구조화해 AI에 보여 줄 때
  자연어 문서만 읽는 것보다 유지보수 판단이 쉬워지는가.
- 권한, sandbox, 감사, 검증, rollback은 작은 안정 코어에 두고, 도구·모델 adapter·workflow
  같은 외곽만 AI가 교체하도록 나누는 것이 왜 안전한가.

## 반드시 밝힐 한계

한계는 한 절에서 한 번 분명히 설명하고 같은 경고를 여러 절에서 반복하지 않는다.

- 논문은 2026년 8월 13일자 active-revision preprint다. arXiv, DOI, 학회 게재와 동료평가
  여부는 발행 시점에 다시 확인한다.
- 형식 모델은 보존, 복구 정확성, 의존 순서, 진행성과 합류성을 다루지만 inverse의 정확성,
  독립성·비순환성 같은 전제가 있다. runtime이 작성자의 inverse를 자동 증명하지 않는다.
- context 밖으로 이미 보낸 network message, 결제, 외부 공유 파일은 자동 rollback 대상이
  아니며 언어 수준 mediation은 악성 코드를 막는 sandbox가 아니다.
- Koishi 사례는 4,000개 이상 커뮤니티 플러그인을 가진 단일 TypeScript 생태계의 관찰
  사례다. 대조 실험, runtime overhead, 생산성 비교가 없고 Koishi는 Cordis v3를 사용한다.
- 논문 결론도 self-evolving agent harness 검증을 미래 연구로 둔다. DeepSeek Harness의
  Cordis 채택과 자율 자기개선 효과의 검증을 같은 주장으로 쓰지 않는다.

## 문체와 구성

논문 심사표처럼 쓰지 않는다. 다음 흐름을 권장한다.

`무엇이 공개됐나 → Cordis 구조를 한 장면으로 이해하기 → AI 유지보수에 주는 이점 →
보장되는 것과 보장되지 않는 것 → 어떤 앱 설계에 적용할 수 있나`

전문성은 유지하되 구체적인 장면을 먼저 보여 주고 용어와 형식 보장을 뒤에서 설명한다.
근거 등급과 상세 검증 기록은 근거 원장에 두고, 본문에서는 같은 주의를 반복하지 않는다.

## 우선 확인할 원문

- 논문 저장소와 draft PDF: https://github.com/cordiverse/paper
- Cordis 공식 구현: https://github.com/cordiverse/cordis
- DeepSeek Harness: https://github.com/deepseek-ai/deepseek-harness
- Cordis primer: https://deepseek-harness.github.io/deepseek-harness/reference/cordis-primer/
- Koishi 공식 저장소: https://github.com/koishijs/koishi

별 수, commit 수와 커뮤니티 반응은 인기 신호일 뿐 설계의 우수성이나 AI 유지보수 효과의
근거로 사용하지 않는다.
