<!-- ppt-master-schema: design-spec/v1 -->
# Agents, Then AI - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | Agents, Then AI — Bringing LLMs into a Social-Science Simulation |
| Canvas Format | PPT 16:9 (1280×720) |
| Page Count | 10 |
| Primary Language | en |
| Target Audience | Mixed general audience: students and researchers from other fields, plus colleagues who know AI but not social-science simulation. No prior knowledge of agent-based modelling, economics, or German energy policy is assumed. |
| Communication Intent | Explain first, demonstrate second, report third: (1) what an "agent" means in social science and why that is not an AI agent; (2) how we put an LLM inside our own agents, and exactly which part of the agent it replaces; (3) what changed in the results — consumers who no longer behave as pure economic optimisers, and manufacturers who now actively argue for cost-cutting R&D; (4) close with an honest statement of what is proven and what is not. |
| Desired Audience Outcome | After five minutes the audience can (a) state the difference between a social-science agent and an AI agent, (b) point to where the AI sits in this model and what it does not touch, (c) name the two behavioural changes it produced, and (d) repeat one honest limitation. |
| Core Message / Ask / Action | In a social-science simulation an "agent" is a small rule-following decision-maker whose rules are the theory; giving some of those agents an LLM replaces the decision step only, and it changes behaviour in two visible ways — consumers stop being purely economic, and manufacturers start actively arguing for the R&D that cuts cost. |
| Delivery Context | Primary: presenter-led 5-minute science-communication talk with live narration. Secondary: a reader can follow the slides alone, and the script doubles as a written explainer. |
| Artifact Afterlife | Reusable explainer deck for talks, teaching and outreach; the script is kept as a stand-alone written version. |
| Reading Mode | presentation |
| Content Strategy | Follow the requested three-part spine — what an agent is → how AI entered → what changed — and expand freely inside each part. Every number must stay traceable to the project's own records; nothing outside the source material may be presented as a measured result. |
| Design Style | Type-led explainer: Swiss-grid discipline with an editorial serif/sans contrast, one electric-blue accent for "AI" and one warm accent for "the rules" |
| Formula Policy | text-only |
| AI Image Acquisition Path | not applicable |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — explicit user request for an English speaker script |
| Custom Animations | disabled — workflow default (proactive custom animations false) |
| Narration Audio | disabled — workflow default (proactive narration audio false) |
| Created Date | 2026-10-10 |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280 × 720 |
| viewBox | `0 0 1280 720` |
| Margins | top 56 / bottom 56 / sides 72 |
| Content Area | 1136 × 608 |

## III. Visual Theme

### Theme Style

- **Mode**: custom
- **Mode References**: instructional
- **Mode Behavior**: instructional cadence throughout — decompose the idea and build it in order: concept, then why it matters, then our case, then the mechanism, then the change. Each page teaches exactly one step, titles state what the page teaches rather than asserting a conclusion, and every third page carries a short signpost (what we just covered → what comes next). The closing page resolves the build with one takeaway line instead of introducing new material.
- **Visual style**: custom
- **Visual Style References**: swiss-minimal, editorial, data-journalism
- **Visual style Behavior**: swiss-minimal supplies the skeleton — a strict two-column grid, generous negative space, square geometry, single-weight hairlines and no decoration or shadow; editorial supplies the serif/sans contrast for titles and the kicker-plus-rule page furniture; data-journalism supplies the evidence discipline — every figure carries its unit and a source line, and number blocks sit in the text flow rather than in cards. Corners stay square, depth stays flat, and colour is used as punctuation (the accent marks the AI layer, the warm accent marks the rule-based layer), never as fill.
- **Theme**: a clean explainer board — white field, near-black ink, one electric-blue accent for everything the AI decides and one warm orange accent for everything the equations decide
- **Tone**: plain-spoken and precise; the audience is assumed curious, not expert

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #FFFFFF | page field |
| Secondary background | #F1F3F6 | comparison columns, code/quote blocks |
| Primary | #101828 | titles, rules, body emphasis |
| Accent | #2B5CE6 | the AI layer: LLM decisions, board, agent voice |
| Secondary accent | #E4572E | the rule-based layer: equations, formula gates, historical baseline |
| Body text | #2A2F3A | body copy |

## IV. Typography System

### Font Plan

| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | serif, editorial authority | Georgia | — | Georgia, Cambria, serif |
| Body | neutral grotesque, screen-clean | Segoe UI | — | Segoe UI, Arial, sans-serif |
| Data | monospace numerals | Consolas | — | Consolas, monospace |

