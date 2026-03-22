from typing import Literal
from .scrollable import _ScrollableList


class CheckBox(_ScrollableList):
    """A checkbox list with multi or single selection modes."""

    def __init__(self, items: dict, mode: Literal["multi", "single"] = "multi"):
        """
        items: dict[str, bool] - label -> checked state
        mode: "multi" allows multiple checked; "single" allows at most one
        """
        self._items = dict(items)
        self._labels = list(items.keys())
        self._mode = mode
        self._active_index = 0
        self._scroll_offset = 0

    def render(self, region, term, focused: bool = False) -> None:
        all_lines = []
        for label in self._labels:
            checked = self._items[label]
            if self._mode == 'multi':
                prefix = '[X]' if checked else '[ ]'
            else:
                prefix = '(●)' if checked else '( )'
            all_lines.append(f'{prefix} {label}')

        viewport = all_lines[self._scroll_offset: self._scroll_offset + region.height]
        self._render_rows(viewport, region, term, focused, active_marker=False)

    def handle_key(self, key) -> tuple:
        if key.is_sequence:
            name = key.name
            if name == 'KEY_UP':
                self._active_index = max(0, self._active_index - 1)
                self._clamp_scroll()
                return False, self.get_value()
            elif name == 'KEY_DOWN':
                self._active_index = min(len(self._labels) - 1, self._active_index + 1)
                self._clamp_scroll()
                return False, self.get_value()
            elif name in ('KEY_ENTER',):
                return self._toggle()
        else:
            char = str(key)
            if char == 'k':
                self._active_index = max(0, self._active_index - 1)
                self._clamp_scroll()
                return False, self.get_value()
            elif char == 'j':
                self._active_index = min(len(self._labels) - 1, self._active_index + 1)
                self._clamp_scroll()
                return False, self.get_value()
            elif char == ' ':
                return self._toggle()
        return False, self.get_value()

    def _toggle(self):
        if not self._labels:
            return False, self.get_value()
        label = self._labels[self._active_index]
        if self._mode == 'single':
            new_state = not self._items[label]
            for k in self._labels:
                self._items[k] = False
            self._items[label] = new_state
        else:
            self._items[label] = not self._items[label]
        return True, self.get_value()

    def get_value(self) -> dict:
        return dict(self._items)

    def set_value(self, value) -> None:
        self._items = dict(value)
        self._labels = list(value.keys())
