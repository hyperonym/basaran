FROM hyperonym/basaran:0.15.3

# Set working directory
WORKDIR /app

# Download the model to be bundled
RUN python utils/download.py bigscience/bloomz-7b1-mt /model

# Provide default environment variables
ENV MODEL="/model"
ENV MODEL_LOCAL_FILES_ONLY="true"
ENV MODEL_HALF_PRECISION="true"
ENV SERVER_MODEL_NAME="bigscience/bloomz-7b1-mt"
