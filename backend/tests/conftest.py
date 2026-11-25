import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite:///./pulsar-test.db")
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
