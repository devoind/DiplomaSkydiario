FROM python:3.11-slim

WORKDIR /todolist_code/todolist

EXPOSE 8000

#RUN groupadd --system service && useradd --system -g service api

ENV PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.2.2 \
    PYTHON_PATH=/todolist_code/todolist \
    PYTHONUNBUFFERED=1

RUN apt update && apt full-upgrade -y && apt autoremove -y

RUN pip install -U pip setuptools

# Dependencies installation with pip
#COPY requirements.txt .
#RUN pip install -r requirements.txt

# Dependencies installation with poetry
RUN pip install "poetry==$POETRY_VERSION" -v
COPY poetry.lock pyproject.toml ./
RUN POETRY_VIRTUALENVS_CREATE=false poetry install --no-interaction --without dev --no-root -v

COPY . .

#USER api

ENTRYPOINT ["bash", "entrypoint.sh"]

#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["gunicorn", "todolist.wsgi:application", "--bind", "0.0.0.0:8000", \
        "--log-level", "info", "--capture-output", \
        "--enable-stdio-inheritance", "--workers", "4", \
        "--access-logfile", "gunicorn-access.log", "--error-logfile", "gunicorn.log"]
