# GitHub Copilot Premium Requests Calculator

This is a simple calculator for premium requests. It allows you to input a premium requests csv and it will calculate a request summary and estimated costs.  


## Usage

1. Clone the repository:
   ```
   git clone https://github.com/jonjozwiak/premium-requests-calculator.git
   ```
2. Navigate to the project directory:
   ```
   cd premium-requests-calculator
   ```
3. Create a virtual environment (optional but recommended):
   ```
   python3 -m venv venv
   source venv/bin/activate  
   ```
4. Install the required packages:
   ```
   pip3 install pandas streamlit plotly.express fpdf kaleido matplotlib watchdog
   ```
5. Run the script to summarize data and generate CSV files:
   ```
   python3 summarize_premium_requests.py <premium_requests_csv_file>
   ```
6. Run the Streamlit app to visualize the data (This must be run in the same directory as the generated CSV files):
   ```
   streamlit run dashboard.py <premium_requests_csv_file>
   ```

## Docker Usage

You can run the application using Docker. This allows you to process premium requests and launch the dashboard in a containerized environment.

### Build the Docker image

```sh
docker build -t premium-requests-calculator:latest .
```

### Run the container

Mount your input directory where you have your premium requests csv to `/data` in the container. Update the `INPUT_CSV` environment variable to point to your input CSV file. For example:

```sh
docker run --rm --name premium-requests-calculator -p 8501:8501 -v /path/to/your/data:/data \
  -e INPUT_CSV=/data/your_input.csv \
  premium-requests-calculator:latest
```

- Access the Streamlit dashboard at [http://localhost:8501](http://localhost:8501).
- When finished, you can stop the container with `Ctrl+C` a few times.  Also run `docker stop premium-requests-calculator` to stop the container. 

## Output CSVs
- `requests_per_model.csv`: A CSV file containing the number of requests per model.
- `requests_per_user_per_model.csv`: A CSV file containing the number of requests per user per model.
- `requests_per_user.csv`: A CSV file containing the number of requests per user.
- `estimated_requests_per_user.csv`: A CSV file containing the estimated number of requests if data is less than 30 days.

## Answers this calculator provides
- Which users are near or over quota?
- Which users would benefit from a Copilot Enterprise license?
- Which premium models are most popular?
- What is estimated number of requests if data is less than 30 days?