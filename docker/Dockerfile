FROM python:3.11-slim

ENV HOST=127.0.0.1 STAGE='DEV' EXTENSION_ID="" APP_NAME='Cloud Save' PORT=8000
WORKDIR /src
EXPOSE 8000

# Install dependencies
# RUN pip install uv
COPY server.py .
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application source code
COPY /app/ /src/app/
 
CMD ["python", "server.py"]