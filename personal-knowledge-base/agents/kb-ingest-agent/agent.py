#!/usr/bin/env python3
import json
import os
import re
import hashlib
import sqlite3
import struct
from datetime import datetime, timezone

import sqlite_vec
from sentence_transformers import SentenceTransformer

from friday_agent_sdk import agent, ok, err, AgentContext, run, parse_input

# Storage location for the SQLite vector DB. Override with KB_DB_PATH if you
# want it somewhere other than the Friday user-data tree.
DB_PATH = os.path.expanduser(
    os.environ.get("KB_DB_PATH", "~/.friday/local/workspaces/personal-knowledge-base/kb.db")
)
# Root of Friday's per-chat upload scratch dir. The agent walks this to locate
# uploaded PDFs by SHA-256 (see Strategy 1 below). Override with
# FRIDAY_UPLOADS_ROOT if your FRIDAY_HOME is non-default.
UPLOADS_ROOT = os.path.expanduser(
    os.environ.get("FRIDAY_UPLOADS_ROOT", "~/.friday/local/scratch/uploads")
)
MODEL_NAME = "BAAI/bge-large-en-v1.5"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_text_from_tool_result(result) -> str:
    """
    ctx.tools.call() returns results in one of several shapes depending on
    whether the runtime inlines or lifts the payload:
      - {"content": [{"type": "text", "text": "..."}]}   ← most common
      - {"markdown": "..."}                               ← parse_artifact direct
      - {"contents": "..."}                               ← get_artifact inline
      - a plain string
    Returns the innermost text string, or "" if nothing found.
    """
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        for block in result:
            if isinstance(block, dict) and block.get("type") == "text":
                return block.get("text", "")
        return ""
    if isinstance(result, dict):
        # Unwrap content-block wrapper first
        blocks = result.get("content", [])
        if blocks:
            for b in blocks:
                if isinstance(b, dict) and b.get("type") == "text":
                    return b.get("text", "")
        # Direct text keys
        for key in ("markdown", "contents", "content", "text"):
            val = result.get(key, "")
            if val and isinstance(val, str):
                return val
    return ""


def follow_lifted_stub(raw: str, ctx: AgentContext) -> str:
    """
    If the runtime auto-lifted a large result to an artifact ref, follow it.
    Pattern: '[attachment lifted to artifact <uuid> ...]'
    Returns the real text content, or the original raw string if not a stub.
    """
    match = re.search(r"attachment lifted to artifact ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", raw)
    if not match:
        return raw
    lifted_id = match.group(1)
    ctx.stream.progress(f"Following lifted artifact {lifted_id[:8]}...")
    try:
        lifted = ctx.tools.call("get_artifact", {"artifactId": lifted_id})
        text = extract_text_from_tool_result(lifted)
        # The lifted artifact for parse_artifact is a JSON envelope: {"markdown": "..."}
        if text and text.strip().startswith("{"):
            try:
                parsed = json.loads(text)
                text = parsed.get("markdown", text)
            except Exception:
                pass
        return text if text else raw
    except Exception:
        return raw


