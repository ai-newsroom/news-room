# AI판 자동 발행과 발행 후 자기개선

## 운영 결과

AI판은 매일 08:00 `Asia/Seoul`에 한 번 실행한다. 실행은 오늘의 공식 AI 발표와
frontier 신호를 조사하고, 가치 있는 기술 변화가 있을 때만 기사 한 편을 준비한다.
발행에 성공하면 같은 실행의 마지막에 한 번의 post-publication 자기개선 turn을
수행한다.

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
읽어 자동 출고 조건을 검사한다. 통과하면 다음 세 파일만 저장소에 materialize한다.

```text
content/ai/<publication-id>/article.md
decisions/ai/<publication-id>/evidence.json
decisions/ai/<publication-id>/release.json
```

이 명령 자체는 commit, push, deploy를 수행하지 않는다. scheduler는 격리된 clean
worktree에서 materialize한 뒤 전체 test와 build를 다시 실행하고, 그 결과가 성공일 때만
Git과 Pages 단계를 수행한다.

## 발행 후 자기개선 turn

공개 URL 검증이 성공한 경우에만 다음을 회고한다.

1. 제목과 세 줄 요약이 중심 근거의 범위를 넘지 않았는지 확인한다.
2. 공식 source와 frontier 신호에서 놓친 coverage를 기록한다.
3. 기사 작성·검증·배포 중 반복된 수작업과 실패 지점을 찾는다.
4. 다음 기사 품질을 높일 작고 검증 가능한 후속 작업을 conductor inbox에 제안한다.
5. 같은 날 두 번째 기사 발행, 공개 기사 무통보 수정, 광범위한 self-modification은
   수행하지 않는다.

발행 실패일에는 오류를 보존하고 회고를 발행 성공으로 취급하지 않는다. 실패 원인
분석은 가능하지만 제품 개선 turn을 자동으로 확대하지 않는다.
