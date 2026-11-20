from dotenv import load_dotenv
import os

# import namespaces
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


SECTION_HEADINGS = {
    "sentiment": "Sentiment",
    "key phrases": "Key phrases",
    "named entities": "Named entities",
    "organizations": "Organizations",
    "locations": "Locations",
}


def format_analysis(analysis: str) -> str:
    lines = []
    in_section = False

    for raw_line in analysis.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        title, _, value = line.partition(":")
        heading = SECTION_HEADINGS.get(title.strip().casefold())
        if heading:
            if lines:
                lines.append("")
            lines.append(f"{heading}:")
            in_section = True
            line = value.strip()
            if not line:
                continue

        if in_section:
            item = line.removeprefix("- ").removeprefix("* ")
            lines.append(f"  - {item}")
        else:
            lines.append(raw_line)

    return "\n".join(lines) if in_section else analysis


def main():
    try:
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Get Configuration Settings
        load_dotenv()
        foundry_endpoint = os.getenv('FOUNDRY_ENDPOINT')
        agent_name = os.getenv('AGENT_NAME')
        
        # Get project client
        project_client = AIProjectClient(
            endpoint=foundry_endpoint,
            credential=DefaultAzureCredential(),
        )
        
        # Get an OpenAI client
        openai_client = project_client.get_openai_client()
        
        # Use the agent to get a response
        prompt = input("User prompt: ")
        analysis_prompt = (
            f"{prompt}\n\n"
            "Present the results as concise plain text, not JSON. "
            "Use only the headings relevant to the request: Sentiment, Key phrases, "
            "Named entities, Organizations, and Locations. "
            "Omit headings for analyses not requested. If an analysis was completed "
            "but found no matches, say 'None found' under its heading."
        )
        response = openai_client.responses.create(
            input=[{"role": "user", "content": analysis_prompt}],
            extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
        )

        print(f"\nResponse Details: {response.model_dump_json(indent=2)}")

        analysis = response.output_text.strip()
        if analysis:
            print(f"\nAnalysis Summary\n{'=' * 16}\n{format_analysis(analysis)}")
        else:
            print("\nNo analysis text returned. Check the response details above.")

    except Exception as ex:
        print(ex)

if __name__ == "__main__":
    main()