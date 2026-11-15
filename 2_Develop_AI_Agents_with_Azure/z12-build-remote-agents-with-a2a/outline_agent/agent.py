""" Azure AI Foundry Agent that generates an outline """

import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentVersionDetails, PromptAgentDefinition
from azure.identity import DefaultAzureCredential

class OutlineAgent:

    def __init__(self):

        # Create the agents client
        self.client = AIProjectClient(
            endpoint=os.environ['PROJECT_ENDPOINT'],
            credential=DefaultAzureCredential(
                exclude_environment_credential=True,
                exclude_managed_identity_credential=True
            )
        )

        self.openai_client = self.client.get_openai_client()
        self.agent: AgentVersionDetails | None = None

    async def create_agent(self) -> AgentVersionDetails:
        if self.agent:
            return self.agent

        # Create the outline agent
        self.agent = self.client.agents.create_version(
            agent_name='foundry-outline-agent',
            definition=PromptAgentDefinition(
                model=os.environ['MODEL_DEPLOYMENT_NAME'],
                instructions="""
                You are a helpful writing assistant.
                Based on the provided title or topic, write a concise outline with 4 to 6 key sections.
                Each section should be 5 to 10 words long, suitable for structuring a short blog post.
                """,
            ),
        )
        return self.agent

    async def run_conversation(self, user_message: str) -> list[str]:
        agent = await self.create_agent()
        response = self.openai_client.responses.create(
            input=user_message,
            extra_body={"agent_reference": {
                "type": "agent_reference", "name": agent.name, "version": agent.version,
            }},
        )
        if response.status != "completed" or not response.output_text:
            raise RuntimeError(
                f"Outline Agent response {response.status}: "
                f"{response.error or response.incomplete_details or 'No text response received'}"
            )
        return [response.output_text]

async def create_foundry_outline_agent() -> OutlineAgent:
    agent = OutlineAgent()
    await agent.create_agent()
    return agent