- **Title stack**: `Georgia, Cambria, "Times New Roman", serif`
- **Body stack**: `"Segoe UI", Arial, sans-serif`
- **Data stack**: `Consolas, "Segoe UI", monospace`

### Font Size Hierarchy

| Purpose | Anchor Size (px) |
| --- | ---: |
| Body | 28 |
| Title | 48 |
| Subtitle | 36 |
| Annotation | 20 |
| Footnote | 18 |
| Display | 72 |

## V. Layout Principles

### Page Structure

- **Header area**: kicker line (annotation size, primary at 78% opacity), then the page title; a single hairline rule closes the header
- **Content area**: two-column grid with a hard left axis; the left column carries the teaching statement, the right column carries the evidence, contrast or diagram
- **Footer area**: source/provenance line on the left, page number on the right, both footnote size

### Spacing Specification

| Element | Current Project |
| --- | --- |
| Safe margin | 72px |
| Content block gap | 36px |
| Icon-text gap | 12px |

## VI. Icon Usage Specification

- **Primary bundled library**: tabler-outline
- **Stroke Width**: 2

| Icon Path | Suitable Scenarios |
| --- | --- |
| tabler-outline/users | agents, adopters, groups of decision-makers |
| tabler-outline/building-factory | manufacturers, production |
| tabler-outline/route | the monthly schedule, process order |
| tabler-outline/robot | the LLM decision layer |
| tabler-outline/brain | reasoning, judgement, argument |
| tabler-outline/scale | the economic-rationality gate |
| tabler-outline/messages | board debate, spoken reasoning |
| tabler-outline/chart-line | diffusion curves, results |
| tabler-outline/sun | solar PV subject marker |
| tabler-outline/bolt | cost reduction, learning effects |
| tabler-outline/arrows-right | replacement / hand-over relationships |
| tabler-outline/circle-check | what is verified |
| tabler-outline/alert-triangle | limits, open questions |
| tabler-outline/coin | price, money, tariff |
| tabler-outline/file-text | minutes, written records |
| tabler-outline/settings | the surrounding model machinery |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| results.png | 1800×1200 | 1.50 (3:2) | Baseline four-panel output of the formula-only model (cumulative capacity, module cost, adopters, policy signals) | Chart screenshot | one dominant plate on the right of the two-column grid, three short labels on the left axis, baseline condition line underneath | no-crop | user | Existing | Formula-only run, 312 ticks, seed 42, synthetic data, produced by the project's own analysis pipeline | n/a | local |

## IX. Content Outline

### Part 1: The idea

#### Slide 01 - Cover

- **Audience move**: walks in expecting an AI talk → realises this is about how social scientists model people, and that AI is the second half of the story
- **Layout**: left column carries the kicker, the title stack and the standfirst; the right column carries three stacked display figures separated by hairlines, closed by a full-width rule with the provenance line
- **Title**: Agents, then AI
- **Core message**: A social-science model was built from rule-following agents; AI was then given the decision step of two of them
- **Content**: kicker "Science explainer · 5 minutes"; standfirst "What happens when you hand the decision step of a social-science simulation to a large language model"; three figures: `500` agents in the model ("scaled 1:1000 from Germany's 20.8 M potential adopters"), `312` monthly steps ("1991–2016, one tick = one month"), `2` agent types handed to an LLM ("module manufacturers and a sample of consumers"); footer: "Case: agent-based model of Germany's solar PV policy mix"
- **Cover impact**: bind the hook to the number `2` — only two of the model's decision types were given to an AI, which is the whole point of the talk; composition adaptable
- **Native shape suggestion**: the three figures and hairlines are plain text and lines; no cards

#### Slide 02 - What is an "agent"?

- **Audience move**: assumes "agent" means an AI agent → understands that in social science an agent is a small rule-following actor and that the rules *are* the theory
- **Layout**: teaching statement on the left axis; on the right a two-column contrast block (social-science agent vs AI agent) with three matched rows; a one-line resolution sits under both columns
- **Title**: In social science, an agent is not an AI
- **Core message**: A social-science agent is a simulated decision-maker defined by its state, its rules and its neighbours — nothing more
- **Content**: left statement "An agent is a small stand-in for a person or a firm. It has a state (how much money it has, what it already owns), a rule (when it buys, when it produces) and neighbours it can see. The rules are the theory — if the rules are wrong, the model is wrong."; contrast rows — "What it is": "a handful of variables and an if-then rule" vs "a model trained on data with a general-purpose interface"; "Where behaviour comes from": "written by the researcher, and inspectable line by line" vs "learned, and not fully inspectable"; "What it is for": "testing a mechanism you can state" vs "producing a response you cannot pre-state"; resolution line: "Both are useful. They answer different questions — and this talk is about what happens when you put the second inside the first."

