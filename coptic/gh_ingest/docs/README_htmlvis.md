# HTML Visualization Generator

This module re-implements ANNIS's HTML visualization as described in the [ANNIS HTML Visualization Guide](http://corpus-tools.org/annis/resources/ANNIS_HTML_Vis_Guide.pdf). The `generate_visualization` function consumes TreeTagger SGML text and renders it into HTML according to an ANNIS HTML visualization configuration file.

It is actually the heart of the whole implementation.

## High-Level Overview

The `htmlvis.py` module is designed to transform SGML text into HTML using a set of configurable rules. This allows for the visualization of annotated corpora in a web-friendly format. The transformation process is controlled by configuration files and CSS files, which are specific to each corpus.

### Key Components

1. **Configuration Files**: Define how SGML tags are transformed into HTML elements.
2. **CSS Files**: Provide styling for the generated HTML elements.
3. **SGML Text**: The input text that contains the annotations to be visualized.

In the proposed implementation we are using the same configuration files and css files for all visualisations.

### Usage

To use the HTML visualization generator, you need to provide:
- An TT text file that contains the annotated corpus.

These are now in the settings/base.py:
- An optional CSS file for styling the HTML output.
- A configuration file that specifies the transformation rules.

The transformations passes through an intermediate internal SGML representation.

So the source could look like:
```tt
<meta annotation="Nina Speranskaja, Nicholas Wagner, Amir Zeldes" chapter="01" corpus="bohairic.nt" document_cts_urn="urn:cts:copticLit:nt.matt.bohairic:01" entities="none" identities="none" languages="Bohairic Coptic" license="&lt;a href=\'https://creativecommons.org/licenses/by-sa/4.0/\'&gt;CC-BY-SA&lt;/a&gt;" parsing="automatic" project="Coptic SCRIPTORIUM" segmentation="automatic" source="&lt;a href=\'https://marcion.sourceforge.net/\'&gt;Marcion&lt;a&gt;, Hany Takla" tagging="automatic" title="01_Matthew_01" translation="World English Bible (WEB)" version_date="2024-10-31" version_n="6.0.0">
<verse_n verse_n="1">
<translation translation="The book of the genealogy of Jesus Christ, the son of David, the son of Abraham.">
<orig_group orig_group="ⲡϫⲱⲙ">
<norm_group norm_group="ⲡϫⲱⲙ">
<orig orig="ⲡ">
<norm xml:id="u1" func="det" head="#u2" new_sent="true" pos="ART" lemma="ⲡ" norm="ⲡ">
ⲡ
</norm>
</orig>
<orig orig="ϫⲱⲙ">
<norm xml:id="u2" func="root" pos="N" lemma="ϫⲱⲙ" norm="ϫⲱⲙ">
ϫⲱⲙ
</norm>
</orig>
</norm_group>
</orig_group>
<orig_group orig_group="ⲙⲙⲓⲥⲓ">
<norm_group norm_group="ⲙⲙⲓⲥⲓ">
<orig orig="ⲙ">
<norm xml:id="u3" func="case" head="#u4" pos="PREP" lemma="ⲛ" norm="ⲙ">
ⲙ
</norm>
</orig>
<orig orig="ⲙⲓⲥⲓ">
<norm xml:id="u4" func="nmod" head="#u2" pos="N" lemma="ⲙⲓⲥⲓ" norm="ⲙⲓⲥⲓ">
ⲙⲓⲥⲓ
</norm>
</orig>
</norm_group>
</orig_group>
<orig_group orig_group="ⲛⲧⲉⲓⲏⲥⲟⲩⲥ">
<norm_group norm_group="ⲛⲧⲉⲓⲏⲥⲟⲩⲥ">
<orig orig="ⲛⲧⲉ">
<norm xml:id="u5" func="case" head="#u6" pos="PREP" lemma="ⲛⲧⲉ" norm="ⲛⲧⲉ">
ⲛⲧⲉ
</norm>
</orig>
<orig orig="ⲓⲏⲥⲟⲩⲥ">
<norm xml:id="u6" func="nmod" head="#u2" pos="NPROP" lemma="ⲓⲏⲥⲟⲩⲥ" norm="ⲓⲏⲥⲟⲩⲥ">
<lang lang="Hebrew">
ⲓⲏⲥⲟⲩⲥ
</lang>
</norm>
</orig>
</norm_group>
</orig_group>
<orig_group orig_group="ⲡⲭⲣⲓⲥⲧⲟⲥ">
<norm_group norm_group="ⲡⲭⲣⲓⲥⲧⲟⲥ">
<orig orig="ⲡ">
<norm xml:id="u7" func="det" head="#u8" pos="ART" lemma="ⲡ" norm="ⲡ">
ⲡ
</norm>
</orig>
<orig orig="ⲭⲣⲓⲥⲧⲟⲥ">
<norm xml:id="u8" func="appos" head="#u6" pos="N" lemma="ⲭⲣⲓⲥⲧⲟⲥ" norm="ⲭⲣⲓⲥⲧⲟⲥ">
<lang lang="Greek">
ⲭⲣⲓⲥⲧⲟⲥ
</lang>
</norm>
</orig>
</norm_group>
</orig_group>
```

