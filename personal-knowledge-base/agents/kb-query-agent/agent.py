#!/usr/bin/env python3
import os
import sqlite3
import struct

import sqlite_vec
from sentence_transformers import SentenceTransformer

from friday_agent_sdk import agent, ok, err, AgentContext, run, parse_input

# Must match the ingest agent — override both with the same KB_DB_PATH if you
# move the DB.
DB_PATH = os.path.expanduser(
    os.environ.get("KB_DB_PATH", "~/.friday/local/workspaces/personal-knowledge-base/kb.db")
)
MODEL_NAME = "BAAI/bge-large-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
TOP_K = 10


def serialize_vector(vec) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


@agent(
    id="kb-query-agent",
    version="1.0.0",
    description="Queries the personal knowledge base. Embeds a question with BAAI/bge-large-en-v1.5, performs ANN search in sqlite-vec, retrieves top-K chunks, and synthesizes a grounded answer.",
)
def execute(prompt: str, ctx: AgentContext):
    try:
        params = parse_input(prompt)
        question = params.get("question")

        if not question:
            return err("A 'question' must be provided.")

        if not os.path.exists(DB_PATH):
            return ok({
                "answer": "The knowledge base is empty — no documents have been ingested yet.",
                "sources_consulted": [],
                "chunks_retrieved": 0,
            })

        ctx.stream.progress("Loading embedding model...")
        model = SentenceTransformer(MODEL_NAME)

        conn = sqlite3.connect(DB_PATH)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)

        ctx.stream.progress("Searching knowledge base...")
        query_text = QUERY_PREFIX + question
        query_embedding = model.encode(
            [query_text], normalize_embeddings=True, show_progress_bar=False
        )[0]
        query_bytes = serialize_vector(query_embedding)

        rows = conn.execute(
            """
            SELECT ce.chunk_id, ce.distance, cm.doc_id, cm.chunk_text
            FROM chunk_embeddings ce
            JOIN chunk_metadata cm ON ce.chunk_id = cm.chunk_id
            WHERE ce.embedding MATCH ? AND k = ?
            ORDER BY ce.distance
            """,
            (query_bytes, TOP_K),
        ).fetchall()

        if not rows:
            conn.close()
            return ok({
                "answer": "No relevant information found in the knowledge base for this question.",
                "sources_consulted": [],
                "chunks_retrieved": 0,
            })

        doc_ids = list({row[2] for row in rows})
        placeholders = ",".join("?" for _ in doc_ids)
        docs = conn.execute(
            f"SELECT id, source, title FROM documents WHERE id IN ({placeholders})",
            doc_ids,
        ).fetchall()
        conn.close()

        doc_map = {row[0]: {"source": row[1], "title": row[2]} for row in docs}

        context_parts = []
        for i, (chunk_id, distance, doc_id, chunk_text) in enumerate(rows, 1):
            doc_info = doc_map.get(doc_id, {"source": "unknown", "title": "unknown"})
            context_parts.append(
                f"[{i}] (Source: {doc_info['title']} — {doc_info['source']})\n{chunk_text}"
            )
        context_block = "\n\n".join(context_parts)

        sources = [
            f"{doc_map[did]['title']} ({doc_map[did]['source']})"
            for did in doc_ids
            if did in doc_map
        ]

        ctx.stream.progress("Synthesizing answer...")
        synthesis_prompt = f"""Answer the following question based solely on the provided context chunks. Cite sources using bracket numbers [1], [2], etc. If the context doesn't contain enough information to answer fully, say so.

Question: {question}

Context:
{context_block}

Provide a clear, well-structured answer grounded in the above context."""

        response = ctx.llm.generate(
            messages=[{"role": "user", "content": synthesis_prompt}],
            model="anthropic:claude-sonnet-4-5",
        )

        return ok({
            "answer": response.text,
            "sources_consulted": sources,
            "chunks_retrieved": len(rows),
        })

    except Exception as e:
        return err(str(e))


if __name__ == "__main__":
    run()
