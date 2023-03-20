FROM hyperonym/basaran:0.12.0

# Set working directory
WORKDIR /app

# Download the model to be bundled
RUN python utils/download.py BelleGroup/BELLE-7B-1M

# Provide default environment variables
ENV MODEL="BelleGroup/BELLE-7B-1M"
ENV MODEL_LOAD_IN_8BIT="true"
ENV MODEL_LOCAL_FILES_ONLY="true"
