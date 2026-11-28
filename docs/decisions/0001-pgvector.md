# 0001. Keep vectors in Postgres with pgvector

- **Status:** Proposed
- **Context:** The knowledge base needs hybrid search and the laptop has 24 GB of memory.
- **Options:** (1) pgvector with Postgres full-text search, (2) Qdrant, (3) another vector database.
- **Decision:** pgvector.
- **Why:** Keyword and vector search and metadata filters run in one service already required.
- **Cost:** Fewer search features than a dedicated vector database. Retrieval quality not yet measured.
- **AI use:** Drafted by Claude Code. Options and numbers still to be checked by both members.
