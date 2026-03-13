FROM python:3.11-slim

WORKDIR /app

COPY shared/requirements.txt /app/shared/requirements.txt
RUN pip install --no-cache-dir -r /app/shared/requirements.txt

COPY services/member_service/requirements.txt /app/services/member_service/requirements.txt
RUN pip install --no-cache-dir -r /app/services/member_service/requirements.txt

COPY shared/ /app/shared/
COPY services/__init__.py /app/services/__init__.py
COPY services/member_service/ /app/services/member_service/

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "services.member_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