#### Slide 03 - Why anyone builds one

- **Audience move**: thinks a model must be planned top-down → sees that the aggregate pattern is an output of the micro rules, not an input
- **Layout**: one quiet illustrative curve across the lower two-thirds (hand-drawn relationship, not a data chart) with three annotations; a single statement line above it
- **Title**: Nobody plans the S-curve
- **Core message**: Aggregate patterns such as slow start, take-off and saturation emerge from thousands of small decisions
- **Content**: statement "Install a solar panel because your neighbour did, and because the subsidy changed, and because the price fell — and the diffusion curve appears on its own. No agent in the model knows what a diffusion curve is."; curve annotations: "slow start — few neighbours, weak economics", "take-off — the subsidy and the peer effect reinforce each other", "saturation — the easy buyers are gone"; side note "This is why the method is called agent-based: the interesting result is not assumed, it is emerged."

### Part 2: The case

#### Slide 04 - The case: Germany's solar policy mix

- **Audience move**: has no idea what the model contains → can name the three agent types and the monthly loop
- **Layout**: left column: the three agent types as a short labelled list with counts, plus the one-line schedule; right column: the four-panel baseline figure as the page's dominant plate with a condition line under it
- **Title**: Three kinds of agent, 26 years of German solar
- **Core message**: The model reproduces the historical story with three rule-following agent types driven by an external policy environment
- **Content**: agent list — "Adopters · 500 households and firms scaled 1:1000 from Germany's 20.8 M potential buyers"; "Manufacturers · 2, one domestic and one foreign, learning by doing and by research"; "Installers · 2, absorbing the order queue and the labour market"; environment line "A macro environment supplies the monthly price, feed-in tariff, media attention and public R&D signals"; figure condition line "Baseline = formula-only run, 312 ticks, seed 42, synthetic data"
- **Images**: results.png placed as the dominant right-hand plate at its native 3:2 ratio; no crop

#### Slide 05 - The rules the agents obey

- **Audience move**: wonders where the behaviour actually comes from → sees that both the consumer decision and the manufacturer cost path are explicit equations
- **Layout**: two stacked rule blocks, each with a small icon, a one-line name, the equation as text and a plain-language gloss; a closing line states the consequence
- **Title**: Two rules, written down in full
- **Core message**: Every decision in the baseline model is an equation a reader can check
- **Content**: Rule 1 — adoption, two stages: "First the agent must get the idea (peers, information, awareness, return), then it must pass an economic test: the net present value of the panels has to be non-negative — unless it is a hard-core environmentalist, who installs regardless."; Rule 2 — cost, two learning channels: "Module cost falls with cumulative production (learning by doing) and with the accumulated stock of knowledge from R&D (learning by research). The equation is the same for every manufacturer in every month."; closing line: "Note what this means: the consumer is a pure optimiser, and the manufacturer never has to be persuaded to invest in R&D."

### Part 3: Where the AI goes in

#### Slide 06 - What we replaced, and what we did not

- **Audience move**: assumes the AI runs the whole simulation → understands that the LLM replaces one step, the decision, while the model still owns every state update
- **Layout**: a three-part hand-over diagram across the middle: model state → decision (the only replaced block, drawn in accent) → state update; below it, two short columns for the two agent types that were opened up
- **Title**: The AI gets one step, not the model
- **Core message**: The LLM decides; the model still does the accounting
- **Content**: diagram labels — "state: prices, knowledge, orders, neighbours" → "decision: what to do this month (replaced)" → "update: the model applies it and moves to the next month"; column one "Manufacturers · every month the firm's decision now comes from a board of five AI directors with different mandates, who vote and leave minutes"; column two "Consumers · a 5% sample of undecided adopters is asked each month instead of running the equation"; safety line "If a call fails, the model falls back to the original equation, so the simulation never stalls."

#### Slide 07 - Change 1: consumers stop being pure optimisers

