# AI·EDA 기술판 독립 편집 프로필 설계

> 상태: 설계안. 아직 워크플로, 자동 발행, 사이트 라우팅에 연결하지 않는다.
>
> 목적: AI판과 EDA판이 공통 발행 엔진은 함께 쓰되, 시사판과 서로의 편집 판단을
> 암묵적으로 상속하지 않게 한다. 이 문서에서 `필수`는 향후 edition 설정과 출고
> 검증기가 지켜야 할 계약을 뜻한다.

## 1. 기존 시사판과의 경계

현재 `newsroom/`은 시사판의 정본이다. 다음 항목은 기술판에 적용하지 않는다.

- `newsroom/charter.md` 4조의 중도 보수·중도 진보 토론 축
- 느티나무·물길을 비롯한 시사판 고정 페르소나와 철학·심리·사회·경제 렌즈 편성
- 보수지·진보지 프레임과 커뮤니티 반응을 맞추는 `newsroom/sources.md`의 수집법
- 매일 한 편을 반드시 내고 실패하면 기사 자리에 휴간 공지를 싣는 운영 전제
- 질문으로 기사를 닫는 형식과 시사판의 논평·데스크 판단 구조

기술판이 재사용할 수 있는 것은 편집 논리가 아니라 다음 공통 엔진 기능뿐이다.

- edition별 작업 디렉터리와 산출물 경로 관리
- 실행 프롬프트·모델·도구·종료 상태 기록
- 기사와 근거 원장의 조립, 정적 사이트 렌더링
- 출고 게이트 실행 결과와 미발행 결정 보존
- 사람이 승인한 경우에만 이루어지는 commit·push·배포

향후 edition 설정은 `inherits: technical-common`처럼 기술 공통 규칙만 명시적으로
가져와야 한다. `newsroom/`, 시사판 persona, 시사판 source 목록을 기본값이나 fallback으로
참조해서는 안 된다. AI판과 EDA판 사이도 마찬가지다. 공통 규칙 밖의 주제 선정 기준,
역할, 게이트는 각 edition이 소유한다.

## 2. 기술판 공통 강령

AI판과 EDA판은 다음 원칙만 공유한다.

1. **중요성을 인기보다 먼저 본다.** 검색량과 커뮤니티 반응은 발견 신호일 뿐이다.
   독자의 기술 선택, 연구 판단, 설계 품질, 비용 또는 안전에 실제로 영향을 주는가를
   먼저 묻는다.
2. **주장을 검증 가능한 단위로 쪼갠다.** "더 똑똑하다", "업계 최고다", "설계를
   혁신한다"를 그대로 옮기지 않는다. 버전, 조건, 비교 대상, 측정값이 있는 문장으로
   바꾼다.
3. **발표 사실과 성능 사실을 구분한다.** 공식 발표는 "회사가 무엇을 발표했는가"의
   1차 근거이지, 회사가 주장한 성능이 참이라는 독립 근거가 아니다.
4. **근거의 한계를 본문에 남긴다.** 비공개 데이터, 선택된 예제, 재현 불가 환경,
   다른 하드웨어나 공정, 작은 표본처럼 결론을 좁히는 조건을 결과와 함께 적는다.
5. **벤치마크를 제품 전체의 순위로 확대하지 않는다.** 과제, 입력, 품질 기준,
   비용, 지연시간, 전력, 도구 설정 가운데 무엇이 고정됐는지 확인한다.
6. **재현성은 이분법이 아니라 상태로 기록한다.** 재현하지 못했으면 실패인 척하지
   않고, 무엇이 공개되지 않아 확인할 수 없는지 적는다.
7. **이해상충과 접근 조건을 공개한다.** 고용·투자·후원·광고·제공받은 계정이나
   하드웨어·벤더 사전 브리핑·엠바고·NDA가 판단에 영향을 줄 수 있으면 표시한다.
8. **가치 있는 변화가 없으면 발행하지 않는다.** 날짜를 채우기 위한 요약, 보도자료
   재작성, 순위표 중계 대신 미발행 결정을 남긴다.
