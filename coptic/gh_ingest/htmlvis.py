"""A re-implementation of ANNIS's htmlvis (http://corpus-tools.org/annis/resources/ANNIS_HTML_Vis_Guide.pdf).
`generate_visualization` consumes TreeTagger SGML text and renders it into HTML according to an ANNIS
htmlvis config file."""

import re
from enum import Enum
from collections import defaultdict


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
                return {"name": text[:colon_index], "attr": text[colon_index + 1 :]}

        name, attrs_text = text[:semicolon_index], text[semicolon_index + 1 :]

        d = {}
        colon_index = text.find(":")
        if colon_index == -1:
            d["name"] = name
        else:
            d["name"] = name[:colon_index]
            d["attr"] = name[colon_index + 1 :]

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
        s = ""
        if self._generated_name != "NULL":
            s = f"<{self._generated_name}"
            if self._generated_class:
                s += f' class="{self._generated_class}"'
            elif self._generated_style:
                s += f' style="{self._generated_style}"'
            s += ">"

        if self._content_type == ContentTypes.STRING:
            s += self._content_value

        return s + text


class AnnDirective(Directive):
    """For a triggering condition like 'title'"""

    def applies(self, elt):
        return elt.name == self._trigger_name

    def apply_left(self, elt, text):
        if self._content_type == ContentTypes.VALUE:
            content = elt.attrs.get(elt.name, "")
        elif self._content_type == ContentTypes.STRING:
            content = self._content_value
            content = content.replace("%%name%%", elt.name)
            content = content.replace("%%value%%", elt.attrs.get(elt.name, ""))
        else:
            content = None

        s = ""
        if self._generated_name != "NULL":
            s = f"<{self._generated_name}"
            if self._generated_class:
                s += f' class="{self._generated_class}"'
            elif self._generated_style:
                s += f' style="{self._generated_style}"'

            if content and self._generated_attr:
                s += f' {self._generated_attr}="{content}">'
            elif content:
                s += ">" + content
            else:
                s += ">"
        elif content:
            s += content

        return s + text


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
            content = elt.attrs.get(self._triggered_attr_name, "")
        elif self._content_type == ContentTypes.STRING:
            content = self._content_value
            content = content.replace("%%name%%", self._triggered_attr_name)
            content = content.replace(
                "%%value%%", elt.attrs.get(self._triggered_attr_name, "")
            )
        else:
            content = None

        s = ""
        if self._generated_name != "NULL":
            s = f"<{self._generated_name}"
            if self._generated_class:
                s += f' class="{self._generated_class}"'
            elif self._generated_style:
                s += f' style="{self._generated_style}"'

            if content and self._generated_attr:
                s += f' {self._generated_attr}="{content}">'
            elif content:
                s += ">" + content
            else:
                s += ">"
        elif content:
            s += content

        return s + text


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
            content = self._content_value
            content = content.replace("%%name%%", self._trigger_name)
            content = content.replace(
                "%%value%%", elt.attrs.get(self._trigger_name, "")
            )
        else:
            content = None

        s = ""
        if self._generated_name != "NULL":
            s = f"<{self._generated_name}"
            if self._generated_class:
                s += f' class="{self._generated_class}"'
            elif self._generated_style:
                s += f' style="{self._generated_style}"'

            if content and self._generated_attr:
                s += f' {self._generated_attr}="{content}">'
            elif content:
                s += ">" + content
            else:
                s += ">"
        else:
            s += content

        return s + text


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


def parse_close_tag(i, line):
    name = re.findall(r"^</([^\s<>/]*)", line)
    if len(name) != 1:
        raise HtmlGenerationException(
            f"Couldn't recognize an SGML element name on closing line {i}:\n\n\t{line}"
        )
    return name[0]


NAME_REGEX = re.compile(r"^<([^\s<>/]*)")
ATTRS_REGEX = re.compile(r'\s([^\s]*)="([^"]*?)"')


def parse_open_tag(i, line, tok_count):
    name = re.findall(NAME_REGEX, line)
    if len(name) != 1:
        raise HtmlGenerationException(
            f"Couldn't recognize an SGML element name on opening line {i}:\n\n\t{line}"
        )
    name = name[0]

    attrs = re.findall(ATTRS_REGEX, line)
    return SgmlElement(name, attrs, tok_count)


def parse_text(text):
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
        to_delete = []
        for attr_name, attr_val in elt.attrs.items():
            if attr_name != elt.name and ":" not in attr_name and elt.name != "meta":
                to_delete.append(attr_name)
                new_elt = SgmlElement(attr_name, [(attr_name, attr_val)])
                new_elt.open_line = elt.open_line
                new_elt.close_line = elt.close_line
                elts.append(new_elt)

        for attr_name in to_delete:
            del elt.attrs[attr_name]

        return elts

    complete_elts = []
    elt_stack = defaultdict(list)

    toks = []
    tok_count = 0

    for i, line in enumerate(text.strip().split("\n")):
        try:
            if line[:2] == "</":
                name = parse_close_tag(i, line)
                elt = elt_stack[name].pop()
                elt.close_line = tok_count - 1
                complete_elts += individuate(elt)
            elif line[0] == "<":
                elt = parse_open_tag(i, line, tok_count)
                elt_stack[elt.name].append(elt)
            else:
                toks.append(line)
                tok_count += 1
        except IndexError:
            toks.append(line)
            tok_count += 1

    return toks, complete_elts


def render_html(toks, elts, directives, css_text):
    tok_directives = list(
        reversed([d for d in directives if isinstance(d, TokDirective)])
    )
    other_directives = list(
        reversed([d for d in directives if not isinstance(d, TokDirective)])
    )

    for directive in tok_directives:
        for i, tok in enumerate(toks):
            if directive.applies(tok):
                toks[i] = directive.apply_left(tok, tok)
                toks[i] = directive.apply_right(tok, tok)
    if len(tok_directives) == 0:
        toks = [""] * len(toks)

    # split elts into separate lists of equivalent length in order of increasing length to ensure
    # we get the right tag order
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

    html = "<!--\n-->".join(toks)
    html = f'<div class="htmlvis">{html}</div>'
    html += f"<style>{css_text}</style>"

    return html


DEBUG = False


def generate_visualization(config_text, text, css_text=""):
    # ensure the font exists
    css_text = (
        """
@font-face {
	font-family: Antinoou;
	src: url('/static/fonts/antinoou-webfont.woff') format('woff');
}
"""
        + css_text
    )
    if DEBUG:
        with open("htmlvis_latest_config_text.txt", "w") as f:
            f.write(config_text)
        with open("htmlvis_latest_text.txt", "w") as f:
            f.write(text)
    directives = parse_config(config_text)
    toks, elts = parse_text(text)

    return render_html(toks, elts, directives, css_text)


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
