FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# Wrap pip install in a retry loop. pip skips packages it has ALREADY
# successfully installed on each re-run (shows "Requirement already
# satisfied"), so re-running the whole command after a failure
# effectively resumes from where it left off instead of starting
# over — countering random mid-download connection drops.
RUN for i in $(seq 1 15); do \
      pip install --no-cache-dir --default-timeout=100 -r requirements.txt && break; \
      echo "pip install attempt $i failed, retrying in 5s..."; \
      sleep 5; \
    done

# Pre-download ChromaDB's embedding model INTO the image at build time,
# instead of letting it download over the network the first time the
# app runs. This uses a small Python script (scripts/download_model.py)
# with its own retry + resume logic -- pure Python, no extra system
# packages needed, resilient to a connection dropping mid-transfer.
COPY scripts/download_model.py /tmp/download_model.py
RUN python3 /tmp/download_model.py

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]