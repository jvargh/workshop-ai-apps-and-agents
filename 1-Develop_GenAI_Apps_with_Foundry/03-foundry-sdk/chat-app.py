import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab_common import completed_text, load_config, model_client, run

INSTRUCTIONS = "You are a helpful AI assistant that answers questions and provides information."


def stream_text(stream):
    last_response = None
    chunks = []
    with stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                print(event.delta, end="", flush=True)
                chunks.append(event.delta)
            elif event.type == "response.completed":
                last_response = event.response
            elif event.type in ("response.failed", "response.incomplete", "error"):
                raise RuntimeError(f"Stream failed: {event}")
    print()
    if last_response is None or not "".join(chunks).strip():
        raise RuntimeError("Stream ended without a completed text response.")
    completed_text(last_response)
    return last_response.id


def main():
    parser = argparse.ArgumentParser(description="Guide-aligned OpenAI chat client.")
    parser.add_argument("--api", choices=["responses", "chat-completions"], default="responses")
    parser.add_argument("--stream", action="store_true", help="Stream Responses API output.")
    parser.add_argument("--no-history", action="store_true", help="Demonstrate independent requests.")
    args = parser.parse_args()
    if args.stream and args.api != "responses":
        raise ValueError("--stream is supported with --api responses.")
    print("[Setup] Loading this lab's endpoint and deployment configuration...", flush=True)
    _, endpoint, model = load_config(__file__)
    api_name = "Chat Completions" if args.api == "chat-completions" else "Responses"
    wait_for = "streamed output" if args.stream else "the complete response"
    print(f"[Mode] {api_name} API; output: {'streamed text' if args.stream else 'full response'}.", flush=True)
    print(f"Selected deployment: {model}", flush=True)
    if args.no_history:
        print("[History] Disabled: each prompt is an independent request.", flush=True)
    elif args.api == "chat-completions":
        print("[History] Enabled: earlier user and assistant messages are sent with each follow-up.", flush=True)
    else:
        print("[History] Enabled: follow-ups reference the previous response ID.", flush=True)
    print("Live model requests may incur inference charges.", flush=True)
    last_response_id = None
    history = [{"role": "system", "content": INSTRUCTIONS}]
    print("[Connect] Preparing the model client with Microsoft Entra authentication...", flush=True)
    with model_client(endpoint) as client:
        while True:
            try:
                text = input('\nEnter a prompt (or type "quit" to exit): ').strip()
            except EOFError:
                print("\n[Input] End of input received. Ending the chat session.", flush=True)
                break
            if text.lower() == "quit":
                print("[Input] Quit requested. Ending the chat session.", flush=True)
                break
            if not text:
                print("Please enter a prompt. No model request was sent.", flush=True)
                continue
            if args.no_history:
                print("[History] Sending this prompt without earlier conversation turns.", flush=True)
            elif args.api == "chat-completions":
                print(
                    f"[History] Including {len(history) - 1} earlier user/assistant message(s) with this prompt.",
                    flush=True,
                )
            elif last_response_id is not None:
                print("[History] Reusing the previous response context for this follow-up.", flush=True)
            else:
                print("[History] First turn: no previous response context.", flush=True)
            print(f"[Request] Sending prompt using {api_name}. Waiting for {wait_for}...", flush=True)
            if args.api == "chat-completions":
                messages = history + [{"role": "user", "content": text}]
                result = client.chat.completions.create(model=model, messages=messages)
                choice = result.choices[0]
                answer = choice.message.content
                if choice.finish_reason != "stop" or not answer or not answer.strip():
                    raise RuntimeError(f"Chat did not complete with text: {choice.finish_reason}")
                print("\n[Response] Model answer:", flush=True)
                print(answer, flush=True)
                if not args.no_history:
                    history = messages + [{"role": "assistant", "content": answer}]
            else:
                result = client.responses.create(
                    model=model, instructions=INSTRUCTIONS, input=text,
                    previous_response_id=last_response_id, stream=args.stream,
                )
                if args.stream:
                    print("\n[Response] Streaming model answer:", flush=True)
                    new_id = stream_text(result)
                    print("[Response] Stream completed and text validated.", flush=True)
                else:
                    answer = completed_text(result)
                    print("\n[Response] Model answer:", flush=True)
                    print(answer, flush=True)
                    new_id = result.id
                if not args.no_history:
                    last_response_id = new_id
            if args.no_history:
                print("[History] The next prompt will be independent of this turn.", flush=True)
            else:
                print("[History] Context updated for the next prompt in this session.", flush=True)
        print("[Cleanup] Closing the model client and Azure credential...", flush=True)
    print("[Exit] Chat session closed.", flush=True)


if __name__ == "__main__":
    sys.exit(run(main))
