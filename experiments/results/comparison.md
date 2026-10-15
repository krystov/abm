# Decision-mode comparison

seed=42, ticks=120, adopters=500, adopter_llm_fraction=0.0, model=gpt-4.1-mini

mode | seconds | adopted | installed MW | dom cost €/W | for cost €/W | dom eff | rd_focus votes | action votes
---------------------------------------------------------------------------------------------------------------
formula | 8.9 | 8 | 0.06 | 0.8175 | 1.4483 | 0.15 | {'cost_reduction': 240} | {'reduce': 240}
single | 188.5 | 8 | 0.06 | 0.8175 | 1.4483 | 0.15 | {'cost_reduction': 240} | {'reduce': 240}
board | 205.4 | 8 | 0.06 | 0.8175 | 1.4483 | 0.15 | {'cost_reduction': 240} | {'reduce': 240}

- **board** board: 240 场会议，一致通过 0.0%，平票裁决 0，未达半数 0，平均反对 1.66 票，弃权 0.0 票