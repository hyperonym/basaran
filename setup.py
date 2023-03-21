"""
Script for building and distributing Python packages.
"""
from setuptools import setup, find_packages

VERSION = "0.12.0"

setup(
    name="basaran",
    version=VERSION,
    description="Open-source alternative to the OpenAI text completion API",
    author="Hyperonym",
    author_email="prompt@hyperonym.org",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8.0",
    install_requires=["tenacity", "torch", "transformers"],
    keywords=["transformer", "huggingface", "openai", "nlp", "gpt", "api"],
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
