# Data Directory

Place the raw competition data files in this folder, using exactly these filenames:

- `Kiva_Loans_Sample.pkl` - the raw loan sample, loaded by `src.data_loader.load_kiva_pickle`.
- `Kiva Data Dictionary.xlsx` - the field-level schema reference for the sample above.

These raw files are treated as **immutable inputs**: no code in this repository writes to, modifies, or overwrites either file. The pipeline only reads them; every derived artifact (features, model outputs, reports) is written elsewhere (e.g. `reports/generated/`), never back into `data/`.

By default, large data files inside this directory (`.csv`, `.pkl`, `.xlsx`, `.zip`, `.json`, `.h5`, `.parquet`) are ignored by `.gitignore` to avoid pushing heavy or competition-restricted files to GitHub. This `README.md` is explicitly excepted so the directory's expectations stay documented even though its data files are not committed.
