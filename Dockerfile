# Start from Node + Python base (TA suggested node:18-bullseye)
FROM --platform=$BUILDPLATFORM node:18-bullseye

# Set working directory
WORKDIR /app

# Install Python 3, pip, and venv
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    apt-get clean

# Create a virtual environment inside container
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first (so Docker can cache installs)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install any npm dependencies you need
RUN npm install -g typescript

# Copy the rest of your project into container
COPY . .

# Default command runs your test suite
CMD ["python", "run.py", "test"]
