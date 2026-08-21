# AI판 정규·특별 발행과 발행 후 자기개선

## 운영 결과

AI 정규판은 매일 07:00 `Asia/Seoul`에 시작하는 단일 발행 실행의 두 번째 판으로 실행한다.
시사판 commit, push, 공개 URL 검증이 모두 성공한 뒤에만 오늘의 공식 AI 발표와 frontier
신호를 조사하고, 가치 있는 기술 변화가 있을 때만 기사 한 편을 준비한다. 발행 후 회고는
기사 생성 턴과 분리된 09:30 컨덕터 routine이 맡는다. 편집자가 특정 주제를 명시적으로
요청하고 출고를 승인한 경우에는 같은 날 AI 특별판을 추가할 수 있다. 특별판은 정규판의
하루 한 편 자리를 소비하지 않으며 공개 검증 직후 컨덕터에 같은 계약의 회고 턴을 별도로
전달한다.

## 고정 안전 경계

- 자동 정규판은 서울 날짜당 최대 한 편이다. 특별판은 편집자 요청·승인이 있을 때만
  추가하며 자동 발견 루프가 임의로 늘리지 않는다.
- 중심 주장에 `E2` 이상이 있어야 한다.
- 최소 두 개의 원문 URL과 claim별 source grade가 필요하다.
- `korean-writing-baseline-v1`, `ai-technical-blog-v2`, 선정 점수, 이해상충, 필수 절,
  publication ID, route 중복,
  artifact hash, site test와 production build를 모두 통과해야 한다.
- `no-publish`는 기사 route를 만들지 않지만, 검증된 날짜별 결정 기록을 `/ai/` 첫 화면의
  발행 상태로 공개한다. 실행 실패는 휴간으로 바꾸거나 공개 상태로 확정하지 않는다.
- 정규판의 자동 권한은 `ai-auto-publish-v1`에만 적용한다. 특별판은
  `ai-special-publish-v1`과 사람 승인 기록을 사용한다. EDA판은 별도
  `eda-auto-publish-v1`을 사용하며 서로 또는 시사판의 권한을 상속하거나 변경하지 않는다.
- 원격 push는 fast-forward만 허용하고 force push와 history rewrite를 하지 않는다.
- GitHub Pages 성공 뒤 공개 URL의 HTTP 상태, 제목, 발행 ID를 확인해야 발행 성공이다.

## 실행 경계

`scripts/publish-ai-candidate.py`는 무시되는 `var/runs/ai` 아래의 article·evidence를
읽어 자동 출고 조건을 검사한다. 기사 frontmatter는 공개 사이트의 엄격한 schema와 같은
필드 집합을 사용하며, `publication_id` 같은 예상 밖 필드는 materialize 전에 거부한다.
후보가 만들어지면 순차 발행기는 결정적 검사 전에 자연어 한국어 편집 턴을 항상 한 번
실행한다. 이 턴은 `docs/16-korean-writing-style.md`에 따라 제목·요약·소제목·설명 본문만
다듬는다. 편집 전후의 수치, URL, 코드 식별자, 고정 frontmatter, 근거 부록을 비교하고
evidence가 한 바이트라도 바뀌면 원본을 복원한 뒤 중단한다.
첫 검증이 실패하면 순차 발행기는 기존 주제와 근거를 바꾸지 않는 제한 복구 턴을 한 번만
실행하고 같은 결정적 검사를 다시 수행한다. 두 번째 검사도 실패하면 공개 경로, commit,
push, deploy 없이 실행 실패로 남긴다. 통과하면 다음 세 파일만 저장소에 materialize한다.

```text
content/ai/<publication-id>/article.md
decisions/ai/<publication-id>/evidence.json
decisions/ai/<publication-id>/release.json
```

이 명령 자체는 commit, push, deploy를 수행하지 않는다. `scripts/publish-ai-daily.sh`가
발행 전용 clean checkout에서 후보 생성, materialize, 전체 test와 build를 수행한다.
그 결과가 성공일 때만 공통 `scripts/finalize-publication.sh`가 허용된 세 파일을 Git과
Pages 단계로 보낸다.

정상 `no-publish`는 `scripts/publish-ai-no-publish.py`가 원본 결정의 날짜, 필드 집합,
사유와 discovery review를 검증한 뒤 다음 한 파일만 materialize한다.

```text
decisions/ai/<publication-id>/no-publish.json
```

`scripts/finalize-publication.sh ai-status`는 이 파일만 별도 상태 커밋으로 push한다. 사이트는
이를 기사나 RSS 항목으로 만들지 않고 `/ai/` 첫 화면에서 `발행 완료`, `편집 기준에 따른
휴간`, `발행 준비·상태 확인 중`을 구분한다. `scripts/verify-publication.sh ai-status`는 실제
첫 화면의 휴간 문구와 날짜를 확인해야 성공한다.

