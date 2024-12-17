import unittest

from gh_ingest.htmlvis import (
    generate_visualization,
    HtmlGenerationException,
    Directive,
    TokDirective,
    AnnDirective,
    ValueDirective,
    AnnAndValueDirective,
    SgmlElement,
    parse_config,
    parse_text,
    render_html,
    TriggerTypes,
    ContentTypes,
)


class TestHtmlVis(unittest.TestCase):

    def test_generate_visualization(self):
        config_text = 'tok\tspan\t"word"\nlemma\tb\tvalue'
        text = "<lemma>word1\nword2\n</lemma>"
        css_text = "body { font-family: Arial; }"
        expected_output = "<div class=\"htmlvis\"><b>word2</span></b></div><style>\n@font-face {\n\tfont-family: Antinoou;\n\tsrc: url('/static/fonts/antinoou-webfont.woff') format('woff');\n}\nbody { font-family: Arial; }</style>"
        output = generate_visualization(config_text, text, css_text)
        self.assertEqual(output, expected_output)

    def test_parse_config(self):
        config_text = 'tok\tspan\t"word"\nlemma\tb\tvalue'
        directives = parse_config(config_text)
        self.assertEqual(len(directives), 2)
        self.assertIsInstance(directives[0], TokDirective)
        self.assertIsInstance(directives[1], AnnDirective)

    def test_parse_text(self):
        text = """<meta annotation="Author" language="Coptic">
<pb_xml_id pb_xml_id="XL93">
<note note="sample note">
<chapter_n chapter_n="x">
<cb_n cb_n="1">
<lb_n lb_n="1">
<verse_n verse_n="x">
<translation translation="sample translation">
<vid_n vid_n="undetermined">
<arabic arabic="عينة">
<orig_group orig_group="ϭⲟⲗ">
<norm_group norm_group="ϭⲟⲗ">
<entity head_tok="#u1" text="ϭⲟⲗ" entity="abstract">
<orig orig="ϭⲟⲗ">
<norm xml:id="u1" func="root" pos="N" lemma="ϭⲟⲗ" norm="ϭⲟⲗ">
ϭⲟⲗ
</norm>
</orig>
<orig orig="ⲉⲛⲧ">
<norm xml:id="u4" func="mark" head="#u7" pos="CREL" lemma="ⲉⲧⲉⲣⲉ" norm="ⲉⲛⲧ">
ⲉⲛⲧ
</norm>
</orig>
</entity>
</norm_group>
</orig_group>
</vid_n>
</arabic>
</translation>
</verse_n>
</lb_n>
</cb_n>
</chapter_n>
</note>
</pb_xml_id>
</meta>"""
        toks, elts = parse_text(text)
        self.assertEqual(toks, ["ϭⲟⲗ", "ⲉⲛⲧ"])
        self.assertEqual(len(elts), 26)
        self.assertEqual(elts[0].name, "norm")
        self.assertEqual(elts[1].name, "func")
        self.assertEqual(elts[2].name, "pos")
        self.assertEqual(elts[3].name, "lemma")

    def test_render_html(self):
        toks = ["ϭⲟⲗ", "ⲉⲛⲧ"]
        elts = [
            SgmlElement(
                "norm",
                [
                    ("open_line", "0"),
                    ("close_line", "0"),
                    ("xml:id", "u1"),
                    ("norm", "ϭⲟⲗ"),
                ],
            ),
            SgmlElement(
                "func", [("open_line", "0"), ("close_line", "0"), ("func", "root")]
            ),
            SgmlElement("pos", [("open_line", "0"), ("close_line", "0"), ("pos", "N")]),
            SgmlElement(
                "lemma", [("open_line", "0"), ("close_line", "0"), ("lemma", "ϭⲟⲗ")]
            ),
        ]
        directives = [
            AnnDirective("pb_xml_id", 'table:title; style="pb"', "value"),
            AnnDirective("pb_xml_id", "tr", ""),
            AnnDirective("cb_n", 'td; style="cb"', ""),
            AnnDirective("lb_n", 'div:line; style="copt_line"', "value"),
            AnnDirective("hi_rend", "hi_rend:rend", "value"),
            TokDirective("tok", "span", "value"),
            AnnDirective("orig_word", "a", '" "'),
        ]

        expected_output = '<div class="htmlvis">ϭⲟⲗ</span>ⲉⲛⲧ</span></div>'
        output = render_html(toks, elts, directives)
        self.assertEqual(output, expected_output)

    def test_directive_parse_triggering_condition(self):
        result = Directive.parse_triggering_condition("tok")
        self.assertEqual(result, {"type": TriggerTypes.TOK})

    def test_directive_parse_generated_element(self):
        result = Directive.parse_generated_element("span;color:red")
        self.assertEqual(result, {"name": "span", "attr": ""})

    def test_directive_parse_content(self):
        result = Directive.parse_content('"word"')
        self.assertEqual(result, {"type": ContentTypes.STRING, "value": "word"})
 
    def test_apply_left_tok_directive(self):
        directive = TokDirective("tok", "span")
        result = directive.apply_left("token", "text")
        self.assertEqual(result, "<span>text")

    def test_apply_left_ann_directive(self):
        elt = SgmlElement("title", [("title", "Test Title")])
        directive = AnnDirective("title", "span", "value")
        result = directive.apply_left(elt, "text")
        self.assertEqual(result, '<span>Test Titletext')

    def test_apply_left_value_directive(self):
        elt = SgmlElement("norm", [("norm", "God")])
        directive = ValueDirective('="God"', "span", "value")
        result = directive.apply_left(elt, "text")
        self.assertEqual(result, '<span>Godtext')

    def test_apply_left_ann_and_value_directive(self):
        elt = SgmlElement("norm", [("norm", "God")])
        directive = AnnAndValueDirective("norm=God", "span", "value")
        result = directive.apply_left(elt, "text")
        self.assertEqual(result, '<span>Godtext')


if __name__ == "__main__":
    unittest.main()