9. **쉽게 쓰되 정확도를 낮추지 않는다.** 전문 용어는 처음 나올 때 풀고, 독자가
   결과의 적용 범위와 다음 확인 방법을 이해할 수 있게 쓴다.

## 3. source/evidence rubric

### 3.1 소스 유형

소스의 "1차·2차" 여부는 기사 전체가 아니라 개별 주장과의 관계로 판정한다. 논문도
자기 실험에는 1차 소스지만 다른 제품을 설명하는 문단에서는 2차 해석일 수 있다.

| 코드 | 유형 | 예 | 사용할 수 있는 범위 |
|------|------|----|----------------------|
| `P0` | 공식 홍보 1차 | 보도자료, 기조연설, 제품 소개 페이지, 데모 영상 | 발표 주체가 한 말과 출시 사실. 성능·우월성의 독립 증거는 아님 |
| `P1` | 기술 1차 | 논문, 기술 보고서, 시스템·모델 카드, 릴리스 노트, 공식 문서, 표준 원문·초안, 규제 제출 문서 | 버전·방법·명시된 결과. 저자의 선택과 누락 가능성을 함께 기록 |
| `P2` | 실행 가능한 1차 | 공개 코드, 모델·가중치, 데이터셋, 평가 스크립트, benchmark submission, 설계 스크립트·로그 | 공개 범위에서 방법과 결과를 검사하거나 재실행하는 근거 |
| `I1` | 독립 검증 | 제3자의 재현 실험, 감사 보고서, 독립 benchmark, 여러 연구팀의 교차 검증 | 원 주장과 같은 조건인지 확인한 뒤 성능·재현성 판단에 사용 |
| `S1` | 전문 2차 | 기술 매체, 학회 해설, 전문가 분석, 조사 기사 | 맥락과 반론 탐색. 핵심 정량 주장의 유일한 근거로 쓰지 않음 |
| `S2` | 발견 신호 | 커뮤니티 글, SNS, 익명 제보, 검색 순위, 출처 없는 표·스크린샷 | 후보 발견과 조사 질문 생성만. 사실 근거로 인용하지 않음 |

접근할 수 없는 자료는 유형을 추정하지 않고 `unavailable`로 둔다. 검색 결과 요약,
다른 기사가 인용한 수치, 생성형 AI의 답은 원문을 열어 확인하기 전에는 `S2`다.

### 3.2 주장별 근거 등급

등급은 가장 좋은 URL의 등급이 아니라, **그 주장에 확보된 근거 묶음의 상태**다.

| 등급 | 조건 | 기사에서 허용되는 표현 |
|------|------|-------------------------|
| `E0 발견` | `S2`뿐이거나 원문에 접근하지 못함 | 발행 근거로 사용하지 않음 |
| `E1 발표 확인` | 발표 주체와 날짜·버전이 `P0` 또는 `P1`로 확인됨 | "발표했다", "문서에 적었다". 사실로 단정할 대상은 발표 행위뿐 |
| `E2 기술 근거` | 핵심 조건과 방법이 `P1`에 있고 필요한 artifact 일부가 `P2`로 검사 가능함 | 공개된 조건 안에서 결과를 설명. 미공개 조건을 한계로 병기 |
| `E3 독립 확인` | 같은 핵심 주장을 `I1`이 확인하거나, 독립적인 복수 근거가 같은 결론을 지지함 | 조건을 명시해 확인된 결과로 서술 가능 |
| `E4 재현·삼각검증` | 편집국 또는 독립 주체가 공개 절차로 재현했고 로그가 남거나, 서로 다른 방법의 독립 검증이 수렴함 | 재현 범위와 차이를 공개하고 강한 결론 가능 |

`E3`가 항상 `P1`보다 "좋은 문서"라는 뜻은 아니다. 예를 들어 공식 릴리스 날짜는
`E1`이면 충분하지만 "경쟁 제품보다 30% 빠르다"는 주장은 비교 가능한 `E3` 없이는
편집국의 결론으로 쓸 수 없다.

### 3.3 근거 원장 필수 필드

