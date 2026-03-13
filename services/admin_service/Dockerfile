FROM python:3.11-slim

WORKDIR /app

COPY shared/requirements.txt /app/shared/requirements.txt
RUN pip install --no-cache-dir -r /app/shared/requirements.txt

COPY services/admin_service/requirements.txt /app/services/admin_service/requirements.txt
RUN pip install --no-cache-dir -r /app/services/admin_service/requirements.txt

COPY shared/ /app/shared/
COPY services/__init__.py /app/services/__init__.py
COPY services/admin_service/ /app/services/admin_service/

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "services.admin_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
