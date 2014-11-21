Data Citation/Linking User Stories
===


__story:__ 1. As a researcher I want to cite HTML normalized visualizations in my publication. 

__data model:__ `http://copticscriptorium.org/<CTSURN>/norm/html`

__fulfilled?:__ yes 

---

__story:__ 2. As a researcher I want to link from the HTML normalized or analytic visualizations to the corresponding location in the diplomatic visualization to check the analysis/normalization. 

__data model:__ the identifiers  `http://copticscriptorium.org/<CTSURN>/norm/html`, `http://copticscriptorium.org/<CTSURN>/norm/ana`, ``http://copticscriptorium.org/<CTSURN>/dipl/html` and `dct:source` relationship linking these to the same source 

__fulfilled?:__ partially - may also require passage level citation scheme and alignment of this across visualizations

---

__story:__ 3. As a researcher I want to search for all forms of a dictionary headword in a text or the entire corpus and cite its occurence in the specific version viewed of the text (where "text" means e.g. the LAWD written work or CTS edition).

__data model:__ the identifiers `http://copticscriptorium.org/<CTSURN>`,  `http://copticscriptorium.org/<CTSURN>/norm/html`, `http://copticscriptorium.org/<CTSURN>/norm/ana`, `http://copticscriptorium.org/<CTSURN>/dipl/html`

__fulfilled?:__ partially - may also require passage level citation scheme and support for subreferences

---

__story:__ 4. As a researcher I want to search for all occurences of a specific POS tag or tags in a text or the entire corpus and cite its occurence, in the context of the phrase in which it occurs, in the text, accompanied by the details of the query, and the specific annotations consulted.

__data model:__ the identifiers `http://copticscriptorium.org/<CTSURN>`,  `http://copticscriptorium.org/<CTSURN>/norm/html`, `http://copticscriptorium.org/<CTSURN>/norm/ana`, `http://copticscriptorium.org/<CTSURN>/dipl/html`

__fulfilled?:__  partially - may also require passage level citation scheme and support for subreferences; will also require definition and use of a provenance standard (e.g. maybe see https://researchobject.github.io/specifications/bundle/) for query details; may require stable identifiers for the annotations themselves.

---

__story:__ 5. As a researcher I want to search loan words using the lang annotation and download the data in original and normalized form, possibly including lang and pos annotations. 

__data model:__ the identifiers `http://copticscriptorium.org/<CTSURN>`,  `http://copticscriptorium.org/<CTSURN>/norm/html`, `http://copticscriptorium.org/<CTSURN>/norm/ana`, `http://copticscriptorium.org/<CTSURN>/dipl/html`

__fulfilled?:__ partially - may also require passage level citation scheme and support for subreferences;  may require stable identifiers for the annotations themselves.

---

__story:__ 6. As a researcher I want to search for N-grams of either norm, norm_group, or pos in order to analyze style and cite the corpora in which they occur.

__data model:__ the identifiers `http://copticscriptorium.org/<CTSURN>`,  `http://copticscriptorium.org/<CTSURN>/norm/html`, `http://copticscriptorium.org/<CTSURN>/norm/ana`, `http://copticscriptorium.org/<CTSURN>/dipl/html`

__fulfilled?:__ partially - may also require passage level citation scheme and support for subreferences 

---

__story:__ 7. As a researcher I want to identify and cite biblical verses quoted by Shenoute, Besa, or the AP, linking these citations to the original biblical texts in the the Coptic Scriptorium (or other?) corpora.

__data model:__ the identifiers `http://copticscriptorium.org/<CTSURN>`,  `http://copticscriptorium.org/<CTSURN>/norm/html`, `http://copticscriptorium.org/<CTSURN>/norm/ana`, ``http://copticscriptorium.org/<CTSURN>/dipl/html` and the `lawd:embodies` relationship linking the editions to the same work

__fulfilled?:__ partially. - will also require passage level citation scheme 

---

__story:__ 8. As a researcher I want to search for and cite certain markers for Scriptural citation in order to see grammatical parallels.

__data model:__ the identifiers `http://copticscriptorium.org/<CTSURN>`,  `http://copticscriptorium.org/<CTSURN>/norm/html`, `http://copticscriptorium.org/<CTSURN>/norm/ana`, `http://copticscriptorium.org/<CTSURN>/dipl/html` 

__fulfilled?:__ partially - may also require passage level citation scheme and support for subreferences 

---

__story:__ 9. As a researcher I want to cite specific passages I am using so that readers of my publication can use those citations to get directly to the cited passages in the Coptic Scriptorium corpus. 

__data model:__ the identifiers `http://copticscriptorium.org/<CTSURN>`,  `http://copticscriptorium.org/<CTSURN>/norm/html`, `http://copticscriptorium.org/<CTSURN>/norm/ana`, `http://copticscriptorium.org/<CTSURN>/dipl/html` 

__fulfilled?:__ partially - will also require passage level citation scheme

---