모든 후보와 기사는 claim 단위 근거 원장을 가진다.

```yaml
- claim_id: C1
  claim: "검증할 수 있는 한 문장"
  source_url: "원문 URL 또는 저장된 artifact 경로"
  source_type: P1 # P0, P1, P2, I1, S1, S2, unavailable 중 하나
  evidence_grade: E2 # E0, E1, E2, E3, E4 중 하나
  version: "모델·도구·문서·commit·표준 초안 버전"
  accessed_at: YYYY-MM-DD
  direct_or_derived: direct | derived
  method: "파생값이면 계산식과 입력"
  limitations: ["적용 범위를 줄이는 조건"]
  conflict_of_interest: ["없음"] # 예: "벤더 제공 계정"
```

하나의 출처가 여러 주장을 받치면 각 claim에 연결한다. 표와 그래프의 파생값은 원자료,
단위, 계산식을 남긴다. 링크가 바뀔 가능성이 큰 자료는 문서 제목과 버전·commit도 적는다.

### 3.4 benchmark·재현성·이해상충 표기

정량 비교에는 가능한 범위에서 다음을 표 또는 각주로 붙인다.

- 비교 대상의 정확한 이름과 버전
- 과제·데이터셋·design/benchmark suite와 train/test split 또는 workload
- 지표 정의, 단위, 높을수록 좋은지 여부, 허용 오차
- baseline과 품질 동등성 조건
- 하드웨어, 운영체제, compiler/runtime/toolchain, precision과 주요 옵션
- batch·context·concurrency·seed·반복 횟수, 분산이나 신뢰구간
- 비용, 시간, 메모리, 전력 가운데 측정한 것과 측정하지 않은 것
- 제외된 실패 사례, 수작업 조정, vendor tuning 여부
- 원 로그·스크립트·submission 접근 가능 여부

재현성은 다음 상태로 기록한다.

| 상태 | 뜻 |
|------|----|
| `R0 비공개` | 방법 또는 필수 입력이 없어 재현을 시도할 수 없음 |
| `R1 설명 가능` | 방법과 조건은 설명됐지만 실행 artifact가 부족함 |
| `R2 실행 가능` | 코드·데이터·환경·스크립트가 공개되어 재실행 가능함 |
| `R3 독립 재현` | 독립 주체의 로그와 결과가 있고 원 결과와 차이를 설명할 수 있음 |

이해상충 표기는 "없음"도 값으로 기록한다. 다음 가운데 하나라도 있으면 기사 하단과
근거 원장에 함께 쓴다.

- 작성자나 검토자의 관련 회사 고용·자문·투자·연구비
- 벤더가 무상 제공한 계정, 크레딧, 라이선스, 장비 또는 데이터
- 광고·제휴·후원 관계
- 사전 브리핑, 엠바고, 인용 승인 조건, NDA
- benchmark나 대회의 운영 주체와 참가자의 관계

NDA나 라이선스 때문에 독자가 볼 수 없는 자료는 독립 근거처럼 사용하지 않는다.
"확인했지만 공개할 수 없다"는 문장으로 출고 게이트를 우회할 수 없다.

## 4. 공통 출고 게이트와 산출물

### 4.1 모든 기술판이 통과할 게이트

아래 항목 중 하나라도 실패하면 심층 기사를 출고하지 않는다.

1. **중요성**: 영향을 받는 독자·연구·제품·설계 결정이 구체적인가.
2. **새 국면**: 이전 기사나 알려진 사실과 달라진 점이 한 문장으로 설명되는가.
3. **핵심 근거**: 중심 주장에 최소 `E2`가 있는가. 출시 사실만 다루면 `E1`도
   가능하지만 제목과 요약이 성능을 단정해서는 안 된다.
4. **추적성**: 기사 속 사실·수치·표가 claim id와 원문으로 역추적되는가.
5. **비교 공정성**: benchmark를 썼다면 버전·조건·품질 기준·비용의 차이를
   공개했는가.
