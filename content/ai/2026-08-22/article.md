---
edition: ai
decision: publish-candidate
title: "Mistral Agentic Search 공개 - 문서 안을 직접 탐색하는 RAG"
date: 2026-08-22
subject: "Mistral Agentic Search and Search Toolkit, August 20 2026"
summary: "Mistral의 Agentic Search는 처음 검색된 문서 조각만으로 답하지 않습니다. 모델이 문서를 열고 앞뒤 맥락과 특정 표현을 찾아가며 필요한 근거를 모읍니다. 공개 문서와 패키지에서 이 구조를 확인할 수 있지만, 성능 수치는 Mistral 자체 측정이어서 실제 업무 문서에서는 별도 검증이 필요합니다."
evidence_ceiling: E2
reproducibility: R1
conflicts: ["Mistral은 Agentic Search, Search Toolkit, Libraries, Vibe의 개발·배포 주체이며 이 기사에 쓴 발표문과 문서를 작성했습니다. 사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다."]
---

Mistral이 2026년 8월 20일 Agentic Search를 공개했습니다. 이 기능은 검색 증강 생성(RAG)이 처음 찾아낸 문서 조각만 읽고 답하는 데서 멈추지 않게 합니다. 모델이 필요한 문서를 직접 열고, 앞뒤 내용을 살피고, 특정 표현을 찾아가며 답의 근거를 모읍니다.

예를 들어 긴 재무 문서에서 표와 주석을 함께 확인해야 한다고 해보겠습니다. 기존 RAG는 검색 결과 상위에 나온 몇 개의 문서 조각(chunk)을 모델에 전달합니다. Agentic Search에서는 모델이 `search`로 문서를 찾은 뒤 `open`, `navigate`, `read`, `grep`을 차례로 사용해 문서 안에서 필요한 내용을 계속 찾을 수 있습니다.

이 변화는 새 모델의 성능보다 검색 과정을 설계하는 방식에 가깝습니다. Mistral은 두 벤치마크에서 정확도와 token 사용량, p90 latency가 좋아졌다고 밝혔습니다. 다만 이 수치는 Mistral이 선택한 환경에서 나온 자체 측정이므로, 이번 공개에서 확인할 수 있는 핵심은 모든 RAG보다 성능이 좋다는 결론이 아니라 문서 검색을 여러 단계의 탐색으로 구성할 수 있게 됐다는 점입니다.

## 기존 RAG는 처음 찾은 문서 조각만 읽습니다

일반적인 one-shot RAG는 질문과 가까운 내용을 embedding이나 keyword 검색으로 찾은 뒤 상위 문서 조각 몇 개를 모델에 넣습니다. 답이 그 안에 있으면 빠르고 단순합니다. 하지만 긴 PDF의 각주, 표가 많은 재무 문서의 주석, 여러 문서에 흩어진 근거를 찾아야 할 때는 문제가 생깁니다. 검색 index가 알맞은 문서를 골라도 답이 들어 있는 정확한 위치까지 찾아 주지는 않기 때문입니다.

지금까지는 첫 검색의 품질을 높이기 위해 chunk 크기, embedding 모델, 검색 결과의 순위를 다시 매기는 reranker를 조정하는 경우가 많았습니다. 그래도 필요한 문장이 처음 고른 조각 밖에 있으면 모델은 그 내용을 읽지 못합니다. Agentic Search는 첫 검색 뒤에 모델이 스스로 다음 검색 행동을 정하는 agent loop를 추가해 이 문제를 다룹니다.

## Agentic Search는 문서를 열고 다시 찾습니다

Mistral 문서에 따르면 기본 검색은 keyword와 semantic retrieval을 사용합니다. Agentic Search는 그 결과를 바로 답변으로 넘기지 않고, 모델이 여러 검색 도구를 호출할 수 있게 합니다. `search(query, top_k, exclude_ids)`는 전체 문서에서 후보를 찾고, `open(source_id, start_offset, end_offset, window)`은 선택한 위치의 앞뒤 내용을 펼쳐 보여 줍니다. `navigate`와 `read`는 같은 문서의 다른 부분으로 이동해 읽고, `grep`은 열린 문서에서 정확한 문자열을 찾습니다.

한 번 본 문서 조각은 `exclude_ids`로 다음 검색에서 뺄 수 있습니다. 처음 검색어가 충분하지 않으면 모델이 질문을 바꾸어 다시 찾을 수도 있습니다. 이 과정을 반복하면 답을 만드는 모델이 검색 결과의 수동적인 소비자가 아니라, 어느 문서를 더 읽을지 결정하는 탐색 주체가 됩니다.

오류를 분석하는 방법도 달라집니다. 답이 틀렸을 때 embedding 모델이나 chunk 크기만 볼 것이 아니라, 모델이 후속 검색어를 잘못 만들었는지, 문서를 충분히 열어 보지 않았는지, `grep`을 써야 할 때 지나쳤는지도 살펴야 합니다. 운영자는 search index를 바꾸지 않고도 loop depth, `top_k`, `exclude_ids`, 문서별 scope를 조정해 검색 행동을 다르게 만들 수 있습니다.

