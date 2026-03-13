FROM python:3.13-alpine

RUN apk add --no-cache curl

WORKDIR /app

COPY . .

RUN python -m pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]