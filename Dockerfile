FROM python:3.9.1-buster
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . /code/