## Search Toolkit과 MCP로 검색 도구를 연결합니다

Mistral은 Search Toolkit을 문서 수집과 검색을 구성하는 Python framework로 제공합니다. 문서를 불러오고(file loader), 내용을 추출하고(extractor), 적당한 크기로 나누고(text splitter), 검색용 벡터로 바꾸는(embedder) 구성 요소가 들어 있습니다. 검색 단계에는 vector search, query preprocessing, reranking, semantic cache가 있습니다. PDF/DOCX/PPTX, HTML, spreadsheet, email, plain text를 처리할 수 있고, 저장소는 Vespa나 custom vector store로 바꿀 수 있습니다.

모델은 MCP server를 통해 이 검색 기능을 도구처럼 호출합니다. starter app은 문서 수집 pipeline, Vespa search index, 문서 이동 도구를 제공하는 MCP server와 sample data를 기본으로 구성합니다. MCP server에 연결된 agent는 `search`, `open`, `grep`, `navigate`, `read`, `ingest`, `delete`를 호출할 수 있습니다. 따라서 발표문의 개념만 공개된 것이 아니라, 어떤 도구를 어떻게 연결하는지 확인할 수 있는 template과 패키지도 함께 나왔습니다.

PyPI의 `mistralai-search-toolkit` 패키지는 2026년 7월 31일 공개된 `0.0.11`을 최신 release로 표시합니다. Python `>=3.12, <3.15`가 필요하며 license는 Apache-2.0입니다. source distribution과 wheel의 hash, Trusted Publishing 여부, GitHub Actions provenance도 공개돼 있습니다. 다만 provenance가 가리키는 source repository 일부는 private로 표시되어 있어, GitHub에서 패키지 내부 구현 전체를 추적할 수 있는 R2 수준의 재현성은 아직 확보하지 못했습니다.

## 성능은 좋아졌지만 실제 환경 검증은 남았습니다

Mistral은 FinanceBench와 OfficeQA Pro로 Agentic Search를 평가했습니다. FinanceBench는 368개 SEC filing에서 만든 150개 질문을 사용합니다. 문서는 평균 약 147쪽이고 전체 corpus는 약 53,900쪽입니다. Mistral은 정답 판정에 쓰는 LLM judge를 human label에 맞춰 보정했다고 설명합니다. OfficeQA Pro는 696개 Treasury Bulletin에서 고른 133개 “pro” subset 질문을 사용하며, 약 89,000쪽의 scanned, table-heavy PDF를 다루는 numeric benchmark입니다.

Mistral이 공개한 결과에서는 문서 안을 이동하는 단계가 추가될수록 성능이 좋아졌습니다. FinanceBench에서 search-only loop는 one-shot RAG보다 Mistral Medium 3.5와 GLM-5.2 모두 약 3배 나은 결과를 냈다고 합니다. navigation을 추가했을 때는 정확도가 더 올라가고 token과 latency도 줄었다고 보고했습니다. OfficeQA Pro에서 GLM-5.2의 결과는 one-shot RAG 6.3%에서 full loop 51.9%로 올랐습니다.

이 결과는 Agentic Search가 긴 문서에서 어떤 가능성을 보여 주는지 이해하는 데는 도움이 됩니다. 그러나 편집국은 같은 환경에서 benchmark를 실행하지 않았고, Mistral의 세부 실행 로그와 전체 실패 사례도 확인하지 못했습니다. 다른 corpus와 모델, 검색 backend에서도 같은 차이가 나는지는 실제 환경에서 따로 검증해야 합니다.

## 긴 문서와 근거 추적이 필요한 업무에 맞습니다

Agentic Search는 답이 첫 검색 결과 밖에 있을 가능성이 큰 업무에 잘 맞습니다. 긴 계약서에서 특정 조항을 찾거나, 재무제표의 표와 주석을 함께 읽거나, 여러 문서를 비교해 답의 근거 위치를 남기는 작업이 대표적입니다. 반대로 짧고 정리된 문서에서 답이 상위 chunk에 꾸준히 나온다면 one-shot RAG가 더 단순하고 결과를 예측하기 쉽습니다.

여러 단계로 검색하는 만큼 운영할 부분은 늘어납니다. 모델이 더 많은 도구 호출을 결정해야 하고, 검색 backend와 MCP server, 문서 offset metadata가 실행 경로에 추가됩니다. 사용자마다 읽을 수 있는 문서가 다르다면 agent가 `open`이나 `grep`을 호출할 때도 같은 접근 제어(ACL)를 적용해야 합니다. 이 규칙이 빠지면 검색 정확도가 아니라 권한 우회가 문제가 될 수 있습니다.

