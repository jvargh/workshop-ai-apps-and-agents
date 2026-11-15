import os
import json
from dotenv import load_dotenv

# Add references
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import PromptAgentDefinition, FunctionTool
from openai.types.responses.response_input_param import FunctionCallOutput, ResponseInputParam
from functions import next_visible_event, calculate_observation_cost, generate_observation_report

def resolve_tool_calls(openai_client, conversation_id, agent_name, response):
    functions = {
        "next_visible_event": next_visible_event,
        "calculate_observation_cost": calculate_observation_cost,
        "generate_observation_report": generate_observation_report,
    }
    while True:
        if response.status != "completed":
            raise RuntimeError(f"Agent response did not complete: {response.status}; {response.error}")
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            if not response.output_text or not response.output_text.strip():
                raise RuntimeError("The agent returned no final text answer.")
            return response.output_text
        outputs: ResponseInputParam = []
        for item in calls:
            if item.name not in functions:
                raise ValueError(f"The agent requested an unsupported local function: {item.name}")
            print(f"[Tool] Agent requested {item.name}; executing it in local Python...", flush=True)
            result = functions[item.name](**json.loads(item.arguments))
            print(f"[Tool result] {result}", flush=True)
            outputs.append(FunctionCallOutput(
                type="function_call_output", call_id=item.call_id, output=result,
            ))
        print(f"[Request] Returning {len(outputs)} function result(s) to the agent. Waiting for the next response...", flush=True)
        response = openai_client.responses.create(
            conversation=conversation_id, input=outputs,
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
        )

def main():
    print("\n[1/5] Loading the Foundry project and model deployment configuration...", flush=True)
    load_dotenv()
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")
    if not project_endpoint or "<" in project_endpoint:
        raise ValueError("Configure PROJECT_ENDPOINT in this lab's .env.")
    if not model_deployment or "<" in model_deployment or model_deployment.startswith("your-"):
        raise ValueError("Configure MODEL_DEPLOYMENT_NAME in this lab's .env.")
    print(f"Selected deployment: {model_deployment}", flush=True)
    print("The agent uses local sample data; it does not make bookings, payments, or live astronomy lookups.", flush=True)
    print("Agent creation and model calls may incur charges.", flush=True)

    # Connect to the project client
    print("\n[2/5] Connecting to Foundry with Microsoft Entra authentication...", flush=True)
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=project_endpoint, credential=credential) as project_client,
        project_client.get_openai_client() as openai_client,
    ):    

        print("\n[3/5] Defining the event, cost, and report function tools...", flush=True)
        # Define the event function tool
        event_tool = FunctionTool(
            name="next_visible_event",
            description="Get the next visible event in a given location.",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "continent to find the next visible event in (e.g. 'north_america', 'south_america', 'australia')",
                    },
                },
                "required": ["location"],
                "additionalProperties": False,
            },
            strict=True,
        )        

        # Define the observation cost function tool
        cost_tool = FunctionTool(
            name="calculate_observation_cost",
            description="Calculate the cost of an observation based on the telescope tier, number of hours, and priority level.",
            parameters={
                "type": "object",
                "properties": {
                    "telescope_tier": {
                        "type": "string",
                        "description": "the tier of the telescope (e.g. 'standard', 'advanced', 'premium')",
                    },
                    "hours": {
                        "type": "number",
                        "description": "the number of hours for the observation",
                    },
                    "priority": {
                        "type": "string",
                        "description": "the priority level of the observation (e.g. 'low', 'normal', 'high')",
                    },
                },
                "required": ["telescope_tier", "hours", "priority"],
                "additionalProperties": False,
            },
            strict=True,
        )        

        # Define the observation report generation function tool
        report_tool = FunctionTool(
            name="generate_observation_report",
            description="Generate a report summarizing an astronomical observation",
            parameters={
                "type": "object",
                "properties": {
                    "event_name": {
                        "type": "string",
                        "description": "the name of the astronomical event being observed",
                    },
                    "location": {
                        "type": "string",
                        "description": "the location of the observer",
                    },
                    "telescope_tier": {
                        "type": "string",
                        "description": "the tier of the telescope used for the observation (e.g. 'standard', 'advanced', 'premium')",
                    },
                    "hours": {
                        "type": "number",
                        "description": "the number of hours the telescope was used for the observation",
                    },
                    "priority": {
                        "type": "string",
                        "description": "the priority level of the observation (e.g. 'low', 'normal', 'high')",
                    },
                    "observer_name": {
                        "type": "string",
                        "description": "the name of the person who conducted the observation",
                    },                   
                },
                "required": ["event_name", "location", "telescope_tier", "hours", "priority", "observer_name"],
                "additionalProperties": False,
            },
            strict=True,
        )        

        # Create a new agent with the function tools
        print("\n[4/5] Creating a new astronomy-agent version with those tool definitions...", flush=True)
        agent = project_client.agents.create_version(
            agent_name="astronomy-agent",
            definition=PromptAgentDefinition(
                model=model_deployment,
                instructions=
                    """You are an astronomy observations assistant that helps users find 
                    information about astronomical events and calculate telescope rental costs. 
                    Use the available tools to assist users with their inquiries.""",
                tools=[event_tool, cost_tool, report_tool],
            ),
        )
        
        print(f"Created agent version: {agent.name} / {agent.version}", flush=True)
        try:
            print("\n[5/5] Creating a conversation for interactive questions...", flush=True)
            conversation = openai_client.conversations.create()
            print(f"Conversation created: {conversation.id}", flush=True)
            print("The same conversation is reused for follow-up questions.", flush=True)

            while True:
                try:
                    user_input = input("Enter a prompt for the astronomy agent. Use 'quit' to exit.\nUSER: ").strip()
                except EOFError:
                    print("[Input] End of input received. Ending the chat.", flush=True)
                    break
                if user_input.lower() == "quit":
                    print("Exiting chat.", flush=True)
                    break
                if not user_input:
                    print("[Input] Please enter a prompt. No model request was sent.", flush=True)
                    continue
                print("[Conversation] Adding your question to the existing conversation...", flush=True)
                openai_client.conversations.items.create(
                    conversation_id=conversation.id,
                    items=[{"type": "message", "role": "user", "content": user_input}],
                )
                print("[Request] Asking the agent to answer or request a function. Waiting for its response...", flush=True)
                response = openai_client.responses.create(
                    conversation=conversation.id,
                    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                    input=[],
                )
                answer = resolve_tool_calls(openai_client, conversation.id, agent.name, response)
                print(f"AGENT: {answer}", flush=True)
        finally:
            print(f"[Cleanup] Deleting only the agent version created by this run: {agent.name} / {agent.version}...", flush=True)
            project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
            print("[Cleanup] Created agent version deleted. Existing versions and local reports are preserved.", flush=True)
        print("[Cleanup] Closing the SDK clients and Azure credential. The cloud conversation is not deleted.", flush=True)
    print("[Complete] Astronomy chat ended and agent-version cleanup completed.", flush=True)

if __name__ == '__main__': 
    main()