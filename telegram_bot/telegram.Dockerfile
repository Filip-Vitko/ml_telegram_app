FROM python:3.13-alpine

WORKDIR /app

COPY . .

RUN python -m pip install --no-cache-dir --user -r requirements.txt

CMD ["python", "bot.py"]