정규판 publication id는 `YYYY-MM-DD`이고 공개 주소는 `/ai/YYYY-MM-DD/`다. 특별판의
내부 publication id는 `YYYY-MM-DD--<slug>`이며 파일시스템에서는 정규판과 나란히
보존한다. 공개 주소만 읽기 쉬운 `/ai/YYYY-MM-DD/<slug>/`로 만든다. 기사와 release에는
`publication_kind: special`을 기록하고 목록·기사 화면에 `특별판`을 표시한다.

`scripts/publish-ai-special.sh`는 지정 브리프, slug, 승인자와 승인 근거를 필수 입력으로
받는다. 일일 시사판의 선행 발행 여부와 무관하게 동작하지만 정규판과 같은 E2, 원문 두 개,
문체, 이해상충, hash, 전체 test·build, fast-forward push와 공개 URL 검증을 통과해야 한다.

시사판과 AI판은 서로 다른 worktree를 만들지 않는다. 한 명의 순차 발행기만 발행 checkout을
소유하고, 시사판 공개 검증 뒤 같은 clean checkout을 최신 `main` 상태로 AI판에 넘긴다.
개선 worker와 컨덕터는 이 checkout을 수정할 수 없다.

기사 생성 turn은 source registry를 강제 순회 목록이 아닌 발견 seed로 사용한다. 지역과
언어에 치우치지 않게 공식 모델 발표·model registry·GitHub·release note를 탐색하고,
선택하지 않은 주요 후보와 이유도 evidence의 `discovery_review`에 남긴다. 특정 URL을
확인하지 않았다는 이유만으로 자동 출고를 막지는 않으며, coverage 누락은 09:30 회고와
다음 개선 작업에서 다룬다.

특정 날짜에 편집자가 주제나 독자 관점을 지정하려면
`prompts/ai-briefs/<publication-id>.md`에 자연어 브리프를 둔다. 순차 발행기는 실행 날짜와
이름이 정확히 같은 파일만 기본 프롬프트 뒤에 전달한다. 브리프는 주제의 우선순위와 취재
질문을 지정하지만 원문 검증, 선정 점수, evidence와 release gate를 완화하지 않는다. 따라서
지정 주제라도 발행일에 검증 가능한 원문이 사라졌거나 중심 주장이 기준을 충족하지 못하면
안전하게 `no-publish`할 수 있다.

특별판 브리프는 `prompts/ai-special-briefs/<date>/<slug>.md`에 둔다. 특별판 runner는 이
경로 아래의 명시된 브리프만 읽으며, 브리프가 없거나 승인 메타데이터가 비어 있으면 기사
생성 전에 중단한다.

공개 기사의 문장 재편집은 자동 회고가 수행하지 않는다. 편집자가 공개 기사와 수정 범위를
명시적으로 지정한 경우에만 기사 hash를 갱신하고 release에 수정 시각, 승인자, 승인 근거,
수정 범위와 이전 hash를 남긴다. 근거 원장과 evidence를 바꾸지 않는 문체 수정이라도 전체
test와 site build, 공개 URL 검증을 다시 통과해야 한다.

## 발행 후 자기개선 turn

09:30 정기 회고와 특별판 공개 직후 컨덕터에 전달하는 회고 턴은 같은 계약을 사용하며,
공개 URL 검증이 성공한 정규·특별판만 다음과 같이 회고한다. 특별판 턴은 발행기의 공개
검증 증거를 입력으로 받아 같은 URL을 다시 요청하지 않는다.

1. 제목과 리드가 중심 근거의 범위를 넘지 않고, 뉴스 설명·기술 이해·기술적 의미와 검증
   과제가 기사 전체에서 전달되는지 확인한다. 이를 특정 소제목의 존재 여부로 대신하지
   않는다.
2. 공식 source와 frontier 신호에서 놓친 coverage를 기록한다.
3. 기사 작성·검증·배포 중 반복된 수작업과 실패 지점을 찾는다.
4. 다음 기사 품질을 높일 작고 검증 가능한 후속 작업을 conductor inbox에 제안한다.
5. 회고가 새 특별판을 스스로 발행하거나 공개 기사를 무통보 수정하거나 광범위한
   self-modification을 수행하지 않는다.

발행 실패일에는 오류를 보존하고 회고를 발행 성공으로 취급하지 않는다. 실패 원인
분석은 가능하지만 제품 개선 turn을 자동으로 확대하지 않는다.
