import json
import os
import uuid
import httpx

from typing import Any
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition
from openai.types.responses import ResponseFunctionToolCall
from openai.types.responses.response_input_param import FunctionCallOutput
from collections.abc import Callable
from dotenv import load_dotenv
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)

load_dotenv()

TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]


class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(self, agent_card: AgentCard, agent_url: str):
        self._httpx_client = httpx.AsyncClient(timeout=120)
        self.agent_client = A2AClient(self._httpx_client, agent_card, url=agent_url)
        self.card = agent_card

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_message(self, message_request: SendMessageRequest) -> SendMessageResponse:
        return await self.agent_client.send_message(message_request)

class RoutingAgent:

    def __init__(self,task_callback: TaskUpdateCallback | None = None):

        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ''
        
        # Initialize Azure AI Agents client
        self.agents_client = AIProjectClient(
            endpoint=os.environ["PROJECT_ENDPOINT"],
            credential=DefaultAzureCredential(
                exclude_environment_credential=True,
                exclude_managed_identity_credential=True
            )
        )

        self.openai_client = self.agents_client.get_openai_client()
        self.azure_agent = None
        self.current_thread = None


    @classmethod
    async def create(cls, remote_agent_addresses: list[str], task_callback: TaskUpdateCallback | None = None) -> 'RoutingAgent':
        """Create and asynchronously initialize an instance of the RoutingAgent."""
        instance = cls(task_callback)
        await instance._async_init_components(remote_agent_addresses)
        return instance
    

    def list_remote_agents(self) -> str:
        if not self.remote_agent_connections:
            return "[]"

        lines = []
        for card in self.cards.values():
            lines.append(f"{card.name}: {card.description}")

        return "[\n  " + ",\n  ".join(lines) + "\n]"
    

    async def _async_init_components(self, remote_agent_addresses: list[str]) -> None:
        """Asynchronous part of initialization."""

        # Use a single httpx.AsyncClient for all card resolutions for efficiency
        async with httpx.AsyncClient(timeout=30) as client:
            for address in remote_agent_addresses:
                card_resolver = A2ACardResolver(client, address)
                try:
                    card = await card_resolver.get_agent_card()

                    remote_connection = RemoteAgentConnections(agent_card=card, agent_url=address)
                    self.remote_agent_connections[card.name] = remote_connection
                    self.cards[card.name] = card

                except httpx.ConnectError as e:
                    print( f'ERROR: Failed to get agent card from {address}: {e}')
                except Exception as e:  # Catch other potential errors
                    print(f'ERROR: Failed to initialize connection for {address}: {e}')
            print(f"Found remote agents: {self.list_remote_agents()}")

    
    async def send_message(self, agent_name: str, task: str) -> Task:
        # Sends a task to remote agent.

        if agent_name not in self.remote_agent_connections:
            raise ValueError(f'Agent {agent_name} not found')
        
        # Retrieve the remote agent's A2A client using the agent name 
        client = self.remote_agent_connections[agent_name]
        
        message_id = str(uuid.uuid4())

        # Construct the payload to send to the remote agent
        payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': task}],
                'messageId': message_id,
            },
        }        
        
        # Wrap the payload in a SendMessageRequest object
        message_request = SendMessageRequest(id=message_id, params=MessageSendParams.model_validate(payload))        

        # Send the message to the remote agent client and await the response
        send_response: SendMessageResponse = await client.send_message(message_request=message_request)        
        
        if not isinstance(send_response.root, SendMessageSuccessResponse):
            raise RuntimeError(f"Remote agent {agent_name} returned an error: {send_response.root}")

        if not isinstance(send_response.root.result, Task):
            raise RuntimeError(f"Remote agent {agent_name} returned a non-task response")

        if send_response.root.result.status.state != "completed":
            raise RuntimeError(
                f"Remote agent {agent_name} task did not complete: {send_response.root.result.status}"
            )

        return send_response.root.result


    def create_agent(self):
        # Create an Azure AI Agent instance
        
        try:
            # Create Azure AI Agent with the send_message function
            function = FunctionTool(
                name="send_message",
                description="Send a writing task to a specialized remote agent.",
                parameters={
                    "type": "object",
                    "properties": {
                        "agent_name": {"type": "string", "enum": list(self.cards)},
                        "task": {"type": "string"},
                    },
                    "required": ["agent_name", "task"],
                    "additionalProperties": False,
                },
                strict=True,
            )
            self.azure_agent = self.agents_client.agents.create_version(
                agent_name="routing-agent",
                definition=PromptAgentDefinition(
                    model=os.environ["MODEL_DEPLOYMENT_NAME"],
                    instructions=f"""
                You are an expert Routing Delegator that helps users with requests.

                Your role:
                - Delegate user inquiries to appropriate specialized remote agents
                - Provide clear and helpful responses to users

                Available Agents: {self.list_remote_agents()}

                When both a title and outline are requested, get the title first,
                then ask the outline agent to outline that title.
                Include both remote agents' results in your final response.
                Always be helpful and route requests to the most appropriate agent.""",
                    tools=[function],
                ),
            )

            self.current_thread = self.openai_client.conversations.create()

            return self.azure_agent
            
        except Exception as e:
            print(f"Error creating Azure AI agent: {e}")
            raise

    async def process_user_message(self, user_message: str) -> str:

        if not hasattr(self, 'azure_agent') or not self.azure_agent:
            return "Azure AI Agent not initialized. Please ensure the agent is properly created."
        
        if not hasattr(self, 'current_thread') or not self.current_thread:
            return "Azure AI Thread not initialized. Please ensure the agent is properly created."
        
        try:
            options = {
                "conversation": self.current_thread.id,
                "extra_body": {"agent_reference": {
                    "type": "agent_reference",
                    "name": self.azure_agent.name,
                    "version": self.azure_agent.version,
                }},
            }
            response = self.openai_client.responses.create(input=user_message, **options)
            for tool_round in range(11):
                if response.status != "completed":
                    raise RuntimeError(
                        f"Routing Agent response {response.status}: "
                        f"{response.error or response.incomplete_details}"
                    )
                tool_calls = [
                    item for item in response.output
                    if isinstance(item, ResponseFunctionToolCall)
                ]
                if not tool_calls:
                    if not response.output_text:
                        raise RuntimeError("No text response received from routing agent.")
                    return response.output_text
                if tool_round == 10:
                    raise RuntimeError("Routing Agent exceeded ten remote-tool response rounds.")

                tool_outputs = []
                for tool_call in tool_calls:
                    if tool_call.name != "send_message":
                        raise ValueError(f"Unknown function: {tool_call.name}")
                    arguments = json.loads(tool_call.arguments)
                    if (
                        not isinstance(arguments, dict)
                        or set(arguments) != {"agent_name", "task"}
                        or not all(isinstance(value, str) and value.strip() for value in arguments.values())
                    ):
                        raise ValueError("send_message requires nonempty agent_name and task strings.")
                    result = await self.send_message(
                        agent_name=arguments["agent_name"], task=arguments["task"],
                    )
                    tool_outputs.append(FunctionCallOutput(
                        type="function_call_output",
                        call_id=tool_call.call_id,
                        output=result.model_dump_json(),
                    ))
                response = self.openai_client.responses.create(input=tool_outputs, **options)
            
        except Exception as e:
            error_msg = f"Error in process_user_message: {e}"
            print(error_msg)
            return f"Error processing request: {e}"
