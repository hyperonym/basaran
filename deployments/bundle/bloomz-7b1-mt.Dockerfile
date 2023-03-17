FROM hyperonym/basaran:0.12.0

# Set working directory
WORKDIR /app

# Download the model to be bundled
RUN python utils/download.py bigscience/bloomz-7b1-mt

# Provide default environment variables
ENV MODEL="bigscience/bloomz-7b1-mt"
ENV MODEL_LOAD_IN_8BIT="true"
ENV MODEL_LOCAL_FILES_ONLY="true"
