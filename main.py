from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from Functions import (
	add_credential,
	create_vault,
	get_credential,
	list_credentials,
	load_vault,
	remove_credential,
	save_vault,
)
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, ListItem, ListView, Static


VAULT_PATH = Path(__file__).with_name("passwords.vault")


class PromptScreen(ModalScreen[Optional[str]]):
	"""Generic modal prompt for passphrases and other short values."""

	def __init__(self, title: str, prompt: str, submit_label: str = "Submit", password: bool = True) -> None:
		super().__init__()
		self.title = title
		self.prompt = prompt
		self.submit_label = submit_label
		self.password = password

	def compose(self) -> ComposeResult:
		yield Container(
			Static(self.title, classes="dialog-title"),
			Static(self.prompt, classes="dialog-prompt"),
			Input(id="prompt-value", password=self.password, placeholder="Enter value"),
			Horizontal(
				Button("Cancel", id="cancel", variant="default"),
				Button(self.submit_label, id="submit", variant="primary"),
				classes="dialog-actions",
			),
			id="dialog-card",
		)

	def on_mount(self) -> None:
		self.query_one(Input).focus()

	@on(Button.Pressed)
	def handle_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "cancel":
			self.dismiss(None)
			return
		self._submit_value()

	@on(Input.Submitted)
	def handle_input_submitted(self, event: Input.Submitted) -> None:
		self._submit_value()

	def _submit_value(self) -> None:
		value = self.query_one(Input).value.strip()
		if not value:
			self.app.notify("A value is required.", severity="warning")
			return
		self.dismiss(value)


class CredentialFormScreen(ModalScreen[Optional[tuple[str, str, str]]]):
	"""Modal form for adding a credential."""

	def compose(self) -> ComposeResult:
		yield Container(
			Static("Add Credential", classes="dialog-title"),
			Static("Create a new entry or update an existing one.", classes="dialog-prompt"),
			Input(id="service", placeholder="Service name"),
			Input(id="username", placeholder="Username"),
			Input(id="password", placeholder="Password", password=True),
			Horizontal(
				Button("Cancel", id="cancel", variant="default"),
				Button("Save", id="save", variant="primary"),
				classes="dialog-actions",
			),
			id="dialog-card",
		)

	def on_mount(self) -> None:
		self.query_one("#service", Input).focus()

	@on(Button.Pressed)
	def handle_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "cancel":
			self.dismiss(None)
			return
		self._submit_values()

	@on(Input.Submitted)
	def handle_input_submitted(self, event: Input.Submitted) -> None:
		self._submit_values()

	def _submit_values(self) -> None:
		service = self.query_one("#service", Input).value.strip()
		username = self.query_one("#username", Input).value.strip()
		password = self.query_one("#password", Input).value
		if not service or not username or not password:
			self.app.notify("Service, username, and password are required.", severity="warning")
			return
		self.dismiss((service, username, password))


class ConfirmScreen(ModalScreen[bool]):
	"""Modal confirmation prompt."""

	def __init__(self, title: str, prompt: str) -> None:
		super().__init__()
		self.title = title
		self.prompt = prompt

	def compose(self) -> ComposeResult:
		yield Container(
			Static(self.title, classes="dialog-title"),
			Static(self.prompt, classes="dialog-prompt"),
			Horizontal(
				Button("Cancel", id="cancel", variant="default"),
				Button("Delete", id="confirm", variant="error"),
				classes="dialog-actions",
			),
			id="dialog-card",
		)

	@on(Button.Pressed)
	def handle_button_pressed(self, event: Button.Pressed) -> None:
		self.dismiss(event.button.id == "confirm")