한국의 금융, 공공, 제조 조직에는 긴 PDF와 표 중심 문서가 많습니다. 답뿐 아니라 근거가 있는 문서 위치를 남겨야 하는 업무도 많아 직접 시험해 볼 가치가 있습니다. 다만 Mistral이 설명하는 cloud, on-premises, isolation boundary가 한국의 개인정보보호법이나 전자금융 규제를 자동으로 충족하는 것은 아닙니다. 실제 도입에서는 데이터 위치, logging, index 보존 기간과 사용자별 문서 권한을 별도로 설계해야 합니다.

## 공개 자료로 확인한 범위

이 기사는 Agentic Search를 직접 실행하지 않았으며 재현성 상태는 R1입니다. 공식 문서에서 retrieval loop, 도구 이름, SDK 구성, MCP server 연결 방법, starter app, PyPI 패키지 version과 license를 확인했습니다. 하지만 FinanceBench나 OfficeQA Pro를 같은 환경에서 다시 실행한 로그는 없습니다.

공개 artifact로는 `mistralai-search-toolkit` 패키지와 `mistralai/search-starter-app` template이 있습니다. PyPI provenance가 가리키는 source repository 일부는 private이며, Mistral의 benchmark 실행 script와 원 로그도 함께 공개되지는 않았습니다. 따라서 이번 공개의 의미는 문서 안을 여러 단계로 탐색하는 search loop와 구현 경로가 나왔다는 데 있습니다. 성능 수치는 Mistral의 자체 측정으로 구분해 봐야 합니다.

## 이해상충과 취재 조건

이 기사에 사용한 발표문, Agentic Search 문서, Search Toolkit 문서, PyPI package page와 starter app은 모두 Mistral 또는 Mistral 공식 계정이 관리하는 1차 자료입니다. 기능 구조, 공개 패키지, version, license, 설치 조건을 확인하는 데는 적합하지만, Mistral의 성능 우월성을 독립적으로 증명하지는 않습니다.

사전 briefing, 제공받은 account·credit·hardware, 후원, 광고, NDA 또는 embargo는 없었습니다. 검색 결과와 다른 후보 경로는 발견 신호로만 사용했고, 기사 사실은 열린 공식 원문과 공개 package metadata로 확인했습니다.

## 근거 원장

| Claim | 판정 | 근거와 한계 |
|---|---|---|
| C1. Mistral은 2026년 8월 20일 Agentic Search를 공개했고, 이를 Search Toolkit, Libraries, Studio, Vibe에서 사용할 수 있는 retrieval layer로 설명했습니다. | E1 · P1 | Mistral 발표문으로 확인했습니다. 출시·제품 설명의 근거이며 성능 우월성의 독립 검증은 아닙니다. |
| C2. Agentic Search는 `search`, `open`, `navigate`, `read`, `grep`을 사용해 검색 결과를 고정 chunk로 끝내지 않고 문서 안을 이동하며 증거를 모으는 retrieval loop입니다. | E2 · P1 | Mistral Agentic Search 문서와 발표문으로 확인했습니다. 실제 도구 호출은 실행하지 않았습니다. |
| C3. Search Toolkit은 ingestion, retrieval, evaluation을 위한 Python framework이며 loader, extractor, splitter, embedder, vector store, retriever, reranker, semantic cache 같은 교체 가능한 구성 요소를 제공합니다. | E2 · P1 | Search Toolkit 공식 문서와 PyPI package page로 확인했습니다. 모든 backend와 optional extra를 설치해 검증하지는 않았습니다. |
| C4. starter app은 Vespa index와 MCP server를 포함한 Agentic Search project scaffold를 제공하며, agent가 search/navigation 도구를 호출하는 경로를 문서화합니다. | E2 · P1/P2 | Agentic Search 문서와 GitHub starter app 경로로 확인했습니다. repository 코드를 local clone하거나 실행하지는 않았습니다. |
| C5. Mistral은 FinanceBench와 OfficeQA Pro에서 accuracy, token, latency 개선을 보고했지만, 이 수치는 Mistral의 자체 benchmark 결과입니다. | E2 · P1 | 발표문과 Agentic Search 문서로 조건과 수치를 확인했습니다. 독립 재현, 원 로그, 전체 실패 분포는 확인하지 못했습니다. |
| C6. PyPI는 `mistralai-search-toolkit` 최신 release를 `0.0.11`, 공개일을 2026년 7월 31일, license를 Apache-2.0, Python 요구사항을 `>=3.12, <3.15`로 표시합니다. | E2 · P2 | PyPI package metadata로 확인했습니다. PyPI provenance의 source repository 일부는 private로 표시됩니다. |

## 출처

1. Mistral, "Agentic Search. More accurate and efficient results from your AI systems.": https://mistral.ai/news/agentic-search/
2. Mistral Docs, "Agentic Search": https://docs.mistral.ai/studio/search/agentic-search
3. Mistral Docs, "Search Toolkit": https://docs.mistral.ai/studio/search/search-toolkit
4. PyPI, `mistralai-search-toolkit`: https://pypi.org/project/mistralai-search-toolkit/
5. GitHub, `mistralai/search-starter-app`: https://github.com/mistralai/search-starter-app/tree/main
