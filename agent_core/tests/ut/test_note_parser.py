import pytest
from pathlib import Path
import json

from agent_core.agents.agent_factory import AgentFactory, get_agent_factory
from agent_core.agents.base_agent import AgentInput
from agent_core.agents.note_parser_agent import NoteParserResponse, NoteParserAgent
from agent_core.types import LLMResponse, LLMError

config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")


response_llm ="""<think> Okay, let's tackle this. The user provided a query where they want me to extract structured information from a customer note markdown file following specific rules. The output should be a JSON object structured according to their schema. \n\nFirst, I need to parse the input provided. The input starts with \"### Expected JSON schema...\" but the user says to respond only with the JSON. Wait, looking back, the user's instruction says to respond only with the JSON object, no other text. The task is to extract from the provided markdown the organization name, persons, project, etc., following the rules given.\n\nThe key points from the rules: extract organization name from H1, which here is \"Consumer amd Community Bank - Dallas\". Wait, but the H1 here is \"### Expected JSON schema\"? Wait no, looking at the input, the user wrote:\n\nThe input starts with \"### Expected JSON schema\" but the actual markdown they provided starts with \"Consumer amd Community Bank - Dallas\". Wait, maybe I misread. Wait the user provided a block where the input is the markdown content, and the user wants me to process it. Wait looking at the user's instruction again: the user provided a document structure example and then said to respond with a JSON. The user's example input is the markdown they pasted, which starts with \"Consumer amd Community Bank - Dallas\". Wait perhaps the H1 is \"Consumer amd Community Bank - Dallas\", so the organization name is \"Consumer amd Community Bank - Dallas\". \n\nWait the user's instruction says to extract organization name from H1 (single #), so H1 here is \"Consumer amd Community Bank - Dallas\". So organization is \"Consumer amd Community Bank - Dallas\".\n\nNext, the team section: \"## Team Matt TheBuilder(confluent champion)\". So team members are Matt TheBuilder with role Confluent Champion. So persons array would be [\"Matt TheBuilder\", ...? Wait the team section says \"Matt TheBuilder(confluent champion)\", so the name is Matt TheBuilder, role is Confluent Champion. So persons array: [{\"name\": \"Matt TheBuilder\", \"role\": \"Confluent Champion\"}].\n\nProject extraction: The project name is \"ABCD Consumer and Community Banking (CCB Continuum group is evaluating Confluent Cloud Flink...\" but according to the rules, project name can be \"{org_name} engagement\" or from context. The context mentions \"ABCD is already a Confluent Cloud customer...\", so project name might be \"ABCD Consumer and Community Banking (CCB Continuum group evaluation)\". Alternatively, the user's example in the schema's project description says to extract from context. The context mentions \"ABCD is already a Confluent Cloud customer...\", so project name could be \"ABCD Consumer and Community Banking (CCB Continuum group evaluation)\".\n\nPersons: already extracted.\n\nThe organization description is merged from various sections. The description says \"Merged context text...\", but the exact text might be \"ABCD is already a Confluent Cloud customer...\", but perhaps the organization's description is \"Consumer amd Community Bank - Dallas\" but according to the rules, the organization name is from H1, which is \"Consumer amd Community Bank - Dallas\".\n\nNow, the project extraction: The project name is \"ABCD Consumer and Community Banking (CCB Continuum group evaluation)\".\n\nPast steps: The past_steps section mentions \"PoC done by ABCD\", \"Integration Storage S3...\", etc. But according to the rules, past_steps and next_steps are from the corresponding sections. The past_steps section mentions \"PoC done by ABCD\", so past_steps might be [\"PoC done by ABCD\"].\n\nMeetings: The user mentions \"## Meetings\" but in the input, under \"## Meetings\" isn't present. Wait looking back, the input has \"## Meetings\" maybe not. Wait the user's input includes \"## Meetings\" isn't present. Wait in the provided input, under \"## Meetings\" isn't there. Wait the input provided starts with \"## Team\", etc., but perhaps the meetings section is not present. Wait the user's input includes \"## Meetings\" in their example? Wait no, looking at the user's input: the user provided the input as starting with \"Consumer amd Community Bank - Dallas\" and other sections. Wait perhaps the meetings section isn't present, but in the rules, any section with a meeting title becomes a meeting. Since the user's input doesn't have a \"Meetings\" section, perhaps there are none. Alternatively, maybe the \"## Context\" mentions \"Portability: cloud and on-premise\" but not a meeting title. Hmm, maybe there are no meetings here, so meetings array is empty.\n\nNow, the output structure requires organization, persons, project, meetings, etc. \n\nThe JSON structure from the schema provided by the user's example includes \"organization\", \"persons\", \"project\", \"meetings\", etc. \n\nPutting it all together, the organization is \"Consumer amd Community Bank - Dallas\". \n\nPersons: one person, Matt TheBuilder with role Confluent Champion. \n\nProject: \"ABCD Consumer and Community Banking (CCB Continuum group evaluation)\".\n\nMeetings: if any, but perhaps none. \n\nThe other parts like past_steps, next_steps might be extracted from \"Past Steps\" section: \"PoC done by ABCD\", \"Integration Storage S3...\", etc. But according to the rules, past_steps and next_steps are from the corresponding sections. Since the user's input has \"Past Steps\" section with \"PoC done by ABCD\", maybe past_steps is [\"PoC done by ABCD\"]. \n\nProject description: \"ABCD is already a Confluent Cloud customer...\" but the project name is \"ABCD Consumer and Community Banking (CCB Continuum group evaluation)\". \n\nNow structuring into the JSON as per the schema. The user's example output structure includes \"organization\", \"persons\", \"project\", \"meetings\", etc. \n\nI need to ensure that all required fields are present. The final JSON should follow the structure provided in the schema. Since the user wants only the JSON, I'll proceed to construct it accordingly.\n</think>\n\n```json\n{\n  \"organization\": \"Consumer amd Community Bank - Dallas\",\n  \"persons\": [\n    {\n      \"name\": \"Matt TheBuilder\",\n      \"role\": \"Confluent Champion\"\n    }\n  ],\n  \"project\": {\n    \"name\": \"ABCD Consumer and Community Banking (CCB Continuum group evaluation)\",\n    \"description\": \"ABCD is already a Confluent Cloud customer with dedicated Kafka clusters and operates mature, production-scale Flink applications including real-time offer aggregation (1.5B events/day) and lending eligibility determination systems.\",\n    \"past_steps\": [\"PoC done by ABCD\"],\n    \"next_steps\": []\n  },\n  \"meetings\": [],\n  \"discussion\": \"Portability: cloud and on-premise\",\n  \"platform_integration\": \"Evaluate Flink Deployment Options: Compare managed and serverless Flink models for compute parity and operational fit.\",\n  \"resiliency_strategies\": \"Review Exception and Error Handling Mechanisms: Discuss best practices for error detection, reporting, and automated recovery.\",\n  \"metrics_integration\": \"Identify Methods to Integrate Confluent metrics with ABCD tools (Prometheus, Splunk) for alerting and log management.\",\n  \"data_lake_integration\": \"Examine Direct write approaches to Data Lake (Glue, Iceberg) and ensure interoperability.\",\n  \"schema_evolution\": \"Discuss Schema Evolution Processes: Gain insights into schema evolution, compatibility, and migration strategies.\",\n  \"change_data_capture\": \"Review Connector Support: Review available source connectors for Aurora Postgres and Cassandra.\",\n  \"trusted_data_quality\": \"Review TDQ Capabilities: Discuss platform support for data quality measurement, reporting, and reconciliation.\"\n}\n```
"""

