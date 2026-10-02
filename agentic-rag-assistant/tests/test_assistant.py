import tempfile
import unittest
from pathlib import Path

from assistant import Assistant, KnowledgeBase


class AssistantTests(unittest.TestCase):
    def test_retrieves_relevant_document_with_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "crops.md").write_text("Tomatoes need regular irrigation and warm soil.", encoding="utf-8")
            (root / "books.md").write_text("A library lends books to registered members.", encoding="utf-8")
            agent = Assistant(KnowledgeBase.from_directory(root))
            answer = agent.handle("How should I irrigate tomatoes?")
            self.assertIn("crops.md", answer)
            self.assertIn("irrigation", answer)

    def test_session_memory_tools(self) -> None:
        agent = Assistant(KnowledgeBase([]))
        self.assertEqual(agent.handle("/remember I prefer concise replies"), "I saved that note for this session.")
        self.assertIn("I prefer concise replies", agent.handle("/memory"))

    def test_unknown_question_does_not_make_up_an_answer(self) -> None:
        agent = Assistant(KnowledgeBase([ ]))
        self.assertIn("could not find relevant information", agent.handle("What is on Mars?"))


if __name__ == "__main__":
    unittest.main()
