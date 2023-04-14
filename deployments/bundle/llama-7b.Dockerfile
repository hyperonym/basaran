FROM hyperonym/basaran:0.15.1

# Set working directory
WORKDIR /app

# Download the model to be bundled
RUN python utils/download.py Enoch/llama-7b-hf /model

# Provide default environment variables
ENV MODEL="/model"
ENV MODEL_LOCAL_FILES_ONLY="true"
ENV MODEL_HALF_PRECISION="true"
ENV SERVER_MODEL_NAME="LLaMA-7B"
