# Container image for deploying the web app (src/api.py) to Google Cloud Run.
#
# WHY THIS FILE LOOKS THE WAY IT DOES
# ------------------------------------
# Two decisions here are worth more than the rest of the file combined, and
# both are about cold-start time. Cloud Run scales to zero, so an idle app has
# no running instance and the next visitor pays for the whole startup. Getting
# that wrong is the difference between a demo that feels broken and one that
# feels slow-but-fine.
#
#   1. CPU-ONLY PYTORCH, INSTALLED FIRST.
#      sentence-transformers depends on torch. `pip install torch` defaults to
#      the CUDA build, which drags in several gigabytes of NVIDIA libraries
#      that are pure dead weight on Cloud Run -- there is no GPU. Installing
#      the CPU wheel first means torch is already satisfied when
#      requirements.txt is processed, and the image drops from roughly 4GB to
#      well under 1GB. A smaller image is pulled and started faster on every
#      cold start.
#
#   2. THE EMBEDDING MODEL IS BAKED IN AT BUILD TIME.
#      all-MiniLM-L6-v2 is ~90MB and sentence-transformers downloads it from
#      HuggingFace on first use. Left to runtime that download happens inside
#      the first request of every cold start, and fails outright if HuggingFace
#      is slow or down. Downloading it during the build makes startup a local
#      file read and removes a third-party service from the request path.
#
# The FAISS index and the book texts are already committed to the repo, so
# there is no build step for them -- they are copied in and the app serves
# immediately.

FROM python:3.11-slim

# PORT is what Cloud Run injects and expects the container to listen on.
# Defaulted here so `docker run` works locally without setting it.
ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Keep HuggingFace's cache at a fixed path so the model baked in below is
    # the same one found at runtime.
    HF_HOME=/opt/hf \
    # The app never trains or fine-tunes; telemetry from these libraries is
    # noise in Cloud Logging.
    TRANSFORMERS_NO_ADVISORY_WARNINGS=1

WORKDIR /app

# See note 1 above: CPU-only torch, before anything that depends on it.
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# See note 2 above: pull the embedding model now, not on the first request.
RUN python -c "from sentence_transformers import SentenceTransformer; \
SentenceTransformer('all-MiniLM-L6-v2')"

# Application code and the committed corpus + prebuilt FAISS index.
COPY src/ ./src/
COPY data/ ./data/
COPY eval/ ./eval/

# Serves src/api.py -- the FastAPI app and the hand-written frontend in
# src/web/.
#
#   --host 0.0.0.0   bind all interfaces, not just localhost, or Cloud Run's
#                    startup probe cannot reach the process
#   --port $PORT     Cloud Run chooses the port; hardcoding one fails
#   --app-dir src    the modules import each other bare (`import config`), so
#                    src/ has to be the import root
#   no --workers     one process, because the embedding model and FAISS index
#                    are process-local. A second worker would load its own
#                    ~400MB copy and double the memory for no throughput gain
#                    at this traffic level.
#
# Shell form on purpose: $PORT has to be expanded at runtime, not at build.
CMD uvicorn api:app --host 0.0.0.0 --port $PORT --app-dir src
