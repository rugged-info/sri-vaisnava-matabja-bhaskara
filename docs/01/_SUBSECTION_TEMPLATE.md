---
layout: page
title: "{{SUBSECTION_TITLE}}"
section: "{{SECTION}}"              # e.g., "01"
subsection_id: "{{SUBSECTION_ID}}"  # e.g., "001"
verse_start: "{{VERSE_START}}"      # e.g., "v000001"
verse_end: "{{VERSE_END}}"          # e.g., "v000008"
---

<nav>
[Table of Contents]({{ "/" | relative_url }}) ·
[Section {{SECTION}}]({{ "/{{SECTION}}/" | relative_url }})
</nav>

---

## Overview

{{SUBSECTION_OVERVIEW}}

---

## Verses in this subsection

**Start:** [{{VERSE_START}}]({{ "/{{SECTION}}/verses/{{VERSE_START}}/" | relative_url }})  
**End:** [{{VERSE_END}}]({{ "/{{SECTION}}/verses/{{VERSE_END}}/" | relative_url }})

### Verse links

<!-- Replace the list below with the actual verse pages you have generated -->
- [{{VERSE_START}}]({{ "/{{SECTION}}/verses/{{VERSE_START}}/" | relative_url }})
- [next…]({{ "/{{SECTION}}/verses/v000002/" | relative_url }})
- [next…]({{ "/{{SECTION}}/verses/v000003/" | relative_url }})
- …
- [{{VERSE_END}}]({{ "/{{SECTION}}/verses/{{VERSE_END}}/" | relative_url }})

---

## Notes / Editorial

{{EDITORIAL_NOTES}}
