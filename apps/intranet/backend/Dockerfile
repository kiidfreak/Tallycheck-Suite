# so the shared libs/py_auth package is inside the build context.
FROM python:3.12-slim

WORKDIR /app

# Shared Python packages (better layer caching)
COPY libs/py_auth /opt/py_auth
COPY libs/py_errors /libs/py_errors
COPY libs/py_config /libs/py_config
COPY libs/py_success /libs/py_success

# Backend dependencies
COPY apps/intranet/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir /opt/py_auth

# Backend source
COPY apps/intranet/backend/ .

ENV FLASK_APP=app.py
EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
