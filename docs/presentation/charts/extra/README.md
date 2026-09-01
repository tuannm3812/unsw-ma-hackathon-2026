# Extra exhibits (house style)

House-style rebuilds of the remaining notebook figures - same typography
spec as the 8 deck exhibits (title 13pt / labels 10.5 / ticks 10 /
annotations 9.5, DM Sans, 300 dpi, sized for native-size insertion). Not
placed in the draft deck; use them as optional/backup slide visuals.

Values are computed from `data/Kiva_Loans.pkl` with the notebooks' exact
logic and verified against printed output where it exists (gender medians,
repayment n=, decile bin edges). Built by `scripts/build_charts.py`.

- `extra_speed_distribution.png` - funding-speed histogram (36.6% within 1 day)
- `extra_period_speed_box.png` - speed by period, boxplot (medians 1.4 / 4.9 / 4.1)
- `extra_gender_speed_box.png` - speed by gender, boxplot (medians 2.3 / 7.7)
- `extra_repayment.png` - mean speed by repayment interval
- `extra_amount_deciles.png` - mean speed by loan-amount decile

The one figure NOT rebuilt: the predicted-vs-actual scatter
(`../notebook/mod_21_5_regression_modeling.png`) - its points are model
predictions and cannot be reproduced without retraining; use the raw
export if needed.
