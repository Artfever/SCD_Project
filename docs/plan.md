# Work plan for two members

Members: `Artfever` (main laptop, all heavy work) and `TahaSohail-Goat`.
Module names are those of the course description. Tasks are
[GitHub issues](https://github.com/Artfever/SCD_Project/issues) grouped into milestones.

## 1. Principle: split by hardware, not by importance

| | `Artfever` | `TahaSohail-Goat` |
| --- | --- | --- |
| Needs | GPU, Kubernetes cluster, Jenkins, large downloads | Any laptop that runs Python and Node |
| Runs | Ingestion, embeddings, model serving, cluster, delivery, full evaluation | Unit and component tests, Docker Compose for the services in use |
| Models | Real local and fine-tuned models | Stubs and recorded model responses |
| Owns | M4, M5, M6, M6i, M7, M10, M10t, M14 | M1, M2, M3, M8, M9, M11, M12, M13 |

`TahaSohail-Goat` should never be blocked by the GPU or the cluster. Every model call goes behind an
interface that can replay recorded responses (Guide section 7), and `Artfever` commits the fixtures.

Both members must be able to explain the whole system. Each reviews every pull request of the other.

## 2. Module ownership

| Module | Owner | Reviewer | Load | Issues |
| --- | --- | --- | --- | --- |
| M1 Web UI and gateway | Taha | Artfever | light | #11, #12, #23 |
| M2 Profile, session, cache | Taha | Artfever | light | #6 |
| M3 Orchestrator | Taha | Artfever | light | #10, #22 |
| M4 Scout agents | Artfever | Taha | heavy | #13 |
| M5 Tool layer | Artfever | Taha | heavy | #9 |
| M6 Knowledge base | Artfever | Taha | heavy | #8, #15 |
| M6i Ingestion | Artfever | Taha | heavy | #14 |
| M7 Niche and trend analyst | Artfever | Taha | heavy | #16 |
| M8 Idea generators | Taha | Artfever | light | #21 |
| M9 Validation agents | Taha | Artfever | light | #18 (rubrics: #17, Artfever) |
| M10 Scoring model | Artfever | Taha | heavy | #26, #27 |
| M10t Fine-tuning | Artfever | Taha | heavy | #24, #25 |
| M11 Verdict engine | Taha | Artfever | light | #7, #19, #33 |
| M12 Critic and guardrails | Taha | Artfever | light | #20 |
| M13 AgenticOps | Taha | Artfever | light | #28, #29, #30 |
| M14 Platform | Artfever | Taha | heavy | #1, #5, #31 |
| Shared | Both | Both | light | #3, #32, #34, #35 |

Estimated effort (S = 1, M = 2, L = 4, shared tasks counted for both) is close to even: about 43
points for `Artfever` and 46 for `TahaSohail-Goat`. Rebalance at the end of each milestone.

## 3. Milestones

The submission date is not recorded yet. The weeks below assume eight weeks and must be replaced
with real dates in issue #3.

| Milestone | Week | `Artfever` | `TahaSohail-Goat` | Done when |
| --- | --- | --- | --- | --- |
| P0 Foundations | 1 | #1, #5, #3 | #2, #4, #3 | Protected main, agreed contracts, Jenkins running |
| P1 Walking skeleton | 2-3 | #8, #9 | #6, #7, #10, #11, #12 | One Validate run goes from UI to verdict on Kubernetes with stubbed scores |
| P2 Data and knowledge base | 3-4 | #13, #14, #15, #16 | continue P1, start #19 | 1,500 cards, hybrid search, retrieval gate active |
| P3 Agents and verdict | 4-6 | #17 | #18, #19, #20, #21, #22, #23 | Validate and Discover work with real evidence |
| P4 Model and AgenticOps | 5-7 | #24, #25, #26, #27 | #28, #29, #30 | Fine-tuned model serving, traces, evaluation and drift report |
| P5 Tuning and submission | 8 | #31, #32, #34, #35 | #32, #33, #34, #35 | Tuned thresholds, screenshots, report, signed table |

If time runs short, keep every required capability thin rather than perfecting some and missing
others. Do not leave Docker, Jenkins or Kubernetes to the end (Guide section 12).

## 4. Hand-offs

| What is handed over | From | To | Unblocks |
| --- | --- | --- | --- |
| Contracts and example fixtures (#4) | Taha | Artfever | Every module |
| Search API with a seed fixture (#8) | Artfever | Taha | #10, #18 |
| Rubrics (#17) | Artfever | Taha | #18, and the dataset #24 |
| Recorded model responses | Artfever | Taha | #18, #20, #21, #30 |
| Gap list (#16) | Artfever | Taha | #21 |
| Scorer `/score` contract, stub first (#26) | Artfever | Taha | #18 |
| Evaluation harness (#29) | Taha | Artfever | Nightly Jenkins stage, #27 |

Start #17 during P2 even though it belongs to P3, because two later tasks wait for it.

## 5. Weekly routine

1. Start of week: pick issues, check hand-offs, move anything blocked.
2. During the week: small pull requests, each reviewed within a day.
3. End of week: `Artfever` deploys `main` on the laptop, both take screenshots, and each explains
   one change the other merged.
4. Both add to the [AI-usage log](ai-usage-log.md) as they go.

## 6. Definition of done

- Linked issue closed by a reviewed pull request with all required checks green.
- Tests cover the new behaviour; input and output match the contracts.
- `/ready` reflects real dependencies.
- Memory request and limit are still right ([resource budget](resource-budget.md)).
- Docs updated.

## 7. Risks

| Risk | Response |
| --- | --- |
| 24 GB is not enough for everything at once | Run one mode at a time, enforce limits, measure each milestone |
| One laptop runs all heavy work | Keep data snapshots and scripts in the repository; push often |
| Unknown deadline | Record it in #3 and re-plan |
| Hosted model needs a key and a route out of the cluster | Decide in #3 (decision record 0005) |
| Source rate limits slow ingestion | Start #13 early, cache, keep a snapshot |
| Uneven git history | Check authored and reviewed pull requests at each milestone |
