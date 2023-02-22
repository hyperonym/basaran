FROM hyperonym/basaran:0.4.0

# Set working directory
WORKDIR /app

# Download the model to be bundled
RUN MODEL="bigscience/bloomz-560m" MODEL_CACHE_DIR="/models" python server.py --download-only

# Provide default environment variables
ENV MODEL="bigscience/bloomz-560m"
ENV MODEL_LOCAL_FILES_ONLY="true"
