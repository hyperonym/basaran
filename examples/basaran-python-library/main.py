"""
Example of using Basaran as a Python Library.
"""
from basaran.model import load_model

model = load_model("gpt2")

for choice in model("once upon a time"):
    print(choice)
