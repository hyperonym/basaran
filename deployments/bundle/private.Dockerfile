FROM hyperonym/basaran:0.12.0

# Copy model files
COPY my-secret-model /models/my-secret-model

# Provide default environment variables
ENV MODEL="/models/my-secret-model"
ENV MODEL_LOCAL_FILES_ONLY="true"
ENV SERVER_MODEL_NAME="my-secret-model"
