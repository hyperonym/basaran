FROM hyperonym/basaran:0.12.0

# Set working directory
WORKDIR /app

# Download the model to be bundled
RUN python utils/download.py bigscience/bloomz-560m

# Provide default environment variables
ENV MODEL="bigscience/bloomz-560m"
ENV MODEL_LOCAL_FILES_ONLY="true"
