#!/usr/bin/env python3
"""INWX DNS TUI Client
Author:  Pascal Bouquet <pascal@ptbos.de>
License: GNU General Public License v3.0 (GPL-3.0)
Year:    2026
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_ENDPOINT = "https://api.domrobot.com/jsonrpc/"
SESSION_ID = None

def get_stored_credentials():
    user = os.getenv("INWX_USER", "").strip()
    pwd = os.getenv("INWX_PASS", "").strip()
    secret = os.getenv("INWX_2FA_SECRET", "").strip()
    
    placeholders = {"", "username", "dein_nutzername", "dein_benutzername", "example_user", "password", "passwort"}
    if user.lower() in placeholders or pwd.lower() in placeholders:
        return None, None, secret
    return user, pwd, secret

def api_call(method, params=None):
    global SESSION_ID
    if params is None:
        params = {}

    headers = {"Content-Type": "application/json"}
    if SESSION_ID:
        headers["Cookie"] = f"domrobot={SESSION_ID}"

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }

    try:
        response = requests.post(API_ENDPOINT, headers=headers, data=json.dumps(payload), timeout=12)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"code": -1, "msg": f"Netzwerkfehler: {e}"}

def login(user, password):
    global SESSION_ID
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "account.login",
        "params": {"user": user, "pass": password},
        "id": 1
    }

    try:
        response = requests.post(API_ENDPOINT, headers=headers, data=json.dumps(payload), timeout=12)
        response.raise_for_status()
        result = response.json()

        if result.get("code") == 1000:
            if "domrobot" in response.cookies:
                SESSION_ID = response.cookies["domrobot"]
            else:
                return "ERROR", "Kein Session-Cookie von INWX erhalten."

            res_data = result.get("resData", {})
            tfa_val = res_data.get("tfa")

            # INWX liefert bei inaktivem 2FA None, 0, "0" oder "NONE"
            if tfa_val in (0, "0", None, False, "", "NONE", "none"):
                return "SUCCESS", "Login erfolgreich."

            return "NEEDS_2FA", f"2FA erforderlich ({tfa_val})."
            
        return "ERROR", result.get("msg", "Zugangsdaten ungültig.")
    except requests.exceptions.RequestException as e:
        return "ERROR", str(e)

def unlock_2fa(tan_code):
    res = api_call("account.unlock", {"tan": str(tan_code).strip()})
    if res.get("code") == 1000:
        return True, "2FA erfolgreich entsperrt."
    return False, res.get("msg", "2FA-Code ungültig.")

def logout():
    global SESSION_ID
    if SESSION_ID:
        api_call("account.logout")
        SESSION_ID = None

def get_domain_list():
    res = api_call("nameserver.list")
    if res.get("code") == 1000:
        domains_data = res.get("resData", {}).get("domains", [])
        return True, [d.get("domain") for d in domains_data if "domain" in d]
    return False, res.get("msg", "Fehler beim Abrufen der Domainliste.")

def get_dns_records(domain):
    res = api_call("nameserver.info", {"domain": domain})
    if res.get("code") == 1000:
        return True, res.get("resData", {}).get("record", [])
    return False, res.get("msg", "Fehler beim Laden der Records.")

def add_dns_record(domain, name, record_type, content, ttl):
    params = {
        "domain": domain,
        "name": name,
        "type": record_type,
        "content": content,
        "ttl": int(ttl)
    }
    res = api_call("nameserver.createRecord", params)
    return res.get("code") == 1000, res.get("msg", "OK")

def update_dns_record(record_id, content=None, ttl=None):
    params = {"id": int(record_id)}
    if content:
        params["content"] = content
    if ttl:
        params["ttl"] = int(ttl)
    res = api_call("nameserver.updateRecord", params)
    return res.get("code") == 1000, res.get("msg", "OK")

def delete_dns_record(record_id):
    res = api_call("nameserver.deleteRecord", {"id": int(record_id)})
    return res.get("code") == 1000, res.get("msg", "OK")
