# F5 XC ACME CNAME Record Validator

This Python script verifies ACME challenge CNAME records by comparing expected DNS targets (retrieved via F5 XC API) with their actual DNS resolutions.

## Features

- Fetches ACME CNAME records from F5 XC Load-Balancers.
- Resolves each record's DNS target using `pydig`.
- Compares expected vs resolved targets.
- Displays results.

## Requirements

- Python 3.7+
- `.env` file with the following variables:
```
XC_API_TOKEN="your_api_token"
XC_API_URL="https://<region>.console.ves.volterra.io/api"
```

## Installation

1. Clone the repository.
2. Open the repository directory and initialise a Python virtual environment (optional)
```bash
cd ./F5-CNAME-Verification
python3 -m venv ./
source ./bin/activate
```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4.	Create a .env file with your credentials.
```
XC_API_TOKEN="your_api_token"
XC_API_URL="https://<region>.console.ves.volterra.io/api"
```

## Usage
```bash
usage: xc_CNAMEverify.py [-h] [--mode {print,table}]

options:
  -h, --help            show this help message and exit
  --mode {print,table}  Choose output format: "table" (default) or "print".
```

The script will output a table showing:
- Load Balancer name
- Record name
- Expected DNS target
- Resolved DNS target
- Match status

## Dependencies
- requests
- rich
- python-dotenv
- pydig