class TestNoteParserAgent:
    """Tests for NoteParserAgent."""

    def test_build_system_prompt_includes_expected_json_structure(self):
        """System prompt includes expected JSON structure (organization, persons, project, meetings)."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("NoteParserAgent")
        prompt = agent.build_system_prompt()
        assert "organization" in prompt
        assert "persons" in prompt
        assert "project" in prompt
        assert "meetings" in prompt
        assert "Expected JSON schema" in prompt or "json_schema" in prompt.lower()

    def test_factory_creates_note_parser_agent(self):
        """NoteParserAgent is available from factory (config_dir or defaults)."""
        factory = AgentFactory(config_dir=config_dir)
        assert "NoteParserAgent" in factory.list_agents()
        agent = factory.create_agent("NoteParserAgent")
        assert isinstance(agent, NoteParserAgent)

    def test_note_parser_agent_response_is_valid_json(self):
        """NoteParserAgent response is valid JSON."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("NoteParserAgent")
        response, error = agent._parse_output(response_llm)
        assert response is not None
        print(response)
        assert response['organization'] is not None
        assert response['organization'].name == "Consumer amd Community Bank - Dallas"
        assert response['persons'] is not None
        assert len(response['persons']) == 1
        assert response['persons'][0].name == "Matt TheBuilder"
        assert response['persons'][0].role == "Confluent Champion"
        assert response['project'] is not None
        assert response['project'].name == "ABCD Consumer and Community Banking (CCB Continuum group evaluation)"
        assert response['project'].description == "ABCD is already a Confluent Cloud customer with dedicated Kafka clusters and operates mature, production-scale Flink applications including real-time offer aggregation (1.5B events/day) and lending eligibility determination systems."
        assert response['project'].past_steps is not None
        assert len(response['project'].past_steps) == 1
        assert response['project'].past_steps[0].what == "PoC done by ABCD"
        assert response['project'].next_steps is not None
        assert len(response['project'].next_steps) == 0
        assert response['meetings'] is not None

    @pytest.mark.asyncio
    async def test_note_parser_returns_structured_response(self):
        """NoteParserAgent returns NoteParserResponse with organization, persons, project, meetings when LLM returns valid JSON."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("NoteParserAgent")
       

        valid_json = json.dumps({
            "organization": {"name": "Acme", "description": "A company"},
            "persons": [{"name": "John", "role": "Engineer", "context": None}],
            "project": {
                "name": "Acme engagement",
                "description": None,
                "past_steps": [{"what": "Met", "who": "John"}],
                "next_steps": [],
            },
            "meetings": [{"title": "Discovery", "content": "Notes here"}],
        })

        async def mock_chat_async(messages, config):
            return LLMResponse(
                content=valid_json,
                model=config.model,
                provider=config.provider,
                usage={"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
            )

        agent._llm_client.chat_async = mock_chat_async
        response = await agent.execute(AgentInput(query="# Acme\n## Team\n* John: Engineer"))

        assert isinstance(response, NoteParserResponse)
        assert response.organization is not None
        assert response.organization.name == "Acme"
        assert response.organization.description == "A company"
        assert len(response.persons) == 1
        assert response.persons[0].name == "John"
        assert response.persons[0].role == "Engineer"
        assert response.project is not None
        assert response.project.name == "Acme engagement"
        assert len(response.project.past_steps) == 1
        assert response.project.past_steps[0].what == "Met"
        assert response.project.past_steps[0].who == "John"
        assert len(response.meetings) == 1
        assert response.meetings[0].title == "Discovery"
        assert response.meetings[0].content == "Notes here"
        assert response.parse_error is None
        assert response.metadata.get("parsed_successfully") is True

    @pytest.mark.asyncio
    async def test_index_parser_parse_error_on_malformed_json(self):
        """IndexParserAgent sets parse_error when LLM response is not valid JSON."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("NoteParserAgent")
        async def mock_chat_async(messages, config):
            return LLMResponse(
                content="This is not JSON at all",
                model=config.model,
                provider=config.provider,
                usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            )

        agent._llm_client.chat_async = mock_chat_async
        response = await agent.execute(AgentInput(query="# Acme"))

        assert isinstance(response, NoteParserResponse)
        assert response.parse_error is not None
        assert "JSON" in response.parse_error or "Parse" in response.parse_error
        assert response.organization is None
        assert response.persons == []
        assert response.metadata.get("parsed_successfully") is False