6. **한계**: 재현성 상태와 확인하지 못한 조건이 결과 바로 옆에 있는가.
7. **이해상충**: 관련 관계와 제공받은 접근이 공개됐는가.
8. **edition 적합성**: 다른 edition의 강령·역할·source rubric을 fallback으로
   사용하지 않았는가.
9. **편집 품질**: 한국어로 정확히 풀었고 홍보 문구를 제목이나 데스크 결론으로
   옮기지 않았는가.
10. **사람 승인**: 실제 publish·commit·push·배포 직전 명시적 승인이 있는가.

### 4.2 심층 기사 형식

기술판 기사는 토론 의사록이 아니라 검증 보고를 읽기 쉽게 편집한 해설문이다. 고정
페르소나의 찬반 토론이나 닫는 질문은 필수가 아니다.

```markdown
---
edition: ai # EDA판은 eda
decision: publish-candidate
title: "검증 범위를 드러내는 제목"
date: YYYY-MM-DD
subject: "제품·논문·표준·사건과 정확한 버전"
summary: "확인된 변화와 가장 큰 한계"
evidence_ceiling: E2 # E1, E2, E3, E4 중 하나
reproducibility: R1 # R0, R1, R2, R3 중 하나
conflicts: ["없음"] # 또는 공개할 관계 목록
---

## 세 줄 요약
## 무엇이 실제로 바뀌었나
## 어떤 근거로 확인했나
## benchmark 또는 재현 결과
## 적용 범위와 확인하지 못한 것
## 독자가 내릴 수 있는 기술 판단
## 이해상충과 취재 조건
## 근거 원장
## 출처
```

`evidence_ceiling`은 기사 안에서 가장 높은 등급이 아니라 **제목과 summary의 중심 결론을
받치는 등급**이다. 독자에게 필요한 절이 없다면 비워 두지 말고 삭제할 수 있지만,
세 줄 요약·한계·이해상충·근거 원장·출처는 필수다.

### 4.3 미발행 결정 형식

가치 있는 소식이 없거나 근거가 부족하면 기사 대신 내부 의사결정 artifact만 만든다.
공통 엔진은 이를 공개 기사 route, commit, push 대상으로 자동 승격하지 않는다.

```markdown
---
edition: ai # EDA판은 eda
decision: no-publish
date: YYYY-MM-DD
reason_codes:
  - PRIMARY_SOURCE_MISSING
  - VENDOR_CLAIM_ONLY
recheck_trigger: "새 문서·독립 검증·정식 릴리스 등 다시 볼 조건"
---

## 검토한 후보
## 발행하지 않는 이유
## 부족한 근거와 현재 등급
## 다시 검토할 조건
## 확인한 출처
```

`reason_codes`에는 해당하는 값만 남긴다. 허용 값은 `NO_MATERIAL_CHANGE`,
`PRIMARY_SOURCE_MISSING`, `VENDOR_CLAIM_ONLY`, `COMPARISON_NOT_VALID`,
`REPRODUCIBILITY_TOO_LOW`, `CONFLICT_UNRESOLVED`, `SECURITY_OR_LICENSE_RISK`다.

미발행은 파이프라인 실패와 다르다. 정상적인 편집 결과이며 억지 휴간 기사로 바꾸지
않는다. 실행 실패는 별도 run 상태로 기록하고, 미발행 결정인 것처럼 포장하지 않는다.

## 5. AI판 편집 프로필

### 5.1 AI판 강령과 주제 선정

AI판의 임무는 모델·데이터·평가·시스템·개발 도구의 변화가 실제 능력, 비용, 안전,
사용 조건을 어떻게 바꾸는지 검증하는 것이다.

AI판은 기술 공통 강령에 다음 원칙을 더한다.

- 모델의 능력과 이를 감싼 제품·도구·system prompt의 능력을 분리한다.
- 사람처럼 이해하거나 판단한다는 표현 대신 관찰된 과제와 실패 조건을 쓴다.
- 평가 점수보다 평가 설계와 실제 사용 조건의 차이를 먼저 확인한다.
- 공개 범위가 좁을수록 결론도 좁힌다. 비공개 학습 데이터나 평가 결과를 추정으로
  메우지 않는다.

