FROM python:3.11-slim

# Install dependencies necessary to build and run FFmpeg
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    yasm \
    git \
    curl \
    portaudio19-dev \
    libffi-dev \
    libssl-dev \
    libx264-dev \
    libopus-dev

RUN echo "deb http://deb.debian.org/debian/ bullseye main\ndeb-src http://deb.debian.org/debian/ bullseye main" | tee /etc/apt/sources.list.d/ffmpeg.list  &&\
    apt-get update && \
    apt-get install -y ffmpeg

WORKDIR /realtime_ai_character
RUN pip install --upgrade pip
# Install Python dependencies
COPY requirements.txt /realtime_ai_character
RUN pip install -r /realtime_ai_character/requirements.txt

# Create a non-root user and switch to it
RUN useradd -m -u 1000 user
RUN chown -R user:user /realtime_ai_character
USER user

# Set the user's home directory
ENV HOME=/home/user

# Copy the project files with appropriate permissions
COPY --chown=user:user ./ /realtime_ai_character

# Expose 7860 port from the docker image.
EXPOSE 7860

# Make the entrypoint script executable
RUN chmod +x /realtime_ai_character/entrypoint.sh

# Run the application
CMD ["/bin/sh", "/realtime_ai_character/entrypoint.sh"]
