<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"

                xmlns:ocr_words="www.h-its.org/NameSpaces/ocr_words"
                xmlns:ocr_lines="www.h-its.org/NameSpaces/ocr_lines"
                xmlns:mmax="org.eml.MMAX2.discourse.MMAX2DiscourseLoader">
 <xsl:output method="text" indent="no" omit-xml-declaration="yes"/>
<xsl:strip-space elements="*"/>

<xsl:template match="words">
<xsl:text>
</xsl:text>
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="word">
 <xsl:value-of select="mmax:registerDiscourseElement(@id)"/>
 <!-- Use basedata-level spc attribute to reconstruct input text -->
 <xsl:choose>
  <xsl:when test="@spc=0">
  </xsl:when>
  <xsl:when test="@spc=1">
  <xsl:text> </xsl:text>
  </xsl:when>
  <xsl:when test="@spc=2">
  <xsl:text>  </xsl:text>
  </xsl:when>
  <xsl:otherwise>
   <!-- Default if spc not present: One space -->
   <xsl:text> </xsl:text>
  </xsl:otherwise>
 </xsl:choose>

 <xsl:apply-templates select="mmax:getStartedMarkables(@id)" mode="opening"/>
  <xsl:value-of select="mmax:setDiscourseElementStart()"/>
   <xsl:apply-templates/>
  <xsl:value-of select="mmax:setDiscourseElementEnd()"/>
 <xsl:apply-templates select="mmax:getEndedMarkables(@id)" mode="closing"/>
</xsl:template>

<xsl:template match="ocr_lines:markable" mode="opening">
</xsl:template>

<xsl:template match="ocr_lines:markable" mode="closing">
<xsl:text>
</xsl:text>
</xsl:template>

<xsl:template match="ocr_words:markable" mode="closing">
<xsl:if test="mmax:isOn('low-conf-labels')">
<xsl:if test="@worst_char_conf &lt; 97">
  <xsl:variable name="paper" select="substring-before(@image,'_')"/>
  <xsl:variable name="img_path" select="concat('showpngimage ',concat(concat(concat(concat(concat('/home/muellemh/Work/DeepCurate/real-deep/hOCR2MMAX2/low-conf-word-images/',$paper),'/'),@image),concat('.',@id)),concat('.','lowconf.png')))"/>
  <xsl:value-of select="mmax:startSubscript()"/>
  <xsl:value-of select="mmax:addHotSpot('#',$img_path)"/>
  <xsl:value-of select="mmax:endSubscript()"/>
</xsl:if>
</xsl:if>

</xsl:template>



</xsl:stylesheet>