AI판은 다음을 우선한다.

- 모델·API·오픈소스 프로젝트의 정식 릴리스와 호환성·가격·사용 조건 변화
- 논문과 시스템 카드가 제시한 새 방법, 평가 결과, 안전·한계
- 독립 평가에서 드러난 능력, 실패 양상, 비용·지연시간·운영 제약
- 데이터셋·평가 방법·라이선스·보안 변화가 연구와 제품 판단에 주는 영향
- AI 개발·배포 도구의 재현 가능한 성능 또는 워크플로 변화

후보는 중요성, 새로움, 검증 가능성, 독자의 의사결정 유용성, 한국 독자에 대한 관련성을
각 0~2점으로 기록한다. 총점 7점 이상이면서 공통 hard gate를 통과해야 심층 기사 후보가
된다. 점수는 발행을 강제하지 않는다.

AI판은 다음을 이유만으로 주제로 고르지 않는다.

- "AGI에 가까워졌다" 같은 정의되지 않은 선언
- 맥락 없는 leaderboard 1위, 선택된 demo, 바이럴 게시물
- 이름만 바뀐 모델·기능이나 이전 기사와 실질 차이가 없는 업데이트
- system card, release note, 논문, 실행 artifact 중 어느 것도 없는 소문
- 접근할 수 없는 비공개 평가만 근거로 한 우월성 주장

### 5.2 AI판 역할

| 역할 | 책임 | 하지 않는 일 |
|------|------|--------------|
| 신호 수집자 | 공식 릴리스, 논문, 저장소, 평가 기관에서 후보와 버전을 찾음 | SNS 관심도를 사실 등급으로 올리지 않음 |
| 1차 근거 기자 | 원문·system/model card·release note·license·commit을 확보하고 claim 원장을 만듦 | 보도자료 요약으로 기술 근거를 대신하지 않음 |
| 평가 방법 검토자 | dataset, contamination, metric, baseline, 통계와 평가 설계를 점검 | 서로 다른 조건의 점수를 한 순위로 합치지 않음 |
| 시스템·재현 검토자 | API와 로컬 실행의 환경, latency, throughput, 비용, 메모리, 재현 상태를 확인 | 한 번의 성공 demo를 일반 성능으로 확대하지 않음 |
| 안전·한계 검토자 | 위험 평가, 알려진 실패, 배포 제한, 데이터·privacy·security 쟁점을 근거로 검토 | 근거 없는 낙관·공포 시나리오를 만들지 않음 |
| 주제 객원 | 의료, 법률, 로봇, 언어 등 해당 응용 분야의 측정 타당성을 검토 | 일반 AI 권위로 모든 영역을 대변하지 않음 |
| AI 데스크 | 중요성, 근거 등급, 적용 범위를 기준으로 publish/no-publish를 결정 | 시사판의 좌우 균형이나 인위적 찬반 수렴을 요구하지 않음 |

한 사람이 여러 역할을 수행할 수 있지만, 원 주장 작성자와 독립 검토자의 구분은 근거
원장에 남긴다.

### 5.3 AI판 source/evidence 적용과 추가 출고 게이트

AI판은 공통 rubric을 다음처럼 적용한다.

| 주장 | 우선할 1차 근거 | 최소 등급과 제한 |
|------|------------------|------------------|
| 출시·지원·가격·사용 조건 | 공식 release note, API 문서, 가격표, license (`P1`) | `E1`. 발표된 사실까지만 단정 |
| 모델 구조·학습·평가 방법 | 논문, technical report, system/model card (`P1`) | `E2`. 비공개 학습·평가 조건 표시 |
| 공개 실행 가능성 | 코드, weight, dataset, eval script와 commit (`P2`) | `E2`, 실제 독립 실행이면 `E3~E4` |
| 타 모델 대비 능력·비용 우월성 | 조건이 맞는 독립 평가 (`I1`)와 실행 artifact (`P2`) | 편집국 결론은 `E3` 이상. 아니면 벤더 주장으로 귀속 |
| 안전성·강건성 | threat model이 있는 평가 보고서·system card (`P1`)와 독립 audit (`I1`) | 공개 결과 설명은 `E2`, 일반적 우월성은 `E3` 이상 |

