"""A simple application using examples/boilerplate.py as a basis."""

from __future__ import annotations

import sys
import threading

from argparse import ArgumentParser, Namespace

import pytermgui as ptg
import time


PALETTE_LIGHT = "#FCBA03"
PALETTE_MID = "#8C6701"
PALETTE_DARK = "#4D4940"
PALETTE_DARKER = "#242321"

log = [
    {"role": "user", "message": "What is up?"},
    {"role": "agent", "message": "Not too much"}
]


def _create_aliases() -> None:
    """Creates all the TIM aliases used by the application.

    Aliases should generally follow the following format:

        namespace.item

    For example, the title color of an app named "myapp" could be something like:

        myapp.title
    """

    ptg.tim.alias("app.text", "#cfc7b0")

    ptg.tim.alias("app.header", f"bold @{PALETTE_MID} #d9d2bd")
    ptg.tim.alias("app.header.fill", f"@{PALETTE_LIGHT}")

    ptg.tim.alias("app.title", f"bold {PALETTE_LIGHT}")
    ptg.tim.alias("app.button.label", f"bold @{PALETTE_DARK} app.text")
    ptg.tim.alias("app.button.highlight", "inverse app.button.label")

    ptg.tim.alias("app.footer", f"@{PALETTE_DARKER}")


def _configure_widgets() -> None:
    """Defines all the global widget configurations.

    Some example lines you could use here:

        ptg.boxes.DOUBLE.set_chars_of(ptg.Window)
        ptg.Splitter.set_char("separator", " ")
        ptg.Button.styles.label = "myapp.button.label"
        ptg.Container.styles.border__corner = "myapp.border"
    """

    ptg.boxes.DOUBLE.set_chars_of(ptg.Window)
    ptg.boxes.ROUNDED.set_chars_of(ptg.Container)

    ptg.Button.styles.label = "app.button.label"
    ptg.Button.styles.highlight = "app.button.highlight"

    ptg.Slider.styles.filled__cursor = PALETTE_MID
    ptg.Slider.styles.filled_selected = PALETTE_LIGHT

    ptg.Label.styles.value = "app.text"

    ptg.Window.styles.border__corner = "#C2B280"
    ptg.Container.styles.border__corner = PALETTE_DARK

    ptg.Splitter.set_char("separator", "")


def _define_layout() -> ptg.Layout:
    """Defines the application layout."""

    layout = ptg.Layout()

    # A header slot with a height of 1
    layout.add_slot("Header", height=1)
    layout.add_break()

    # A slot for the scrolling log area, occupying 80% of the width
    layout.add_slot("logarea", width=0.8)
    
    # A slot for the HUD, occupying 20% of the width
    layout.add_slot("hud", width=0.2)

    layout.add_break()

    # A footer with a static height of 1
    layout.add_slot("Footer", height=1)

    return layout


def _confirm_quit(manager: ptg.WindowManager) -> None:
    """Creates an "Are you sure you want to quit" modal window"""

    modal = ptg.Window(
        "[app.title]Are you sure you want to quit?",
        "",
        ptg.Container(
            ptg.Splitter(
                ptg.Button("Yes", lambda *_: manager.stop()),
                ptg.Button("No", lambda *_: modal.close()),
            ),
        ),
    ).center()

    modal.select(0)
    manager.add(modal)


def main() -> None:
    """Runs the application."""

    _create_aliases()
    _configure_widgets()

    with ptg.WindowManager() as manager:
        manager.layout = _define_layout()

        header = ptg.Window(
            "[app.header] HOWEE ",
            box="EMPTY",
            is_persistant=True,
        )

        header.styles.fill = "app.header.fill"
        manager.add(header)

        footer = ptg.Window(
            ptg.Button("Quit", lambda *_: _confirm_quit(manager)),
            box="EMPTY",
        )
        footer.styles.fill = "app.footer"
        manager.add(footer, assign="footer")

        log_window = None
        def macro_log(fmt: str) -> str:
            formatted_log = ""
            for entry in log:
                role = f"[bold]{entry['role'].capitalize()}[/]"
                message = entry["message"]
                formatted_log += f"{role}: {message}\n"
                if log_window:
                    log_window.scroll(2)
            return ptg.tim.parse(formatted_log.rstrip())

        ptg.tim.define("!log", macro_log)

        def submit(input_field, log_window):
            global log
            message = input_field.value
            log.append({"role": "user", "message": message})

            input_field._lines = [""]
            input_field.cursor.col = 0


        input_field = ptg.InputField("", prompt="Prompt: ")

        log_content_container = ptg.Container(
            ptg.Label("[bold][/]\n\n[!log]%c", parent_align=0),
            height=20  # Or whatever height you want
        )

        log_window = ptg.Window(
                    ptg.Label("[bold][/][!log]%c", parent_align=0),
                    height=12,
                    overflow=ptg.Overflow.SCROLL,
                    vertical_align=ptg.VerticalAlignment.BOTTOM,
                )

        # Scrolling log area
        log_area = ptg.Window(
                log_window,
                 ptg.Container(
                    ptg.Splitter(
                        input_field,
                        ptg.Button("Submit", lambda *_: submit(input_field, log_window))
                    ),
                    horizontal_align=ptg.HorizontalAlignment.CENTER
                ),
                title="Log",
                vertical_align=ptg.VerticalAlignment.TOP,
                horizontal_align=ptg.HorizontalAlignment.LEFT
        )
        log_area.focused = input_field

        input_field.bind(ptg.keys.ENTER, lambda *_: submit(input_field, log_window))


        # Add the log_area to the manager
        manager.add(log_area, assign="logarea")
        # manager.focused(input_field)

        def macro_time(fmt: str) -> str:
            return time.strftime(fmt)


        def macro_mic(fmt: str) -> str:
            return "123"
        
        # HUD
        ptg.tim.define("!time", macro_time)
        ptg.tim.define("!mic", macro_mic)

        hud = ptg.Window(
            "[app.title]",
            "",
            ptg.Container(
                ptg.Label("Time:\n[!time 75]%X[/]"),
                "",
                ptg.Label("Mic:\n[!mic]%c[/]"),
                horizontal_align=ptg.HorizontalAlignment.LEFT,
            ),
            overflow=ptg.Overflow.SCROLL,
            vertical_align=ptg.VerticalAlignment.TOP,
            horizontal_align=ptg.HorizontalAlignment.LEFT,
            title="HUD",
        )
        manager.add(hud, assign="hud")




    ptg.tim.print(f"[{PALETTE_LIGHT}]Goodbye!")


if __name__ == "__main__":
    main()