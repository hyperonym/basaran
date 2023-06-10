FROM hyperonym/basaran:0.19.0

# Set working directory
WORKDIR /app

# Download the model to be bundled
RUN TENSOR_FORMAT=safetensors python utils/download.py bigscience/bloomz-560m /model

# Provide default environment variables
ENV MODEL="/model"
ENV MODEL_LOCAL_FILES_ONLY="true"
ENV SERVER_MODEL_NAME="bigscience/bloomz-560m"
