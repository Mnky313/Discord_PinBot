FROM python
COPY ./PinBot/ /app
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python", "./main.py"]

