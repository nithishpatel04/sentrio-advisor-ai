import importlib.util
import json
from pathlib import Path


project_root = Path(__file__).resolve().parents[1]
module_path = project_root / "portfolio-api" / "lambda_function.py"
spec = importlib.util.spec_from_file_location("portfolio_lambda", module_path)
portfolio_lambda = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portfolio_lambda)

event = {"pathParameters": {"household_id": "HH-0001"}}
response = portfolio_lambda.lambda_handler(event, None)

print("statusCode:", response["statusCode"])
print(json.dumps(json.loads(response["body"]), indent=2))