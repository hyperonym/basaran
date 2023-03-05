"""
Example of using Basaran with the OpenAI Python Library.
"""
import openai

# Point requests to Basaran by overwriting openai.api_base.
# Or you can use the OPENAI_API_BASE environment variable instead.
openai.api_base = "http://127.0.0.1/v1"

# Enter any non-empty API key to pass the client library's check.
openai.api_key = "xxx"

# Enter any non-empty model name to pass the client library's check.
completion = openai.Completion.create(
    model="xxx", prompt="once upon a time", max_tokens=32, echo=True
)

# Print the completion.
print(completion.choices[0].text)
