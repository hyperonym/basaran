"""
Script for building and distributing Python packages.
"""
from setuptools import find_packages, setup

VERSION = "0.13.2"

setup(
    name="basaran",
    version=VERSION,
    description="Open-source alternative to the OpenAI text completion API",
    long_description="Basaran is an open-source alternative to the OpenAI "
    "text completion API. It provides a compatible streaming API for your "
    "Hugging Face Transformers-based text generation models.",
    author="Hyperonym",
    author_email="prompt@hyperonym.org",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8.0",
    install_requires=["torch", "transformers"],
    keywords=["api", "gpt", "huggingface", "nlp", "openai", "transformer"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
