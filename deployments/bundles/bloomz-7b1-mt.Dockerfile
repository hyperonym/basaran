FROM hyperonym/basaran:0.3.0

# Set working directory
WORKDIR /app

# Download the model to be bundled
RUN MODEL="bigscience/bloomz-7b1-mt" MODEL_CACHE_DIR="/models" python server.py --download-only

# Provide default environment variables
ENV MODEL="bigscience/bloomz-7b1-mt"
ENV MODEL_LOAD_IN_8BIT="true"
ENV MODEL_LOCAL_FILES_ONLY="true"
