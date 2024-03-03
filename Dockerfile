# Stage 1: Build and install dependencies
FROM python:3.10-slim as builder

# Install poetry
RUN pip install --no-cache-dir poetry==1.8.2

# Copy only necessary files for installing dependencies
WORKDIR /app
COPY pyproject.toml poetry.lock* /app/

# Install dependencies without dev dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Stage 2: Build the final image
FROM python:3.10-slim as final

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

# Pre-download the model file
COPY embedding_models.py /app/
RUN python -c "from embedding_models import get_embedder; get_embedder()"

# Copy the application code
COPY . /app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "webserver:app", "--host", "0.0.0.0", "--port", "8000"]
