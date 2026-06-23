import os
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents="Hi, can you send me a catalog?",
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name="send_catalog_document",
                            description="Send catalog.",
                            parameters=types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "query_term": types.Schema(type=types.Type.STRING),
                                    "caption": types.Schema(type=types.Type.STRING),
                                    "sentiment_score": types.Schema(type=types.Type.NUMBER),
                                },
                            ),
                        )
                    ]
                )
            ]
        )
    )
    print("Response parts:")
    for part in response.candidates[0].content.parts:
        print(part)
        if part.function_call:
            print("Function Call args type:", type(part.function_call.args))
            print("Args:", dict(part.function_call.args))

except Exception as e:
    print(f"Error: {e}")
