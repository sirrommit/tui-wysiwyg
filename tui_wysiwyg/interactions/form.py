from .base import Interaction


_VALID_TYPES = {"str", "int", "float", "bool", "choices"}


class FormInput(Interaction):
    """A structured data-entry form with multiple typed fields."""

    def __init__(self, fields: dict):
        """
        fields: dict[str, dict] mapping variable names to field definitions.
        Each field definition must have 'type' and 'descriptor'.
        """
        self._fields = {}  # ordered dict of field definitions
        self._field_keys = []
        self._field_states = {}  # key -> current text/value
        self._field_errors = {}  # key -> error message or None
        self._active_index = 0  # 0..len(fields) is fields, len(fields) is Submit
        self._wants_exit = False
        self._exit_value = None
        self._scroll_offset = 0

        for key, defn in fields.items():
            if 'type' not in defn:
                raise ValueError(f"field '{key}' missing required key 'type'")
            if 'descriptor' not in defn:
                raise ValueError(f"field '{key}' missing required key 'descriptor'")
            ftype = defn['type']
            if ftype not in _VALID_TYPES:
                raise ValueError(f"field '{key}' has unknown type '{ftype}'")
            if ftype == 'choices':
                if 'options' not in defn:
                    raise ValueError(f"field '{key}' type 'choices' requires 'options'")
                if not defn['options']:
                    raise ValueError(f"field '{key}' options must be a non-empty list")

            # Validate and set default
            default = defn.get('default')
            if default is not None:
                try:
                    _coerce(ftype, default)
                except (ValueError, TypeError):
                    raise ValueError(f"field '{key}' default value does not match type")

            self._fields[key] = dict(defn)
            self._field_keys.append(key)

            # Initialize state
            if ftype == 'bool':
                self._field_states[key] = bool(default) if default is not None else False
            elif ftype == 'choices':
                options = defn['options']
                if default is not None and default in options:
                    self._field_states[key] = options.index(default)
                else:
                    self._field_states[key] = 0
            else:
                self._field_states[key] = str(default) if default is not None else ''

            self._field_errors[key] = None

    def render(self, region, term, focused: bool = False) -> None:
        num_fields = len(self._field_keys)
        # Each field takes 1 row (possibly 2 if there's an error)
        # + separator + submit
        rows_available = region.height

        # Build display lines
        display_rows = []
        for i, key in enumerate(self._field_keys):
            defn = self._fields[key]
            descriptor = defn['descriptor']
            ftype = defn['type']
            state = self._field_states[key]
            error = self._field_errors.get(key)

            # Format field value
            if ftype == 'bool':
                value_str = '< Yes >' if state else '< No  >'
            elif ftype == 'choices':
                options = defn['options']
                selected = options[state] if 0 <= state < len(options) else ''
                value_str = f'< {selected} >'
            else:
                placeholder = defn.get('placeholder', '')
                if state == '' and placeholder:
                    value_str = f'[{placeholder[:max(0, region.width - len(descriptor) - 5)]}]'
                else:
                    value_str = f'[{state}]'

            line = f'  {descriptor:<12}: {value_str}'
            line = line[:region.width].ljust(region.width)

            is_active = (i == self._active_index) and focused
            if is_active:
                try:
                    line = term.reverse + line + term.normal
                except Exception:
                    line = '> ' + line[2:]

            display_rows.append(line)

            if error:
                err_line = f'  {"":12}  ! {error}'
                err_line = err_line[:region.width].ljust(region.width)
                display_rows.append(err_line)

        # Separator
        sep = '-' * min(region.width, 34)
        display_rows.append(sep.ljust(region.width))

        # Submit button
        submit_line = '  [ Submit ]'.ljust(region.width)
        is_submit_active = (self._active_index == num_fields) and focused
        if is_submit_active:
            try:
                submit_line = term.reverse + submit_line + term.normal
            except Exception:
                submit_line = '> [ Submit ]'.ljust(region.width)
        display_rows.append(submit_line)

        # Compute which display row the active item is on
        active_display_row = 0
        if self._active_index == num_fields:
            active_display_row = len(display_rows) - 1   # Submit is last
        else:
            row_cursor = 0
            for i, key in enumerate(self._field_keys):
                if i == self._active_index:
                    active_display_row = row_cursor
                    break
                row_cursor += 2 if self._field_errors.get(key) else 1

        # Scroll to keep active row visible
        total_rows = len(display_rows)
        if total_rows <= region.height:
            self._scroll_offset = 0
        else:
            if active_display_row < self._scroll_offset:
                self._scroll_offset = active_display_row
            elif active_display_row >= self._scroll_offset + region.height:
                self._scroll_offset = active_display_row - region.height + 1
            self._scroll_offset = max(0, min(self._scroll_offset, total_rows - region.height))

        # Render visible rows
        visible = display_rows[self._scroll_offset:self._scroll_offset + region.height]
        for i in range(region.height):
            row = region.row + i
            if i < len(visible):
                content = visible[i]
            else:
                content = ' ' * region.width
            print(term.move(row, region.col) + content, end='', flush=False)

    def handle_key(self, key) -> tuple:
        self._wants_exit = False
        num_fields = len(self._field_keys)

        if key.is_sequence:
            name = key.name
            if name == 'KEY_UP':
                self._active_index = max(0, self._active_index - 1)
                return False, self.get_value()
            elif name == 'KEY_DOWN':
                self._active_index = min(num_fields, self._active_index + 1)
                return False, self.get_value()
            elif name == 'KEY_ENTER':
                if self._active_index == num_fields:
                    return self._submit()
                else:
                    # For bool/choices, treat Enter as toggle/cycle
                    return self._interact_field()
            elif name == 'KEY_LEFT':
                return self._interact_field_left()
            elif name == 'KEY_RIGHT':
                return self._interact_field_right()
            elif name in ('KEY_BACKSPACE', 'KEY_DELETE'):
                return self._field_backspace()
        else:
            char = str(key)
            if char == ' ':
                return self._interact_field()
            elif char.isprintable() and char not in ('\t',):
                return self._field_type_char(char)

        return False, self.get_value()

    def _current_key(self):
        if self._active_index < len(self._field_keys):
            return self._field_keys[self._active_index]
        return None

    def _interact_field(self):
        key = self._current_key()
        if key is None:
            return False, self.get_value()
        defn = self._fields[key]
        ftype = defn['type']
        if ftype == 'bool':
            self._field_states[key] = not self._field_states[key]
            return True, self.get_value()
        elif ftype == 'choices':
            options = defn['options']
            self._field_states[key] = (self._field_states[key] + 1) % len(options)
            return True, self.get_value()
        return False, self.get_value()

    def _interact_field_left(self):
        key = self._current_key()
        if key is None:
            return False, self.get_value()
        defn = self._fields[key]
        ftype = defn['type']
        if ftype == 'bool':
            self._field_states[key] = False
            return True, self.get_value()
        elif ftype == 'choices':
            options = defn['options']
            self._field_states[key] = (self._field_states[key] - 1) % len(options)
            return True, self.get_value()
        return False, self.get_value()

    def _interact_field_right(self):
        key = self._current_key()
        if key is None:
            return False, self.get_value()
        defn = self._fields[key]
        ftype = defn['type']
        if ftype == 'bool':
            self._field_states[key] = True
            return True, self.get_value()
        elif ftype == 'choices':
            options = defn['options']
            self._field_states[key] = (self._field_states[key] + 1) % len(options)
            return True, self.get_value()
        return False, self.get_value()

    def _field_backspace(self):
        key = self._current_key()
        if key is None:
            return False, self.get_value()
        defn = self._fields[key]
        ftype = defn['type']
        if ftype in ('str', 'int', 'float'):
            state = self._field_states[key]
            if state:
                self._field_states[key] = state[:-1]
                return True, self.get_value()
        return False, self.get_value()

    def _field_type_char(self, char: str):
        key = self._current_key()
        if key is None:
            return False, self.get_value()
        defn = self._fields[key]
        ftype = defn['type']
        state = self._field_states[key]

        if ftype == 'str':
            self._field_states[key] = state + char
            return True, self.get_value()
        elif ftype == 'int':
            if char.isdigit() or (char == '-' and not state):
                self._field_states[key] = state + char
                return True, self.get_value()
        elif ftype == 'float':
            if char.isdigit() or (char == '-' and not state) or (char == '.' and '.' not in state):
                self._field_states[key] = state + char
                return True, self.get_value()
        return False, self.get_value()

    def _validate_field(self, key) -> str | None:
        """Validate a field, return error message or None."""
        defn = self._fields[key]
        ftype = defn['type']
        state = self._field_states[key]

        if ftype in ('int', 'float'):
            if state:
                try:
                    parsed = _coerce(ftype, state)
                except (ValueError, TypeError):
                    return f'Must be a {"whole number" if ftype == "int" else "number"}'
                validator = defn.get('validator')
                if validator:
                    result = validator(parsed)
                    if result is not True and result:
                        return str(result)
            elif defn.get('required'):
                return 'This field is required'
        elif ftype == 'str':
            if state:
                validator = defn.get('validator')
                if validator:
                    result = validator(state)
                    if result is not True and result:
                        return str(result)
            elif defn.get('required'):
                return 'This field is required'

        return None

    def _submit(self):
        """Attempt to submit the form."""
        # Validate all fields
        has_errors = False
        first_error_index = None

        for i, key in enumerate(self._field_keys):
            error = self._validate_field(key)
            self._field_errors[key] = error
            if error:
                has_errors = True
                if first_error_index is None:
                    first_error_index = i

        if has_errors:
            self._active_index = first_error_index
            return False, self.get_value()

        # Build result dict
        result = {}
        for key in self._field_keys:
            defn = self._fields[key]
            ftype = defn['type']
            state = self._field_states[key]

            if ftype == 'str':
                result[key] = state if state else None
            elif ftype == 'int':
                result[key] = int(state) if state else None
            elif ftype == 'float':
                result[key] = float(state) if state else None
            elif ftype == 'bool':
                result[key] = state
            elif ftype == 'choices':
                options = defn['options']
                result[key] = options[state] if 0 <= state < len(options) else None

        self._exit_value = result
        self._wants_exit = True
        return True, result

    def get_value(self) -> dict:
        """Return current state as a dict."""
        result = {}
        for key in self._field_keys:
            defn = self._fields[key]
            ftype = defn['type']
            state = self._field_states[key]

            if ftype == 'choices':
                options = defn['options']
                result[key] = options[state] if 0 <= state < len(options) else None
            elif ftype == 'bool':
                result[key] = state
            else:
                result[key] = state
        return result

    def set_value(self, value) -> None:
        """Set field values from a dict."""
        for key, val in value.items():
            if key in self._fields:
                defn = self._fields[key]
                ftype = defn['type']
                if ftype == 'bool':
                    self._field_states[key] = bool(val)
                elif ftype == 'choices':
                    options = defn['options']
                    if val in options:
                        self._field_states[key] = options.index(val)
                else:
                    self._field_states[key] = str(val) if val is not None else ''

    def signal_return(self) -> tuple:
        if self._wants_exit:
            return True, self._exit_value
        return False, None


def _coerce(ftype: str, value):
    """Coerce a value to the given type, raising ValueError if not possible."""
    if ftype == 'str':
        return str(value)
    elif ftype == 'int':
        return int(value)
    elif ftype == 'float':
        return float(value)
    elif ftype == 'bool':
        return bool(value)
    return value