class PasswordManagerApp(App):
	CSS = """
	Screen {
		background: #08111f;
		color: #e5eef9;
	}

	#root {
		height: 100%;
		padding: 1;
	}

	#panes {
		height: 1fr;
	}

	#left-pane,
	#right-pane {
		background: #101a2d;
		border: round #2b3d5e;
		padding: 1;
	}

	#right-pane {
		margin-left: 1;
	}

	#left-pane {
		width: 42%;
	}

	#right-pane {
		width: 58%;
	}

	#credential-list {
		height: 1fr;
		background: #0c1526;
		border: round #20304a;
	}

	#details {
		height: 1fr;
		background: #0c1526;
		border: round #20304a;
		padding: 1;
	}

	.panel-title {
		color: #7dd3fc;
		text-style: bold;
		margin-bottom: 1;
	}

	.toolbar {
		height: auto;
		margin-top: 1;
	}

	.toolbar Button {
		margin-right: 1;
	}

	#dialog-card {
		width: 70%;
		max-width: 90;
		padding: 1 2;
		background: #101a2d;
		border: round #7dd3fc;
	}

	.dialog-title {
		text-style: bold;
		color: #f8fafc;
		margin-bottom: 1;
	}

	.dialog-prompt {
		color: #cbd5e1;
		margin-bottom: 1;
	}

	.dialog-actions {
		height: auto;
		margin-top: 1;
	}
	"""

	BINDINGS = [
		("a", "add_credential", "Add"),
		("r", "refresh_vault", "Refresh"),
		("p", "reveal_password", "Reveal"),
		("delete", "remove_credential", "Remove"),
		("q", "quit", "Quit"),
	]

	def __init__(self) -> None:
		super().__init__()
		self.selected_service: Optional[str] = None

	def compose(self) -> ComposeResult:
		yield Header(show_clock=True)
		with Container(id="root"):
			with Horizontal(id="panes"):
				with Vertical(id="left-pane"):
					yield Static("Stored Credentials", classes="panel-title")
					yield Static("Click a credential to select it.", id="left-hint")
					yield ListView(id="credential-list")
					with Horizontal(classes="toolbar"):
						yield Button("Add", id="add", variant="success")
						yield Button("Remove", id="remove", variant="error")
						yield Button("Reveal", id="reveal", variant="primary")
						yield Button("Refresh", id="refresh", variant="default")
				with Vertical(id="right-pane"):
					yield Static("Details", classes="panel-title")
					yield Static("Select a credential to see its username.\nUse Reveal to enter the passphrase and show the password.", id="details")
		yield Footer()

	async def on_mount(self) -> None:
		self.refresh_vault_view()

	def _read_vault_data(self) -> dict:
		if not VAULT_PATH.exists():
			return {"entries": []}
		with VAULT_PATH.open("r") as vault_file:
			return json.load(vault_file)

	def _credential_snapshot(self) -> list[dict]:
		vault_data = self._read_vault_data()
		return list_credentials({"key": b"", "data": vault_data})

	def _find_entry(self, service: str) -> Optional[dict]:
		for entry in self._read_vault_data().get("entries", []):
			if entry["service"] == service:
				return entry
		return None

	def _details_text(self, password: Optional[str] = None) -> str:
		if not self.selected_service:
			return "Select a credential from the list."

		entry = self._find_entry(self.selected_service)
		if entry is None:
			return "The selected credential is no longer available."

		lines = [
			f"Service: {entry['service']}",
			f"Username: {entry['username']}",
		]
		if password is None:
			lines.append("Password: [hidden]")
		else:
			lines.append(f"Password: {password}")
		return "\n".join(lines)

	def refresh_vault_view(self) -> None:
		credential_list = self.query_one("#credential-list", ListView)
		credential_list.clear()

		credentials = self._credential_snapshot()
		if not credentials:
			credential_list.append(ListItem(Static("No credentials stored yet."), disabled=True))
			self.selected_service = None
			self.query_one("#details", Static).update("The vault is empty. Add a credential to get started.")
			return

		for credential in credentials:
			credential_list.append(
				ListItem(
					Static(f"{credential['service']}\n[dim]{credential['username']}[/dim]", markup=True),
					name=credential["service"],
				)
			)

		if self.selected_service not in {credential["service"] for credential in credentials}:
			self.selected_service = credentials[0]["service"]

		self.query_one("#details", Static).update(self._details_text())

	@on(ListView.Highlighted)
	def handle_list_highlighted(self, event: ListView.Highlighted) -> None:
		if event.item is None or event.item.disabled:
			return
		self.selected_service = event.item.name
		self.query_one("#details", Static).update(self._details_text())

	@on(ListView.Selected)
	def handle_list_selected(self, event: ListView.Selected) -> None:
		if event.item is None or event.item.disabled:
			return
		self.selected_service = event.item.name
		self.query_one("#details", Static).update(self._details_text())

	@on(Button.Pressed)
	def handle_button_pressed(self, event: Button.Pressed) -> None:
		button_id = event.button.id
		if button_id == "add":
			self.action_add_credential()
		elif button_id == "remove":
			self.action_remove_credential()
		elif button_id == "reveal":
			self.action_reveal_password()
		elif button_id == "refresh":
			self.refresh_vault_view()

	def action_add_credential(self) -> None:
		self.run_worker(self._add_credential_flow(), name="add-credential", group="modal-flow", exclusive=True)

	async def _add_credential_flow(self) -> None:
		form_result = await self.push_screen_wait(CredentialFormScreen())
		if form_result is None:
			return

		service, username, password = form_result
		if not VAULT_PATH.exists():
			vault_passphrase = await self.push_screen_wait(
				PromptScreen(
					"Create Vault",
					"Set a master passphrase for the new vault.",
					submit_label="Create",
				)
			)
			if vault_passphrase is None:
				return

			create_vault(vault_passphrase, str(VAULT_PATH))
			vault = load_vault(vault_passphrase, str(VAULT_PATH))
			add_credential(vault, service, username, password)
			save_vault(vault, str(VAULT_PATH))
			self.selected_service = service
			self.refresh_vault_view()
			self.notify(f"Created vault and added '{service}'.", severity="information")
			return

		passphrase = await self.push_screen_wait(
			PromptScreen(
				"Authorize Add",
				"Enter the vault passphrase to encrypt and save this credential.",
				submit_label="Continue",
			)
		)
		if passphrase is None:
			return

		try:
			vault = load_vault(passphrase, str(VAULT_PATH))
		except Exception:
			self.notify("Incorrect passphrase or unreadable vault.", severity="error")
			return

		add_credential(vault, service, username, password)
		save_vault(vault, str(VAULT_PATH))
		self.selected_service = service
		self.refresh_vault_view()
		self.notify(f"Saved credential for '{service}'.", severity="information")

	def action_remove_credential(self) -> None:
		self.run_worker(self._remove_credential_flow(), name="remove-credential", group="modal-flow", exclusive=True)

	async def _remove_credential_flow(self) -> None:
		if self.selected_service is None:
			self.notify("Select a credential first.", severity="warning")
			return

		confirmed = await self.push_screen_wait(
			ConfirmScreen(
				"Remove Credential",
				f"Delete the credential for '{self.selected_service}'? This cannot be undone.",
			)
		)
		if not confirmed:
			return

		passphrase = await self.push_screen_wait(
			PromptScreen(
				"Confirm Passphrase",
				"Enter the vault passphrase to remove the selected credential.",
				submit_label="Remove",
			)
		)
		if passphrase is None:
			return

		try:
			vault = load_vault(passphrase, str(VAULT_PATH))
		except Exception:
			self.notify("Incorrect passphrase or unreadable vault.", severity="error")
			return

		removed = remove_credential(vault, self.selected_service)
		if not removed:
			self.notify("The selected credential was not found.", severity="warning")
			return

		save_vault(vault, str(VAULT_PATH))
		self.selected_service = None
		self.refresh_vault_view()
		self.notify("Credential removed.", severity="information")

	def action_reveal_password(self) -> None:
		self.run_worker(self._reveal_password_flow(), name="reveal-password", group="modal-flow", exclusive=True)

	async def _reveal_password_flow(self) -> None:
		if self.selected_service is None:
			self.notify("Select a credential first.", severity="warning")
			return

		passphrase = await self.push_screen_wait(
			PromptScreen(
				"Reveal Password",
				f"Enter the vault passphrase to reveal '{self.selected_service}'.",
				submit_label="Reveal",
			)
		)
		if passphrase is None:
			return

		try:
			vault = load_vault(passphrase, str(VAULT_PATH))
			credential = get_credential(vault, self.selected_service)
		except Exception:
			self.notify("Incorrect passphrase or unreadable vault.", severity="error")
			return

		if credential is None:
			self.notify("The selected credential was not found.", severity="warning")
			return

		self.query_one("#details", Static).update(self._details_text(password=credential["password"]))
		self.notify(f"Password revealed for '{self.selected_service}'.", severity="information")

	async def action_refresh_vault(self) -> None:
		self.refresh_vault_view()


if __name__ == "__main__":
	PasswordManagerApp().run()

