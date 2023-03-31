# syntax=docker/dockerfile:1

FROM python:3.11-alpine

WORKDIR /app

#RUN python3 -m pip install --upgrade pip
COPY requirements.txt requirements-telegrambot.txt
RUN pip3 install -r requirements-telegrambot.txt
ENV TG_BOT_TOKEN="Run telegram-bot-setup.sh"
COPY . .

EXPOSE 5000 5000

CMD ["python", "telegram-bot-run.py"]
