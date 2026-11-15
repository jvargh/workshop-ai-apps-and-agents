import argparse
import json
from pathlib import Path
import sys

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab_common import (
    DefaultAzureCredential, account_path, arm_get, load_config, model_client, run,
    save_report,
)


def validate_strict_policy(policy):
    mode = policy["properties"].get("mode")
    if mode not in ("Default", "Blocking"):
        raise ValueError(
            f"The strict policy must use Default or Blocking mode; received {mode!r}. "
            "Asynchronous or unknown filtering modes do not meet this lab's checks."
        )
    filters = policy["properties"].get("contentFilters", [])
    expected = {(name, source) for name in ("Hate", "Violence", "Sexual", "Selfharm")
                for source in ("Prompt", "Completion")}
    actual = {(item["name"], item["source"]): item for item in filters}
    if len(actual) != len(filters):
        raise ValueError("Policy contains duplicate category/source filters.")
    for pair in expected:
        item = actual.get(pair)
        if not item or item.get("enabled") is not True or item.get("blocking") is not True or (
            item.get("severityThreshold") != "Low"
        ):
            raise ValueError(f"Policy must block Low and above for {pair[0]}/{pair[1]}.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Read-only deployment guardrail audit.")
    parser.add_argument("--expect-policy", help="Require an applied, custom highest-blocking policy.")
    args = parser.parse_args()
    print("Read-only guardrail audit: no policies or deployments will be changed.", flush=True)
    print("No harmful test prompts will be sent.", flush=True)
    print("\n[1/8] Loading this lab's endpoint and deployment configuration...", flush=True)
    folder, endpoint, model = load_config(__file__)
    print(f"Selected deployment: {model}", flush=True)
    if args.expect_policy:
        print(f"Mode: verify the applied custom strict policy {args.expect_policy}.", flush=True)
    else:
        print("Mode: inspect the current assignment without verifying strict thresholds.", flush=True)
    print("\n[2/8] Reading and checking the local strict-policy template...", flush=True)
    template = json.loads((folder / "guardrail-policy.json").read_text(encoding="utf-8"))
    validate_strict_policy(template)
    print(
        "Local template passed: all eight required category/source pairs block Low and above. "
        "This check does not apply the template to Azure.",
        flush=True,
    )
    policy_definition = None
    print(
        "\n[3/8] Preparing Azure authentication and reading the deployment through Azure Resource Manager...",
        flush=True,
    )
    with DefaultAzureCredential() as credential:
        root = account_path()
        deployment = arm_get(credential, f"{root}/deployments/{model}")
        policy_name = deployment["properties"].get("raiPolicyName")
        if not policy_name:
            raise RuntimeError("Deployment did not expose an assigned RAI policy name.")
        print(f"Deployment's assigned policy: {policy_name}", flush=True)
        print("\n[4/8] Checking the assignment and retrieving the actual policy definition...", flush=True)
        if args.expect_policy and policy_name != args.expect_policy:
            raise ValueError(
                f"Expected policy {args.expect_policy}; deployment uses {policy_name}."
            )
        if args.expect_policy:
            print("The assigned policy name matches the expected custom policy.", flush=True)
        try:
            policy_definition = arm_get(credential, f"{root}/raiPolicies/{policy_name}")
            print("The assigned policy definition is available.", flush=True)
            print(f"Assigned policy mode: {policy_definition['properties'].get('mode')}", flush=True)
        except requests.HTTPError as exc:
            if not (
                exc.response.status_code == 404
                and policy_name.startswith("Microsoft.")
                and not args.expect_policy
            ):
                raise
            print(
                "Built-in policy name is assigned, but its definition is not exposed "
                "as an account-owned RAI policy. Thresholds are NOT verified.",
                file=sys.stderr, flush=True,
            )
    strict_verified = False
    print("\n[5/8] Determining whether applied strict-policy verification is required...", flush=True)
    if args.expect_policy:
        print(
            "Checking the actual assigned definition for Default or Blocking mode and all eight "
            "required enabled, blocking, Low-threshold filters...",
            flush=True,
        )
        strict_verified = validate_strict_policy(policy_definition)
        print("Applied custom policy passed the strict configuration checks.", flush=True)
    else:
        print(
            "Skipping applied strict-policy checks: --expect-policy was not supplied. "
            "The local template result is separate from the deployed policy.",
            flush=True,
        )
    print("\n[6/8] Preparing the model client with Microsoft Entra authentication...", flush=True)
    print("The following benign model request may incur inference charges.", flush=True)
    with model_client(endpoint) as client:
        prompt = "Suggest three safe daytime sightseeing activities in Rome."
        print(f"Prompt: {prompt}", flush=True)
        print("[Request] Sending the prompt using Chat Completions. Waiting for the model response...", flush=True)
        result = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        print("\n[7/8] Checking that the benign request completed with text...", flush=True)
        choice = result.choices[0]
        if choice.finish_reason != "stop" or not choice.message.content:
            raise RuntimeError("The benign safety smoke prompt did not complete with text.")
        print(f"Response finish reason: {choice.finish_reason}", flush=True)
        print(f"\nModel answer:\n{choice.message.content}", flush=True)
        print("A successful benign answer does not demonstrate harmful-content blocking.", flush=True)
        print("[Cleanup] Closing the model client and Azure credential...", flush=True)
    print("\n[8/8] Saving the audit results and raw benign response to a local JSON report...", flush=True)
    save_report(folder, "guardrail-audit.json", {
        "success": True, "scope": "Read-only assigned-policy audit and benign smoke request",
        "deployment": model, "assigned_policy": policy_name,
        "policy_mode": policy_definition["properties"].get("mode") if policy_definition is not None else None,
        "policy_definition_available": policy_definition is not None,
        "strict_guardrail_verified": strict_verified,
        "local_strict_template_valid": True, "shared_settings_changed": False,
        "harmful_prompts_executed": False, "smoke_response": result.model_dump(),
    })
    print(f"Assigned policy: {policy_name}; custom strict policy verified: {strict_verified}", flush=True)
    print("[Complete] Audit finished and its report was saved. No cloud settings were changed.", flush=True)


if __name__ == "__main__":
    sys.exit(run(main))
