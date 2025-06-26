FROM python:3.13-slim

WORKDIR /app

RUN pip3 install pandas streamlit plotly.express fpdf kaleido matplotlib watchdog

COPY summarize_premium_requests.py dashboard.py ./

# Create a directory for data volume
RUN mkdir /data

EXPOSE 8501

# Default CMD allows overriding input/output CSVs
CMD python summarize_premium_requests.py "${INPUT_CSV:-/data/premium_requests.csv}" && \
    streamlit run dashboard.py "${INPUT_CSV:-/data/premium_requests.csv}" --server.port 8501 --server.address 0.0.0.0
