FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime

# Create app directory
WORKDIR /app

# Bundle app source
COPY . .

# Install app dependencies
RUN pip install -U pip && pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu116

# Expose ports
EXPOSE 80

# Provide default environment variables
ENV MODEL="bigscience/bloomz-560m"
ENV HOST="0.0.0.0"
ENV PORT="80"
ENV MODEL_CACHE_DIR="/models"
ENV MODEL_LOAD_IN_8BIT="false"
ENV MODEL_LOCAL_FILES_ONLY="false"
ENV SERVER_THREADS="8"
ENV SERVER_IDENTITY="basaran"
ENV SERVER_CONNECTION_LIMIT="1024"
ENV SERVER_CHANNEL_TIMEOUT="300"
ENV SERVER_MODEL_NAME=""
ENV COMPLETION_MAX_PROMPT_LENGTH="4096"
ENV COMPLETION_MAX_TOKENS="4096"
ENV COMPLETION_MAX_N="5"
ENV COMPLETION_MAX_LOGPROBS="5"
ENV COMPLETION_MAX_STREAM_INTERVAL_MS="100"

# Specify entrypoint and default parameters
ENTRYPOINT [ "python", "server.py" ]
