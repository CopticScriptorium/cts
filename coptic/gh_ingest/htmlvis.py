"""A re-implementation of ANNIS's htmlvis (http://corpus-tools.org/annis/resources/ANNIS_HTML_Vis_Guide.pdf).
`generate_visualization` consumes TreeTagger SGML text and renders it into HTML according to an ANNIS
htmlvis config file."""

import re
from enum import Enum
from collections import defaultdict

from coptic.settings.base import HTML_CONFIGS


class HtmlGenerationException(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class TriggerTypes(Enum):
    ANN = 1
    VALUE = 2
    ANN_AND_VALUE = 3
    TOK = 4


class ContentTypes(Enum):
    NONE = 0
    VALUE = 1
    STRING = 2


class Directive:
    """Represents a line in the htmlvis configuration."""

    def __init__(self, triggering_condition, generated_element, content=""):
        triggering_condition_dict = Directive.parse_triggering_condition(
            triggering_condition
        )
        self._type = triggering_condition_dict["type"]
        self._trigger_name = triggering_condition_dict.get("name", None)
        self._trigger_val = triggering_condition_dict.get("val", None)

        generated_element_dict = Directive.parse_generated_element(generated_element)
        self._generated_name = generated_element_dict.get("name", None)
        self._generated_attr = generated_element_dict.get("attr", None)
        self._generated_style = generated_element_dict.get("style", None)
        self._generated_class = generated_element_dict.get("class", None)

        content_dict = Directive.parse_content(content)
        self._content_type = content_dict["type"]
        self._content_value = content_dict.get("value", None)

        self._original_line = (triggering_condition, generated_element, content)

    def applies(self, elt):
        "Returns True if the directive applies to this element, False otherwise"
        raise NotImplemented()

    def apply_left(self, elt, text):
        "Applies the transformation defined by this line to the text at elt.open_line"
        raise NotImplemented()

    def apply_right(self, elt, text):
        "Applies the transformation defined by this line to the text at elt.close_line"
        if self._generated_name == "NULL":
            return text
        else:
            return text + f"</{self._generated_name}>"

    @classmethod
    def parse_triggering_condition(cls, text):
        "Parses the first column in a config"
        if text.lower() == "tok":
            return {"type": TriggerTypes.TOK}
        if "=" in text:
            try:
                elt, val = text.split("=")
            except ValueError as e:
                raise HtmlGenerationException(
                    f"Malformed target element in config: {text}"
                ) from e

            if elt != "":
                return {"type": TriggerTypes.ANN_AND_VALUE, "name": elt, "value": val}
            else:
                return {"type": TriggerTypes.VALUE, "value": val}
        return {"type": TriggerTypes.ANN, "name": text}

    @classmethod
    def parse_generated_element(cls, text):
            "Parses the second column in a config"
            semicolon_index = text.find(";")
            if semicolon_index == -1:
                colon_index = text.find(":")
                if colon_index == -1:
                    return {"name": text}
                else:
                    return {"name": text[:colon_index], "attr": text[colon_index + 1:]}

            name, attrs_text = text[:semicolon_index], text[semicolon_index + 1:]

            d = {}
            colon_index = text.find(":")
            if colon_index == -1:
                d["name"] = name
            else:
                d["name"] = name[:colon_index]
                d["attr"] = name[colon_index + 1:]

            # only support the "style" attr for now
            style = re.findall(r'style="([^"]*?)"', attrs_text)

            if len(style) == 0:
                return d
            style = style[0]

            # perhaps regrettably, "style" can actually mean "class" if there's no colon inside.
            if ":" not in style:
                d["class"] = style
            else:
                d["style"] = style
            return d

    @classmethod
    def parse_content(cls, text):
        text = text.strip()
        if not text:
            return {"type": ContentTypes.NONE}
        if text.lower() == "value":
            return {"type": ContentTypes.VALUE}
        if text[-1] == '"' and text[0] == '"':
            return {"type": ContentTypes.STRING, "value": text[1:-1]}
        return {"type": ContentTypes.STRING, "value": text}

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'<{self.__class__.__name__} tsv_line="{self._original_line}">'


class TokDirective(Directive):
    """For the triggering condition 'tok'"""

    def applies(self, elt):
        return isinstance(elt, str)

    def apply_left(self, elt, text):
        parts = []
        if self._generated_name != "NULL":
            parts.append(f"<{self._generated_name}")
            if self._generated_class:
                parts.append(f' class="{self._generated_class}"')
            elif self._generated_style:
                parts.append(f' style="{self._generated_style}"')
            parts.append(">")

        if self._content_type == ContentTypes.STRING:
            parts.append(self._content_value)

        parts.append(text)
        return " ".join(parts)


class AnnDirective(Directive):
    """For a triggering condition like 'title'"""

    def applies(self, elt):
        return elt.name == self._trigger_name

    def apply_left(self, elt, text):
        if self._content_type == ContentTypes.VALUE:
            content = elt.attrs.get(elt.name, "")
        elif self._content_type == ContentTypes.STRING:
            content = self._content_value.replace("%%name%%", elt.name)
            content = content.replace("%%value%%", elt.attrs.get(elt.name, ""))
        else:
            content = None

        parts = []
        if self._generated_name != "NULL":
            parts.append(f"<{self._generated_name}")
            if self._generated_class:
                parts.append(f' class="{self._generated_class}"')
            elif self._generated_style:
                parts.append(f' style="{self._generated_style}"')

            if content and self._generated_attr:
                parts.append(f' {self._generated_attr}="{content}">')
            elif content:
                parts.append(f">{content}")
            else:
                parts.append(">")
        elif content:
            parts.append(content)

        parts.append(text)
        return "".join(parts)


class ValueDirective(Directive):
    """For a triggering condition like '="God"'"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._triggered_attr_name = None

    def applies(self, elt):
        for name, value in elt.attrs:
            if value == self._trigger_val:
                # there could in principle be multiple matches, but only apply the rule once at most
                self._triggered_attr_name = name
                return True
        return False

    def apply_left(self, elt, text):
        if self._content_type == ContentTypes.VALUE:
            content = elt.attrs.get(elt.name, "")
        elif self._content_type == ContentTypes.STRING:
            content = self._content_value.replace("%%name%%", elt.name)
            content = content.replace("%%value%%", elt.attrs.get(elt.name, ""))
        else:
            content = None

        parts = []
        if self._generated_name != "NULL":
            parts.append(f"<{self._generated_name}")
            if self._generated_class:
                parts.append(f' class="{self._generated_class}"')
            elif self._generated_style:
                parts.append(f' style="{self._generated_style}"')

            if content and self._generated_attr:
                parts.append(f' {self._generated_attr}="{content}">')
            elif content:
                parts.append(f">{content}")
            else:
                parts.append(">")
        elif content:
            parts.append(content)

        parts.append(text)
        return "".join(parts)


class AnnAndValueDirective(Directive):
    """For a triggering condition like 'norm="God"'"""

    def applies(self, elt):
        return (
            self._trigger_name in elt.attrs
            and elt.attrs[self._trigger_name] == self._trigger_val
        )

    def apply_left(self, elt, text):
        if self._content_type == ContentTypes.VALUE:
            content = elt.attrs.get(self._trigger_name, "")
        elif self._content_type == ContentTypes.STRING:
            content = self._content_value.replace("%%name%%", self._trigger_name)
            content = content.replace("%%value%%", elt.attrs.get(self._trigger_name, ""))
        else:
            content = None

        parts = []
        if self._generated_name != "NULL":
            parts.append(f"<{self._generated_name}")
            if self._generated_class:
                parts.append(f' class="{self._generated_class}"')
            elif self._generated_style:
                parts.append(f' style="{self._generated_style}"')

            if content and self._generated_attr:
                parts.append(f' {self._generated_attr}="{content}">')
            elif content:
                parts.append(f">{content}")
            else:
                parts.append(">")
        else:
            parts.append(content or "")

        parts.append(text)
        return "".join(parts)


class SgmlElement:
    def __init__(self, name, attrs=[], open_line=-1):
        self.name = name
        self.attrs = dict(attrs)
        self.open_line = open_line
        self.close_line = -1

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return (
            f'<SgmlElement="{self.name}" open_line="{self.open_line}" close_line="{self.close_line}" '
            + " ".join(f'{name}="{value}"' for name, value in self.attrs.items())
            + ">"
        )

    def __len__(self):
        return self.close_line - self.open_line


DIRECTIVE_MAP = {
    TriggerTypes.TOK: TokDirective,
    TriggerTypes.ANN: AnnDirective,
    TriggerTypes.VALUE: ValueDirective,
    TriggerTypes.ANN_AND_VALUE: AnnAndValueDirective,
}


def parse_config(config_text):
    directives = []
    for line in config_text.strip().split("\n"):
        if line.startswith("#"):
            continue
        # Some config files have a space instead of a tab separating the first column--tolerate it because we
        # still know what to do. But this really shouldn't be necessary...
        line = re.sub(r"^([^\s]*)\s", r"\1\t", line)
        line = line.split("\t")
        triggering_condition = line[0]
        trigger_type = Directive.parse_triggering_condition(triggering_condition)[
            "type"
        ]
        directives.append(DIRECTIVE_MAP[trigger_type](*line))

    return directives

CLOSE_TAG_REGEX = re.compile(r"^</([^\s<>/]*)")
NAME_REGEX = re.compile(r"^<([^\s<>/]*)")
ATTRS_REGEX = re.compile(r'\s([^\s]*)="([^"]*?)"')

def parse_close_tag(i, line):
    name_match = CLOSE_TAG_REGEX.search(line)
    if not name_match:
        raise HtmlGenerationException(
            f"Couldn't recognize an SGML element name on closing line {i}:\n\n\t{line}"
        )
    return name_match.group(1)


def parse_open_tag(i, line, tok_count):
    name_match = NAME_REGEX.search(line)
    if not name_match:
        raise HtmlGenerationException(
            f"Couldn't recognize an SGML element name on opening line {i}:\n\n\t{line}"
        )
    name = name_match.group(1)

    attrs = ATTRS_REGEX.findall(line)
    return SgmlElement(name, attrs, tok_count)


def individuate(elt):
    """Some TT SGML elements have more than one attr with names that are not their own, e.g.:

            <norm xml:id="u1" func="root" pos="N" lemma="ⲕⲟⲥⲙⲟⲥ" norm="ⲕⲟⲥⲙⲟⲥ">

    This function, conceptually, turns that into this:

            <norm xml:id="u1" norm="ⲕⲟⲥⲙⲟⲥ">
            <func func="root">
            <pos pos="N">
            <lemma lemma="ⲕⲟⲥⲙⲟⲥ">
    """
    elts = [elt]
    to_delete = [attr_name for attr_name in elt.attrs if attr_name != elt.name and ":" not in attr_name and elt.name != "meta"]

    for attr_name in to_delete:
        attr_val = elt.attrs[attr_name]
        new_elt = SgmlElement(attr_name, [(attr_name, attr_val)])
        new_elt.open_line = elt.open_line
        new_elt.close_line = elt.close_line
        elts.append(new_elt)
        del elt.attrs[attr_name]

    return elts

def parse_text(text):
    """
    Parses the given text, extracting elements and tokens.

    Args:
        text (str): The input text to be parsed.

    Returns:
        tuple: A tuple containing:
            - toks (list of str): A list of token strings extracted from the text.
            - complete_elts (list): A list of complete elements parsed from the text.
    """
    complete_elts = []  # List to store complete elements
    elt_stack = defaultdict(list)  # Stack to manage nested elements
    toks = []  # List to store token strings
    tok_count = 0  # Counter for tokens

    for i, line in enumerate(text.strip().split("\n")):
        try:
            if line.startswith("</"):  # If the line is a closing tag
                name = parse_close_tag(i, line)  # Parse the closing tag
                elt = elt_stack[name].pop()  # Pop the element from the stack
                elt.close_line = tok_count - 1  # Set the closing line for the element
                complete_elts.extend(individuate(elt))  # Process and add the element to complete elements
            elif line.startswith("<"):  # If the line is an opening tag
                elt = parse_open_tag(i, line, tok_count)  # Parse the opening tag
                elt_stack[elt.name].append(elt)  # Push the element onto the stack
            else:  # If the line is a token
                toks.append(line)  # Add the token to the list
                tok_count += 1  # Increment the token counter
        except IndexError:  # Handle potential index errors
            toks.append(line)  # Add the token to the list
            tok_count += 1  # Increment the token counter

    return toks, complete_elts  # Return the tokens and complete elements


def render_html(toks, elts, directives, config_name):
    """
    Renders HTML from tokens, elements, directives

    Args:
        toks (list of str): A list of token strings.
        elts (list): A list of elements.
        directives (list): A list of directives to apply.

    Returns:
        str: The rendered HTML string.
    """
    # Separate token directives and other directives, reversing their order
    tok_directives = list(
        reversed([d for d in directives if isinstance(d, TokDirective)])
    )
    other_directives = list(
        reversed([d for d in directives if not isinstance(d, TokDirective)])
    )

    # Apply token directives to tokens
    for directive in tok_directives:
        for i, tok in enumerate(toks):
            if directive.applies(tok):
                toks[i] = directive.apply_left(tok, tok)
                toks[i] = directive.apply_right(tok, tok)
    if len(tok_directives) == 0:
        toks = [""] * len(toks)

    # Split elements into separate lists of equivalent length to ensure correct tag order
    if elts:
        elt_lens = [len(elt) for elt in elts]
        elts_by_len = [[] for i in range(max(elt_lens) + 1)]
        for i, elt in enumerate(elts):
            elts_by_len[elt_lens[i]].append(elt)
        for elts in elts_by_len:
            if len(elts) == 0:
                continue
            for directive in other_directives:
                for elt in elts:
                    if directive.applies(elt):
                        toks[elt.open_line] = directive.apply_left(
                            elt, toks[elt.open_line]
                        )
                        toks[elt.close_line] = directive.apply_right(
                            elt, toks[elt.close_line]
                        )

    # Join tokens with HTML comment to form the final HTML
    inner_html = "".join(toks)
    html = f'<div class="htmlvis {config_name}">{inner_html}</div>'

    return html


DEBUG = False


def generate_visualization(config_name, text ):
    if DEBUG:
        with open("htmlvis_latest_config_text.txt", "w") as f:
            f.write( HTML_CONFIGS[config_name])
        with open("htmlvis_latest_text.txt", "w") as f:
            f.write(text)
    directives = parse_config( HTML_CONFIGS[config_name])
    toks, elts = parse_text(text)

    return render_html(toks, elts, directives,config_name)


if __name__ == "__main__":
    from argparse import ArgumentParser
    import os

    os.environ["DJANGO_SETTINGS_MODULE"] = "coptic.settings"
    p = ArgumentParser()
    p.add_argument("config_text", default="htmlvis_latest_config_text.txt")
    p.add_argument("text", default="htmlvis_latest_text.txt")
    args = p.parse_args()
    with open(args.config_text) as f:
        config_text = f.read()
    with open(args.text) as f:
        text = f.read()

    import cProfile, io, pstats

    pr = cProfile.Profile()
    pr.enable()
    pr.run("output = generate_visualization(config_text, text, '')")
    pr.disable()
    ps = pstats.Stats(pr).sort_stats("cumtime")
    ps.print_stats()
