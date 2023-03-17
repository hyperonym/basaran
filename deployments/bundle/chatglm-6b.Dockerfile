FROM hyperonym/basaran:0.12.0

# Set working directory
WORKDIR /app

# Install extra dependencies
RUN pip install icetk cpm_kernels

# Download the model to be bundled
RUN MODEL_REVISION=refs/pr/7 python utils/download.py THUDM/chatglm-6b

# Provide default environment variables
ENV MODEL="THUDM/chatglm-6b"
ENV MODEL_REVISION="refs/pr/7"
ENV MODEL_LOCAL_FILES_ONLY="true"
ENV MODEL_TRUST_REMOTE_CODE="true"
ENV MODEL_HALF_PRECISION="true"
