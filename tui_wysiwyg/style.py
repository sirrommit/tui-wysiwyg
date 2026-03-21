"""
Styled text utilities for tui_wysiwyg.

Style tags use a simple XML-like format:
    <attr1[=val1][;attr2[=val2]...]>text</>

Opening tag examples:
    <bold>text</bold>
    <color=red>text</>
    <color=red;bg=blue;bold;underline>text</>

Closing tag: </> or </anything> (the tag name is ignored; all styles reset).

Supported attributes
--------------------
Text style:
    bold            — bold / bright text
    dim / faint     — dim/faint text
    italic          — italic (terminal-dependent)
    underline / ul  — underline
    blink / flash   — blinking text (terminal-dependent)
    reverse / invert — reverse video (swap fg/bg)
    standout        — standout (often same as reverse)
    strike / strikethrough / line-through — strikethrough (terminal-dependent)
    normal / reset  — explicit reset to default

Foreground color  (key: color, fg, foreground, fg-color, text-color):
    black, red, green, yellow, blue, magenta, cyan, white
    bright_black / gray / grey, bright_red, bright_green, bright_yellow,
    bright_blue, bright_magenta, bright_cyan, bright_white
    plus common aliases: purple→magenta, pink→bright_magenta,
    orange→yellow, lime→bright_green, teal→cyan, navy→blue,
    maroon→red, silver→white
    256-colour: any integer 0–255 (e.g. color=196)

Background color  (key: bg, background, bg-color, bgcolor, background-color):
    same names as foreground

All styling degrades gracefully: if the terminal doesn't support an attribute,
it is silently skipped and plain text is emitted instead.
"""

import re

# Matches any <...> tag (content must not contain < or >).
_TAG_RE = re.compile(r'<([^<>]*)>')

# ── colour aliases ──────────────────────────────────────────────────────────

_COLOR_ALIASES: dict[str, str] = {
    'gray': 'bright_black',
    'grey': 'bright_black',
    'darkgray': 'bright_black',
    'darkgrey': 'bright_black',
    'lightgray': 'white',
    'lightgrey': 'white',
    'silver': 'white',
    'purple': 'magenta',
    'violet': 'magenta',
    'pink': 'bright_magenta',
    'orange': 'yellow',       # closest 16-colour approximation
    'lime': 'bright_green',
    'teal': 'cyan',
    'navy': 'blue',
    'maroon': 'red',
    'indigo': 'blue',
    'aqua': 'cyan',
    'olive': 'yellow',
    'fuchsia': 'bright_magenta',
}

# ── tag parsing ─────────────────────────────────────────────────────────────

def _is_close_tag(content: str) -> bool:
    return content.strip().startswith('/')


def _parse_attrs(attr_str: str) -> dict:
    """Parse 'attr1=val1;attr2;attr3=val3' into a dict."""
    attrs: dict = {}
    for part in attr_str.split(';'):
        part = part.strip()
        if not part:
            continue
        if '=' in part:
            k, _, v = part.partition('=')
            attrs[k.strip().lower()] = v.strip().lower()
        else:
            attrs[part.strip().lower()] = True
    return attrs


def parse_styled(text: str) -> list:
    """
    Parse *text* containing style tags into a list of ``(attrs, chunk)`` pairs.

    *attrs* is a ``dict`` (possibly empty — means unstyled).
    *chunk* is a plain-text string with no tags.

    Example::

        parse_styled('<bold>hello</> world')
        # → [({'bold': True}, 'hello'), ({}, ' world')]
    """
    segments: list = []
    current_attrs: dict = {}
    last_end = 0

    for match in _TAG_RE.finditer(text):
        # Flush text before this tag
        chunk = text[last_end:match.start()]
        if chunk:
            segments.append((dict(current_attrs), chunk))
        last_end = match.end()

        content = match.group(1)
        if _is_close_tag(content):
            current_attrs = {}
        else:
            current_attrs = _parse_attrs(content)

    # Flush remaining text after the last tag
    tail = text[last_end:]
    if tail:
        segments.append((dict(current_attrs), tail))

    return segments


# ── plain-text helpers ──────────────────────────────────────────────────────

def styled_plain_text(text: str) -> str:
    """Return *text* with all style tags stripped."""
    return _TAG_RE.sub('', text)


def styled_visual_len(text: str) -> int:
    """Return the visible character length of *text* (ignoring style tags)."""
    return len(styled_plain_text(text))


# ── terminal rendering ──────────────────────────────────────────────────────

def _normalize_color(name: str) -> str:
    """Normalise a colour name to a blessed terminal property name."""
    name = name.lower().replace('-', '_')
    if name in _COLOR_ALIASES:
        name = _COLOR_ALIASES[name]
    # 'brightX' → 'bright_X'
    if name.startswith('bright') and not name.startswith('bright_'):
        name = 'bright_' + name[6:]
    return name


