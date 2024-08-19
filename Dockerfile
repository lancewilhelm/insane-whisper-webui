# Stage 1: Build the frontend
FROM node:18-alpine as frontend-build

# Set working directory for frontend
WORKDIR /app/frontend

# Copy frontend source code and .env file
COPY frontend/package*.json ./
COPY frontend/ ./
COPY frontend/.env ./

# Install dependencies and build the frontend
RUN npm install
RUN npm run build

# Stage 2: Build the backend and install dependencies
FROM python:3.10-slim as backend-build

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory for backend
WORKDIR /app

# Copy backend source code and .env file
COPY backend/ ./
RUN true
COPY backend/.env ./
RUN true

# Copy the built frontend from the previous stage
COPY --from=frontend-build /app/frontend/dist /app/frontend

# Install backend dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Expose the Flask port
EXPOSE 5000

# Start the Flask app
CMD ["flask", "run"]

