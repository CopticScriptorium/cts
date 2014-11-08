LOD (Linked Open Data) Implementation Details
===

## Persistent Identifiers

Coptic Scriptorium uses [CTS URNs](http://www.homermultitext.org/hmt-docs/specifications/ctsurn/) to provide persistent, machine-independent, identifiers for the texts in its corpus. It combines these with a URL prefix and format postfixes to provide stable, Linked-Data friendly URIs for the texts.

The scheme used is as follows:

Format-independent identifier for a text:

`http://copticscriptorium.org/<CTSURN>`

Visualization and Format specific identifiers for texts:

__Visualization__ | __Format__ | __URI__
--- | --- | ---
Diplomatic | TEI XML | `http://copticscriptorium.org/<CTSURN>/dipl/xml`
Diplomatic | HTML | `http://copticscriptorium.org/<CTSURN>/dipl/html`
Normalized | TEI XML | `http://copticscriptorium.org/<CTSURN>/norm/xml`
Normalized | HTML | `http://copticscriptorium.org/<CTSURN>/norm/html`
Analytical | TEI XML | `http://copticscriptorium.org/<CTSURN>/ana/xml`
Analytical | HTML | `http://copticscriptorium.org/<CTSURN>/ana/html`

## Versioning

Coptic Scriptorium uses the *exemplar* component of a CTS URN to identify specific versions of a text.  At the point of "publication" (exact meaning of this TBD), new URNs will be minted for the Coptic Scriptorium texts with either a datetime stamp or a Git commit hash to represent the version information.

Note that Coptic Scriptorium commits to not changing the representation of a text identified by a specific exemplar (i.e. versioned) URN, but it may not provide online access to the texts represented by those versions for perpetuity. It will however always redirect a request for a specific exemplar to a more recent version of the text, if the specifically requested exemplar is no longer available on via the Coptic Scriptorium online publication site. (See below under HTTP Responses for additional details.)

An example of a versioned exemplar URN for a Coptic Scriptorium text might be:

`urn:cts:copticLit:shenoute.A22.MONB_YA.20141108T000000Z`

## Vocabulary

Relationships between the texts in the Coptic Scriptorium corpus are described using the [LAWD Ontology](https://github.com/lawdi/LAWD).

## HTTP Responses

Coptic Scriptorium uses the [303 URI approach](http://linkeddatabook.com/editions/1.0/#htoc12) to resolve requests for texts identified by the persistent URIs described above.

A request for a text without reference to a specific exemplar will return an HTTP 303 response which redirects the browser or requesting client application to the most recent version of the text.  Requests for texts without specification of the format will return the most recent HTML diplomatic version of a text.

Example requests, HTTP status code and returned representation are provided below.

__URI__ | __HTTP Response Status__ | __Returned Representation__
--- | --- | ---
http://copticscriptorium.org/urn:cts:copticLit:shenoute.A22.MONB_YA | 303 | Most recent version of the diplomatic HTML edition of the text
http://copticscriptorium.org/urn:cts:copticLit:shenoute.A22.MONB_YA.YYYYMMDDTHHMMSSZ | 303 | HTML representation of either the requested exemplar (or if no longer example, the most recent version) of the diplomatic HTML edition of the text
http://copticscriptorium.org/urn:cts:copticLit:shenoute.A22.MONB_YA.YYYYMMDDTHHMMSSZ/dipl/xml | 200 or 303 | the TEI XML representation of either the requested exemplar (with status 200) or the most recent version (with status 303)
http://copticscriptorium.org/urn:cts:copticLit:shenoute.A22.MONB_YA/norm/html | 303 | Most recent version of the normalized HTML edition of the text


## CTS API and Citation/Passage Requests

TBD



