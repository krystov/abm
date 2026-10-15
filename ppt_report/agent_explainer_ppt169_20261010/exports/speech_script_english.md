# 01_cover

Hi. A quick question first: what does the word "agent" mean? In computer science it's a program that acts on your behalf — something like a chatbot. In social science it's much smaller: a stand-in for a person or a firm. Today I want to show you what happened when we put the first kind of agent inside the second kind. Three parts: what an agent is, where the AI goes in, and what changed when it did.

---

# 02_what_is_an_agent

A social-science agent is a small piece of code standing in for a decision-maker. It has a state — what it owns, what it can spend. A rule — when it buys, when it produces. And neighbours it can see. Here is the key idea: the rules are the theory. If the rules are wrong, the model is wrong. Nothing is learned inside the agent; everything was written down by the researcher, and you can read it line by line. An AI agent is almost the opposite — flexible, general, and not fully inspectable. Both are useful. This talk is about putting the second one inside the first.

---

# 03_s_curve

Why build a model like this at all? Install a panel because your neighbour did. Install one because the subsidy changed. Install one because the price fell. Do that across a few hundred households and a pattern appears: a slow start, a take-off, a saturation. Nobody planned that curve. No agent in the model even knows what a diffusion curve is. That is the point of the method — the interesting result emerges from the rules. The curve on this page is a sketch, by the way; no data is plotted on it.

---

# 04_the_case

Our case is Germany's solar boom, 1991 to 2016. Three kinds of agent. Five hundred adopters — households and firms, scaled down a thousand-fold from about twenty million potential buyers. Two manufacturers, one domestic and one foreign. Two installers, handling the order queue and the labour market. Above them, a macro environment hands out the monthly signals: electricity price, feed-in tariff, media attention, and public research spending. One tick is one month. This is the baseline — formula only.

---

# 05_two_rules

What makes the agents move? Two rules. Rule one is adoption, and it happens in two stages. First the agent has to get the idea — neighbours, information, green-mindedness, expected return. Then it has to pass an economic test: net present value must be non-negative — unless it's a hard-core environmentalist, who installs anyway. Rule two is the cost of a module: it falls with cumulative production, learning by doing, and with the knowledge built up by research, learning by research. The same equation, every manufacturer, every month. So notice: the consumer is a pure optimiser, and no manufacturer ever has to be persuaded to invest.

---

# 06_where_ai_enters

So where does the AI go in? We did not hand over the model. We replaced one step: the decision. The state — prices, knowledge, orders, neighbours — is still the original model. The language model decides; the model applies the decision and moves to the next month. Two agent types were opened up. For manufacturers, the monthly decision now comes from a board of five AI directors with different mandates — they vote, and they leave minutes. For consumers, five per cent of the undecided adopters are asked each month. And if a call fails, the model falls back to the equation, so the simulation never stalls.

---

# 07_change_rationality

First change. The rule-based consumer has a gate: if the numbers don't work, you don't buy. The AI consumer gets the same figures, and there is no gate. It can buy because the neighbours are doing it, because it likes the technology, or because it expects the next subsidy round to be generous. Those are reasons an equation cannot hold — and they are how people actually behave. Our baseline ends at about ten per cent adoption, against a historical rate closer to seven. One honest caveat: we have verified this mechanism in the code and in short live runs; the full twenty-six-year comparison is still pending.

---

# 08_change_board

Second change: the manufacturer. In the formula model, cost reduction is silent and automatic. Here it has to be argued. Five directors, five mandates: chair, finance, technology, marketing, compliance. They disagree by design. In the first live board meeting the vote was three to one to one — the firm expanded, and it chose to spend that month's research budget rather than stand still. Every reason and every reservation is written into the minutes. So research stops being a setting in the code and becomes an argument you can read afterwards.

---

# 09_what_it_means

So what does this buy? Behaviour an equation cannot express: peer pressure, emotion, expectations — and real disagreement inside a firm, with a record you can inspect. It also keeps a clean seam: the decision changes, the accounting does not. What it does not buy is accuracy. The long run is not finished; language-model decisions are not reproducible run to run; and each one costs money and time. A more realistic story is not automatically a truer number. Every AI decision is schema-checked and falls back to the equation — that is what makes the experiment safe to try.

---

# 10_closing

Let me leave you with the boundary we drew. The equations stay. The world — prices, costs, orders, the monthly loop — is still the model. The AI only decides: buy or not, expand or not, which research to fund. Agents gave the model its mechanism. The AI gave the agents a voice. Thank you.