기술 매체의 hands-on과 전문가 해설(`S1`)은 사용 맥락과 조사 질문을 보완하지만, 모델
우월성 수치의 유일한 근거가 될 수 없다. 커뮤니티 prompt 결과(`S2`)는 재현 가능한 입력,
버전, 반복 실험을 갖춰 `P2` 또는 `I1` artifact가 되기 전에는 일화로만 남긴다.

공통 게이트와 함께 다음을 확인한다.

- 정확한 모델·API·checkpoint·날짜·지역·요금제와 availability가 식별되는가.
- 모델 자체, system prompt·도구를 포함한 제품, 사용자 workflow의 결과를 구분했는가.
- dataset 오염·중복·grader 편향·표본 크기·pass@k 등 결과를 바꾸는 조건을 확인했는가.
- quality를 고정한 latency/throughput/cost 비교인지, 품질 차이를 숨긴 속도 비교인지
  구분했는가.
- open weight, open source, 공개 API를 같은 뜻으로 쓰지 않았는가.
- 안전성 주장은 평가 주체, threat model, 공격 예산, 거부율과 유용성 trade-off를
  가능한 범위에서 제시했는가.
- "더 우수하다"는 중심 결론에 `E3` 이상이 있는가. 없다면 회사의 `E1~E2` 주장으로
  명확히 귀속하고 편집국 결론으로 승격하지 않았는가.

### 5.4 AI판 결정 예시

**심층 기사 후보 예시**

한 회사가 새 모델을 발표했고 같은 버전의 system card, API release note, 가격표,
평가 방법을 공개했다. 독립 평가 한 곳이 일부 과제와 비용을 같은 조건에서 비교했다.
기사는 "모든 면에서 최고"가 아니라 확인된 과제의 개선, 비용 변화, 독립 평가가 아직
다루지 않은 안전·언어 범위를 나눈다. 중심 결론은 `E3`, 재현성은 API 의존이므로 `R1`
또는 제공된 스크립트 범위에서 `R2`로 기록한다.

**미발행 예시**

기조연설 demo와 "추론이 두 배 좋아졌다"는 제품 페이지뿐이고 모델 버전, 평가셋,
baseline, system card가 없다. 출시 발표 자체는 `E1`이지만 독자가 판단할 새 기술 정보가
부족하다. `VENDOR_CLAIM_ONLY`, `PRIMARY_SOURCE_MISSING`으로 미발행하고 정식 문서나 독립
평가 공개를 recheck trigger로 남긴다.

## 6. EDA판 편집 프로필

### 6.1 EDA판 강령과 주제 선정

EDA판의 임무는 반도체 설계·검증·구현·signoff·제조 연계 기술의 변화가 정확성,
PPA(power, performance, area), runtime, 비용, 상호운용성에 미치는 영향을 조건과 함께
검증하는 것이다.

EDA판은 기술 공통 강령에 다음 원칙을 더한다.

- PPA와 runtime은 design·flow·constraint·공정 조건에 묶인 결과로 쓴다.
- simulation, implementation estimate, signoff, tapeout, measured silicon을 섞지 않는다.
- 벤더 기밀과 benchmark·PDK·IP 라이선스를 지키며, 비공개 접근을 권위로 사용하지 않는다.
- 정확성이나 signoff 기준을 낮춰 얻은 속도·면적 개선을 같은 품질의 개선으로 쓰지 않는다.

EDA판은 다음을 우선한다.

- synthesis, place-and-route, timing, power, verification, analog, packaging 도구의
  정식 릴리스와 flow 변화
- IEEE·Accellera 등 표준의 정식 버전 또는 명시된 draft 변화와 호환성 영향
- 재현 가능한 연구 방법, 공개 benchmark, open-source EDA와 검증 가능한 개선
- PDK·process·IP·foundry 발표가 설계 제약과 signoff에 주는 실제 변화
- silicon 결과, tapeout, 공개된 측정과 pre-silicon 추정 사이의 차이를 보여주는 사례

