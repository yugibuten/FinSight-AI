import json
import os

from openai import OpenAI
from dotenv import load_dotenv

from core.tool_registry import tools, tool_functions

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def ask_llm(user_query):

    response = client.responses.create(
        model="gpt-5.6",
        input=user_query,
        tools=tools
    )

    while True:

        tool_calls = [
            item for item in response.output
            if item.type == "function_call"
        ]

        if not tool_calls:
            return response.output_text

        tool_outputs = []

        for call in tool_calls:

            function = tool_functions[call.name]

            arguments = json.loads(call.arguments)

            result = function(**arguments)

            tool_outputs.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": json.dumps(result)
            })

        response = client.responses.create(
            model="gpt-5.6",
            previous_response_id=response.id,
            input=tool_outputs
        )