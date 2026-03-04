import os
import textwrap

from dotenv import load_dotenv
from llama_cpp import Llama



def load_config() -> dict:
    """
    Load configuration from environment variables / .env.
    """
    load_dotenv()
    # Default to your actual model file if MODEL_PATH is not set
    model_path = os.getenv("MODEL_PATH", "models/ECE-Qwen0.5B-FT-V2.Q2_K.gguf")
    n_ctx = int(os.getenv("N_CTX", "4096"))
    n_gpu_layers = int(os.getenv("N_GPU_LAYERS", "0"))

    return {
        "model_path": model_path,
        "n_ctx": n_ctx,
        "n_gpu_layers": n_gpu_layers,
    }


def create_model(config: dict) -> Llama:
    """
    Initialize the llama.cpp model.
    """
    model_path = config["model_path"]

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file not found at '{model_path}'. "
            "Please download a Qwen GGUF model and update MODEL_PATH in .env."
        )

    print(f"Loading model from: {model_path}")
    llm = Llama(
        model_path=model_path,
        n_ctx=config["n_ctx"],
        n_gpu_layers=config["n_gpu_layers"],
        verbose=True,
    )
    return llm


def build_system_prompt() -> str:
    """
    System prompt that enforces interview tone & behavior.
    This is intentionally simple; we will make it more sophisticated later.
    """
    prompt = """
    You are a senior technical interviewer for AI / machine learning roles.

    Content focus:
    - Only ask questions about AI, machine learning, deep learning, LLMs, data science, MLOps, and related math.
    - You can cover topics like: supervised/unsupervised learning, model evaluation, overfitting, regularization, transformers,
      attention, training pipelines, deployment, prompt engineering, vector databases, embeddings, and real-world ML system design.

    Your goals:
    - Maintain a professional, friendly interview tone.
    - Ask exactly one question at a time.
    - Focus on conceptual depth, problem-solving, and trade-offs.
    - Adjust difficulty slightly up or down based on the candidate's last answer quality.
    - Keep your own messages short (1–3 sentences) and to the point.
    - Do NOT repeat the exact same question you asked previously; always move to a new angle or subtopic based on the conversation history.

    Conversation rules:
    - Do NOT role-play as the candidate; you are only the interviewer.
    - In each turn, ask ONE single, clear AI/ML-related question. Do not list or number multiple questions.
    - Do not include follow-up questions in the same message; each message must contain only one question.
    - Do not re-ask a question that already appears in the recent conversation history unless the candidate explicitly asks you to repeat it.
    - End each message with a single question mark '?'.
    - Avoid small talk, generic HR questions, and non-technical topics.]
    - DONOT REPEAT THE SAME QUESTION.
    - ask a different question everytime.
    """
    return textwrap.dedent(prompt).strip()


def format_messages(history, system_prompt: str):
    """
    Convert chat history into a llama.cpp-compatible prompt.
    We use a simple chat template style (no special tokens)
    to keep it model-agnostic for Qwen GGUF.
    """
    # Basic chat-style formatting
    parts = [f"System: {system_prompt}\n"]
    for role, content in history:
        parts.append(f"{role}: {content}\n")
    parts.append(
        "System: Ask exactly one short AI/ML question now. "
        "Do not list or number multiple questions. Do not include follow-ups.\n"
    )
    parts.append("Interviewer: ")
    return "".join(parts)


def interview_loop(llm: Llama):
    system_prompt = build_system_prompt()
    history = []

    print("\n=== AI Interview Simulator (Qwen + llama.cpp) ===")
    print("Type your answers and press Enter. Type 'exit' or 'quit' to stop.\n")

    # Seed: candidate indicates readiness
    history.append(
        (
            "Candidate",
            "Hi, I'm ready to start the technical interview. Please begin.",
        )
    )

    while True:
        prompt_str = format_messages(history, system_prompt)

        output = llm(
            prompt_str,
            max_tokens=256,
            temperature=0.4,
            top_p=0.9,
            stop=["Candidate:", "System:"],
        )

        raw_reply = output["choices"][0]["text"].strip()

        # Post-process: keep only the first question (up to the first '?')
        question = raw_reply
        q_index = question.find("?")
        if q_index != -1:
            question = question[: q_index + 1]
        # Fallback: if no '?' was generated, just keep the first sentence-ish chunk
        if q_index == -1:
            for sep in [".", "!", "\n"]:
                s_index = question.find(sep)
                if s_index != -1:
                    question = question[: s_index + 1]
                    break

        reply = question.strip()
        print(f"\nInterviewer: {reply}\n")

        # Get candidate response
        user_input = input("You (Candidate): ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("\nInterviewer: That's all for today. Thank you for your time, and good luck with your preparation.\n")
            return

        history.append(("Interviewer", reply))
        history.append(("Candidate", user_input))


def main():
    config = load_config()
    llm = create_model(config)
    interview_loop(llm)


if __name__ == "__main__":
    main()

