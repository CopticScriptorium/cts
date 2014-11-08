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
        <rdf:Description rdf:about="{concat($baseurl,@urn)}">
            <rdf:type rdf:resource="http://lawd.info/ontology/ConceptualWork"></rdf:type>
            <dc:title xml:lang="{cts:title/@xml:lang}"><xsl:value-of select="cts:title"></xsl:value-of></dc:title>
        </rdf:Description>
        <xsl:apply-templates select="cts:edition"/>
    </xsl:template>
    
    <xsl:template match="cts:edition">
        <rdf:Description rdf:about="{concat($baseurl,@urn)}">
            <rdf:type rdf:resource="http://lawd.info/ontology/WrittenWork"></rdf:type>
            <rdfs:label xml:lang="{cts:label/@xml:lang}"><xsl:value-of select="cts:label"></xsl:value-of></rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
        </rdf:Description>
        <!-- This is Coptic Scriptorium specific - we want to represent for each conceptualization of the 
             written work visualizations of the diplomatic, normalized, tei and html as separate LAWD 'editions' -->
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/dipl/xml')}">
            <rdf:type rdf:resource="http://lawd.info/ontology/Edition"></rdf:type>
            <rdfs:label xml:lang="{cts:label/@xml:lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Diplomatic xml XML Edition)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
        </rdf:Description>
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/dipl/html')}">
            <rdf:type rdf:resource="http://lawd.info/ontology/Edition"></rdf:type>
            <rdfs:label xml:lang="{cts:label/@xml:lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Diplomatic HTML Edition)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
        </rdf:Description>
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/norm/xml')}">
            <rdf:type rdf:resource="http://lawd.info/ontology/Edition"></rdf:type>
            <rdfs:label xml:lang="{cts:label/@xml:lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Normalized xml XML Edition)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
        </rdf:Description>
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/norm/html')}">
            <rdf:type rdf:resource="http://lawd.info/ontology/Edition"></rdf:type>
            <rdfs:label xml:lang="{cts:label/@xml:lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Normalized HTML Edition)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
        </rdf:Description>
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/ana/xml')}">
            <rdf:type rdf:resource="http://lawd.info/ontology/Edition"></rdf:type>
            <rdfs:label xml:lang="{cts:label/@xml:lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Analytic xml XML Edition)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
        </rdf:Description>
        <rdf:Description rdf:about="{concat($baseurl,@urn,'/ana/html')}">
            <rdf:type rdf:resource="http://lawd.info/ontology/Edition"></rdf:type>
            <rdfs:label xml:lang="{cts:label/@xml:lang}"><xsl:value-of select="cts:label"></xsl:value-of> (Analytic HTML Edition)</rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
        </rdf:Description>
        

    </xsl:template>
    
    <xsl:template match="cts:translation">
        <rdf:Description rdf:about="{concat($baseurl,@urn)}">
            <rdf:type rdf:resource="http://lawd.info/ontology/Translation"></rdf:type>
            <rdfs:label xml:lang="{@xml:lang}"><xsl:value-of select="cts:label"></xsl:value-of></rdfs:label>
            <lawd:embodies rdf:resource="{concat($baseurl,parent::cts:work/@urn)}"></lawd:embodies>
        </rdf:Description>
    </xsl:template>
</xsl:stylesheet>