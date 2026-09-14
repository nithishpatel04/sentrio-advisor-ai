# AWS Lambda Deployment

The existing FastAPI applications remain unchanged for local development. They provide the current local HTTP services and continue to run with Uvicorn and their existing dependencies.

The Lambda versions are separate, standard-library-only entry points. AWS Lambda invokes `lambda_function.lambda_handler` directly, so they do not need FastAPI or Uvicorn. API Gateway will provide the public HTTP interface and translate incoming routes into the Lambda proxy event format.

## Lambda configuration

| Service | Lambda name | Runtime | Architecture | Handler |
| --- | --- | --- | --- | --- |
| Portfolio | `sentrio-portfolio-api` | Python 3.12 | `x86_64` | `lambda_function.lambda_handler` |
| Trading | `sentrio-trading-api` | Python 3.12 | `x86_64` | `lambda_function.lambda_handler` |

## Validate and package

From the project root:

```powershell
python -m py_compile portfolio-api/lambda_function.py
python -m py_compile trading-api/lambda_function.py

powershell -ExecutionPolicy Bypass -File .\scripts\package_portfolio_lambda.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\package_trading_lambda.ps1
```

The portfolio ZIP is `portfolio-api/portfolio-lambda.zip` and contains only:

```text
lambda_function.py
lambda_data/
    portfolio_accounts.csv
    holdings.csv
    performance.csv
```

The trading ZIP is `trading-api/trading-lambda.zip` and contains only:

```text
lambda_function.py
lambda_data/
    transactions.csv
```

Both scripts remove an existing ZIP before creating a new one, and place `lambda_function.py` at the ZIP root.

## Local Lambda tests

```powershell
python scripts/test_portfolio_lambda.py
python scripts/test_trading_lambda.py
```

## Future API Gateway routes

```text
GET /households/{household_id}/portfolio
GET /households/{household_id}/transactions
GET /households/{household_id}/transactions?since=YYYY-MM-DD
```

No AWS CDK, Terraform, SAM, Serverless Framework, Docker configuration, or AWS resources are created by this setup.