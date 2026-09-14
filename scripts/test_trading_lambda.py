import importlib.util
import json
from pathlib import Path


project_root = Path(__file__).resolve().parents[1]
module_path = project_root / "trading-api" / "lambda_function.py"
spec = importlib.util.spec_from_file_location("trading_lambda", module_path)
trading_lambda = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trading_lambda)

events = [
    {
        "pathParameters": {"household_id": "HH-0001"},
        "queryStringParameters": None,
    },
    {
        "pathParameters": {"household_id": "HH-0001"},
        "queryStringParameters": {"since": "2026-06-15"},
    },
]

for index, event in enumerate(events, start=1):
    response = trading_lambda.lambda_handler(event, None)
    print(f"Case {index} statusCode:", response["statusCode"])
    print(json.dumps(json.loads(response["body"]), indent=2))