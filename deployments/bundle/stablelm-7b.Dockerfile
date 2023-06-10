FROM hyperonym/basaran:0.19.0

# Set working directory
WORKDIR /app

# Download the model to be bundled
RUN python utils/download.py stabilityai/stablelm-tuned-alpha-7b /model

# Provide default environment variables
ENV MODEL="/model"
ENV MODEL_LOCAL_FILES_ONLY="true"
ENV MODEL_HALF_PRECISION="true"
ENV SERVER_MODEL_NAME="stabilityai/stablelm-tuned-alpha-7b"
