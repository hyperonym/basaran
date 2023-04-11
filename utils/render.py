"""
Use this script to render a Jinja template with variables read from JSON.
This is mainly used to debug the prompt template required for the chat API.
Each model has different requirements for the format of chat history.
Please refer to the specific model's documentation for details.
"""
import json
import sys

import jinja2

if len(sys.argv) < 3:
    sys.exit("usage: python render.py TEMPLATE_FILE JSON_FILE")

with open(sys.argv[1]) as file:
    template = jinja2.Template(file.read())

with open(sys.argv[2]) as file:
    data = json.load(file)

sys.stdout.write(template.render(data))
