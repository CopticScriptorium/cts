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
    
    <xsl:output method="text" indent="no"/>
    <xsl:strip-space elements="*"/>
    <xsl:variable name="baseurl" select="'http://copticscriptorium.org/'"/>
    <xsl:template match="/">
        <xsl:for-each select="//cts:work">
            <xsl:sort select="@urn"/>
            <xsl:value-of select="@urn"/><xsl:text>&#x0a;</xsl:text>
            <xsl:apply-templates/>
        </xsl:for-each> 
    </xsl:template>
    
    <xsl:template match="cts:edition|cts:translation">
        <xsl:value-of select="@urn"/><xsl:text>&#x0a;</xsl:text>
        <xsl:value-of select="concat($baseurl,@urn,'/relannis')"/><xsl:text>&#x0a;</xsl:text>
        <xsl:value-of select="concat($baseurl,@urn,'/annis')"/><xsl:text>&#x0a;</xsl:text>
        <xsl:value-of select="concat($baseurl,@urn,'/tei/xml')"/><xsl:text>&#x0a;</xsl:text>
        <xsl:value-of select="concat($baseurl,@urn,'/paula/xml')"/><xsl:text>&#x0a;</xsl:text>
        <xsl:value-of select="concat($baseurl,@urn,'/dipl/html')"/><xsl:text>&#x0a;</xsl:text>
        <xsl:value-of select="concat($baseurl,@urn,'/norm/html')"/><xsl:text>&#x0a;</xsl:text>
        <xsl:value-of select="concat($baseurl,@urn,'/analytic/html')"/><xsl:text>&#x0a;</xsl:text>
    </xsl:template>
    
    <xsl:template match="*"/>
</xsl:stylesheet>