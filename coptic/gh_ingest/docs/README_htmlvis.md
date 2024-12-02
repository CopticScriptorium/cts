# HTML Visualization Generator

This module re-implements ANNIS's HTML visualization as described in the [ANNIS HTML Visualization Guide](http://corpus-tools.org/annis/resources/ANNIS_HTML_Vis_Guide.pdf). The `generate_visualization` function consumes TreeTagger SGML text and renders it into HTML according to an ANNIS HTML visualization configuration file.

## High-Level Overview

The `htmlvis.py` module is designed to transform SGML text into HTML using a set of configurable rules. This allows for the visualization of annotated corpora in a web-friendly format. The transformation process is controlled by configuration files and CSS files, which are specific to each corpus.

### Key Components

1. **Configuration Files**: Define how SGML tags are transformed into HTML elements.
2. **CSS Files**: Provide styling for the generated HTML elements.
3. **SGML Text**: The input text that contains the annotations to be visualized.

### Usage

To use the HTML visualization generator, you need to provide:
- A configuration file that specifies the transformation rules.
- An SGML text file that contains the annotated corpus.
- An optional CSS file for styling the HTML output.

### Example

Here is an example of how to use the `generate_visualization` function:

```python
from htmlvis import generate_visualization

config_text = """
chapter_n	div:chapter; style="chapter"	value
translation div:trans; style="translation"	value
verse_n	div:verse; style="verse"	value
identity	div; style="named"	
entity	div:entity_type; style="entity"	value
identity	div; style="identity"	"<a href='https://en.wikipedia.org/wiki/%%value%%' title='%%value%%' class='wikify' target='__new'></a>"
norm_group	i; style="copt_word"
norm	ruby; style="norm"
lemma	NULL	"<a href='https://coptic-dictionary.org/results.cgi?quick_search=%%value%%' target='_new'>"
norm	NULL	"%%value%%"
pos	NULL	"</a>"
pos	rt:pos; style="pos"	value
pb_xml_id	q:page; style="page"	value
"""

sgml_text = """
<chapter_n>1</chapter_n>
<verse_n>1</verse_n>
<norm_group>ⲥⲉⲛⲟⲩⲑⲓⲟⲩ</norm_group>
<entity entity_type="person">ⲁⲃⲣⲁϩⲁⲙ</entity>
<translation trans="This is a translation."></translation>
"""

css_text = """
div.htmlvis {
    font-family: Antinoou, sans-serif; width: 500px; white-space: normal !important;
}
.entity_list { background-color: #ffffb4; font-style: italic; width: 100%; margin-bottom: 3px; }
.entity_list:before { content: "Named entities: "; font-weight: bold; font-style: normal; }
.norm { white-space: inherit; }
.norm:after { content: " "; }
.named { display: inline-block; }
.entity { display: inline-block; border: 1px solid; margin-right: 2px; margin-left: 2px; padding-right: 3px; margin-bottom: 2px; margin-top: 2px; }
.named > .entity { border-style: solid !important; background-color: rgba(255, 240, 6, 0.5); }
.entity[entity_type="person"] { border-color: blue !important; outline-color: black !important; }
.entity[entity_type="place"] { border-color: red !important; outline-color: black !important; }
/* Additional CSS rules omitted for brevity */
"""

html = generate_visualization(config_text, sgml_text, css_text)
print(html)