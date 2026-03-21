from typing import Literal
from .base import Interaction


class TextBox(Interaction):
    """A text input box with optional word-wrap modes."""

    def __init__(
        self,
        initial: str = "",
        wrap: Literal["word", "anywhere", "extend"] = "word",
        readonly: bool = False,
    ):
        self._text = initial
        self._wrap = wrap
        self._readonly = readonly
        self._cursor_pos = len(initial)  # position in text
        self._scroll_offset = 0  # row scroll offset

    def render(self, region, term, focused: bool = False) -> None:
        lines = self._get_display_lines(region.width)

        # Adjust scroll to show cursor
        if focused:
            cursor_line = self._get_cursor_line(region.width)
            if cursor_line < self._scroll_offset:
                self._scroll_offset = cursor_line
            elif cursor_line >= self._scroll_offset + region.height:
                self._scroll_offset = cursor_line - region.height + 1

        visible_lines = lines[self._scroll_offset:self._scroll_offset + region.height]

        for i in range(region.height):
            row = region.row + i
            if i < len(visible_lines):
                line = visible_lines[i]
                display = line[:region.width].ljust(region.width)
            else:
                display = ' ' * region.width
            print(term.move(row, region.col) + display, end='', flush=False)

        # Draw cursor if focused
        if focused and not self._readonly:
            cursor_line = self._get_cursor_line(region.width)
            cursor_col_in_line = self._get_cursor_col_in_line(region.width)
            visible_cursor_row = cursor_line - self._scroll_offset
            if 0 <= visible_cursor_row < region.height:
                abs_row = region.row + visible_cursor_row
                abs_col = region.col + min(cursor_col_in_line, region.width - 1)
                lines_at_cursor = lines[cursor_line] if cursor_line < len(lines) else ''
                char_at_cursor = lines_at_cursor[cursor_col_in_line:cursor_col_in_line+1] or ' '
                try:
                    cursor_char = term.reverse + char_at_cursor + term.normal
                except Exception:
                    cursor_char = char_at_cursor
                print(term.move(abs_row, abs_col) + cursor_char, end='', flush=False)

    def _get_display_lines(self, width: int) -> list:
        """Split text into display lines based on wrap mode."""
        if self._wrap == 'extend':
            return self._text.split('\n') if self._text else ['']

        if not self._text:
            return ['']

        result = []
        for paragraph in self._text.split('\n'):
            if not paragraph:
                result.append('')
                continue
            if self._wrap == 'anywhere':
                # Split at exactly width chars
                while len(paragraph) > width:
                    result.append(paragraph[:width])
                    paragraph = paragraph[width:]
                result.append(paragraph)
            else:  # word wrap
                words = paragraph.split(' ')
                current_line = ''
                for word in words:
                    if not current_line:
                        current_line = word
                    elif len(current_line) + 1 + len(word) <= width:
                        current_line += ' ' + word
                    else:
                        result.append(current_line)
                        current_line = word
                result.append(current_line)

        return result if result else ['']

    def _get_cursor_line(self, width: int) -> int:
        """Get the display line number the cursor is on."""
        lines = self._get_display_lines(width)
        char_count = 0
        for i, line in enumerate(lines):
            line_len = len(line)
            if char_count + line_len >= self._cursor_pos:
                return i
            char_count += line_len + 1  # +1 for newline between paragraphs (simplified)
        return max(0, len(lines) - 1)

    def _get_cursor_col_in_line(self, width: int) -> int:
        """Get the column within the display line where the cursor is."""
        lines = self._get_display_lines(width)
        char_count = 0
        for line in lines:
            line_len = len(line)
            if char_count + line_len >= self._cursor_pos:
                return self._cursor_pos - char_count
            char_count += line_len + 1
        return 0

    def handle_key(self, key) -> tuple:
        if self._readonly:
            return False, self.get_value()

        if key.is_sequence:
            name = key.name
            if name == 'KEY_BACKSPACE' or name == 'KEY_DELETE':
                if self._cursor_pos > 0:
                    self._text = self._text[:self._cursor_pos-1] + self._text[self._cursor_pos:]
                    self._cursor_pos -= 1
                    return True, self.get_value()
            elif name == 'KEY_DC':  # Delete forward
                if self._cursor_pos < len(self._text):
                    self._text = self._text[:self._cursor_pos] + self._text[self._cursor_pos+1:]
                    return True, self.get_value()
            elif name == 'KEY_LEFT':
                if self._cursor_pos > 0:
                    self._cursor_pos -= 1
            elif name == 'KEY_RIGHT':
                if self._cursor_pos < len(self._text):
                    self._cursor_pos += 1
            elif name == 'KEY_HOME':
                self._cursor_pos = 0
            elif name == 'KEY_END':
                self._cursor_pos = len(self._text)
            elif name == 'KEY_ENTER':
                # Insert newline
                self._text = self._text[:self._cursor_pos] + '\n' + self._text[self._cursor_pos:]
                self._cursor_pos += 1
                return True, self.get_value()
        else:
            char = str(key)
            if char and char.isprintable():
                self._text = self._text[:self._cursor_pos] + char + self._text[self._cursor_pos:]
                self._cursor_pos += 1
                return True, self.get_value()

        return False, self.get_value()

    def get_value(self) -> str:
        return self._text

    def set_value(self, value) -> None:
        self._text = str(value)
        self._cursor_pos = len(self._text)
