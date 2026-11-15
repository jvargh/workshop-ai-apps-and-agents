import os
import asyncio
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from dotenv import load_dotenv

# Add references
from agent_framework import tool, Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from pydantic import Field
from typing import Annotated


load_dotenv(Path(__file__).with_name(".env"))

async def main():
    print("[1/5] Reading local expense data; Python runs locally and the model runs in Foundry.")
    print("The only tool prints a draft. No email, claim submission, payment, or file write occurs.")
    script_dir = Path(__file__).parent
    file_path = script_dir / 'data.txt'
    with file_path.open('r', encoding='utf-8') as file:
        data = file.read() + "\n"

    print(f"Here is the expenses data in data.txt:\n\n{data}")
    print("[2/5] Enter one request below, or press Enter / type exit to stop before inference.")
    try:
        user_prompt = input("What would you like me to do with it? ").strip()
    except EOFError:
        user_prompt = ""
    if not user_prompt or user_prompt.lower() == "exit":
        print("Stopped before model inference; no draft was produced.")
        return
    
    await process_expenses_data(user_prompt, data)
    
async def process_expenses_data(prompt, expenses_data):
    print("[3/5] Checking local configuration and preparing the Foundry model client.")
    claim_email = os.getenv("EXPENSE_CLAIM_EMAIL", "").strip()
    project_endpoint = os.getenv("PROJECT_ENDPOINT", "").strip()
    model = os.getenv("MODEL_DEPLOYMENT_NAME", "").strip()
    for key, value in (
        ("EXPENSE_CLAIM_EMAIL", claim_email),
        ("PROJECT_ENDPOINT", project_endpoint),
        ("MODEL_DEPLOYMENT_NAME", model),
    ):
        if not value:
            raise ValueError(f"Set {key} in this lab's local .env file.")

    async with AsyncExitStack() as stack:
        credential = AzureCliCredential()
        stack.callback(credential.close)
        client = FoundryChatClient(
            project_endpoint=project_endpoint,
            model=model,
            credential=credential,
        )
        # This provider has no close/context-manager API; close its owned SDK clients.
        stack.push_async_callback(client.project_client.close)
        stack.push_async_callback(client.client.close)
        agent = await stack.enter_async_context(
            Agent(
                client=client,
                name="ExpenseClaimAgent",
                instructions=f"""You help review expense data and prepare printed email drafts.
                Only when the user requests a draft, call submit_claim with recipient
                {claim_email}, subject 'Expense Claim', and itemized expenses plus their total.
                submit_claim only prints a draft and returns its text; it never sends email,
                submits a claim, saves a file, or makes a payment. State that it is draft-only.
                Do not claim that anything was sent or submitted. For analysis-only requests,
                answer without calling the tool. Use only the supplied expense data and do not
                invent a currency, approval, receipt, or reimbursement status.""",
                tools=[submit_claim],
            )
        )
        try:
            print("[4/5] Sending the request and expense text to the remote model; waiting for its reply.")
            response = await agent.run(
                f"Request:\n{prompt}\n\nExpense data:\n{expenses_data}",
                options={"store": False},
            )
            if not str(response).strip():
                raise RuntimeError("The model returned no final text.")
            print(f"\n# Agent:\n{response}")
        finally:
            print("[5/5] Closing the SDK clients and Azure CLI credential.")
    print("Finished. Review the printed tool output; nothing was sent, submitted, or saved.")

# Keep this tool draft-only: approval is unnecessary because it only prints.
@tool(approval_mode="never_require")
def submit_claim(
    to: Annotated[str, Field(description="Configured recipient for the printed draft, not an email send.")],
    subject: Annotated[str, Field(description="The subject of the printed email draft.")],
    body: Annotated[str, Field(description="The printed draft body with itemized expenses and total.")]):
    if to != os.getenv("EXPENSE_CLAIM_EMAIL", "").strip() or not to:
        raise ValueError("The draft recipient must match EXPENSE_CLAIM_EMAIL.")
    print("\n[tool: submit_claim] PRINTED DRAFT ONLY - no email or claim was sent.")
    print("To:", to)
    print("Subject:", subject)
    print(body, "\n")
    return {"status": "draft_only", "to": to, "subject": subject, "body": body}



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted; no email or claim was sent.", file=sys.stderr)
        sys.exit(130)
    except Exception as error:
        print(f"\nLab failed ({type(error).__name__}): {error}", file=sys.stderr)
        sys.exit(1)
