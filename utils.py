def extract_app_sid(data):
    return (
        data.get("auth[application_token]")
        or data.get("APP_SID")
        or data.get("app_sid")
        or data.get("auth[APP_SID]")
        or data.get("AUTH_APP_SID")
    )

def extract_author_id(data):
    return (
        data.get("data[PARAMS][AUTHOR_ID]")
        or data.get("data[PARAMS][FROM_USER_ID]")
        or data.get("data[MESSAGE][AUTHOR_ID]")
        or data.get("data[MESSAGE][FROM_USER_ID]")
    )

def extract_domain(data):
    return data.get("auth[domain]") or data.get("DOMAIN")

def get_auth_from_request(data):
    return {
        "access_token": data.get("auth[access_token]") or data.get("AUTH_ID"),
        "domain": extract_domain(data),
        "application_token": extract_app_sid(data),
        "client_endpoint": data.get("auth[client_endpoint]"),
    }
