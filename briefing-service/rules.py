from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation


RISK_REVIEW_THRESHOLD_DAYS = 365
CLOSED_CASE_STATUS = "Closed"
CLOSED_TASK_STATUS = "Completed"
CLOSED_OPPORTUNITY_STAGES = {"Closed Won", "Closed Lost"}


def _as_list(value):
    return value if isinstance(value, list) else []


def _text(value):
    return value.strip() if isinstance(value, str) else value


def parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10]) if len(value) >= 10 else None
    except ValueError:
        return None


def parse_datetime(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _money(value):
    amount = _decimal(value)
    return format(amount, "f") if amount is not None else "0"


def _pick(item, *names):
    for name in names:
        if name in item:
            return item[name]
    return None


def _item_with_fields(item, fields):
    return {output: _pick(item, *names) for output, names in fields.items()
            if any(name in item for name in names)}


def analyze_service_requests(cases):
    cases = _as_list(cases)
    open_cases = [case for case in cases if _text(_pick(case, "status", "Status")) != CLOSED_CASE_STATUS]
    high_priority = [
        case for case in open_cases
        if _text(_pick(case, "priority", "Priority")).lower() == "high"
    ]
    fields = {
        "service_request_external_id": ("service_request_external_id", "Service_Request_External_ID"),
        "case_number": ("case_number", "CaseNumber"),
        "subject": ("subject", "Subject"),
        "status": ("status", "Status"),
        "priority": ("priority", "Priority"),
    }
    return {
        "total": len(cases),
        "open": len(open_cases),
        "high_priority_open": len(high_priority),
        "high_priority_items": [_item_with_fields(case, fields) for case in high_priority],
    }


def analyze_tasks(tasks, today=None):
    tasks = _as_list(tasks)
    today = today or datetime.now(timezone.utc).date()
    open_tasks = [task for task in tasks if _text(_pick(task, "status", "Status")) != CLOSED_TASK_STATUS]
    overdue = [
        task for task in open_tasks
        if (task_date := parse_date(_pick(task, "activity_date", "ActivityDate", "Activity_Date")))
        is not None and task_date < today
    ]
    fields = {
        "activity_external_id": ("activity_external_id", "Activity_External_ID"),
        "subject": ("subject", "Subject"),
        "status": ("status", "Status"),
        "activity_date": ("activity_date", "ActivityDate", "Activity_Date"),
    }
    return {
        "total": len(tasks),
        "open": len(open_tasks),
        "overdue": len(overdue),
        "overdue_items": [_item_with_fields(task, fields) for task in overdue],
    }


def analyze_opportunities(opportunities):
    opportunities = _as_list(opportunities)
    open_items = [
        opportunity for opportunity in opportunities
        if _text(_pick(opportunity, "stage", "StageName")) not in CLOSED_OPPORTUNITY_STAGES
    ]
    fields = {
        "opportunity_external_id": ("opportunity_external_id", "Opportunity_External_ID"),
        "name": ("name", "Name"),
        "stage": ("stage", "StageName"),
        "close_date": ("close_date", "CloseDate"),
        "amount": ("amount", "Amount"),
        "type": ("type", "Type"),
    }
    return {
        "total": len(opportunities),
        "open": len(open_items),
        "open_items": [_item_with_fields(item, fields) for item in open_items],
    }


def analyze_risk_review(risk_profile, risk_profile_last_reviewed, today=None):
    today = today or datetime.now(timezone.utc).date()
    reviewed = parse_date(risk_profile_last_reviewed)
    status = "UNKNOWN"
    if reviewed is not None:
        status = "STALE" if (today - reviewed).days > RISK_REVIEW_THRESHOLD_DAYS else "CURRENT"
    return {
        "risk_profile": risk_profile,
        "last_reviewed": risk_profile_last_reviewed,
        "status": status,
        "threshold_days": RISK_REVIEW_THRESHOLD_DAYS,
    }


def analyze_portfolio(accounts):
    accounts = _as_list(accounts)
    performance_dates = set()
    underperforming = []
    total_market_value = Decimal("0")
    for account in accounts:
        amount = _decimal(_pick(account, "market_value", "Market_Value"))
        if amount is not None:
            total_market_value += amount
        performance = account.get("performance")
        performance = performance if isinstance(performance, dict) else {}
        as_of = parse_date(_pick(performance, "As_Of_Date", "as_of_date"))
        if as_of is not None:
            performance_dates.add(as_of.isoformat())
        relative = _decimal(_pick(performance, "Relative_Performance", "relative_performance"))
        if relative is not None and relative < 0:
            account_id = _pick(account, "portfolio_account_id", "Portfolio_Account_ID")
            underperforming.append({
                "portfolio_account_id": account_id,
                "relative_performance": format(relative, "f"),
            })
    sorted_dates = sorted(performance_dates)
    return {
        "account_count": len(accounts),
        "total_market_value": format(total_market_value, "f"),
        "portfolio_data_as_of": sorted_dates[-1] if sorted_dates else None,
        "portfolio_as_of_dates": sorted_dates,
        "portfolio_date_conflict": len(sorted_dates) > 1,
        "underperforming_accounts": underperforming,
    }


def analyze_trading(transactions):
    transactions = _as_list(transactions)
    buys = [item for item in transactions if _text(_pick(item, "transaction_type", "Transaction_Type")) == "BUY"]
    sells = [item for item in transactions if _text(_pick(item, "transaction_type", "Transaction_Type")) == "SELL"]
    transaction_ids = [
        _pick(item, "transaction_id", "Transaction_ID")
        for item in transactions
        if _pick(item, "transaction_id", "Transaction_ID") is not None
    ]
    return {
        "transactions_since_last_meeting": len(transactions),
        "buy_transactions": len(buys),
        "sell_transactions": len(sells),
        "total_buy_amount": _money(sum((_decimal(_pick(item, "total_amount", "Total_Amount")) or Decimal("0") for item in buys), Decimal("0"))),
        "total_sell_amount": _money(sum((_decimal(_pick(item, "total_amount", "Total_Amount")) or Decimal("0") for item in sells), Decimal("0"))),
        "transaction_ids": transaction_ids,
    }


def _flag(code, severity, message, source):
    return {"code": code, "severity": severity, "message": message, "source": source}


def analyze_evidence(evidence):
    evidence = evidence if isinstance(evidence, dict) else {}
    crm = evidence.get("crm") if isinstance(evidence.get("crm"), dict) else {}
    reference_dates = evidence.get("reference_dates") if isinstance(evidence.get("reference_dates"), dict) else {}
    last_meeting_date = _pick(reference_dates, "last_meeting_date")
    meeting_date = parse_date(last_meeting_date)
    days_since = (datetime.now(timezone.utc).date() - meeting_date).days if meeting_date else None

    risk_profile = _pick(evidence, "risk_profile", "Risk_Profile__c")
    risk_reviewed = _pick(evidence, "risk_profile_last_reviewed", "Risk_Profile_Last_Reviewed__c")
    if risk_profile is None:
        risk_profile = _pick(crm, "risk_profile", "Risk_Profile__c")
    if risk_reviewed is None:
        risk_reviewed = _pick(crm, "risk_profile_last_reviewed", "Risk_Profile_Last_Reviewed__c")
    risk = analyze_risk_review(risk_profile, risk_reviewed)

    accounts = _as_list((evidence.get("portfolio") or {}).get("accounts")) if isinstance(evidence.get("portfolio"), dict) else []
    transactions_container = evidence.get("changes_since_last_meeting")
    trading_response = (transactions_container or {}).get("transactions") if isinstance(transactions_container, dict) else {}
    transactions = trading_response.get("transactions") if isinstance(trading_response, dict) else trading_response
    transactions = transactions if isinstance(transactions, list) else []
    portfolio = analyze_portfolio(accounts)
    trading = analyze_trading(transactions)
    flags = []
    if meeting_date is None:
        flags.append(_flag("NO_PREVIOUS_MEETING", "INFO", "No valid previous meeting date is available.", "reference_dates"))
    if risk_reviewed is None or parse_date(risk_reviewed) is None:
        flags.append(_flag("MISSING_RISK_REVIEW_DATE", "WARNING", "Risk profile review date is missing or invalid.", "crm"))
    if risk["status"] == "STALE":
        flags.append(_flag("STALE_RISK_REVIEW", "WARNING", "Risk profile review is older than 365 days.", "crm"))
    if not accounts:
        flags.append(_flag("NO_PORTFOLIO_ACCOUNTS", "WARNING", "No portfolio accounts are available.", "portfolio"))
    if accounts and any(not isinstance(account.get("performance"), dict) or not account.get("performance") for account in accounts):
        flags.append(_flag("MISSING_PORTFOLIO_PERFORMANCE", "WARNING", "One or more portfolio accounts lack performance data.", "portfolio"))
    if portfolio["portfolio_date_conflict"]:
        flags.append(_flag("PORTFOLIO_DATE_CONFLICT", "WARNING", "Portfolio accounts have different performance dates.", "portfolio"))
    if not transactions:
        flags.append(_flag("NO_TRANSACTIONS_SINCE_LAST_MEETING", "INFO", "No transactions are available since the last meeting.", "trading"))

    return {
        "meeting": {"last_meeting_date": last_meeting_date, "days_since_last_meeting": days_since},
        "service_requests": analyze_service_requests(crm.get("cases")),
        "tasks": analyze_tasks(crm.get("tasks")),
        "opportunities": analyze_opportunities(crm.get("opportunities")),
        "risk_review": risk,
        "portfolio": portfolio,
        "trading": trading,
        "data_quality_flags": flags,
    }