# INWX DNS TUI Client

A modern, interactive Terminal User Interface (TUI) client built with Python and **Textual** to manage INWX domains and DNS records directly from your terminal.

## Features

- **Interactive Terminal UI**: Full mouse support and intuitive keyboard navigation.
- **Automatic Domain Discovery**: Automatically retrieves and lists all configured domains in a dedicated sidebar upon login.
- **Complete DNS Record Management**:
  - View DNS records (A, AAAA, CNAME, MX, TXT, SRV, CAA, NS, PTR, etc.).
  - Quick inline editing via mouse double-click or `Enter`.
  - Add new records using a dropdown preset or custom type input.
  - Delete records with confirmation.
- **Conditional 2FA / TOTP Support**:
  - Only prompts for a 2FA code if two-factor authentication is active on the account.
  - Supports automatic 2FA unlocking via a TOTP secret stored in `.env`.
- **Responsive Non-blocking UI**: API calls run on background worker threads to keep the interface smooth and responsive.

---

## File Structure

```text
inwx_tui/
├── .env                  # INWX API credentials and configuration (ignored by git)
├── inwx_api.py           # INWX JSON-RPC API logic, session handling, and 2FA
├── tui_modals.py         # Modal dialog screens (Login, 2FA prompt, Record Edit/Add)
├── tui_app.py            # Main Textual TUI layout, styles, and event handling
├── main.py               # Application entrypoint
└── README.md             # Project documentation
```

## Requirements

Python 3.10+

Linux / macOS / WSL (Windows Terminal)

```bash
pip install textual python-dotenv requests pyotp
```

## Configuration

You can provide your credentials in a .env file in the project root to bypass manual login:

```bash
# INWX Account Credentials
INWX_USER=your_username
INWX_PASS=your_password

# Optional: TOTP Secret Key (Base32) for automatic 2FA unlock
# If left empty, an interactive 6-digit TAN modal will appear when required.
INWX_2FA_SECRET=
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