후보는 설계 흐름 영향, 새로움, 조건 공개 수준, 재현 가능성, 실무 의사결정 유용성을
각 0~2점으로 기록한다. 총점 7점 이상이면서 공통 hard gate를 통과해야 심층 기사 후보가
된다. 시장 규모나 회사 인지도는 독립 점수가 아니다.

EDA판은 다음을 이유만으로 주제로 고르지 않는다.

- design, node, library, constraint, tool version이 없는 "PPA 20% 개선" 문구
- vendor가 고른 단일 design의 before/after 화면
- simulation·emulation·estimated 결과를 silicon 측정처럼 표현한 발표
- 유출된 PDK, NDA 자료, benchmark 라이선스를 위반한 결과
- 공식 draft나 change log 없이 전해진 표준·foundry roadmap 소문

### 6.2 EDA판 역할

| 역할 | 책임 | 하지 않는 일 |
|------|------|--------------|
| 릴리스·표준 추적자 | 공식 release note, 지원 matrix, 표준 원문·draft와 날짜를 추적 | 기사나 세션 발표만으로 표준 확정을 선언하지 않음 |
| 1차 근거 기자 | 논문, 도구 문서, benchmark, script, log, errata와 라이선스를 claim에 연결 | 벤더 수치를 독립 측정처럼 쓰지 않음 |
| flow 방법 검토자 | RTL-to-GDS, verification, analog 등 해당 flow의 단계·constraint·signoff 정의를 점검 | 서로 다른 flow 결과를 설정 차이 없이 비교하지 않음 |
| PPA·benchmark 검토자 | design set, node/library, corner, seed, quality, runtime hardware, 통계를 검토 | PPA 세 축 중 유리한 하나만으로 우승자를 정하지 않음 |
| silicon·제조 검토자 | pre-silicon, tapeout, measured silicon, yield·package 조건을 구분 | 시뮬레이션 추정치를 양산 결과로 확대하지 않음 |
| 재현·라이선스 검토자 | 공개 artifact의 실행 가능성과 PDK·IP·benchmark 공개 권한을 확인 | 비공개·유출 자료로 재현성을 주장하지 않음 |
| 주제 객원 | RTL, formal, DFT, physical design, analog/RF, packaging 등 해당 분야를 검토 | 다른 EDA 분야까지 일반화하지 않음 |
| EDA 데스크 | 실무 영향, 조건 동등성, 근거 등급으로 publish/no-publish를 결정 | 시사판의 좌우 구도나 vendor A/B의 기계적 균형을 만들지 않음 |

### 6.3 EDA판 source/evidence 적용과 추가 출고 게이트

EDA판은 공통 rubric을 다음처럼 적용한다.

| 주장 | 우선할 1차 근거 | 최소 등급과 제한 |
|------|------------------|------------------|
| 도구 출시·지원 범위·호환성 | 공식 release note, manual, support matrix, errata (`P1`) | `E1~E2`. 문서에 명시된 범위만 단정 |
| 표준 상태와 변경 | 표준 기구의 proposal·draft·ratified 원문과 change log (`P1`) | `E1`은 상태 확인, 조항 영향 분석은 `E2` |
| 방법·flow의 기술 결과 | 논문·technical report (`P1`), script·log·benchmark (`P2`) | 조건이 검사 가능해야 `E2` |
| PPA·runtime 우월성 | 같은 design·공정·constraint의 독립 재현 (`I1`) | 편집국 결론은 `E3` 이상. 아니면 저자·벤더 결과로 귀속 |
| tapeout·silicon 결과 | 공개 test report·측정 방법 (`P1`)과 독립 측정·고객 검증 (`I1`) | 단계가 분명한 `E2`, 일반화는 `E3` 이상 |
| 상호운용성 | 표준 conformance 결과, 재현 가능한 다중 도구 flow (`P2`, `I1`) | 실제 조합 범위에서 `E2~E3` |