def _get_color_seq(value: str, bg: bool, term) -> str:
    """Return terminal escape sequence for *value* as fg or bg colour."""
    try:
        # Numeric 256-colour
        n = int(value)
        if bg:
            fn = getattr(term, 'on_color', None)
        else:
            fn = getattr(term, 'color', None)
        if callable(fn):
            seq = fn(n)
            return str(seq) if seq else ''
        return ''
    except (ValueError, TypeError):
        pass

    try:
        name = _normalize_color(value)
        if bg:
            attr = f'on_{name}'
        else:
            attr = name
        seq = getattr(term, attr, None)
        return str(seq) if seq else ''
    except Exception:
        return ''


# Attribute key groups → action taken when applying
_FG_KEYS = frozenset({'color', 'fg', 'foreground', 'fg-color', 'fg_color', 'text-color', 'text_color'})
_BG_KEYS = frozenset({'bg', 'background', 'bg-color', 'bg_color', 'bgcolor',
                      'background-color', 'background_color'})

_STYLE_MAP = {
    # key (lowercase) → terminal property name(s) to try in order
    'bold':           ('bold',),
    'dim':            ('dim',),
    'faint':          ('dim',),
    'italic':         ('italic',),
    'underline':      ('underline',),
    'ul':             ('underline',),
    'underlined':     ('underline',),
    'underline-text': ('underline',),
    'blink':          ('blink',),
    'flash':          ('blink',),
    'reverse':        ('reverse',),
    'invert':         ('reverse',),
    'reverse-video':  ('reverse',),
    'reverse_video':  ('reverse',),
    'standout':       ('standout',),
    'strike':         ('strikethru', 'strike', 'strikethrough'),
    'strikethrough':  ('strikethru', 'strike', 'strikethrough'),
    'strikeout':      ('strikethru', 'strike', 'strikethrough'),
    'line-through':   ('strikethru', 'strike', 'strikethrough'),
    'normal':         ('normal',),
    'reset':          ('normal',),
}


def _apply_attrs(attrs: dict, term) -> str:
    """
    Convert *attrs* dict to a terminal escape sequence string.

    Attributes that the terminal doesn't support are silently skipped.
    Returns an empty string if nothing could be applied.
    """
    result = ''
    for key, val in attrs.items():
        try:
            if key in _FG_KEYS:
                result += _get_color_seq(str(val), bg=False, term=term)
            elif key in _BG_KEYS:
                result += _get_color_seq(str(val), bg=True, term=term)
            elif key in _STYLE_MAP:
                for prop in _STYLE_MAP[key]:
                    seq = getattr(term, prop, None)
                    if seq:
                        result += str(seq)
                        break
        except Exception:
            pass
    return result


def _truncate_segments(segments: list, max_len: int) -> list:
    """Truncate *segments* so total visible text is at most *max_len* chars."""
    result = []
    remaining = max_len
    for attrs, chunk in segments:
        if remaining <= 0:
            break
        if len(chunk) <= remaining:
            result.append((attrs, chunk))
            remaining -= len(chunk)
        else:
            result.append((attrs, chunk[:remaining]))
            remaining = 0
    return result


def render_styled(text: str, term, max_len: int = None) -> str:
    """
    Render *text* — which may contain style tags — using *term* escape sequences.

    *max_len*: if given, visible text is truncated to this many characters.

    If the terminal doesn't support a given attribute it is silently omitted,
    so the function always returns something displayable.  After each styled
    span a ``term.normal`` reset is emitted to avoid bleeding into adjacent text.
    """
    segments = parse_styled(text)
    if max_len is not None:
        segments = _truncate_segments(segments, max_len)

    result = ''
    for attrs, chunk in segments:
        if attrs:
            seq = _apply_attrs(attrs, term)
            if seq:
                try:
                    reset = str(term.normal) if term.normal else ''
                except Exception:
                    reset = ''
                result += seq + chunk + reset
            else:
                result += chunk
        else:
            result += chunk
    return result


# ── C-style comment stripping ───────────────────────────────────────────────

_COMMENT_RE = re.compile(r'/\*.*?\*/', re.DOTALL)


def strip_comments(text: str) -> str:
    """
    Remove ``/* … */`` comments from a shell definition string.

    Newlines inside a comment are preserved so that the line structure of
    the definition is not disrupted.
    """
    def _replacer(m: re.Match) -> str:
        # Preserve the newlines contained in the comment.
        return '\n' * m.group().count('\n')

    return _COMMENT_RE.sub(_replacer, text)
