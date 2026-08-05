# AI판 자동 발행과 발행 후 자기개선

## 운영 결과

AI판은 매일 07:00 `Asia/Seoul`에 시작하는 단일 발행 실행의 두 번째 판으로 실행한다.
시사판 commit, push, 공개 URL 검증이 모두 성공한 뒤에만 오늘의 공식 AI 발표와 frontier
신호를 조사하고, 가치 있는 기술 변화가 있을 때만 기사 한 편을 준비한다. 발행 후 회고는
기사 생성 턴과 분리된 09:30 컨덕터 routine이 맡는다.

## 고정 안전 경계

- 하루 최대 한 편이다.
- 중심 주장에 `E2` 이상이 있어야 한다.
- 최소 두 개의 원문 URL과 claim별 source grade가 필요하다.
- `ai-technical-blog-v2`, 선정 점수, 이해상충, 필수 절, publication ID, route 중복,
  artifact hash, site test와 production build를 모두 통과해야 한다.
- `no-publish`와 실행 실패는 공개 route를 만들지 않는다.
- 자동 권한은 AI판의 `ai-auto-publish-v1`에만 적용한다. EDA판과 시사판의 권한을
  상속하거나 변경하지 않는다.
- 원격 push는 fast-forward만 허용하고 force push와 history rewrite를 하지 않는다.
- GitHub Pages 성공 뒤 공개 URL의 HTTP 상태, 제목, 발행 ID를 확인해야 발행 성공이다.

## 실행 경계

`scripts/publish-ai-candidate.py`는 무시되는 `var/runs/ai` 아래의 article·evidence를
읽어 자동 출고 조건을 검사한다. 기사 frontmatter는 공개 사이트의 엄격한 schema와 같은
필드 집합을 사용하며, `publication_id` 같은 예상 밖 필드는 materialize 전에 거부한다.
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

시사판과 AI판은 서로 다른 worktree를 만들지 않는다. 한 명의 순차 발행기만 발행 checkout을
소유하고, 시사판 공개 검증 뒤 같은 clean checkout을 최신 `main` 상태로 AI판에 넘긴다.
개선 worker와 컨덕터는 이 checkout을 수정할 수 없다.

기사 생성 turn은 source registry를 강제 순회 목록이 아닌 발견 seed로 사용한다. 지역과
언어에 치우치지 않게 공식 모델 발표·model registry·GitHub·release note를 탐색하고,
선택하지 않은 주요 후보와 이유도 evidence의 `discovery_review`에 남긴다. 특정 URL을
확인하지 않았다는 이유만으로 자동 출고를 막지는 않으며, coverage 누락은 09:30 회고와
다음 개선 작업에서 다룬다.

## 발행 후 자기개선 turn

09:30 회고 routine은 공개 URL 검증이 성공한 판만 다음과 같이 회고한다.

1. 제목과 세 줄 요약이 중심 근거의 범위를 넘지 않았는지 확인한다.
2. 공식 source와 frontier 신호에서 놓친 coverage를 기록한다.
3. 기사 작성·검증·배포 중 반복된 수작업과 실패 지점을 찾는다.
4. 다음 기사 품질을 높일 작고 검증 가능한 후속 작업을 conductor inbox에 제안한다.
5. 같은 날 두 번째 기사 발행, 공개 기사 무통보 수정, 광범위한 self-modification은
   수행하지 않는다.

발행 실패일에는 오류를 보존하고 회고를 발행 성공으로 취급하지 않는다. 실패 원인
분석은 가능하지만 제품 개선 turn을 자동으로 확대하지 않는다.
