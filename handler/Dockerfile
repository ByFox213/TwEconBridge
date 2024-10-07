FROM python:3.11-alpine
ADD ./ /tw
ADD ../util /tw/util
WORKDIR /tw
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "-u", "/tw/main.py"]
