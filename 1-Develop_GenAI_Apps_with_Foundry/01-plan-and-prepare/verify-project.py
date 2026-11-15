from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab_common import (
    DefaultAzureCredential, account_path, arm_get, completed_text, load_config,
    model_client, required, run, save_report,
)


def main():
    print("Foundry project validation: checking existing resources only.", flush=True)
    print("No Azure resources will be created or changed.", flush=True)
    print("\n[1/8] Loading configuration from this lab's .env file...", flush=True)
    folder, endpoint, model = load_config(__file__)
    print(f"Selected model deployment: {model}", flush=True)
    print("\n[2/8] Preparing Azure authentication with DefaultAzureCredential...", flush=True)
    with DefaultAzureCredential() as credential:
        root = account_path()
        print("\n[3/8] Reading Foundry resource details from Azure Resource Manager...", flush=True)
        account = arm_get(credential, root)
        print(f"Resource region: {account['location']}", flush=True)
        print("\n[4/8] Reading the Foundry project's provisioning status...", flush=True)
        project = arm_get(credential, f"{root}/projects/{required('AZURE_PROJECT_NAME')}")
        print(f"Project provisioning state: {project['properties']['provisioningState']}", flush=True)
        print("\n[5/8] Listing the resource's model deployments...", flush=True)
        deployments = arm_get(credential, f"{root}/deployments")["value"]
        print(f"Found {len(deployments)} model deployment(s).", flush=True)
    print("\n[6/8] Checking that the project and selected deployment are ready...", flush=True)
    if project["properties"]["provisioningState"] != "Succeeded":
        raise RuntimeError("The Foundry project is not ready.")
    deployment = next((item for item in deployments if item["name"] == model), None)
    if deployment is None or deployment["properties"]["provisioningState"] != "Succeeded":
        raise RuntimeError(f"Deployment {model} is missing or not ready.")
    print("Project and selected deployment are both Succeeded.", flush=True)
    print("\n[7/8] Testing the deployed model with a live inference request...", flush=True)
    print("This model call may incur inference charges.", flush=True)
    with model_client(endpoint) as client:
        prompt = (
            "Describe three key considerations for working with Large Language Models "
            "for AI application development."
        )
        print(f"Prompt: {prompt}", flush=True)
        print("Sending the prompt using the Responses API. Waiting for the model response...", flush=True)
        response = client.responses.create(
            model=model,
            instructions="You are an AI assistant that provides advice about AI software development.",
            input=prompt,
        )
        answer = completed_text(response)
        print("\nModel response:", flush=True)
        print(answer, flush=True)
    print("\n[8/8] Saving the validation results to a local JSON report...", flush=True)
    report = {
        "success": True,
        "scope": "Existing project/resource/deployment readiness and live model inference",
        "region": account["location"],
        "project_state": project["properties"]["provisioningState"],
        "deployment": model,
        "underlying_model": deployment["properties"]["model"],
        "response": answer,
        "usage": response.usage.model_dump(),
        "portal_and_toolkit_ui_validated": False,
        "new_resources_created": False,
    }
    save_report(folder, "project-validation.json", report)
    print("\nValidation completed successfully.", flush=True)
    print("Portal navigation and the VS Code Foundry Toolkit UI were not validated.", flush=True)


if __name__ == "__main__":
    sys.exit(run(main))
