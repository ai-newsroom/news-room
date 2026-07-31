# news-room 승인 작업 조정 턴

`prompts/conductor-role.md`와 `docs/12-continuous-improvement-loop.md`를 먼저 읽고 그대로
따라라. 이 턴은 회고 제안을 승인하는 턴이 아니다.

1. `.coco-agents/conductor-loop.json`에서 conductor와 worker session id를 읽는다.
2. `inbox list`로 active(`running`, `awaiting-review`, `reviewing`, `ready-to-finalize`,
   `finalizing`) 항목을 확인한다. 하나라도 있으면 새 작업을 배정하지 말고 현재 항목의
   메시지·증거만 점검한다.
3. `proposed` 항목은 그대로 둔다. 스스로 approve하지 않는다.
4. `ready` 항목이 없으면 `NO_READY_ITEM`으로 끝낸다.
5. ready 항목이 여러 개면 priority, 독자 영향, 명확한 완료 조건, 다른 작업과의 중복을
   기준으로 하나만 선택한다. 공개 기사 수정·재발행, deploy, schedule, credential을 요구하는
   high-risk 항목은 자동 배정하지 않는다.
6. 선택한 항목을 `inbox dispatch`로 configured worker에 배정한다. instruction에는 다음을
   포함한다.
   - 항목 하나만 구현할 것
   - 기존 worktree 변경을 먼저 기록하고 보존할 것
   - archived `content/`를 수정하지 않을 것
   - 완료 조건마다 검증 증거를 남길 것
   - 첫 result 전에 commit/push/publish/deploy하지 않을 것
7. 배정 item id, worker session id, request message id만 간결하게 보고하고 끝낸다.

배정 이후 worker result는 ordinary message로 돌아온다. 그때는
`prompts/conductor-role.md`의 독립 검토·수정·finalization 규칙을 따른다.
