FROM python:3.10-alpine AS builder

########### to view prints #############
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
########################################

ENV APP_HOME=/home/app
ENV VENV_PATH=/opt/venv
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

RUN addgroup -S app && adduser -S app -G app

RUN python -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

RUN python -m pip install --upgrade pip
COPY . .
RUN python -m pip install -Ur requirements.txt

RUN chown -R app:app $APP_HOME $VENV_PATH
USER app

EXPOSE 50051
ENTRYPOINT [ "python", "-m", "simtest" ]
