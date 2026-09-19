#!/usr/bin/env python3
"""INWX DNS TUI Client
Author:  Pascal Bouquet <pascal@ptbos.de>
License: GNU General Public License v3.0 (GPL-3.0)
Year:    2026
"""

import pyotp
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Button, DataTable, Static, OptionList, Label
from textual.widgets.option_list import Option
from textual import work

import inwx_api as api
from tui_modals import LoginModal, TwoFactorModal, RecordEditModal

class InwxTUIApp(App):
    CSS = """
    Screen {
        layout: vertical;
        background: $surface;
    }
    
    #main_container {
        height: 1fr;
    }

    #sidebar {
        width: 36;
        min-width: 32;
        background: $panel;
        border-right: solid $primary-background;
    }

    #sidebar_title {
        width: 100%;
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $boost;
        color: $accent;
        border-bottom: solid $primary-background;
    }

    #domain_list {
        height: 1fr;
        border: none;
        background: $panel;
    }

    #domain_list:focus {
        border: none;
    }

    #content_area {
        width: 1fr;
        height: 1fr;
    }

    #table_header_info {
        width: 100%;
        height: 3;
        content-align: left middle;
        padding-left: 2;
        background: $boost;
        color: $text;
        text-style: bold;
        border-bottom: solid $primary-background;
    }

    DataTable {
        height: 1fr;
        border: none;
    }

    #action_bar {
        height: 3;
        background: $boost;
        align: left middle;
        padding: 0 1;
        border-top: solid $primary-background;
    }

    .action-btn {
        margin-right: 1;
        height: 1;
        min-width: 16;
        border: none;
    }

    #status_bar {
        height: 1;
        background: $surface-darken-2;
        color: $text-muted;
        padding-left: 1;
    }

    .dialog-box {
        padding: 1 2;
        background: $surface;
        border: thick $primary;
        width: 65;
        height: auto;
        align: center middle;
    }

    .dialog-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        width: 100%;
        text-align: center;
    }

    .field-label {
        color: $text-muted;
        margin-top: 1;
    }

    .type-row {
        height: 3;
        align: left middle;
        margin-bottom: 1;
    }

    #rec_type_select {
        width: 22;
        margin-right: 1;
    }

    #rec_type_input {
        width: 1fr;
        margin-bottom: 0;
    }

    .dialog-buttons {
        height: 3;
        margin-top: 1;
        align: right middle;
    }

    .modal-btn {
        min-width: 14;
        height: 3;
        margin-left: 1;
    }

    Input {
        margin-bottom: 0;
    }
    """

    BINDINGS = [
        ("q", "quit", "Beenden"),
        ("r", "refresh_current", "Aktualisieren"),
        ("a", "add_record", "Neu"),
        ("e", "edit_record", "Bearbeiten"),
        ("d", "delete_record", "Löschen"),
    ]

    def __init__(self):
        super().__init__()
        self.current_domain = ""
        self.records_cache = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal(id="main_container"):
            with Vertical(id="sidebar"):
                yield Label("🌐 Domains", id="sidebar_title")
                yield OptionList(id="domain_list")

            with Vertical(id="content_area"):
                yield Label("Keine Domain gewählt", id="table_header_info")
                yield DataTable(id="record_table", cursor_type="row")

        with Horizontal(id="action_bar"):
            yield Button("➕ Hinzufügen (a)", variant="success", id="btn_add", classes="action-btn")
            yield Button("✏️ Bearbeiten (e)", variant="warning", id="btn_edit", classes="action-btn")
            yield Button("🗑️ Löschen (d)", variant="error", id="btn_delete", classes="action-btn")

        yield Static("Initialisiere...", id="status_bar")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#record_table", DataTable)
        table.add_columns("ID", "Name/Host", "Typ", "TTL", "Inhalt/Content")

        user, pwd, secret = api.get_stored_credentials()
        if user and pwd:
            self.set_status("Melde über .env an...")
            self.async_login(user, pwd, secret)
        else:
            self.prompt_login_modal()

    def set_status(self, text: str) -> None:
        try:
            self.query_one("#status_bar", Static).update(text)
        except Exception:
            pass

    @work(thread=True)
    def async_login(self, user, pwd, secret=None):
        status, msg = api.login(user, pwd)
        
        if status == "SUCCESS":
            self.app.call_from_thread(self.set_status, "✅ Angemeldet. Lade Domains...")
            self.async_load_domains()
            
        elif status == "NEEDS_2FA":
            if secret:
                try:
                    totp = pyotp.TOTP(secret)
                    tan = totp.now()
                    ok, unlock_msg = api.unlock_2fa(tan)
                    if ok:
                        self.app.call_from_thread(self.set_status, "✅ 2FA via Secret bestätigt.")
                        self.async_load_domains()
                        return
                except Exception:
                    pass
            self.app.call_from_thread(self.prompt_2fa_modal)
            
        else:
            self.app.call_from_thread(self.set_status, f"❌ Login fehlgeschlagen: {msg}")
            self.app.call_from_thread(self.prompt_login_modal)

    def prompt_login_modal(self) -> None:
        def on_login_submitted(creds):
            if not creds:
                self.set_status("Abgebrochen.")
                return
            u, p = creds
            _, _, secret = api.get_stored_credentials()
            self.async_login(u, p, secret)

        self.push_screen(LoginModal(), on_login_submitted)

    def prompt_2fa_modal(self) -> None:
        def on_2fa_submitted(tan):
            if not tan:
                self.set_status("2FA abgebrochen.")
                return
            self.async_unlock(tan)

        self.push_screen(TwoFactorModal(), on_2fa_submitted)

    @work(thread=True)
    def async_unlock(self, tan):
        ok, msg = api.unlock_2fa(tan)
        if ok:
            self.app.call_from_thread(self.set_status, "✅ 2FA entsperrt.")
            self.async_load_domains()
        else:
            self.app.call_from_thread(self.set_status, f"❌ 2FA-Fehler: {msg}")
            self.app.call_from_thread(self.prompt_2fa_modal)

    @work(thread=True)
    def async_load_domains(self):
        ok, domains = api.get_domain_list()
        
        def update_ui():
            try:
                d_list = self.query_one("#domain_list", OptionList)
                d_list.clear_options()
                if ok and domains:
                    for d in domains:
                        d_list.add_option(Option(prompt=d, id=d))
                    d_list.highlighted = 0
                    self.set_status(f"✅ {len(domains)} Domains geladen.")
                    self.async_load_dns_records(domains[0])
                elif ok:
                    self.set_status("Keine Domains vorhanden.")
                else:
                    self.set_status(f"❌ Fehler: {domains}")
            except Exception as e:
                self.set_status(f"UI-Fehler: {e}")

        self.app.call_from_thread(update_ui)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected_domain = str(event.option_id)
        self.async_load_dns_records(selected_domain)

    @work(thread=True)
    def async_load_dns_records(self, domain: str):
        self.current_domain = domain
        
        def set_loading():
            try:
                self.query_one("#table_header_info", Label).update(f"DNS-Zone: [b]{domain}[/b]")
                self.set_status(f"Lade Einträge für {domain}...")
            except Exception:
                pass

        self.app.call_from_thread(set_loading)

        ok, data = api.get_dns_records(domain)

        def update_table():
            try:
                table = self.query_one("#record_table", DataTable)
                table.clear()
                self.records_cache.clear()
                
                if ok:
                    for rec in data:
                        r_id = str(rec.get("id"))
                        self.records_cache[r_id] = rec
                        table.add_row(
                            r_id,
                            rec.get("name", "@"),
                            rec.get("type", ""),
                            str(rec.get("ttl", "")),
                            rec.get("content", ""),
                            key=r_id
                        )
                    self.set_status(f"✅ {len(data)} Records für {domain} geladen.")
                else:
                    self.set_status(f"❌ Fehler: {data}")
            except Exception as e:
                self.set_status(f"Tabelle konnte nicht aktualisiert werden: {e}")

        self.app.call_from_thread(update_table)

    def get_selected_record(self) -> dict | None:
        table = self.query_one("#record_table", DataTable)
        if table.row_count == 0 or table.cursor_coordinate is None:
            return None
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        return self.records_cache.get(cell_key.row_key.value)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_edit_record()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn_add":
            self.action_add_record()
        elif btn_id == "btn_edit":
            self.action_edit_record()
        elif btn_id == "btn_delete":
            self.action_delete_record()

    def action_refresh_current(self) -> None:
        if self.current_domain:
            self.async_load_dns_records(self.current_domain)
        else:
            self.async_load_domains()

    # --- Asynchrone Worker-Methoden ---

    @work(thread=True)
    def async_add_record(self, domain: str, data: dict) -> None:
        ok, msg = api.add_dns_record(
            domain, data["name"], data["type"], data["content"], data["ttl"]
        )
        self.app.call_from_thread(
            self.set_status, "✅ Record hinzugefügt." if ok else f"❌ Fehler: {msg}"
        )
        if ok:
            self.async_load_dns_records(domain)

    @work(thread=True)
    def async_edit_record(self, record_id: str, data: dict) -> None:
        ok, msg = api.update_dns_record(record_id, data["content"], data["ttl"])
        self.app.call_from_thread(
            self.set_status, f"✅ Record {record_id} aktualisiert." if ok else f"❌ Fehler: {msg}"
        )
        if ok:
            self.async_load_dns_records(self.current_domain)

    @work(thread=True)
    def async_delete_record(self, record_id: str) -> None:
        ok, msg = api.delete_dns_record(record_id)
        self.app.call_from_thread(
            self.set_status, f"✅ Record {record_id} gelöscht." if ok else f"❌ Fehler: {msg}"
        )
        if ok:
            self.async_load_dns_records(self.current_domain)

    # --- UI Aktionen ---

    def action_add_record(self) -> None:
        if not self.current_domain:
            self.set_status("Erst Domain links auswählen.")
            return

        def handle_add(data):
            if data:
                self.async_add_record(self.current_domain, data)

        self.push_screen(RecordEditModal(default_domain=self.current_domain), handle_add)

    def action_edit_record(self) -> None:
        rec = self.get_selected_record()
        if not rec:
            self.set_status("Kein Record ausgewählt.")
            return

        def handle_edit(data):
            if data:
                self.async_edit_record(rec["id"], data)

        self.push_screen(RecordEditModal(record=rec), handle_edit)

    def action_delete_record(self) -> None:
        rec = self.get_selected_record()
        if not rec:
            self.set_status("Kein Record ausgewählt.")
            return

        self.async_delete_record(rec["id"])

    def action_quit(self) -> None:
        api.logout()
        self.exit()
