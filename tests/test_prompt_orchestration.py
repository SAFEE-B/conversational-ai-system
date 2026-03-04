from backend import extract_first_question
from main import build_system_prompt, format_messages


def test_extract_first_question_truncates_at_question_mark() -> None:
    raw = "What is attention in transformers? Also, what is RoPE?"
    assert extract_first_question(raw) == "What is attention in transformers?"


def test_extract_first_question_falls_back_to_sentence() -> None:
    raw = "Explain gradient descent. Then talk about Adam"
    out = extract_first_question(raw)
    assert out.startswith("Explain gradient descent")


def test_format_messages_contains_roles_and_system_prompt() -> None:
    sys = build_system_prompt()
    history = [("Candidate", "I am ready."), ("Interviewer", "What is overfitting?")]
    prompt = format_messages(history, sys)
    assert "System:" in prompt
    assert "Candidate: I am ready." in prompt
    assert "Interviewer: What is overfitting?" in prompt

