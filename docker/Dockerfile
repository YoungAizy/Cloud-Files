FROM python:3.11-slim

# Copy the AWS Lambda Web Adapter binary into my image
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3 /lambda-adapter /opt/extensions/lambda-adapter

ENV HOST=127.0.0.1 STAGE='DEV' EXTENSION_ID="" APP_NAME='Drive-Save'
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