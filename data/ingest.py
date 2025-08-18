import os
import sys
import gzip
import glob
import hashlib
import argparse
import re
import concurrent.futures
from typing import Iterable, List, Tuple, Dict, Any

import chromadb
from tqdm import tqdm
import ollama
import time

# Add parent directory to path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import EMBEDDING_MODEL, VECTOR_STORE_DIR, COLLECTION_NAME
from llama_index.core import Document
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.ollama import OllamaEmbedding

# Global pool of Ollama clients for parallel embedding across multiple servers
OLLAMA_CLIENTS: list[Any] = []

def _normalize_host_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return raw
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return f"http://{raw}"


def collect_file_paths(root_dirs: List[str]) -> List[str]:
    patterns = [
        *(os.path.join(d, "**", "*.txt") for d in root_dirs),
        *(os.path.join(d, "**", "*.txt.gz") for d in root_dirs),
    ]
    seen: set[str] = set()
    files: List[str] = []
    for pattern in patterns:
        for path in glob.iglob(pattern, recursive=True):
            if not os.path.isfile(path):
                continue
            if path in seen:
                continue
            seen.add(path)
            files.append(path)
    return files


def read_text_file(path: str) -> str:
    try:
        if path.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
                return f.read()
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


VERSE_RE = re.compile(r"^\[\d{3}_\d{3}\]")