- **Audience move**: assumes an AI buyer behaves like a better calculator → sees that the AI removes the hard rationality gate and can buy for reasons equations cannot hold
- **Layout**: a single comparison axis: the formula path drawn as a gate (pass / fail) against the AI path drawn as an open decision; three short reason labels beneath the open side; a status line at the foot
- **Title**: The rationality gate disappears
- **Core message**: The equation may only buy when the numbers work; the LLM may also buy because of neighbours, emotion or expectations
- **Content**: left side "Rule-based consumer: get the idea → net present value must be non-negative → buy / do not buy"; right side "AI consumer: gets the same market figures, then decides — no non-negativity gate"; reason labels "what the neighbours are doing", "how it feels about the technology", "what it expects the next subsidy round to look like"; consequence line "In our baseline the formula model adopts 50 of 500 agents, about 10%, against a historical rate closer to 7%; removing the gate changes who buys and when, which is exactly the behaviour the equation could not express."; status line "Mechanism verified in the code and in short live runs; the full 26-year AI-versus-formula comparison is still pending."

#### Slide 08 - Change 2: manufacturers argue about R&D

- **Audience move**: assumes the firm's R&D is a setting in the code → sees it become a monthly argument between five AI directors with a vote and a written record
- **Layout**: left column: the five board seats as a compact roster with mandates; right column: one real vote tally and one quoted line of reasoning; a closing line states what this changes
- **Title**: R&D becomes an argument, not a default
- **Core message**: In the AI version the firm must be persuaded to invest in cost-reducing R&D — and it argues, votes and leaves a record
- **Content**: roster "Chair — long-run strategy and the policy window; CFO — cash, margin and utilisation; CTO — efficiency and the knowledge that drives cost down; CMO — order backlog and demand; CSO — compliance and supply-chain resilience"; observed meeting "In the first live board meeting the vote was 3 to 1 to 1: the firm expanded, and it chose to spend the month's R&D on the technology rather than standing still — every director's reason and reservation is stored in the minutes"; closing line "The equation always cost-reduced silently; the AI board has to decide it, and can be outvoted — which is what makes the resulting cost path a behavioural result rather than an assumption."

### Part 4: What it means

#### Slide 09 - What this buys — and what it does not

- **Audience move**: is ready to believe AI makes the model better → leaves with a precise claim and a named limitation
- **Layout**: two matched columns (what it buys / what it does not), each with three short lines; a single hand-off line under both
- **Title**: A better model of people, not a better crystal ball
- **Core message**: The AI adds behaviour the equations could not express; it does not yet add measured accuracy
- **Content**: "What it buys" — "reasons a formula cannot hold: peers, emotion, expectations of the next policy round"; "corporate disagreement with a written record you can read"; "a clean seam: the decision changes, the accounting does not"; "What it does not" — "the full 26-year AI run is not finished, so no long-run accuracy claim"; "LLM decisions are not reproducible run to run, and they cost money and time per decision"; "a more realistic story is not automatically a more accurate number"; hand-off line "Everything the AI decides is validated against a schema and falls back to the equation on failure, so the model stays runnable — that is what makes the experiment safe to try."

#### Slide 10 - Closing

- **Audience move**: has followed the three steps → leaves with one sentence and one image of where the boundary sits
- **Layout**: a single large takeaway line on the left, and on the right the two-layer motif (equation layer in the warm accent, AI layer in blue) drawn once and simply; no new information
- **Title**: The equations stay. The AI only decides.
- **Core message**: The model still owns the world; the AI owns the choice
- **Content**: takeaway "Agents gave the model its mechanism. The AI gave the agents a voice."; motif labels "equations — the world: prices, costs, orders, the monthly loop" and "the AI — the choice: buy or not, expand or not, which R&D to fund"; provenance line "Case built on Nuñez-Jimenez et al. (2022), Research Policy — Germany's solar PV policy mix, 1991–2016"
- **Closing impact**: the two-layer boundary is the last thing on screen, so the audience leaves with the seam rather than the technology

## X. Speaker Notes Requirements

- **Generation**: enabled
- **Filename**: match each SVG filename under `notes/`
- **Content**: an English speaker script written to be read aloud in a five-minute talk: plain language, short sentences, no jargon left undefined, one idea per page, first person plural for the project, roughly 60–80 spoken words per page and about 650 words in total. State the source of every number as it is spoken (baseline run vs live board meeting). Nothing outside the project's own records may be claimed as a measured result: the full 26-year AI comparison is described as pending wherever the mechanism is described.
- **Total duration**: 5 minutes
- **Notes style**: conversational explainer
- **Presentation purpose**: explain and report; keep one honest limitation in view
