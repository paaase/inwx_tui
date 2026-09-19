#!/usr/bin/env python3
"""INWX DNS TUI Client
Author:  Pascal Bouquet <pascal@ptbos.de>
License: GNU General Public License v3.0 (GPL-3.0)
Year:    2026
"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Input, Button, Select
from textual.screen import ModalScreen

RECORD_TYPES = [
    ("A", "A"),
    ("AAAA", "AAAA"),
    ("CNAME", "CNAME"),
    ("MX", "MX"),
    ("TXT", "TXT"),
    ("SRV", "SRV"),
    ("CAA", "CAA"),
    ("NS", "NS"),
    ("PTR", "PTR"),
    ("TLSA", "TLSA"),
]

class LoginModal(ModalScreen[tuple[str, str] | None]):
    """Login-Maske bei fehlender oder fehlerhafter .env."""
    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog-box"):
            yield Label("🔐 INWX Login", classes="dialog-title")
            yield Input(placeholder="Benutzername", id="user_input")
            yield Input(placeholder="Passwort", password=True, id="pass_input")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Einloggen", variant="primary", id="btn_submit", classes="modal-btn")
                yield Button("Abbrechen", variant="error", id="btn_cancel", classes="modal-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_submit":
            user = self.query_one("#user_input", Input).value.strip()
            pwd = self.query_one("#pass_input", Input).value.strip()
            self.dismiss((user, pwd))
        else:
            self.dismiss(None)


class TwoFactorModal(ModalScreen[str | None]):
    """Fragt den 6-stelligen 2FA / TOTP-Code ab."""
    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog-box"):
            yield Label("🛡️ 2FA-Bestätigung", classes="dialog-title")
            yield Label("6-stelligen TAN-Code eingeben:")
            yield Input(placeholder="z.B. 123456", id="tan_input", max_length=6)
            with Horizontal(classes="dialog-buttons"):
                yield Button("Bestätigen", variant="primary", id="btn_submit_tan", classes="modal-btn")
                yield Button("Abbrechen", variant="error", id="btn_cancel", classes="modal-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_submit_tan":
            tan = self.query_one("#tan_input", Input).value.strip()
            self.dismiss(tan)
        else:
            self.dismiss(None)


class RecordEditModal(ModalScreen[dict | None]):
    """Dialog zum Anlegen und Bearbeiten von DNS-Records."""
    def __init__(self, record: dict | None = None, default_domain: str = ""):
        super().__init__()
        self.record = record
        self.default_domain = default_domain

    def compose(self) -> ComposeResult:
        is_edit = self.record is not None
        title = f"Record ID {self.record['id']} bearbeiten" if is_edit else f"Neuer Record für {self.default_domain}"

        with Vertical(classes="dialog-box"):
            yield Label(title, classes="dialog-title")
            
            if not is_edit:
                yield Label("Name / Host (@ oder z.B. mail):", classes="field-label")
                yield Input(placeholder="@", value="@", id="rec_name")
                
                yield Label("Record-Typ (Auswählen oder eintippen):", classes="field-label")
                with Horizontal(classes="type-row"):
                    yield Select(
                        RECORD_TYPES, 
                        value="A", 
                        prompt="Typ wählen", 
                        id="rec_type_select",
                        allow_blank=False
                    )
                    yield Input(value="A", placeholder="Typ", id="rec_type_input")

            yield Label("Inhalt / Ziel:", classes="field-label")
            val_content = str(self.record.get("content", "")) if is_edit else ""
            yield Input(placeholder="z.B. IP, mx01.domain.tld, Text", value=val_content, id="rec_content")

            yield Label("TTL (Sekunden):", classes="field-label")
            val_ttl = str(self.record.get("ttl", "3600")) if is_edit else "3600"
            yield Input(placeholder="3600", value=val_ttl, id="rec_ttl")

            with Horizontal(classes="dialog-buttons"):
                yield Button("Speichern", variant="success", id="btn_save", classes="modal-btn")
                yield Button("Abbrechen", variant="error", id="btn_cancel", classes="modal-btn")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Überträgt die Dropdown-Auswahl direkt in das Text-Eingabefeld."""
        if event.select.id == "rec_type_select" and event.value != Select.BLANK:
            type_input = self.query_one("#rec_type_input", Input)
            type_input.value = str(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_save":
            content = self.query_one("#rec_content", Input).value.strip()
            ttl = self.query_one("#rec_ttl", Input).value.strip() or "3600"

            if self.record:
                data = {"content": content, "ttl": ttl}
            else:
                name = self.query_one("#rec_name", Input).value.strip()
                rec_type = self.query_one("#rec_type_input", Input).value.strip().upper()
                data = {"name": name, "type": rec_type, "content": content, "ttl": ttl}
            self.dismiss(data)
        else:
            self.dismiss(None)
