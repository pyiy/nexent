# Base image stage
FROM quay.io/unstructured-io/base-images:wolfi-base-latest AS base

ARG PYTHON=python3.11
ARG PIP="${PYTHON} -m pip"

USER root
WORKDIR /app

# Install system dependencies and set up Python
RUN apk add font-ubuntu git && \
    fc-cache -fv && \
    [ -e /usr/bin/python3 ] || ln -s /usr/bin/$PYTHON /usr/bin/python3

USER notebook-user

# Set environment variables
ENV PATH="${PATH}:/home/notebook-user/.local/bin" \
    TESSDATA_PREFIX=/usr/local/share/tessdata \
    NLTK_DATA=/home/notebook-user/nltk_data \
    HF_HUB_OFFLINE=1

# Builder stage
FROM base AS builder

USER root
WORKDIR /build

# Copy only the requirements first to leverage Docker cache
COPY backend/requirements.txt .
COPY sdk /build/sdk

# Install dependencies in builder stage
RUN pip config --user set global.progress_bar off && \
    pip install --user --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple && \
    cd /build/sdk && pip install . -i https://mirrors.aliyun.com/pypi/simple && \
    pip install --user --no-cache-dir "unstructured[all-docs]" -i https://mirrors.aliyun.com/pypi/simple && \
    rm -rf /root/.cache/pip/* && \
    rm -rf /home/notebook-user/.cache/pip/*

# Final stage
FROM base

USER root
WORKDIR /opt

# Copy only necessary files from builder
COPY --from=builder /home/notebook-user/.local /home/notebook-user/.local
COPY backend /opt/backend
COPY sdk /opt/sdk

# Copy pre-downloaded model from workflow
COPY model-assets/clip-vit-base-patch32 /opt/models/clip-vit-base-patch32

# Set permissions and prepare NLTK data
RUN chown -R notebook-user:notebook-user /opt/backend && \
    chown -R notebook-user:notebook-user /opt/sdk && \
    chown -R notebook-user:notebook-user /opt/models && \
    chmod +x /opt/backend/data_process_service.py && \
    mkdir -p ${NLTK_DATA} && \
    $PYTHON -m nltk.downloader -d ${NLTK_DATA} punkt_tab averaged_perceptron_tagger_eng

# Switch to non-root user
USER notebook-user

# Expose the service port
EXPOSE 5012

# Set the entrypoint
ENTRYPOINT ["python", "/opt/backend/data_process_service.py"]