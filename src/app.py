from __future__ import annotations

from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Label, Log, Static

from core import ClipRequest, extract_clip


class YouTubeClipApp(App[None]):
    TITLE = "YouTube Clip Studio"
    SUB_TITLE = "recorte vídeo e áudio sem sair do terminal"
    THEME_SEQUENCE = ("tokyo-night", "catppuccin-mocha", "nord", "textual-light")
    CSS = """
    Screen { background: $background; color: $text; }
    VerticalScroll { align-horizontal: center; }
    #shell { width: 86; max-width: 95%; height: auto; margin: 2 0; padding: 1 3;
             border: round $primary; background: $surface; }
    #brand { text-align: center; color: $primary; text-style: bold; margin-bottom: 1; }
    .field-label { margin-top: 1; color: $text-muted; }
    Input { border: tall $primary-muted; background: $background; }
    Input:focus { border: tall $accent; }
    #times { height: auto; }
    #times > Container { width: 1fr; height: auto; }
    #times > Container:first-child { margin-right: 2; }
    #actions { height: auto; margin-top: 2; align-horizontal: center; }
    Button { margin: 0 1; }
    #extract { text-style: bold; }
    #status { margin: 1 0; text-align: center; color: $text; text-style: bold; }
    #log { height: 13; border: round $primary-muted; background: $background; }
    """
    BINDINGS = [
        ("ctrl+q", "quit", "Sair"),
        ("ctrl+l", "clear_log", "Limpar log"),
        ("ctrl+t", "switch_theme", "Trocar tema"),
    ]

    def on_mount(self) -> None:
        self.theme = self.THEME_SEQUENCE[0]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            with Container(id="shell"):
                yield Static("▶  YOUTUBE CLIP STUDIO", id="brand")
                yield Label("URL do YouTube", classes="field-label")
                yield Input(placeholder="https://www.youtube.com/watch?v=...", id="url")
                with Horizontal(id="times"):
                    with Container():
                        yield Label("Início", classes="field-label")
                        yield Input(placeholder="1:00", id="start")
                    with Container():
                        yield Label("Fim", classes="field-label")
                        yield Input(placeholder="1:30", id="end")
                with Horizontal(id="actions"):
                    yield Button("Extrair vídeo + áudio", id="extract", variant="primary")
                    yield Button("Limpar", id="clear")
                yield Static("Pronto para criar seu trecho.", id="status")
                yield Log(id="log", highlight=True, auto_scroll=True)
        yield Footer()

    def action_clear_log(self) -> None:
        self.query_one("#log", Log).clear()

    def action_switch_theme(self) -> None:
        current = self.THEME_SEQUENCE.index(self.theme)
        self.theme = self.THEME_SEQUENCE[(current + 1) % len(self.THEME_SEQUENCE)]
        self.notify(f"Tema: {self.theme}")

    @on(Button.Pressed, "#clear")
    def clear_form(self) -> None:
        for selector in ("#url", "#start", "#end"):
            self.query_one(selector, Input).value = ""
        self.action_clear_log()
        self.query_one("#status", Static).update("Pronto para criar seu trecho.")
        self.query_one("#url", Input).focus()

    @on(Button.Pressed, "#extract")
    def begin_extract(self) -> None:
        try:
            request = ClipRequest.create(
                self.query_one("#url", Input).value,
                self.query_one("#start", Input).value,
                self.query_one("#end", Input).value,
                Path.cwd() / "downloads",
            )
        except ValueError as error:
            self.notify(str(error), severity="error", title="Dados inválidos")
            return
        self.run_extract(request)

    @work(thread=True, exclusive=True)
    def run_extract(self, request: ClipRequest) -> None:
        button = self.query_one("#extract", Button)
        status = self.query_one("#status", Static)
        log_widget = self.query_one("#log", Log)
        self.call_from_thread(setattr, button, "disabled", True)
        self.call_from_thread(status.update, "Extraindo… isso pode levar alguns minutos.")

        def write_log(message: str) -> None:
            self.call_from_thread(log_widget.write_line, message)

        try:
            extract_clip(request, write_log)
        except Exception as error:
            self.call_from_thread(status.update, "A extração falhou.")
            self.call_from_thread(self.notify, str(error), severity="error", title="Erro")
        else:
            self.call_from_thread(status.update, "Concluído! Arquivos salvos em ./downloads")
            self.call_from_thread(
                self.notify, "Vídeo MP4 e áudio MP3 criados.", title="Tudo pronto!"
            )
        finally:
            self.call_from_thread(setattr, button, "disabled", False)


def main() -> None:
    YouTubeClipApp().run()


if __name__ == "__main__":
    main()