학회 발표나 전문 매체 해설(`S1`)은 원 논문·표준·artifact를 찾는 길잡이로 쓸 수 있지만,
PPA 수치의 원문을 대신하지 않는다. 고객 testimonial과 익명 forum 결과는 조건을 공개한
검증 artifact가 되기 전에는 각각 `P0` 또는 `S2`를 넘지 않는다.

공통 게이트와 함께 다음을 확인한다.

- 도구·표준·PDK·library·IP의 정확한 버전과 공개 범위가 식별되는가.
- design/benchmark suite, node, library, voltage·temperature·process corner, clock·I/O·area
  constraint가 비교에 충분히 공개됐는가.
- synthesis/route/signoff 기준, DRC/LVS/timing closure, power 산정 방법과 허용 오차가
  같은가.
- PPA와 runtime 비교에서 seed·반복 횟수·서버 사양·thread·license 기능·수작업 tuning을
  확인했는가.
- 다른 process node나 design rule의 결과를 정규화 근거 없이 직접 비교하지 않았는가.
- estimated, post-synthesis, post-route, signoff, tapeout, measured silicon을 정확히
  구분했는가.
- 표준 기사는 proposal, draft, ratified version, vendor implementation 상태를 구분했는가.
- PDK·IP·benchmark의 NDA와 재배포 조건을 지키며 독자가 볼 수 없는 자료를 근거 등급
  상승에 사용하지 않았는가.
- "PPA가 더 좋다"는 중심 결론에 비교 가능한 `E3` 이상이 있는가. 없다면 벤더 또는
  논문 저자의 `E1~E2` 결과로 귀속했는가.

### 6.4 EDA판 결정 예시

**심층 기사 후보 예시**

새 place-and-route 릴리스에 공식 release note와 지원 matrix가 있고, 공개 benchmark의
flow script·constraint·tool version·서버 사양·복수 seed 로그가 제공됐다. 독립 팀이 같은
design 일부에서 quality를 맞춘 runtime과 PPA를 재실행했다. 기사는 확인된 design의 개선과
재현되지 않은 design, signoff 차이, 라이선스 비용이 공개되지 않은 한계를 나눈다. 중심
결론은 해당 조건에서 `E3`, 재현 상태는 `R3`다.

**미발행 예시**

벤더가 "AI 배치로 PPA 20% 향상"이라고 발표했지만 design, node, baseline tool version,
constraint, 성공·실패 분포가 없다. 고객 이름은 있으나 수치 원문과 silicon 결과도 없다.
발표 사실은 `E1`이어도 우월성은 검증할 수 없다. `VENDOR_CLAIM_ONLY`,
`COMPARISON_NOT_VALID`, `REPRODUCIBILITY_TOO_LOW`로 미발행하고 technical paper, 공개
submission 또는 비교 가능한 독립 검증을 recheck trigger로 남긴다.

## 7. edition 설정이 가져야 할 최소 계약

실행 구현은 후속 항목에서 다룬다. 이 설계가 설정으로 옮겨질 때는 적어도 다음 값이
edition별로 명시되어야 하며, 값이 없다고 시사판으로 fallback하면 안 된다.

```yaml
id: ai # EDA판은 eda
inherits: technical-common
charter: "edition 전용 강령 경로"
roles: "edition 전용 역할 정의 경로"
sources: "edition 전용 source policy 경로"
evidence_rubric: "이 문서의 공통 rubric 경로"
selection_rules: "edition 전용 선정 기준"
release_gates: "공통 + edition 전용 gate"
article_template: "기술 심층 기사 형식"
no_publish_template: "미발행 결정 형식"
publish_requires_human_approval: true
forbidden_fallbacks:
  - newsroom/charter.md
  - newsroom/personas/
  - newsroom/sources.md
```

구현 검증은 같은 후보 bundle을 각 edition에 넣었을 때 AI판과 EDA판이 자기 기준으로
서로 다른 결정을 내릴 수 있고, 어떤 edition도 시사판 역할을 로드하지 않는지를 확인해야
한다. 그것은 이 문서의 설계를 실행 계약으로 옮기는 별도 작업이며, 이번 설계안이 자동
발행 준비 완료를 뜻하지는 않는다.
