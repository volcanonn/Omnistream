FROM python:3.14-slim

WORKDIR /code

RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -m grpc_tools.protoc \
    --proto_path=./protos \
    --python_out=./app/core/proto \
    --grpc_python_out=./app/core/proto \
    ./protos/*.proto

# just a test
#RUN ls -la app/core/proto/ | grep _pb2

EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]