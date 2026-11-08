# Map data provenance

| File | Source | Licence | Retrieved |
| --- | --- | --- | --- |
| `ne_110m_admin_0_countries.zip` | Natural Earth 1:110m Cultural Vectors, Admin 0 – Countries, version 5.1.1 (zip dated 2022-05-09), <https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip> | Public domain (<https://www.naturalearthdata.com/about/terms-of-use/>) | 2026-11-08; SHA-256 `0f243aeac8ac6cf26f0417285b0bd33ac47f1b5bdb719fd3e0df37d03ea37110` |
| `country_share_map.png` | Rendered by `scripts/build_country_map.py` from the file above and `reports/evidence_sources/country_shares.json` | Derived; same terms as its inputs | 2026-11-08 |

Rendering needs the isolated environment, which is gitignored:

```bash
python3 -m venv .venv-maps && .venv-maps/bin/pip install geopandas matplotlib
.venv-maps/bin/python scripts/build_country_map.py
```

Countries join on ISO alpha-2 codes (`ISO_A2_EH`); all 48 Kiva countries matched on 2026-11-08.
