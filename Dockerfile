FROM public.ecr.aws/lambda/python:3.9

COPY lambda_function.py /var/task/
COPY besso /var/task/besso

RUN pip install ask-sdk-core ask-sdk-model firebase-admin

CMD ["lambda_function.handler"]
