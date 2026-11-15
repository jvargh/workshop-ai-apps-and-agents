import asyncio
from pathlib import Path
import sys

from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncOpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab_common import completed_text, load_config, run


async def main():
    print("[Setup] Loading this lab's endpoint and deployment configuration...", flush=True)
    _, endpoint, model = load_config(__file__)
    print("[Mode] Async Responses API; output: full response.", flush=True)
    print(f"Selected deployment: {model}", flush=True)
    print("[History] Enabled: follow-ups reference the previous response ID.", flush=True)
    print("Live model requests may incur inference charges.", flush=True)
    last_response_id = None
    print("[Connect] Preparing the async model client with Microsoft Entra authentication...", flush=True)
    async with DefaultAzureCredential() as credential, AsyncOpenAI(
        base_url=endpoint,
        api_key=get_bearer_token_provider(credential, "https://ai.azure.com/.default"),
        timeout=120,
        max_retries=2,
    ) as client:
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
            if last_response_id is not None:
                print("[History] Reusing the previous response context for this follow-up.", flush=True)
            else:
                print("[History] First turn: no previous response context.", flush=True)
            print(
                "[Request] Sending prompt using async Responses. Waiting for the complete response...",
                flush=True,
            )
            response = await client.responses.create(
                model=model,
                instructions="You are a helpful AI assistant that answers questions and provides information.",
                input=text,
                previous_response_id=last_response_id,
            )
            answer = completed_text(response)
            print("\n[Response] Model answer:", flush=True)
            print(answer, flush=True)
            last_response_id = response.id
            print("[History] Context updated for the next prompt in this session.", flush=True)
        print("[Cleanup] Closing the async model client and Azure credential...", flush=True)
    print("[Exit] Chat session closed.", flush=True)


if __name__ == "__main__":
    sys.exit(run(lambda: asyncio.run(main())))
