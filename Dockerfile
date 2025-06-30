FROM python:3.13-slim

WORKDIR /app

# Install Chromium and dependencies for Kaleido/Plotly
RUN apt-get update && \
    apt-get install -y chromium chromium-driver fonts-liberation libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libdrm2 libexpat1 libfontconfig1 \
    libgbm1 libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 \
    libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 \
    libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 lsb-release xdg-utils \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/lib/chromium/:${PATH}"
ENV BROWSER=chromium

RUN pip3 install pandas streamlit plotly.express fpdf kaleido matplotlib watchdog

COPY summarize_premium_requests.py dashboard.py ./

# Create a directory for data volume
RUN mkdir /data

EXPOSE 8501

# Default CMD allows overriding input/output CSVs
CMD python summarize_premium_requests.py "${INPUT_CSV:-/data/premium_requests.csv}" && \
    streamlit run dashboard.py "${INPUT_CSV:-/data/premium_requests.csv}" --server.port 8501 --server.address 0.0.0.0
