"""
Example of using Basaran as a Python Library.
"""
from basaran.model import load_model

model = load_model("hf-internal-testing/tiny-random-t5")

for choice in model("once upon a time"):
    print(choice)
