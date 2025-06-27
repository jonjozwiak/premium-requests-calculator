import pandas as pd
import sys

# Accept CSV file as command-line argument
if len(sys.argv) < 2:
    print('Usage: python3 summarize_premium_requests.py <input_csv_file>')
    sys.exit(1)
input_csv = sys.argv[1]

# Load the CSV file
df = pd.read_csv(input_csv)

# Standardize column names to lowercase for easier access
df.columns = [col.lower() for col in df.columns]

# Ensure timestamp column is datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Filter out rows where the last column is "Unlimited"
last_col = df.columns[-1]
df = df[df[last_col] != "Unlimited"]

# Filter out rows where the last column is "2147483647"
df = df[df[last_col] != "2147483647"]

# Group by model to get request counts, then calculate premium requests
model_counts = df.groupby('model').size().reset_index(name='requests_used')

# 1. First and last timestamp, duration
first_ts = df['timestamp'].min()
last_ts = df['timestamp'].max()
duration = last_ts - first_ts
hours = duration.total_seconds() / 3600
days = duration.days + duration.seconds / (3600*24)

print('--- Data Summary ---')
print(f'First timestamp: {first_ts}')
print(f'Last timestamp: {last_ts}')
print(f'Duration: {hours:.2f} hours ({days:.2f} days)')

# Print average number of hours in a 31-day month and percentage of full month
avg_month_hours = 31 * 24
percent_of_month = (hours / avg_month_hours) * 100
print(f'Average hours in a 31-day month: {avg_month_hours} hours')
print(f'Percent of full 31-day month: {percent_of_month:.2f}%')

# 2. Table per model: requests used and premium requests consumed
print('\n--- Requests per Model ---')
model_table = model_counts.copy()
model_table = model_table[['model', 'requests_used']]
model_table.to_csv('requests_per_model.csv', index=False)

print(model_table.to_string(index=False))

# 3. Table per user per model: requests used (no sorting)
user_model_counts = df.groupby(['user', 'model']).size().reset_index(name='requests_used')

user_model_table = user_model_counts[['user', 'model', 'requests_used']]
user_model_table.to_csv('requests_per_user_per_model.csv', index=False)

# 4. Table per user: total premium requests across all models, sorted descending
user_total_table = user_model_counts.groupby('user').agg({
    'requests_used': 'sum'
}).reset_index()
user_total_table = user_total_table.sort_values('requests_used', ascending=False)
user_total_table.to_csv('requests_per_user.csv', index=False)

# --- Add: Compute total monthly quota per user (ignoring 'Unlimited') ---
def parse_quota(val):
    try:
        return float(val)
    except Exception:
        return None

# Only consider rows where quota is not 'Unlimited'
quota_df = df[df['total monthly quota'].astype(str).str.lower() != 'unlimited'].copy()
quota_df['quota_num'] = quota_df['total monthly quota'].apply(parse_quota)

# For each user, get the max quota (if any)
user_quota = quota_df.groupby('user')['quota_num'].max().reset_index()
user_quota = user_quota.rename(columns={'quota_num': 'total_monthly_quota'})

# Merge quota into user_total_table
user_total_table = user_total_table.merge(user_quota, on='user', how='left')

# Filter out users with only 'Unlimited' quotas (i.e., total_monthly_quota is NaN)
user_total_table = user_total_table[~user_total_table['total_monthly_quota'].isna()].copy()

# Save with quota column
user_total_table[['user', 'requests_used', 'total_monthly_quota']].to_csv('requests_per_user.csv', index=False)

# 5. Estimate monthly total requests per user (premium requests)
# Use the hours and percent_of_month already calculated

# If data covers >= 30 days, do not scale up, just use actuals
if days >= 30:
    print("\nFull month of data detected (>= 30 days). No scaling applied for monthly estimate.")
    user_total_table['estimated_requests_used'] = user_total_table['requests_used'].round().astype(int)
else:
    scaling_factor = avg_month_hours / hours if hours > 0 else 0
    user_total_table['estimated_requests_used'] = (user_total_table['requests_used'] * scaling_factor).round().astype(int)

# Save monthly estimates with quota column
monthly_sorted = user_total_table.sort_values('estimated_requests_used', ascending=False)
monthly_sorted[['user', 'estimated_requests_used', 'total_monthly_quota']].to_csv(
    'estimated_requests_per_user.csv', index=False
)

print('\n--- Estimated Overage (Based on Premium Requests) ---')
# Calculate overage for estimated_requests_used (portion over each user's quota)
overage = (monthly_sorted['estimated_requests_used'] - monthly_sorted['total_monthly_quota']).clip(lower=0)
sum_overage = overage.sum()

print(f"Sum of estimated monthly premium request overage: {sum_overage}")

# Calculate and print cost for each sum
cost_overage = sum_overage * 0.04

print(f"Estimated monthly overage cost: ${cost_overage:.2f}")
