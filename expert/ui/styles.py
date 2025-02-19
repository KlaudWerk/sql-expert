"""Styles for the Expert UI."""
CUSTOM_CSS = """
TabbedContent {
    height: 1fr;
    margin: 0;
}

Tabs {
    dock: top;
    width: 100%;
    height: 3;
    background: $panel;
}

Tab {
    width: 25;
    height: 3;
    color: $text;
    background: $surface;
    margin: 0 1;
    content-align: center middle;
    text-align: center;
    padding: 0 1;
}

Tab:hover {
    background: $primary;
    color: white;
}

Tab.-active {
    background: $accent;
    color: white;
}

TabPane {
    padding: 1;
    color: $text;
}

.tab-section-title {
    background: $primary;
    color: white;
    padding: 1;
    text-style: bold;
    text-align: center;
}

.section-title {
    width: 60%;
    background: black;
    color: white;
    text-style: bold;
    text-align: center;
}

Label {
    margin: 1;
}

Input {
    margin: 1;
    width: 100%;
}

Select {
    margin: 1;
    width: 100%;
}

Button {
    margin: 1;
}

Button:disabled {
    background: $panel;
    color: $text-disabled;
    border: none;
}

.popup-container {
    width: 40;
    height: 10;
    background: $surface;
    border: thick $primary;
    padding: 1;
    align: center middle;
}

.popup-text {
    text-align: center;
    color: $text;
    margin-top: 1;
    width: 100%;
}

LoadingIndicator {
    width: 100%;
    height: 3;
}

Screen.SavingPopup {
    align: center middle;
}

.popup-dialog {
    width: 60;
    height: 15;
    border: thick $primary;
    background: $surface;
    padding: 2;
    margin: 1;
    align: center middle;
}

#saving-text {
    text-style: bold;
    content-align: center middle;
    width: 100%;
    height: 3;
    color: $text;
}

ModalScreen {
    align: center middle;
}

.left-panel {
    width: 50%;
    height: 100%;
    padding: 1;
    border-right: solid $primary;
}

.right-panel {
    width: 50%;
    height: 100%;
    padding: 1;
}

RichLog {
    height: 100%;
    border: solid $primary;
    background: $surface;
    padding: 1;
}

Checkbox {
    margin: 1 0;
    padding: 0 2;
}

.button-container {
    margin-top: 1;
    width: 100%;
    height: auto;
    align: center middle;
    layout: horizontal;
}

.db-button {
    width: 1fr;
    margin: 0 1;
}

#connect-btn {
    margin-right: 1;
}

.log-header {
    width: 100%;
    height: 3;
    layout: horizontal;
    align: left middle;
}

.log-buttons {
    width: 40%;
    height: 3;
    layout: horizontal;
    align: left middle;
    padding-left: 1;
}

.log-buttons Button {
    width: 10;
    height: 3;
    background: $surface;
    border: solid $primary;
    content-align: center middle;
    margin-right: 1;
}

.log-buttons Button:hover {
    background: $primary;
    color: $text;
}

#content-container {
    height: 100%;
    padding: 1;
}

#input-container {
    width: 100%;
    height: auto;
    padding: 1;
    background: $surface;
    border-top: solid $primary;
    align-vertical: bottom;
}

#expert-log {
    width: 100%;
    height: 1fr;
    border: solid $primary;
    background: $surface;
    margin: 1;
    padding: 1;
}

#message-input {
    width: 1fr;
    margin: 1;
    height: 5;
}

#send-button {
    width: 10;
    margin: 1;
    align: right middle;
}
""" 