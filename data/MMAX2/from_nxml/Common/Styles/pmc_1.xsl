<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0"
                xmlns:mmax="org.eml.MMAX2.discourse.MMAX2DiscourseLoader"
                xmlns:structure="www.h-its.org/NameSpaces/structure"
                xmlns:mappings="www.h-its.org/NameSpaces/mappings">
 <xsl:output method="text" indent="no" omit-xml-declaration="yes"/>
<!-- <xsl:strip-space elements="*"/> -->

<!-- Top level template, do not modify -->
<xsl:template match="words">
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="word">
 <xsl:value-of select="mmax:registerDiscourseElement(@id)"/>
 <!-- Use basedata-level spc attribute to reconstruct input text -->
 <xsl:choose>
  <xsl:when test="not(@spc)">
   <xsl:text> </xsl:text>
  </xsl:when>
  <xsl:when test="@spc=0">
   <xsl:text></xsl:text>
  </xsl:when>
  <xsl:when test="@spc=1">
   <xsl:text> </xsl:text>
  </xsl:when>
  <xsl:when test="@spc=2">
   <xsl:text>  </xsl:text>
  </xsl:when>
  <xsl:when test="@spc=3">
   <xsl:text>   </xsl:text>
  </xsl:when>
  <xsl:when test="@spc=4">
   <xsl:text>    </xsl:text>
  </xsl:when>
  <xsl:when test="@spc=5">
   <xsl:text>     </xsl:text>
  </xsl:when>
  <xsl:when test="@spc=6">
   <xsl:text>      </xsl:text>
  </xsl:when>
  <xsl:when test="@spc=7">
   <xsl:text>       </xsl:text>
  </xsl:when>
  <xsl:when test="@spc=8">
   <xsl:text>        </xsl:text>
  </xsl:when>
  <xsl:when test="@spc=9">
   <xsl:text>         </xsl:text>
  </xsl:when>
  <xsl:when test="@spc=10">
   <xsl:text>          </xsl:text>
  </xsl:when>
 </xsl:choose>

 <xsl:apply-templates select="mmax:getStartedMarkables(@id)" mode="opening"/>
  <xsl:value-of select="mmax:setDiscourseElementStart()"/>
   <xsl:apply-templates/>
  <xsl:value-of select="mmax:setDiscourseElementEnd()"/>
 <xsl:apply-templates select="mmax:getEndedMarkables(@id)" mode="closing"/>
</xsl:template>



<xsl:template match="structure:markable" mode="opening">
 <xsl:choose>
 <xsl:when test="@type='xref'">
<xsl:text> [</xsl:text>
 </xsl:when>

<xsl:when test="@type='surname'">
<xsl:value-of select="mmax:startBold()"/>
 </xsl:when>

 <xsl:when test="@type='aff'">
<xsl:text>
</xsl:text>
 </xsl:when>

 <xsl:when test="@type='rendered-tex-math'">
<xsl:text>
</xsl:text>
 </xsl:when>


</xsl:choose>
</xsl:template>



<xsl:template match="structure:markable" mode="closing">
 <xsl:choose>
  <xsl:when test="@type='sec' or @type='abstract'">
<xsl:text>

</xsl:text>
</xsl:when>
 <xsl:when test="@type='p' or @type='title' or @type='pub-title' or @type='tr'">
<xsl:text> 
</xsl:text>
 </xsl:when>

 <xsl:when test="@type='surname'">
 <xsl:value-of select="mmax:endBold()"/>
<xsl:text>, </xsl:text>
 </xsl:when>

<!-- <xsl:when test="@type='given-names'">
<xsl:text> </xsl:text>
 </xsl:when> -->

 <xsl:when test="@type='xref'">
<xsl:text>] </xsl:text>
 </xsl:when>
 <xsl:when test="@type='email'">
<xsl:text>
</xsl:text>
 </xsl:when>

 <xsl:when test="@type='aff'">
<xsl:text>

</xsl:text>
 </xsl:when>

<xsl:when test="@type='rendered-tex-math'">
<xsl:text>
</xsl:text>
 </xsl:when>


</xsl:choose>
</xsl:template>

</xsl:stylesheet>
