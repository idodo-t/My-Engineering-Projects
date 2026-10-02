import argparse
from pathlib import Path

from assistant import Assistant, KnowledgeBase, configured_generator


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with a local document-grounded assistant")
    parser.add_argument("--knowledge", default=str(Path(__file__).parent / "knowledge"))
    args = parser.parse_args()
    agent = Assistant(KnowledgeBase.from_directory(args.knowledge), configured_generator())
    mode = "LLM generation enabled" if agent.generator else "offline retrieval mode"
    print(f"Document assistant ({mode}). Commands: /remember NOTE, /memory, /quit")
    while True:
        try:
            message = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if message.lower() in {"/quit", "/exit"}:
            break
        print(f"Assistant> {agent.handle(message)}")


if __name__ == "__main__":
    main()
