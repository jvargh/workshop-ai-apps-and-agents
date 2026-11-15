""" Azure AI Foundry Agent that generates a title """

import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import AgentVersionDetails, PromptAgentDefinition

class TitleAgent:

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

        # Create the title agent
        self.agent = self.client.agents.create_version(
            agent_name='title-agent',
            definition=PromptAgentDefinition(
                model=os.environ['MODEL_DEPLOYMENT_NAME'],
                instructions="""
                You are a helpful writing assistant.
                Given a topic the user wants to write about, suggest a single clear and catchy blog post title.
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
                f"Title Agent response {response.status}: "
                f"{response.error or response.incomplete_details or 'No text response received'}"
            )
        return [response.output_text]

async def create_foundry_title_agent() -> TitleAgent:
    agent = TitleAgent()
    await agent.create_agent()
    return agent