It would internally be transformed into an array of SGML elements:

```
[<SgmlElement="norm" open_line="0" close_line="0" xml:id="u1" norm="ⲡ">, <SgmlElement="func" open_line="0" close_line="0" func="det">, <SgmlElement="head" open_line="0" close_line="0" head="#u2">, <SgmlElement="new_sent" open_line="0" close_line="0" new_sent="true">, <SgmlElement="pos" open_line="0" close_line="0" pos="ART">, <SgmlElement="lemma" open_line="0" close_line="0" lemma="ⲡ">, <SgmlElement="orig" open_line="0" close_line="0" orig="ⲡ">, <SgmlElement="norm" open_line="1" close_line="1" xml:id="u2" norm="ϫⲱⲙ">, <SgmlElement="func" open_line="1" close_line="1" func="root">, <SgmlElement="pos" open_line="1" close_line="1" pos="N">, <SgmlElement="lemma" open_line="1" close_line="1" lemma="ϫⲱⲙ">, <SgmlElement="orig" open_line="1" close_line="1" orig="ϫⲱⲙ">, <SgmlElement="norm_group" open_line="0" close_line="1" norm_group="ⲡϫⲱⲙ">, <SgmlElement="orig_group" open_line="0" close_line="1" orig_group="ⲡϫⲱⲙ">, <SgmlElement="norm" open_line="2" close_line="2" xml:id="u3" norm="ⲙ">, <SgmlElement="func" open_line="2" close_line="2" func="case">, <SgmlElement="head" open_line="2" close_line="2" head="#u4">, <SgmlElement="pos" open_line="2" close_line="2" pos="PREP">, <SgmlElement="lemma" open_line="2" close_line="2" lemma="ⲛ">, <SgmlElement="orig" open_line="2" close_line="2" orig="ⲙ">, <SgmlElement="norm" open_line="3" close_line="3" xml:id="u4" norm="ⲙⲓⲥⲓ">, <SgmlElement="func" open_line="3" close_line="3" func="nmod">, <SgmlElement="head" open_line="3" close_line="3" head="#u2">, <SgmlElement="pos" open_line="3" close_line="3" pos="N">, <SgmlElement="lemma" open_line="3" close_line="3" lemma="ⲙⲓⲥⲓ">, <SgmlElement="orig" open_line="3" close_line="3" orig="ⲙⲓⲥⲓ">, <SgmlElement="norm_group" open_line="2" close_line="3" norm_group="ⲙⲙⲓⲥⲓ">, <SgmlElement="orig_group" open_line="2" close_line="3" orig_group="ⲙⲙⲓⲥⲓ">, <SgmlElement="norm" open_line="4" close_line="4" xml:id="u5" norm="ⲛⲧⲉ">, <SgmlElement="func" open_line="4" close_line="4" func="case">, <SgmlElement="head" open_line="4" close_line="4" head="#u6">, <SgmlElement="pos" open_line="4" close_line="4" pos="PREP">, <SgmlElement="lemma" open_line="4" close_line="4" lemma="ⲛⲧⲉ">, <SgmlElement="orig" open_line="4" close_line="4" orig="ⲛⲧⲉ">, <SgmlElement="lang" open_line="5" close_line="5" lang="Hebrew">, <SgmlElement="norm" open_line="5" close_line="5" xml:id="u6" norm="ⲓⲏⲥⲟⲩⲥ">, <SgmlElement="func" open_line="5" close_line="5" func="nmod">, <SgmlElement="head" open_line="5" close_line="5" head="#u2">, <SgmlElement="pos" open_line="5" close_line="5" pos="NPROP">, <SgmlElement="lemma" open_line="5" close_line="5" lemma="ⲓⲏⲥⲟⲩⲥ">, <SgmlElement="orig" open_line="5" close_line="5" orig="ⲓⲏⲥⲟⲩⲥ">, <SgmlElement="norm_group" open_line="4" close_line="5" norm_group="ⲛⲧⲉⲓⲏⲥⲟⲩⲥ">, <SgmlElement="orig_group" open_line="4" close_line="5" orig_group="ⲛⲧⲉⲓⲏⲥⲟⲩⲥ">, <SgmlElement="norm" open_line="6" close_line="6" xml:id="u7" norm="ⲡ">, <SgmlElement="func" open_line="6" close_line="6" func="det">, <SgmlElement="head" open_line="6" close_line="6" head="#u8">, <SgmlElement="pos" open_line="6" close_line="6" pos="ART">, <SgmlElement="lemma" open_line="6" close_line="6" lemma="ⲡ">, <SgmlElement="orig" open_line="6" close_line="6" orig="ⲡ">, <SgmlElement="lang" open_line="7" close_line="7" lang="Greek">, <SgmlElement="norm" open_line="7" close_line="7" xml:id="u8" norm="ⲭⲣⲓⲥⲧⲟⲥ">, <SgmlElement="func" open_line="7" close_line="7" func="appos">, <SgmlElement="head" open_line="7" close_line="7" head="#u6">, <SgmlElement="pos" open_line="7" close_line="7" pos="N">, <SgmlElement="lemma" open_line="7" close_line="7" lemma="ⲭⲣⲓⲥⲧⲟⲥ">, <SgmlElement="orig" open_line="7" close_line="7" orig="ⲭⲣⲓⲥⲧⲟⲥ">, <SgmlElement="norm_group" open_line="6" close_line="7" norm_group="ⲡⲭⲣⲓⲥⲧⲟⲥ">, <SgmlElement="orig_group" open_line="6" close_line="7" orig_group="ⲡⲭⲣⲓⲥⲧⲟⲥ">, <SgmlElement="norm" open_line="8" close_line="8" xml:id="u9" norm="ⲡ">, ...]
```

