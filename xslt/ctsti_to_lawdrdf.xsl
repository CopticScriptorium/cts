<?xml version="1.0" encoding="UTF-8"?>
<!-- This Stylesheet converts the Coptic Scriptorium CTS TextInventory from XML to 
     an equivalent RDF/XML representation the LAWD ontology --> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:lawd="http://lawd.info/ontology/"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:cs="http://copticscriptorium.org"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:cts="http://chs.harvard.edu/xmlns/cts"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dct="http://purl.org/dc/terms/"
    exclude-result-prefixes="xs"
    version="2.0">
    
    <xsl:output method="xml" indent="yes"/>
    <xsl:variable name="baseurl" select="'http://copticscriptorium.org/'"/>
    <xsl:template match="/">
        <rdf:RDF>
            <!-- TODO ideally the textgroups would also be included in the 
                 RDF representation but we need to have identifiers for the authors
                 and a decision about how to represent the relationship between 
                 CTS textgroups and authors 
            -->
            <xsl:apply-templates select="//cts:work"/>
        </rdf:RDF>
    </xsl:template>
    
    <xsl:template match="cts:work">
        <xsl:variable name="lang">
            <xsl:call-template name="fix_lang_code">
                <xsl:with-param name="lang" select="cts:title/@xml:lang"/>
            </xsl:call-template>
        </xsl:variable>
        <rdf:Description rdf:about="{concat($baseurl,@urn)}">
            <rdf:type rdf:resource="http://lawd.info/ontology/ConceptualWork"></rdf:type>
            <dc:title xml:lang="{$lang}"><xsl:value-of select="cts:title"></xsl:value-of></dc:title>
        </rdf:Description>
        <xsl:apply-templates select="cts:edition|cts:translation"/>
    </xsl:template>
    
    <xsl:template match="cts:edition|cts:translation">
        <xsl:variable name="lang">
            <xsl:call-template name="fix_lang_code">
                <xsl:with-param name="lang" select="cts:label/@xml:lang"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="edition">http://lawd.info/ontology/Edition</xsl:variable>
        <xsl:variable name="type">
            <xsl:choose>
                <xsl:when test="local-name(.) = 'edition'">http://lawd.info/ontology/WrittenWork</xsl:when>
                <xsl:otherwise>http://lawd.info/ontology/Translation</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <rdf:Description rdf:about="{concat($baseurl,@urn)}">
            <rdf:type rdf:resource="{$type}"></rdf:type>
            <rdfs:label xml:lang="{$lang}"><xsl:value-of select="cts:label"></xsl:value-of></rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
        </rdf:Description>
        <!-- This is Coptic Scriptorium specific - we want to represent for each conceptualization of the 
             written work visualizations of the diplomatic, normalized, tei and html as separate LAWD 'editions' -->
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/relannis')}">
            <rdf:type rdf:resource="{$edition}"></rdf:type>
            <rdfs:label xml:lang="{$lang}"><xsl:value-of select="cts:label"></xsl:value-of> (relAnnis representation)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
            <dct:source rdf:resource="{concat($baseurl,@urn)}"/>
        </rdf:Description>
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/annis')}">
            <rdf:type rdf:resource="{$edition}"></rdf:type>
            <rdfs:label xml:lang="{$lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Annis representation)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
            <dct:source rdf:resource="{concat($baseurl,@urn)}"/>
        </rdf:Description>
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/tei/xml')}">
            <rdf:type rdf:resource="{$edition}"></rdf:type>
            <rdfs:label xml:lang="{$lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Diplomatic XML representation)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
            <dct:source rdf:resource="{concat($baseurl,@urn)}"/> 
        </rdf:Description>
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/paula/xml')}">
            <rdf:type rdf:resource="{$edition}"></rdf:type>
            <rdfs:label xml:lang="{$lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Normalized XML representation)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
            <dct:source rdf:resource="{concat($baseurl,@urn)}"/>
        </rdf:Description>
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/dipl/html')}">
            <rdf:type rdf:resource="{$edition}"></rdf:type>
            <rdfs:label xml:lang="{$lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Diplomatic HTML representation)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
            <dct:source rdf:resource="{concat($baseurl,@urn)}"/>
        </rdf:Description>
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/norm/html')}">
            <rdf:type rdf:resource="{$edition}"></rdf:type>
            <rdfs:label xml:lang="{$lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Normalized HTML representation)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
            <dct:source rdf:resource="{concat($baseurl,@urn)}"/>
        </rdf:Description>
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/analytic/html')}">
            <rdf:type rdf:resource="{$edition}"></rdf:type>
            <rdfs:label xml:lang="{$lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Analytic HTML representation)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
            <dct:source rdf:resource="{concat($baseurl,@urn)}"/>
        </rdf:Description>
    </xsl:template>
    
    <xsl:template name="fix_lang_code">
        <xsl:param name="lang"/>
        <!-- this is a bit of a hack .. RDF wants 2 letter lang codes when they are available, but
             CTS wants the 3 letter codes.  This needs to be improved to do the right thing for
             languages other than English 
        -->
        <xsl:choose>
            <xsl:when test="$lang='eng'">
                <xsl:value-of select="'en'"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$lang"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>