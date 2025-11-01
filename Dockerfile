FROM python:3.12-slim

WORKDIR /app

# Copy dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose Flask port
EXPOSE 5000

# Auto initialize DB before start
ENV FLASK_APP=app.py

CMD ["python", "app.py"]
