import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str


class KnowledgeBase:
    def __init__(self, documents: list[Chunk]) -> None:
        self.documents = documents
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None
        if documents:
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            self.matrix = self.vectorizer.fit_transform([item.text for item in documents])

    @classmethod
    def from_directory(cls, directory: str | Path, chunk_size: int = 700, overlap: int = 80):
        if chunk_size < 1 or overlap < 0 or overlap >= chunk_size:
            raise ValueError("Require chunk_size > overlap >= 0")
        root = Path(directory).expanduser()
        documents: list[Chunk] = []
        if not root.is_dir():
            return cls(documents)

        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8").strip()
            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                chunk = text[start:end].strip()
                if chunk:
                    documents.append(Chunk(chunk, path.name))
                if end == len(text):
                    break
                start = end - overlap
        return cls(documents)

    def search(self, query: str, limit: int = 3) -> list[dict[str, str | float]]:
        if not query.strip() or limit < 1 or self.vectorizer is None or self.matrix is None:
            return []
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).ravel()
        ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
        return [
            {"text": self.documents[index].text, "source": self.documents[index].source, "score": float(score)}
            for index, score in ranked[:limit]
            if score > 0
        ]


class OpenAICompatibleGenerator:
    def __init__(self, api_key: str, model: str, base_url: str, timeout: float = 30) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def __call__(self, question: str, sources: list[dict[str, str | float]], memory: list[dict[str, str]]) -> str:
        context = "\n\n".join(f"[{item['source']}] {item['text']}" for item in sources)
        messages = [
            {"role": "system", "content": "Answer using only the supplied context. If it does not contain the answer, say so. Cite source filenames."},
            *memory[-6:],
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]
        payload = json.dumps({"model": self.model, "messages": messages, "temperature": 0.2}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as error:
            raise RuntimeError(f"Text generation request failed: {error}") from error
        try:
            return str(result["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError("The text-generation service returned an unexpected response") from error


def configured_generator() -> Callable | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAICompatibleGenerator(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )


class Assistant:
    def __init__(self, knowledge: KnowledgeBase, generator: Callable | None = None, memory_limit: int = 12) -> None:
        if memory_limit < 1:
            raise ValueError("memory_limit must be positive")
        self.knowledge = knowledge
        self.generator = generator
        self.memory_limit = memory_limit
        self.memory: list[str] = []
        self.history: list[dict[str, str]] = []

    def handle(self, message: str) -> str:
        text = message.strip()
        if not text:
            return "Please enter a question or command."
        if text.startswith("/remember "):
            fact = text.removeprefix("/remember ").strip()
            if not fact:
                return "Add a note after /remember."
            self.memory.append(fact)
            self.memory = self.memory[-self.memory_limit :]
            return "I saved that note for this session."
        if text == "/memory":
            return "\n".join(f"- {fact}" for fact in self.memory) or "There are no saved notes in this session."

        sources = self.knowledge.search(text)
        if not sources:
            answer = "I could not find relevant information in the local knowledge base."
        elif self.generator:
            recent = self.history[-6:]
            memory_context = [{"role": "system", "content": f"User notes: {'; '.join(self.memory)}"}] if self.memory else []
            answer = self.generator(text, sources, memory_context + recent)
        else:
            answer = "\n\n".join(f"From {item['source']}: {item['text']}" for item in sources)

        self.history.extend([{"role": "user", "content": text}, {"role": "assistant", "content": answer}])
        self.history = self.history[-self.memory_limit :]
        return answer
