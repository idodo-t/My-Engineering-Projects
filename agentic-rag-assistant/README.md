# Agentic RAG Conversational Assistant

I built a local document-grounded assistant with retrieval, source attribution, session memory, and a small command router. It works offline with extractive answers; an OpenAI-compatible chat-completions endpoint can optionally generate answers from retrieved context.

## Requirements

- Python 3.10 or newer
- scikit-learn
- Optional: an OpenAI-compatible API key and endpoint for generated answers

```bash
python -m pip install -r requirements.txt
python chat.py
```

Add private `.md` or `.txt` documents to `knowledge/` locally. Keep private documents and credentials out of this public repository.

## Usage

Ask a question in the terminal. The offline mode returns the best matching excerpts with source filenames. `/remember NOTE` stores a note for the current session, `/memory` lists session notes, and `/quit` exits.

To enable API generation, set `OPENAI_API_KEY`. Optionally set `OPENAI_BASE_URL` and `OPENAI_MODEL`. The key is read from the environment and is never stored in this repository. The generator is instructed to answer from retrieved context and cite source files.

## Scope

The local retriever uses TF-IDF and cosine similarity, not a hosted vector database. This is a clean, testable implementation of the described RAG and memory workflow; it does not include the original project's fine-tuning data or claim to reproduce its prior results.

Run tests with `python -m unittest discover -s tests -v`.
