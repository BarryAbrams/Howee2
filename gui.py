import pytermgui as ptg
import time

class HoweeApp:
    PALETTE_LIGHT = "#FCBA03"
    PALETTE_MID = "#8C6701"
    PALETTE_DARK = "#4D4940"
    PALETTE_DARKER = "#242321"

    def __init__(self, input_field_callback=None):
        self.log = [
            {"role": "user", "message": "What is up?"},
            {"role": "agent", "message": "Not too much"}
        ]
        self.setup_styles()
        self.input_field_callback = input_field_callback

    def setup_styles(self):
        ptg.tim.alias("app.text", "#cfc7b0")

        ptg.tim.alias("app.header", f"bold @{self.PALETTE_MID} #d9d2bd")
        ptg.tim.alias("app.header.fill", f"@{self.PALETTE_LIGHT}")

        ptg.tim.alias("app.title", f"bold {self.PALETTE_LIGHT}")
        ptg.tim.alias("app.button.label", f"bold @{self.PALETTE_DARK} app.text")
        ptg.tim.alias("app.button.highlight", "inverse app.button.label")

        ptg.tim.alias("app.footer", f"@{self.PALETTE_DARKER}")

        ptg.boxes.DOUBLE.set_chars_of(ptg.Window)
        ptg.boxes.ROUNDED.set_chars_of(ptg.Container)

        ptg.Button.styles.label = "app.button.label"
        ptg.Button.styles.highlight = "app.button.highlight"

        ptg.Slider.styles.filled__cursor = self.PALETTE_MID
        ptg.Slider.styles.filled_selected = self.PALETTE_LIGHT

        ptg.Label.styles.value = "app.text"

        ptg.Window.styles.border__corner = "#C2B280"
        ptg.Container.styles.border__corner = self.PALETTE_DARK

        ptg.Splitter.set_char("separator", "")

    def define_layout(self) -> ptg.Layout:
        layout = ptg.Layout()

        layout.add_slot("Header", height=1)
        layout.add_break()

        layout.add_slot("logarea", width=0.8)
        layout.add_slot("hud", width=0.2)

        layout.add_break()

        layout.add_slot("Footer", height=1)

        return layout

    def create_header(self) -> ptg.Window:
        """Create the header window."""
        header = ptg.Window("[app.header] HOWEE ", box="EMPTY", is_persistant=True)
        header.styles.fill = "app.header.fill"
        return header

    def create_footer(self, manager: ptg.WindowManager) -> ptg.Window:
        """Create the footer window."""
        footer = ptg.Window(ptg.Button("Quit", lambda *_: _confirm_quit(manager)), box="EMPTY")
        footer.styles.fill = "app.footer"

        def _confirm_quit(manager: ptg.WindowManager) -> None:
            """Creates an "Are you sure you want to quit" modal window"""

            modal = ptg.Window(
                "[app.title]Are you sure you want to quit?",
                "",
                ptg.Container(
                    ptg.Splitter(
                        ptg.Button("Yes", lambda *_: manager.stop()),
                        ptg.Button("No", lambda *_: modal.close()),
                        ratios=[0.5, 0.5]
                    ),
                ),
            ).center()

            modal.select(0)
            manager.add(modal)

        return footer

    def create_log_area(self) -> ptg.Window:
        log_window = None
        def macro_log(fmt: str) -> str:
            formatted_log = ""
            for entry in self.log:
                role = f"[bold]{entry['role'].capitalize()}[/]"
                message = entry["message"]
                formatted_log += f"{role}: {message}\n"
                if log_window:
                    log_window.scroll(2)
            return ptg.tim.parse(formatted_log.rstrip())

        ptg.tim.define("!log", macro_log)

        def submit(input_field):
            global log
            message = input_field.value
            self.log.append({"role": "user", "message": message})

            input_field._lines = [""]
            input_field.cursor.col = 0
            if self.input_field_callback:
                self.input_field_callback()

        input_field = ptg.InputField("")
        input_field.parent_align = ptg.HorizontalAlignment.RIGHT

        log_window = ptg.Window(
            ptg.Label("[bold][/][!log]%c", parent_align=0),
            height=16,
            overflow=ptg.Overflow.SCROLL,
            vertical_align=ptg.VerticalAlignment.BOTTOM,
        )

        # Scrolling log area
        log_area = ptg.Window(
                log_window,
                    ptg.Container(
                    ptg.Splitter(
                        input_field,
                        ptg.Button("Submit", lambda *_: submit(input_field)),
                        ratios=[0.8, 0.2]
                    ),
                ),
                title="Log",
                vertical_align=ptg.VerticalAlignment.TOP,
                is_noresize = True
        )
        log_area.focused = input_field

        input_field.bind(ptg.keys.ENTER, lambda *_: submit(input_field))

        return log_area
    
    def create_hud(self) -> ptg.Window:
        def macro_time(fmt: str) -> str:
            return time.strftime(fmt)

        def macro_mic(fmt: str) -> str:
            return "123"
            
        ptg.tim.define("!time", macro_time)
        ptg.tim.define("!mic", macro_mic)

        hud = ptg.Window(
            "[app.title]",
            "",
            ptg.Container(
                ptg.Label("Time:\n[!time 75]%X[/]"),
                "",
                ptg.Label("Mic:\n[!mic]%c[/]"),
                ptg.PixelMatrix(5, 5, default="gray")
            ),
            overflow=ptg.Overflow.SCROLL,
            vertical_align=ptg.VerticalAlignment.TOP,
            horizontal_align=ptg.HorizontalAlignment.LEFT,
            title="HUD",
        )
        return hud

    def update_log(self, new_entry: dict):
        self.log.append(new_entry)

    def input_field_callback(self, value: str):
        # You can customize this method to handle input field submissions
        pass

    def update_time(self, new_time: str):
        # Update the time value here
        pass

    def update_mic(self, new_mic_value: str):
        # Update the mic value here
        pass

    def run(self):
        with ptg.WindowManager() as manager:
            manager.layout = self.define_layout()
            manager.add(self.create_header())
            logarea = self.create_log_area()
            manager.add(logarea, assign="logarea")
            manager.add(self.create_hud(), assign="hud")
            manager.add(self.create_footer(manager))

            manager.focus(logarea)

        ptg.tim.print(f"[{self.PALETTE_LIGHT}]Goodbye!\n\n")

if __name__ == "__main__":

    def do_this():
        pass

    app = HoweeApp(input_field_callback=do_this)
    app.run()
    
