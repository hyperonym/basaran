FROM nvcr.io/nvidia/pytorch:22.08-py3

# Create app directory
WORKDIR /app

# Install app dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Bundle app source
COPY . .

# Expose ports
EXPOSE 80

# Force the stdout and stderr streams to be unbuffered
ENV PYTHONUNBUFFERED="1"

# Hide welcome message from bitsandbytes
ENV BITSANDBYTES_NOWELCOME="1"

# Provide default environment variables
ENV MODEL="bigscience/bloomz-560m"
ENV HOST="0.0.0.0"
ENV PORT="80"
ENV MODEL_REVISION=""
ENV MODEL_CACHE_DIR="/models"
ENV MODEL_LOAD_IN_8BIT="false"
ENV MODEL_LOCAL_FILES_ONLY="false"
ENV MODEL_TRUST_REMOTE_CODE="false"
ENV MODEL_HALF_PRECISION="false"
ENV SERVER_THREADS="8"
ENV SERVER_IDENTITY="basaran"
ENV SERVER_CONNECTION_LIMIT="1024"
ENV SERVER_CHANNEL_TIMEOUT="300"
ENV SERVER_MODEL_NAME=""
ENV SERVER_NO_PLAYGROUND="false"
ENV COMPLETION_MAX_PROMPT="4096"
ENV COMPLETION_MAX_TOKENS="4096"
ENV COMPLETION_MAX_N="5"
ENV COMPLETION_MAX_LOGPROBS="5"
ENV COMPLETION_MAX_INTERVAL="50"
ENV CUDA_MEMORY_FRACTION="1.0"

# Specify entrypoint and default parameters
ENTRYPOINT [ "python", "-m", "basaran" ]
