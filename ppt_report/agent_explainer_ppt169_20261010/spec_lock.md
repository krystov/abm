<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: en
- audience: mixed general audience — students and researchers from other fields, plus colleagues who know AI but not social-science simulation
- objective: Explain what a social-science agent is, show where an LLM was inserted into this model and what it does not touch, report the two behavioural changes it produced, and close on one honest limitation so the audience can separate mechanism from measured accuracy
- core_message: In a social-science simulation an agent is a small rule-following decision-maker whose rules are the theory; giving some agents an LLM replaces the decision step only, and it changes behaviour in two visible ways — consumers stop being purely economic, and manufacturers start actively arguing for the R&D that cuts cost
- consumption_mode: presentation

## mode
- mode: custom
- mode_references: instructional
- mode_behavior: Instructional cadence — decompose the idea and build it in order (concept, why it matters, the case, the mechanism, the change, the meaning). Each page teaches exactly one step, titles state what the page teaches rather than asserting a conclusion, each transition is signposted, and the closing page resolves the build with a single takeaway instead of new material.

## visual_style
- visual_style: custom
- visual_style_references: swiss-minimal, editorial, data-journalism
- visual_style_behavior: Swiss-grid skeleton — strict two-column grid, generous negative space, square geometry, single-weight hairlines, no decoration and no shadow; editorial adds the serif/sans title contrast and the kicker-plus-rule page furniture; data-journalism adds the evidence discipline of unit-bearing figures with a provenance line and number blocks that sit in the text flow instead of cards. Colour is punctuation: the blue accent marks everything the AI decides, the warm accent marks everything the equations decide.

## colors
- background: #FFFFFF
- secondary_bg: #F1F3F6
- primary: #101828
- accent: #2B5CE6
- secondary_accent: #E4572E
- body_text: #2A2F3A
- surface: #F8FAFC
- grid: #D7DCE5

## typography
- font_family: "Segoe UI", Arial, sans-serif
- title_family: Georgia, Cambria, "Times New Roman", serif
- body_family: "Segoe UI", Arial, sans-serif
- data_family: Consolas, "Segoe UI", monospace
- body: 28
- title: 48
- subtitle: 36
- annotation: 20
- footnote: 18
- display: 72

## icons
- library: tabler-outline
- stroke_width: 2
- inventory: tabler-outline/users, tabler-outline/building-factory, tabler-outline/route, tabler-outline/robot, tabler-outline/brain, tabler-outline/scale, tabler-outline/messages, tabler-outline/chart-line, tabler-outline/sun, tabler-outline/bolt, tabler-outline/arrows-right, tabler-outline/circle-check, tabler-outline/alert-triangle, tabler-outline/coin, tabler-outline/file-text, tabler-outline/settings

## page_rhythm
- P01: anchor
- P02: dense
- P03: breathing
- P04: dense
- P05: dense
- P06: breathing
- P07: dense
- P08: dense
- P09: dense
- P10: anchor

## pptx_structure
- mode: flat

## images
- p04: images/results.png | source=user | pattern=one dominant plate on the right of the two-column grid, three short labels on the left axis, baseline condition line underneath | crop=no-crop

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
