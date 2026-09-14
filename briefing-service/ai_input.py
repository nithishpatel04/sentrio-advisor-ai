from rules import analyze_evidence


def _list(value):
    return value if isinstance(value, list) else []


def _pick(item, *names):
    if not isinstance(item, dict):
        return None
    for name in names:
        if name in item:
            return item[name]
    return None


def _case_item(item):
    fields = {
        "service_request_external_id": ("service_request_external_id", "Service_Request_External_ID"),
        "case_number": ("case_number", "CaseNumber"),
        "subject": ("subject", "Subject"),
        "status": ("status", "Status"),
        "priority": ("priority", "Priority"),
    }
    return {key: _pick(item, *names) for key, names in fields.items() if _pick(item, *names) is not None}


def _opportunity_item(item):
    fields = {
        "opportunity_external_id": ("opportunity_external_id", "Opportunity_External_ID"),
        "name": ("name", "Name"),
        "stage": ("stage", "StageName"),
        "close_date": ("close_date", "CloseDate"),
        "amount": ("amount", "Amount"),
        "type": ("type", "Type"),
    }
    return {key: _pick(item, *names) for key, names in fields.items() if _pick(item, *names) is not None}


def _task_item(item):
    fields = {
        "activity_external_id": ("activity_external_id", "Activity_External_ID"),
        "subject": ("subject", "Subject"),
        "status": ("status", "Status"),
        "activity_date": ("activity_date", "ActivityDate", "Activity_Date"),
    }
    return {key: _pick(item, *names) for key, names in fields.items() if _pick(item, *names) is not None}


def _is_open_case(item):
    return _pick(item, "status", "Status") != "Closed"


def _is_open_task(item):
    return _pick(item, "status", "Status") != "Completed"


def _is_open_opportunity(item):
    return _pick(item, "stage", "StageName") not in {"Closed Won", "Closed Lost"}


def _transaction_item(item):
    allowed = (
        "Transaction_ID", "Transaction_Date", "Transaction_Type", "Symbol",
        "Quantity", "Price", "Total_Amount", "Currency",
    )
    return {key: item[key] for key in allowed if key in item}


def _attention_item(item_type, severity, message, evidence):
    return {
        "type": item_type,
        "severity": severity,
        "message": message,
        "evidence": evidence,
    }


def build_ai_evidence(evidence):
    evidence = evidence if isinstance(evidence, dict) else {}
    crm = evidence.get("crm") if isinstance(evidence.get("crm"), dict) else {}
    analysis = analyze_evidence(evidence)
    risk = analysis.get("risk_review", {})
    portfolio_analysis = analysis.get("portfolio", {})
    trading_analysis = analysis.get("trading", {})
    cases = _list(crm.get("cases"))
    opportunities = _list(crm.get("opportunities"))
    tasks = _list(crm.get("tasks"))
    portfolio = evidence.get("portfolio") if isinstance(evidence.get("portfolio"), dict) else {}
    accounts = _list(portfolio.get("accounts"))
    transaction_container = evidence.get("changes_since_last_meeting")
    transaction_response = transaction_container.get("transactions") if isinstance(transaction_container, dict) else {}
    transactions = transaction_response.get("transactions") if isinstance(transaction_response, dict) else []
    transactions = _list(transactions)

    high_priority_items = analysis.get("service_requests", {}).get("high_priority_items", [])
    overdue_items = analysis.get("tasks", {}).get("overdue_items", [])
    open_cases = [_case_item(item) for item in cases if _is_open_case(item)]
    open_opportunities = [_opportunity_item(item) for item in opportunities if _is_open_opportunity(item)]
    open_tasks = [_task_item(item) for item in tasks if _is_open_task(item)]
    attention_items = []
    if risk.get("status") == "STALE":
        attention_items.append(_attention_item("STALE_RISK_REVIEW", "WARNING", "Risk profile review is stale.", [risk]))
    attention_items.extend(
        _attention_item("HIGH_PRIORITY_SERVICE_REQUEST", "HIGH", "High-priority open service request requires attention.", [item])
        for item in high_priority_items
    )
    attention_items.extend(
        _attention_item("OVERDUE_TASK", "WARNING", "Open task is overdue.", [item])
        for item in overdue_items
    )
    attention_items.extend(
        _attention_item("PORTFOLIO_UNDERPERFORMANCE", "WARNING", "Account is underperforming its benchmark.", [item])
        for item in portfolio_analysis.get("underperforming_accounts", [])
    )
    if portfolio_analysis.get("portfolio_date_conflict"):
        attention_items.append(_attention_item("PORTFOLIO_DATE_CONFLICT", "WARNING", "Portfolio performance dates conflict.", [
            {"portfolio_as_of_dates": portfolio_analysis.get("portfolio_as_of_dates", [])}
        ]))

    portfolio_accounts = []
    for account in accounts:
        item = {}
        for key in ("portfolio_account_id", "account_type", "market_value", "currency"):
            if key in account:
                item[key] = account[key]
        if isinstance(account.get("performance"), dict):
            item["performance"] = account["performance"]
        portfolio_accounts.append(item)

    clients = []
    for client in _list(crm.get("contacts")):
        fields = ("client_external_id", "first_name", "last_name", "title")
        clients.append({key: client[key] for key in fields if key in client})

    return {
        "household": {
            "household_external_id": evidence.get("household_external_id"),
            "household_name": crm.get("household_name"),
            "risk_profile": risk.get("risk_profile"),
            "risk_profile_last_reviewed": risk.get("last_reviewed"),
        },
        "meeting_context": analysis.get("meeting", {}),
        "clients": clients,
        "service_requests": {
            "summary": analysis.get("service_requests", {}),
            "items": open_cases,
        },
        "opportunities": {
            "summary": analysis.get("opportunities", {}),
            "items": open_opportunities,
        },
        "tasks": {
            "summary": analysis.get("tasks", {}),
            "items": open_tasks,
        },
        "portfolio": {
            "account_count": portfolio_analysis.get("account_count", 0),
            "total_market_value": portfolio_analysis.get("total_market_value", "0"),
            "portfolio_data_as_of": portfolio_analysis.get("portfolio_data_as_of"),
            "underperforming_accounts": portfolio_analysis.get("underperforming_accounts", []),
            "accounts": portfolio_accounts,
        },
        "trading": {
            "transactions_since_last_meeting": trading_analysis.get("transactions_since_last_meeting", 0),
            "buy_transactions": trading_analysis.get("buy_transactions", 0),
            "sell_transactions": trading_analysis.get("sell_transactions", 0),
            "total_buy_amount": trading_analysis.get("total_buy_amount", "0"),
            "total_sell_amount": trading_analysis.get("total_sell_amount", "0"),
            "transactions": [_transaction_item(item) for item in transactions],
        },
        "attention_items": attention_items,
        "data_quality_flags": analysis.get("data_quality_flags", []),
        "source_metadata": {
            "crm_source": "Salesforce",
            "portfolio_source": "Portfolio API",
            "trading_source": "Trading API",
        },
    }