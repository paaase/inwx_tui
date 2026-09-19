# INWX DNS TUI Client

Python ane **Textual** no upyog kari banavavama aavelo ek aadhunik, clickable Terminal User Interface (TUI) client, jena thi tame INWX na DNS records ane domains ne sahelta thi manage kari shako chho.

## Features

- **Clickable GUI in Terminal**: Mouse ane keyboard shortcuts banne dwara chalavi shakay chhe.
- **Domain Overview**: Login thaya pachhi account ma rahela badha domains automatic left sidebar ma load thai jaay chhe.
- **DNS Records Management**:
  - DNS records jova (A, AAAA, CNAME, MX, TXT, SRV, CAA, NS, PTR, vagere).
  - Double-click athva `Enter` dabavi ne record edit karvo.
  - Nava records dropdown menu ane custom input sathe add karva.
  - Records delete ane live refresh karva.
- **2FA / TOTP Support**:
  - Jo account ma 2FA chalu hoy to j code mangshe.
  - `.env` ma TOTP secret mukine automatic unlock pan kari shakay chhe.
- **Non-blocking Workers**: Background async workers lidhe API call vakhte UI freeze thatu nathi.

---

## File Structure

```text
inwx_tui/
├── .env                  # INWX API credentials ane config
├── inwx_api.py           # INWX JSON-RPC API logic ane session management
├── tui_modals.py         # Modal popups (Login, 2FA prompt, Record Edit/Add)
├── tui_app.py            # Textual TUI main interface ane event handling
├── main.py               # Application start karvani entrypoint script
└── README.md             # Project documentation
```
## Requirements

Python 3.10+

Linux / macOS / WSL (Windows Terminal)

´´´bash
pip install textual python-dotenv requests pyotp
```
## Usage

```bash
python3 main.py
```
Or, by granting execution permission:

```bash
chmod +x main.py
./main.py
```
