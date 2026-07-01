FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./
RUN uv pip compile pyproject.toml -o requirements.txt
RUN uv pip install --system -r requirements.txt

COPY app ./app
COPY pytest.ini ./pytest.ini

CMD ["python", "-m", "app.bot.run_bot"]