def extract_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF given its raw bytes, using pymupdf."""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        for i, page in enumerate(doc):
            t = page.get_text()
            if t.strip():
                pages.append(f"=== Page {i+1} ===\n{t}")
        return "\n\n".join(pages)
    except Exception:
        return ""


def find_upload_by_sha256(sha256: str) -> str | None:
    """Walk the uploads directory and return the path of the file with the given SHA-256."""
    if not sha256 or not os.path.exists(UPLOADS_ROOT):
        return None
    for dirpath, _dirs, filenames in os.walk(UPLOADS_ROOT):
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, "rb") as f:
                    data = f.read()
                if hashlib.sha256(data).hexdigest() == sha256:
                    return fpath
            except OSError:
                continue
    return None


def find_upload_by_artifact_id(artifact_id: str) -> str | None:
    """
    Fallback: scan uploads for any PDF whose bytes hash to what we'd expect,
    or just return the first PDF we find that was uploaded in any chat for this
    workspace. Used when contentRef is not available from get_artifact.
    Strategy: look for files in uploads dirs for this workspace session.
    """
    if not os.path.exists(UPLOADS_ROOT):
        return None
    # Collect all upload files sorted by mtime (newest first)
    candidates = []
    for dirpath, _dirs, filenames in os.walk(UPLOADS_ROOT):
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            try:
                candidates.append((os.path.getmtime(fpath), fpath))
            except OSError:
                continue
    candidates.sort(reverse=True)
    # Return the first one that looks like a PDF (magic bytes %PDF)
    # and hasn't already been seen (we check by sha256 against DB later)
    for _, fpath in candidates:
        try:
            with open(fpath, "rb") as f:
                header = f.read(4)
            if header == b"%PDF":
                return fpath
        except OSError:
            continue
    return None


def strip_html(text: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</\s*script\s*>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</\s*style\s*>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def chunk_text(text: str) -> list:
    segments = []
    for block in re.split(r"\n\n+", text):
        for sentence in re.split(r"(?<=\. )", block):
            piece = sentence.strip()
            if piece:
                segments.append(piece)

    chunks = []
    current = ""
    for seg in segments:
        if len(current) + len(seg) + 1 > CHUNK_SIZE and current:
            chunks.append(current)
            overlap_start = max(0, len(current) - CHUNK_OVERLAP)
            current = current[overlap_start:] + " " + seg
        else:
            current = (current + " " + seg).strip() if current else seg
    if current:
        chunks.append(current)
    return chunks


def serialize_vector(vec) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def init_db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            source TEXT,
            title TEXT,
            ingested_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunk_metadata (
            chunk_id TEXT PRIMARY KEY,
            doc_id TEXT,
            chunk_text TEXT,
            chunk_index INTEGER
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunk_embeddings USING vec0(
            chunk_id TEXT PRIMARY KEY,
            embedding float[1024]
        )
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

@agent(
    id="kb-ingest-agent",
    version="1.0.0",
    description="Ingests a URL or PDF artifact into the personal knowledge base. Chunks content, embeds with BAAI/bge-large-en-v1.5, stores vectors in SQLite with sqlite-vec.",
)
def execute(prompt: str, ctx: AgentContext):
    try:
        params = parse_input(prompt)
        # FSM signal payloads are wrapped as {"config": {...}} — unwrap if needed
        if "config" in params and isinstance(params["config"], dict) and "url" not in params and "artifact_id" not in params:
            params = params["config"]
        url = params.get("url")
        artifact_id = params.get("artifact_id")
        source_label = params.get("source_label", "")

        if not url and not artifact_id:
            return err("Either 'url' or 'artifact_id' must be provided.")

        ctx.stream.progress("Initializing embedding model...")
        model = SentenceTransformer(MODEL_NAME)
        conn = init_db()

        title = source_label or ""
        source = ""
        text = ""

        # ---------------------------------------------------------------
        # URL ingestion
        # ---------------------------------------------------------------
        if url:
            source = url
            ctx.stream.progress(f"Fetching {url}...")
            response = ctx.http.fetch(url)
            raw_text = response.body
            text = strip_html(raw_text)
            if not title:
                m = re.search(r"<title[^>]*>(.*?)</title>", raw_text, re.IGNORECASE | re.DOTALL)
                title = m.group(1).strip() if m else url

        # ---------------------------------------------------------------
        # Artifact ingestion — 4-strategy cascade
        # ---------------------------------------------------------------
        elif artifact_id:
            source = f"artifact:{artifact_id}"
            if not title:
                title = source_label or f"Artifact {artifact_id}"

            # --- Read artifact metadata (contentRef + mimeType) ---
            ctx.stream.progress("Reading artifact metadata...")
            meta_raw = ctx.tools.call("get_artifact", {"artifactId": artifact_id})
            meta_text = extract_text_from_tool_result(meta_raw)
            artifact_meta = {}
            if meta_text and meta_text.strip().startswith("{"):
                try:
                    artifact_meta = json.loads(meta_text)
                except Exception:
                    pass

            data_field = artifact_meta.get("data", {}) if isinstance(artifact_meta, dict) else {}
            mime_type = data_field.get("mimeType", "") if isinstance(data_field, dict) else ""
            content_ref = data_field.get("contentRef", "") if isinstance(data_field, dict) else ""
            is_pdf = mime_type == "application/pdf"

            # --- Strategy 1a: locate file by contentRef SHA-256 ---
            if content_ref and not text:
                ctx.stream.progress("Locating upload by contentRef...")
                disk_path = find_upload_by_sha256(content_ref)
                if disk_path:
                    ctx.stream.progress(f"Found at {disk_path}, extracting...")
                    with open(disk_path, "rb") as f:
                        raw_bytes = f.read()
                    if raw_bytes[:4] == b"%PDF":
                        text = extract_pdf_bytes(raw_bytes)
                    else:
                        text = raw_bytes.decode("utf-8", errors="replace")

            # --- Strategy 1b: scan uploads for any matching PDF (when contentRef stripped) ---
            if not text and is_pdf:
                ctx.stream.progress("Scanning uploads for PDF...")
                disk_path = find_upload_by_artifact_id(artifact_id)
                if disk_path:
                    ctx.stream.progress(f"Found candidate at {disk_path}, extracting...")
                    with open(disk_path, "rb") as f:
                        raw_bytes = f.read()
                    if raw_bytes[:4] == b"%PDF":
                        text = extract_pdf_bytes(raw_bytes)

            # --- Strategy 2: parse_artifact + follow any lifted stub ---
            if not text:
                ctx.stream.progress("Trying parse_artifact...")
                try:
                    pa_result = ctx.tools.call("parse_artifact", {"artifactId": artifact_id})
                    raw_str = extract_text_from_tool_result(pa_result)
                    raw_str = follow_lifted_stub(raw_str, ctx)
                    # parse_artifact may return a JSON envelope {"markdown": "..."}
                    if raw_str and raw_str.strip().startswith("{"):
                        try:
                            raw_str = json.loads(raw_str).get("markdown", raw_str)
                        except Exception:
                            pass
                    if raw_str and "attachment lifted to artifact" not in raw_str and len(raw_str.strip()) > 10:
                        text = raw_str
                except Exception:
                    pass

            # --- Strategy 3: inline contents from get_artifact (small text artifacts) ---
            if not text:
                ctx.stream.progress("Trying inline artifact contents...")
                inline = artifact_meta.get("contents", "") if isinstance(artifact_meta, dict) else ""
                inline = follow_lifted_stub(inline, ctx) if inline else ""
                if inline and "attachment lifted to artifact" not in inline and len(inline.strip()) > 10:
                    text = inline

        # ---------------------------------------------------------------
        # Embed and store
        # ---------------------------------------------------------------
        if not text or len(text.strip()) < 10:
            conn.close()
            return err("No meaningful content could be extracted from the source.")

        doc_id = hashlib.sha256(source.encode()).hexdigest()[:16]

        existing = conn.execute("SELECT id FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if existing:
            conn.close()
            return ok({"doc_id": doc_id, "status": "already_ingested", "source": source})

        chunks = chunk_text(text)
        if not chunks:
            conn.close()
            return err("Content could not be split into chunks.")

        ctx.stream.progress(f"Embedding {len(chunks)} chunks...")
        embeddings = model.encode(
            chunks, batch_size=32, show_progress_bar=False, normalize_embeddings=True
        )

        ctx.stream.progress("Storing in knowledge base...")
        now = datetime.now(timezone.utc).isoformat()

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{doc_id}_{i:04d}"
            conn.execute(
                "INSERT INTO chunk_metadata (chunk_id, doc_id, chunk_text, chunk_index) VALUES (?, ?, ?, ?)",
                (chunk_id, doc_id, chunk, i),
            )
            conn.execute(
                "INSERT INTO chunk_embeddings (chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, serialize_vector(embedding)),
            )

        conn.execute(
            "INSERT INTO documents (id, source, title, ingested_at) VALUES (?, ?, ?, ?)",
            (doc_id, source, title, now),
        )
        conn.commit()
        conn.close()

        ctx.tools.call(
            "save_memory_entry",
            {
                "memoryName": "knowledge-base",
                "text": f"SOURCE: {source}\nTITLE: {title}\nDOC_ID: {doc_id}\nINGESTED: {now}\nCHUNKS: {len(chunks)}",
            },
        )

        return ok({"doc_id": doc_id, "chunks": len(chunks), "source": source, "title": title})

    except Exception as e:
        return err(str(e))


if __name__ == "__main__":
    run()
