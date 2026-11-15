import argparse
from contextlib import ExitStack
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab_common import completed_text, load_config, model_client, run, save_report

INSTRUCTIONS = (
    "You are a travel assistant that provides information on travel services "
    "available from Margie's Travel. Answer questions about services offered "
    "by Margie's Travel using the provided travel brochures. Search the web "
    "for general information about destinations or current travel advice."
)


def delete_resource(delete, resource_id):
    print(f"[Cleanup] Deleting this run's resource: {resource_id}", flush=True)
    if not delete(resource_id).deleted:
        raise RuntimeError(f"Azure did not confirm deletion of {resource_id}.")


def response_evidence(response):
    calls = []
    citations = []
    for item in response.output:
        if item.type in ("web_search_call", "file_search_call"):
            print(f"[Tools] {item.type}: {item.status}", flush=True)
            if item.status != "completed":
                raise RuntimeError(f"Search tool did not complete: {item.type}: {item.status}")
            call: dict[str, object] = {"type": item.type, "status": item.status}
            if item.type == "file_search_call":
                files = []
                if item.results is not None:
                    for match in item.results:
                        files.append({"filename": match.filename, "file_id": match.file_id})
                        print(f"[Retrieved] Brochure: {match.filename}", flush=True)
                if not files:
                    print("[Retrieved] No brochure result details were returned.", flush=True)
                call["files"] = files
            calls.append(call)
        elif item.type == "message":
            for content in item.content:
                if content.type != "output_text":
                    continue
                for annotation in content.annotations:
                    if annotation.type == "url_citation":
                        citations.append({
                            "type": annotation.type, "title": annotation.title, "url": annotation.url,
                        })
                        print(f"[Source] {annotation.title}: {annotation.url}", flush=True)
                    elif annotation.type == "file_citation":
                        citations.append({
                            "type": annotation.type, "filename": annotation.filename,
                            "file_id": annotation.file_id,
                        })
                        print(f"[Source] Brochure: {annotation.filename}", flush=True)
    if not calls:
        print("[Tools] No search tool was called for this response.", flush=True)
    return calls, citations


def chat(client, model, vector_store_id):
    results = []
    previous_id = None
    print("\n[Chat] Both file_search and web_search are available; the model chooses when to use them.", flush=True)
    while True:
        try:
            question = input('\nEnter a question (or type "quit" to exit): ').strip()
        except EOFError:
            print("\n[Input] End of input received. Ending the conversation.", flush=True)
            break
        if question.lower() == "quit":
            print("[Input] Quit requested. Ending the conversation.", flush=True)
            break
        if not question:
            print("Please enter a question. No model request was sent.", flush=True)
            continue
        print(
            "[History] Reusing the previous response context."
            if previous_id is not None else "[History] First question; no previous response context.",
            flush=True,
        )
        print("[Request] Sending prompt using Responses. Waiting for the answer and any search calls...", flush=True)
        response = client.responses.create(
            model=model, instructions=INSTRUCTIONS, input=question,
            previous_response_id=previous_id,
            include=["file_search_call.results"],
            tools=[
                {"type": "file_search", "vector_store_ids": [vector_store_id]},
                {"type": "web_search"},
            ],
        )
        answer = completed_text(response)
        print(f"\n[Response] Model answer:\n{answer}", flush=True)
        calls, citations = response_evidence(response)
        results.append({
            "question": question, "answer": answer, "response_id": response.id,
            "tool_calls": calls, "citations": citations,
        })
        previous_id = response.id
    return results


def main():
    parser = argparse.ArgumentParser(description="Chat with Margie's Travel brochures and web search.")
    parser.parse_args()
    print("[Setup] Loading this lab's endpoint and deployment configuration...", flush=True)
    folder, endpoint, model = load_config(__file__)
    brochures = sorted((folder / "brochures").glob("*.pdf"))
    if not brochures:
        raise ValueError(f"No PDF brochures found in {folder / 'brochures'}.")
    print(f"Selected deployment: {model}; local brochures: {len(brochures)}.", flush=True)
    print("Uploads, vector storage, model calls, and search tools may incur charges.", flush=True)
    print("Web search sends search queries to Bing. Do not enter sensitive information.", flush=True)
    print("[Connect] Preparing the client with Microsoft Entra authentication...", flush=True)
    with model_client(endpoint) as client:
        with ExitStack() as cleanup:
            try:
                print("[Store] Creating a temporary travel-brochures vector store...", flush=True)
                store = client.vector_stores.create(name="travel-brochures")
                cleanup.callback(delete_resource, client.vector_stores.delete, store.id)
                print(f"Vector store created: {store.id}", flush=True)
                file_ids = []
                for number, path in enumerate(brochures, 1):
                    print(f"[Upload {number}/{len(brochures)}] {path.name}", flush=True)
                    with path.open("rb") as stream:
                        uploaded = client.files.create(file=stream, purpose="assistants")
                    file_ids.append(uploaded.id)
                    cleanup.callback(delete_resource, client.files.delete, uploaded.id)
                print("[Index] Attaching the uploaded files and waiting for indexing...", flush=True)
                batch = client.vector_stores.file_batches.create_and_poll(
                    vector_store_id=store.id, file_ids=file_ids,
                )
                if batch.status != "completed" or batch.file_counts.completed != len(brochures):
                    raise RuntimeError(
                        f"Brochure indexing failed: status={batch.status}; "
                        f"completed={batch.file_counts.completed}/{len(brochures)}."
                    )
                print(f"[Index] All {len(brochures)} brochures are ready for file search.", flush=True)
                results = chat(client, model, store.id)
            finally:
                print("[Cleanup] Removing any files and vector store tracked by this run...", flush=True)
        print("[Cleanup] This run's uploaded files and vector store were deleted.", flush=True)
    if results:
        print("[Report] Saving answers, tool-call evidence, and citations locally...", flush=True)
        save_report(folder, "tools-chat.json", {
            "success": True, "scope": "Responses chat with brochure and web search",
            "deployment": model, "brochures": [path.name for path in brochures],
            "responses": results, "temporary_resources_deleted": True,
        })
    else:
        print("No questions submitted; no chat report saved.", flush=True)
    print("[Complete] Tools chat ended and temporary-resource cleanup completed.", flush=True)


if __name__ == "__main__":
    sys.exit(run(main))