def detect_structure(sample_text: str) -> str:
    lines = [ln.rstrip() for ln in sample_text.splitlines() if ln.strip()]
    if not lines:
        return "prose"
    verse_like = sum(1 for ln in lines if VERSE_RE.match(ln))
    if verse_like / max(1, len(lines)) >= 0.6:
        return "verse"

    short_lines = sum(1 for ln in lines if len(ln) < 80)
    median_len = sorted(len(ln) for ln in lines)[len(lines)//2]
    if median_len <= 60 and short_lines / max(1, len(lines)) >= 0.5:
        return "poetry"
    return "prose"


def split_paragraphs(text: str) -> list[str]:
    # Remove common boilerplate lines that add noise
    filtered_lines: list[str] = []
    for ln in text.splitlines():
        lns = ln.strip()
        lower = lns.lower()
        if not lns:
            filtered_lines.append("")
            continue
        if any(bad in lower for bad in [
            "scanned, proofed", "this text is in the public domain", "click to enlarge",
            "at sacred-texts.com", "publication", "contents", "[p.", "<page",
        ]):
            continue
        filtered_lines.append(ln)
    cleaned = "\n".join(filtered_lines)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", cleaned) if p.strip()]
    return paragraphs


def parse_verses(text: str) -> list[tuple[str, str]]:
    verses: list[tuple[str, str]] = []
    current_id: str | None = None
    current_lines: list[str] = []
    for ln in text.splitlines():
        if VERSE_RE.match(ln.strip()):
            # flush previous
            if current_id is not None and current_lines:
                verses.append((current_id, "\n".join(current_lines).strip()))
            # start new
            first_space = ln.find(" ")
            current_id = ln[:first_space] if first_space != -1 else ln.strip()
            current_lines = [ln[first_space+1:].strip() if first_space != -1 else ""]
        else:
            if current_id is not None:
                current_lines.append(ln.rstrip())
    if current_id is not None and current_lines:
        verses.append((current_id, "\n".join(current_lines).strip()))
    return verses


def pack_units_by_chars(units: list[str], target_chars: int, overlap_units: int) -> list[list[str]]:
    chunks: list[list[str]] = []
    buf: list[str] = []
    count = 0
    for u in units:
        if not buf:
            buf.append(u)
            count = len(u)
            continue
        if count + 1 + len(u) <= target_chars:
            buf.append(u)
            count += 1 + len(u)
        else:
            chunks.append(buf)
            # prepare next buffer with overlap
            if overlap_units > 0:
                buf = buf[-overlap_units:].copy()
                count = sum(len(s) for s in buf) + max(0, len(buf) - 1)
            else:
                buf = []
                count = 0
            if not buf:
                buf = [u]
                count = len(u)
            else:
                if count + 1 + len(u) <= target_chars:
                    buf.append(u)
                    count += 1 + len(u)
                else:
                    chunks.append([u])
                    buf = []
                    count = 0
    if buf:
        chunks.append(buf)
    return chunks


def chunk_semantic(text: str) -> list[Dict[str, Any]]:
    try:
        embed = OllamaEmbedding(model_name=EMBEDDING_MODEL)
        splitter = SemanticSplitterNodeParser(
            embed_model=embed,
            breakpoint_percentile_threshold=95,
            buffer_size=1,
        )
        nodes = splitter.get_nodes_from_documents([Document(text=text)])
        results: list[Dict[str, Any]] = []
        for i, node in enumerate(nodes):
            try:
                node_text = node.get_content()  # type: ignore[attr-defined]
            except Exception:
                node_text = getattr(node, "text", "")
            node_text = (node_text or "").strip()
            if not node_text:
                continue
            results.append({
                "text": node_text,
                "meta": {"strategy": "semantic", "semantic_index": i, "char_count": len(node_text)},
            })
        if results:
            return results
    except Exception:
        pass
    # Fallback to simple paragraph packing
    paragraphs = split_paragraphs(text)
    packed = pack_units_by_chars(paragraphs, target_chars=1200, overlap_units=1)
    chunks: list[Dict[str, Any]] = []
    for i, group in enumerate(packed):
        txt = "\n\n".join(group).strip()
        if txt:
            chunks.append({
                "text": txt,
                "meta": {"strategy": "paragraph_fallback", "para_count": len(group), "char_count": len(txt)},
            })
    return chunks


def chunk_verses(text: str) -> list[Dict[str, Any]]:
    verses = parse_verses(text)
    if not verses:
        return chunk_semantic(text)
    verse_units = [f"{vid} {vtxt}".strip() for vid, vtxt in verses]
    groups = pack_units_by_chars(verse_units, target_chars=1000, overlap_units=2)
    chunks: list[Dict[str, Any]] = []
    for i, group in enumerate(groups):
        txt = "\n".join(group).strip()
        if not txt:
            continue
        start_marker = verses[i * 1][0] if i < len(verses) else ""
        end_marker = start_marker
        # Try to infer first/last verse id in group
        first_id = None
        last_id = None
        for line in group:
            m = VERSE_RE.match(line)
            if m and first_id is None:
                first_id = m.group(0)
            if m:
                last_id = m.group(0)
        chunks.append({
            "text": txt,
            "meta": {
                "strategy": "verse",
                "char_count": len(txt),
                "first_marker": first_id or "",
                "last_marker": last_id or "",
                "verse_count": len(group),
            },
        })
    return chunks


def adaptive_chunks_with_meta(text: str, mode: str = "semantic") -> list[Dict[str, Any]]:
    if mode == "fast":
        paragraphs = split_paragraphs(text)
        packed = pack_units_by_chars(paragraphs, target_chars=1200, overlap_units=1)
        chunks: list[Dict[str, Any]] = []
        for i, group in enumerate(packed):
            txt = "\n\n".join(group).strip()
            if txt:
                chunks.append({
                    "text": txt,
                    "meta": {"strategy": "paragraph_fast", "para_count": len(group), "char_count": len(txt)},
                })
        return chunks
    sample = text[:4000]
    kind = detect_structure(sample)
    if kind == "verse":
        return chunk_verses(text)
    else:
        return chunk_semantic(text)


def _embed_single(text: str) -> List[float]:
    last_error: Exception | None = None
    for attempt_index in range(3):
        try:
            resp = ollama.embeddings(
                model=EMBEDDING_MODEL,
                prompt=text,
            )
            return resp["embedding"]  # type: ignore[index]
        except Exception as error:  # retry transient connection errors
            last_error = error
            # simple exponential backoff: 1s, 2s, 4s
            time.sleep(1 * (2 ** attempt_index))
    # if all retries failed, re-raise the last error
    assert last_error is not None
    raise last_error


def compute_embeddings(batch_texts: List[str], workers: int = 4) -> List[List[float]]:
    if workers <= 1 or len(batch_texts) <= 1:
        return [_embed_single(t) for t in batch_texts]
    futures: list[concurrent.futures.Future] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for t in batch_texts:
            futures.append(executor.submit(_embed_single, t))
        # preserve order of inputs
        results = [f.result() for f in futures]
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sources",
        nargs="+",
        default=[
            "sacred_texts_archive/extracted",
            "sacred_texts_archive",
        ],
        help="One or more directories to ingest from",
    )
    parser.add_argument("--mode", choices=["semantic", "fast"], default="semantic", help="Chunking mode: semantic (default) or fast paragraph-based")
    parser.add_argument("--embed-workers", type=int, default=4, help="Parallel embedding workers per batch")
    parser.add_argument("--db-batch-size", type=int, default=32, help="Number of chunks per upsert batch")
    args = parser.parse_args()

    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    sources = args.sources

    add_batch_ids: List[str] = []
    add_batch_docs: List[str] = []
    add_batch_metas: List[dict] = []
    add_batch_embeddings: List[List[float]] = []

    BATCH_SIZE = max(1, int(args.db_batch_size))

    file_paths = collect_file_paths(sources)
    for path in tqdm(file_paths, desc="Files", unit="file"):
        content = read_text_file(path)
        chunk_items = adaptive_chunks_with_meta(content, mode=args.mode)
        if not chunk_items:
            continue
        for idx, item in enumerate(tqdm(chunk_items, desc="Chunks", unit="chunk", leave=False)):
            ch = item["text"]
            meta_extra = item.get("meta", {}) if isinstance(item, dict) else {}
            uid_raw = f"{path}:{idx}:{meta_extra.get('first_marker', '')}"
            uid = hashlib.sha1(uid_raw.encode("utf-8")).hexdigest()
            add_batch_ids.append(uid)
            add_batch_docs.append(ch)
            base_meta: Dict[str, Any] = {
                "source_path": path,
                "chunk_index": idx,
            }
            if isinstance(meta_extra, dict):
                base_meta.update(meta_extra)
            add_batch_metas.append(base_meta)

            if len(add_batch_docs) >= BATCH_SIZE:
                add_batch_embeddings = compute_embeddings(add_batch_docs, workers=int(args.embed_workers))
                # Use upsert to safely re-run ingestion without duplicate-id errors
                collection.upsert(  # type: ignore[attr-defined]
                    ids=add_batch_ids,
                    documents=add_batch_docs,
                    metadatas=add_batch_metas,
                    embeddings=add_batch_embeddings,
                )
                add_batch_ids.clear()
                add_batch_docs.clear()
                add_batch_metas.clear()
                add_batch_embeddings.clear()

    if add_batch_docs:
        add_batch_embeddings = compute_embeddings(add_batch_docs, workers=int(args.embed_workers))
        collection.upsert(  # type: ignore[attr-defined]
            ids=add_batch_ids,
            documents=add_batch_docs,
            metadatas=add_batch_metas,
            embeddings=add_batch_embeddings,
        )

    print(f"Ingestion complete. Collection '{COLLECTION_NAME}' stored at '{VECTOR_STORE_DIR}'.")


if __name__ == "__main__":
    main()