The parse_text method returns tokens and elements

While the render_html(toks, elts, directives) takes in those with directives.
It then separates token directives and other directives, reversing their order.
It then iterates over the tokens. This the toks (tokens) array.
And for each applies a left and a right part. Mutating each tok.
Afterwards it iterates over the SGML elements and then applies other_directives to the tokens array -

**Probably** wrapping a "group" that has open_line and a close so this slowly becomes an array of HTML elements that will be joined.

So this becomes an array such as the following:
['<div class="translation" trans="The book of the genealogy of Jesus Christ, the son of David, the son of Abraham."><div class="verse" verse="1"><i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲡ\' target=\'_new\'>ⲡ</a><rt class="pos" pos="ART"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ϫⲱⲙ\' target=\'_new\'>ϫⲱⲙ</a><rt class="pos" pos="N"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲛ\' target=\'_new\'>ⲙ</a><rt class="pos" pos="PREP"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲙⲓⲥⲓ\' target=\'_new\'>ⲙⲓⲥⲓ</a><rt class="pos" pos="N"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲛⲧⲉ\' target=\'_new\'>ⲛⲧⲉ</a><rt class="pos" pos="PREP"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲓⲏⲥⲟⲩⲥ\' target=\'_new\'>ⲓⲏⲥⲟⲩⲥ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲡ\' target=\'_new\'>ⲡ</a><rt class="pos" pos="ART"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲭⲣⲓⲥⲧⲟⲥ\' target=\'_new\'>ⲭⲣⲓⲥⲧⲟⲥ</a><rt class="pos" pos="N"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲡ\' target=\'_new\'>ⲡ</a><rt class="pos" pos="ART"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ϣⲏⲣⲓ\' target=\'_new\'>ϣⲏⲣⲓ</a><rt class="pos" pos="N"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲛ\' target=\'_new\'>ⲛ</a><rt class="pos" pos="PREP"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲇⲁⲩⲓⲇ\' target=\'_new\'>ⲇⲁⲩⲓⲇ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲡ\' target=\'_new\'>ⲡ</a><rt class="pos" pos="ART"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ϣⲏⲣⲓ\' target=\'_new\'>ϣⲏⲣⲓ</a><rt class="pos" pos="N"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲛ\' target=\'_new\'>ⲛ</a><rt class="pos" pos="PREP"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲁⲃⲣⲁⲁⲙ\' target=\'_new\'>ⲁⲃⲣⲁⲁⲙ</a><rt class="pos" pos="N"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=.\' target=\'_new\'>.</a><rt class="pos" pos="PUNCT"></rt></ruby></i></div></div>', '<div class="translation" trans="Abraham became the father of Isaac. Isaac became the father of Jacob. Jacob became the father of Judah and his brothers."><div class="verse" verse="2"><i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲁⲃⲣⲁⲁⲙ\' target=\'_new\'>ⲁⲃⲣⲁⲁⲙ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲇⲉ\' target=\'_new\'>ⲇⲉ</a><rt class="pos" pos="PTC"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲁ\' target=\'_new\'>ⲁ</a><rt class="pos" pos="APST"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲛⲑⲟϥ\' target=\'_new\'>ϥ</a><rt class="pos" pos="PPERS"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ϫⲫⲟ\' target=\'_new\'>ϫⲫⲉ</a><rt class="pos" pos="V"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲓⲥⲁⲁⲕ\' target=\'_new\'>ⲓⲥⲁⲁⲕ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲓⲥⲁⲁⲕ\' target=\'_new\'>ⲓⲥⲁⲁⲕ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲇⲉ\' target=\'_new\'>ⲇⲉ</a><rt class="pos" pos="PTC"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲁ\' target=\'_new\'>ⲁ</a><rt class="pos" pos="APST"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲛⲑⲟϥ\' target=\'_new\'>ϥ</a><rt class="pos" pos="PPERS"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ϫⲫⲟ\' target=\'_new\'>ϫⲫⲉ</a><rt class="pos" pos="V"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲓⲁⲕⲱⲃ\' target=\'_new\'>ⲓⲁⲕⲱⲃ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲓⲁⲕⲱⲃ\' target=\'_new\'>ⲓⲁⲕⲱⲃ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲇⲉ\' target=\'_new\'>ⲇⲉ</a><rt class="pos" pos="PTC"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲁ\' target=\'_new\'>ⲁ</a><rt class="pos" pos="APST"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲛⲑⲟϥ\' target=\'_new\'>ϥ</a><rt class="pos" pos="PPERS"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ϫⲫⲟ\' target=\'_new\'>ϫⲫⲉ</a><rt class="pos" pos="V"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲓⲟⲩⲇⲁⲥ\' target=\'_new\'>ⲓⲟⲩⲇⲁⲥ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲛⲉⲙ\' target=\'_new\'>ⲛⲉⲙ</a><rt class="pos" pos="PREP"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲡⲉϥ\' target=\'_new\'>ⲛⲉϥ</a><rt class="pos" pos="PPOS"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲥⲟⲛ\' target=\'_new\'>ⲥⲛⲏⲟⲩ</a><rt class="pos" pos="N"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=.\' target=\'_new\'>.</a><rt class="pos" pos="PUNCT"></rt></ruby></i></div></div>', '<div class="translation" trans="Judah became the father of Perez and Zerah by Tamar. Perez became the father of Hezron. Hezron became the father of Ram."><div class="verse" verse="3"><i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲓⲟⲩⲇⲁⲥ\' target=\'_new\'>ⲓⲟⲩⲇⲁⲥ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲇⲉ\' target=\'_new\'>ⲇⲉ</a><rt class="pos" pos="PTC"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲁ\' target=\'_new\'>ⲁ</a><rt class="pos" pos="APST"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲛⲑⲟϥ\' target=\'_new\'>ϥ</a><rt class="pos" pos="PPERS"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ϫⲫⲟ\' target=\'_new\'>ϫⲫⲉ</a><rt class="pos" pos="V"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲫⲁⲣⲉⲥ\' target=\'_new\'>ⲫⲁⲣⲉⲥ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲛⲉⲙ\' target=\'_new\'>ⲛⲉⲙ</a><rt class="pos" pos="PREP"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲍⲁⲣⲁ\' target=\'_new\'>ⲍⲁⲣⲁ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲉⲃⲟⲗ\' target=\'_new\'>ⲉⲃⲟⲗ</a><rt class="pos" pos="ADV"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ϧⲉⲛ\' target=\'_new\'>ϧⲉⲛ</a><rt class="pos" pos="PREP"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲑⲁⲙⲁⲣ\' target=\'_new\'>ⲑⲁⲙⲁⲣ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲫⲁⲣⲉⲥ\' target=\'_new\'>ⲫⲁⲣⲉⲥ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲇⲉ\' target=\'_new\'>ⲇⲉ</a><rt class="pos" pos="PTC"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲁ\' target=\'_new\'>ⲁ</a><rt class="pos" pos="APST"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲛⲑⲟϥ\' target=\'_new\'>ϥ</a><rt class="pos" pos="PPERS"></rt></ruby>', '<ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ϫⲫⲟ\' target=\'_new\'>ϫⲫⲉ</a><rt class="pos" pos="V"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲉⲥⲣⲱⲙ\' target=\'_new\'>ⲉⲥⲣⲱⲙ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=.\' target=\'_new\'>.</a><rt class="pos" pos="PUNCT"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲉⲥⲣⲱⲙ\' target=\'_new\'>ⲉⲥⲣⲱⲙ</a><rt class="pos" pos="NPROP"></rt></ruby></i>', '<i class="copt_word"><ruby class="norm"><a href=\'https://coptic-dictionary.org/results.cgi?quick_search=ⲇⲉ\' target=\'_new\'>ⲇⲉ</a><rt class="pos" pos="PTC"></rt></ruby></i>', ...]


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