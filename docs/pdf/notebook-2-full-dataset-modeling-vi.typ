// ============================================================================
// UNSW MARKETING ANALYTICS HACKATHON 2026
// Sổ tay Kaggle 2: Mô hình hóa Thống kê & Dự báo Toàn diện (Full-Dataset Modeling)
// Bản dịch tiếng Việt đầy đủ và chuẩn hóa học thuật
// ============================================================================

#set page(
  paper: "a4",
  margin: (x: 2cm, top: 2.5cm, bottom: 2.5cm),
  header: [
    #grid(
      columns: (1fr, auto),
      align(left)[#text(fill: rgb("#205493"), weight: "bold", size: 8pt)[UNSW MARKETING ANALYTICS HACKATHON 2026]],
      align(right)[#text(fill: rgb("#6b7280"), size: 8pt)[Kaggle notebook — Notebook 2 - Full-Dataset Modeling (Bản tiếng Việt)]]
    )
    #v(2pt)
    #line(length: 100%, stroke: 0.5pt + rgb("#e5e7eb"))
  ],
  footer: context [
    #align(right)[#text(fill: rgb("#6b7280"), size: 8.5pt)[#numbering("01", counter(page).get().first())]]
  ]
)

#set text(
  font: ("Helvetica Neue", "Arial"),
  size: 9pt,
  lang: "vi",
  fill: rgb("#1f2937")
)
#set par(justify: true, leading: 0.65em)

#show heading: set text(fill: rgb("#111827"))
#show heading.where(level: 1): it => {
  v(14pt, weak: true)
  text(size: 16pt, weight: "bold", it.body)
  v(8pt, weak: true)
}
#show heading.where(level: 2): it => {
  v(12pt, weak: true)
  text(size: 12.5pt, weight: "bold", it.body)
  v(6pt, weak: true)
}
#show heading.where(level: 3): it => {
  v(10pt, weak: true)
  text(size: 10.5pt, weight: "bold", it.body)
  v(4pt, weak: true)
}

#show raw.where(lang: "python"): it => block(
  fill: rgb("#f8f9fa"),
  inset: 8pt,
  radius: 4pt,
  width: 100%,
  stroke: 0.5pt + rgb("#e5e7eb"),
  text(font: ("Menlo", "Courier New"), size: 7.6pt, it)
)

#show raw.where(lang: "output"): it => block(
  fill: rgb("#fbfcfd"),
  inset: 7pt,
  radius: 3pt,
  width: 100%,
  stroke: 0.5pt + rgb("#d1d5db"),
  text(font: ("Menlo", "Courier New"), size: 7.2pt, it.text)
)

#show raw.where(block: false): it => box(
  fill: rgb("#f3f4f6"),
  inset: (x: 3pt, y: 0pt),
  outset: (y: 2pt),
  radius: 2pt,
  text(font: ("Menlo", "Courier New"), size: 8pt, it)
)

#let insight_box(content) = block(
  fill: rgb("#f0fdf4"),
  inset: 9pt,
  radius: 4pt,
  width: 100%,
  stroke: 0.8pt + rgb("#86efac"),
  [
    #text(weight: "bold", fill: rgb("#166534"))[Điểm cốt lõi (Insight): ]
    #content
  ]
)

#let warning_box(content) = block(
  fill: rgb("#fffbeb"),
  inset: 9pt,
  radius: 4pt,
  width: 100%,
  stroke: 0.8pt + rgb("#fcd34d"),
  [
    #text(weight: "bold", fill: rgb("#b45309"))[Lưu ý phương pháp quan trọng: ]
    #content
  ]
)

= Kiva Loans: Mô hình hóa Dữ liệu Toàn diện (1.45 triệu khoản vay)

Sổ tay này kế thừa nền tảng phân tích mô tả của `1_full_dataset_eda.ipynb` bằng các *mô hình thống kê kiểm soát đồng thời tất cả các yếu tố* — cách thức duy nhất để trả lời câu hỏi liệu phong cách kể chuyện (narrative framing) có thực sự quan trọng hay không một khi quy mô khoản vay, kỳ hạn hoàn trả, ngành nghề, khu vực địa lý và yếu tố thời gian đều đã được kiểm soát đồng thời. 

Sổ tay giải quyết hai câu hỏi nghiên cứu khác nhau về cùng một biến mục tiêu (tốc độ gọi vốn):
- *Dự báo (Predictive)*: Tốc độ gọi vốn có thể được dự báo chính xác đến mức nào đối với một khoản vay mới đăng tải, chỉ sử dụng thông tin có sẵn tại thời điểm đăng? Được kiểm định một cách trung thực — trên các khoản vay đăng tải trong giai đoạn 2024–2025 mà mô hình *hoàn toàn chưa từng nhìn thấy trong quá trình huấn luyện*.
- *Giải thích (Explanatory)*: Những đặc trưng nào của khoản vay và của câu chuyện mô tả có mối liên hệ với việc gọi vốn nhanh hơn hoặc chậm hơn, khi tất cả các yếu tố khác được giữ cố định? Phần này báo cáo *mối liên hệ tương quan (association), tuyệt đối không khẳng định quan hệ nhân quả (causation)* — mối liên hệ giữa hai biến không chứng minh yếu tố này gây ra yếu tố kia, bởi vì người đi vay không được phân bổ ngẫu nhiên phong cách viết, số tiền vay hay giới tính.

== Thuật ngữ cốt lõi (Glossary)

#table(
  columns: (1.2fr, 2.8fr),
  fill: (col, row) => if row == 0 { rgb("#f3f4f6") } else { none },
  stroke: 0.5pt + rgb("#e5e7eb"),
  inset: 6pt,
  [#text(weight: "bold")[Thuật ngữ]], [#text(weight: "bold")[Ý nghĩa]],
  [*MAE* (Mean Absolute Error)], [Sai số tuyệt đối trung bình: đo lường dự báo chệch trung bình bao nhiêu ngày. Giá trị càng nhỏ càng tốt.],
  [*$R^2$* (Hệ số xác định)], [Tỷ lệ phương sai của tốc độ gọi vốn mà mô hình giải thích được, từ 0% đến 100%.],
  [*ROC AUC*], [Khả năng mô hình phân biệt giữa \"khoản vay gọi vốn nhanh (trong 24h)\" và \"không nhanh\", từ 0,5 (đoán ngẫu nhiên) đến 1,0 (hoàn hảo).],
  [*Tập kiểm thử giữ lại* (Holdout set)], [Các khoản vay mô hình chưa từng thấy trong lúc huấn luyện — phương pháp công bằng để kiểm định khả năng tổng quát hóa trên dữ liệu mới.],
  [*Hệ số hồi quy* (Coefficient)], [Mức độ một yếu tố làm tăng hoặc giảm tốc độ gọi vốn, khi giữ tất cả các yếu tố khác không đổi.],
  [*Ý nghĩa thống kê* ($p$-value)], [Mức độ tin cậy rằng mối liên hệ là thực chất chứ không phải do nhiễu ngẫu nhiên; $p$-value càng nhỏ thể hiện độ tin cậy càng cao.],
  [*Nhóm cơ sở / Tham chiếu* (Reference category)], [Nhóm nền tảng mà mọi phép so sánh \"nhanh hơn/chậm hơn bao nhiêu\" được đối chiếu trực tiếp.],
  [*Giá trị SHAP*], [Phương pháp lý thuyết trò chơi đo lường mức độ đóng góp thực tế của từng đặc trưng vào quyết định dự báo của mô hình phức tạp.]
)

== 1. Cài đặt môi trường (Setup)

```python
import re
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import nltk
import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import average_precision_score, mean_absolute_error, r2_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
HOLDOUT_START = "2024-01-01"
MIN_REGION_OBSERVATIONS = 10
MIN_SECTOR_OBSERVATIONS = 1000
SMALL_LOAN_MAX_USD = 250
MEDIUM_LOAN_MAX_USD = 750

KAGGLE_DATA_DIR = Path("/kaggle/input/datasets/tuannm3812/kiva-loans-hackathon-data")
if not KAGGLE_DATA_DIR.exists():
    KAGGLE_DATA_DIR = Path("/kaggle/input/kiva-loans-hackathon-data")
if KAGGLE_DATA_DIR.exists():
    DATA_PATH = KAGGLE_DATA_DIR / "Kiva_Loans.pkl"
else:
    def _find_project_root(start: Path) -> Path:
        candidate = start
        for _ in range(5):
            if (candidate / "data" / "Kiva_Loans_Sample.pkl").exists():
                return candidate
            if candidate.parent == candidate:
                break
            candidate = candidate.parent
        return start
    try:
        PROJECT_ROOT = Path(__file__).resolve().parents[1]
    except NameError:
        PROJECT_ROOT = _find_project_root(Path.cwd())
    DATA_PATH = PROJECT_ROOT / "data" / "Kiva_Loans.pkl"
```

== 2. Tải dữ liệu (Load Data)

```python
import pickle
with open(DATA_PATH, "rb") as handle:
    _raw = pickle.load(handle)
df = pd.DataFrame(_raw) if isinstance(_raw, list) else _raw
print(f"Shape: {df.shape[0]:,} loans x {df.shape[1]} raw columns")
df.info()
```

```output
Shape: 1,453,846 loans x 27 raw columns
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 1453846 entries, 0 to 1453845
Data columns (total 27 columns):
 #   Column               Non-Null Count    Dtype  
---  ------               --------------    -----  
 0   id                   1453846 non-null  int64  
 1   status               1453846 non-null  object 
 2   borrowerCount        1453846 non-null  int64  
 3   name                 1453846 non-null  object 
 4   gender               1453846 non-null  object 
 5   loanAmount           1453846 non-null  float64
 6   lenderRepaymentTerm  1453846 non-null  int64  
 7   repaymentInterval    1453846 non-null  object 
 8   sector               1453846 non-null  object 
 9   activity             1453846 non-null  object 
 10  use                  1453846 non-null  object 
 11  city                 1392239 non-null  object 
 12  latitude             1362860 non-null  float64
 13  longitude            1362860 non-null  float64
 14  country_iso          1453846 non-null  object 
 15  country_name         1453846 non-null  object 
 16  region               1453846 non-null  object 
 17  country_ppp          1453846 non-null  float64
 18  fundsLentInCountry   1453846 non-null  int64  
 19  country_latitude     1453846 non-null  float64
 20  country_longitude    1453846 non-null  float64
 21  description          1453846 non-null  object 
 22  whySpecial           1414768 non-null  object 
 23  image_url            1453846 non-null  object 
 24  disbursalDate        1453846 non-null  object 
 25  fundraisingDate      1453846 non-null  object 
 26  raisedDate           1453846 non-null  object 
dtypes: float64(6), int64(4), object(17)
memory usage: 299.5+ MB
```

== 3. Kỹ thuật Tạo Đặc trưng (Feature Engineering)

Ba nhóm đặc trưng chính cung cấp dữ liệu cho mô hình: biến mục tiêu (thời gian gọi vốn), các biến cấu trúc của khoản vay, và các biến diễn ngôn/cảm xúc trích xuất từ câu chuyện mô tả.

=== 3.1 Biến Mục Tiêu (Target Variable)
Tương tự Notebook 1: `funding_speed_days` tính bằng khoảng cách ngày giữa ngày đăng và ngày gọi đủ vốn, chuyển sang dạng logarit `log_funding_speed = log1p(...)` để khắc phục độ lệch phải nặng nề, cùng với biến nhị phân `funded_within_24h`. Biến `analysis_period` phân chia thành 3 giai đoạn: tiền đại dịch (đến 2019), đại dịch (2020–2021) và hậu đại dịch (2022–2025).

```python
fundraising = pd.to_datetime(df["fundraisingDate"], errors="coerce", utc=True)
raised = pd.to_datetime(df["raisedDate"], errors="coerce", utc=True)
df["funding_speed_days"] = (raised - fundraising).dt.total_seconds() / 86400
df["log_funding_speed"] = np.log1p(df["funding_speed_days"].clip(lower=0))
df["funded_within_24h"] = (df["funding_speed_days"] <= 1).astype(float)
df["fundraisingDate_parsed"] = fundraising
year = fundraising.dt.year
df["analysis_period"] = pd.cut(
    year, bins=[-np.inf, 2019, 2021, np.inf],
    labels=["pre_pandemic", "pandemic_disruption", "post_pandemic"],
).astype(str)
```

=== 3.2 Các Đặc Trưng Cấu Trúc (Structural Features)
- `log_loan_amount`: quy mô khoản vay được logarit hóa.
- `loan_size_band`: phân nhóm quy mô nhỏ ($<$ 250 USD), trung bình (250–750 USD), và lớn ($>$ 750 USD) để nắm bắt hiệu ứng phi tuyến.
- `gender_classification`: chuẩn hóa các trường hợp nhiều người vay thành nhóm \"mixed\" (hỗn hợp).
- `is_group_loan`: chỉ báo khoản vay nhóm ($> 1$ người vay).
- `region_group` / `sector_group`: gộp các nhóm nhỏ vào \"Other\" nếu số quan sát dưới 10 (khu vực) hoặc 1.000 (ngành nghề).

```python
df["log_loan_amount"] = np.log1p(df["loanAmount"])
df["loan_size_band"] = pd.cut(
    df["loanAmount"], bins=[-np.inf, SMALL_LOAN_MAX_USD, MEDIUM_LOAN_MAX_USD, np.inf],
    labels=["small", "medium", "large"],
).astype(str)
df["gender_classification"] = df["gender"].fillna("unknown").apply(
    lambda g: "mixed" if "," in str(g) else str(g)
)
df["is_group_loan"] = (df["borrowerCount"] > 1).astype(int)
for col, min_obs, new_col in [
    ("region", MIN_REGION_OBSERVATIONS, "region_group"),
    ("sector", MIN_SECTOR_OBSERVATIONS, "sector_group"),
]:
    counts = df[col].value_counts()
    major = counts[counts >= min_obs].index
    df[new_col] = df[col].where(df[col].isin(major), "Other")
```

=== 3.3 Đặc Trưng Diễn Ngôn & Cảm Xúc (Narrative & Sentiment Features)
Tính toán tỷ lệ trên 100 từ cho 3 phong cách (gia đình, năng lực tự chủ, cấp bách) và điểm cảm xúc VADER (`desc_sentiment_compound`) trên toàn bộ tập dữ liệu hợp lệ (1.453.840 dòng).

```python
description = (
    df["description"].fillna("")
    .str.replace(r"<[^>]+>", " ", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)
word_count = description.str.split().str.len().clip(lower=1)

FAMILY_PATTERN = re.compile(r"\b(child|children|family|son|daughter|mother|father|wife|husband|school)\b", re.I)
AGENCY_PATTERN = re.compile(r"\b(decide|plan|manage|responsible|hard.?working|independent|own|run|lead)\w*\b", re.I)
URGENCY_PATTERN = re.compile(r"\b(urgent|immediately|emergency|crisis|desperate|asap|quickly)\w*\b", re.I)

for name, pattern in [("family", FAMILY_PATTERN), ("agency", AGENCY_PATTERN), ("urgency", URGENCY_PATTERN)]:
    df[f"{name}_mentions_per_100_words"] = description.str.count(pattern) / word_count * 100

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)
from nltk.sentiment.vader import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()
df["desc_sentiment_compound"] = description.apply(lambda text: analyzer.polarity_scores(text)["compound"])

valid = df.loc[df["funding_speed_days"].notna() & (df["funding_speed_days"] >= 0)].copy()
print(f"Valid rows: {len(valid)} / {len(df)}")
```

== 4. Phân Chia Dữ Liệu Theo Trình Tự Thời Gian (Data Split)

Để đánh giá trung thực xem mô hình có hoạt động hiệu quả trong thực tế hay không, dữ liệu bắt buộc phải được kiểm thử trên những khoản vay trong tương lai mà mô hình chưa từng thấy trong quá trình huấn luyện:
- *Tập huấn luyện (Train)*: 1.174.953 khoản vay đăng tải từ năm 2016 đến hết năm 2023.
- *Tập kiểm thử giữ lại (Holdout)*: 278.887 khoản vay đăng tải trong giai đoạn 2024–2025 (chiếm ~19% tổng dữ liệu).

Cách phân tách theo trục thời gian (chronological split) mô phỏng chính xác kịch bản triển khai sản phẩm thực tế và ngăn ngừa hoàn toàn hiện tượng rò rỉ dữ liệu (data leakage).

```python
train_raw = valid.loc[valid["fundraisingDate_parsed"] < pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
holdout_raw = valid.loc[valid["fundraisingDate_parsed"] >= pd.Timestamp(HOLDOUT_START, tz="UTC")].copy()
print(f"Train rows: {len(train_raw):,}  |  Holdout rows: {len(holdout_raw):,}")

NUMERIC_COLS = [
    "borrowerCount", "log_loan_amount", "lenderRepaymentTerm",
    "family_mentions_per_100_words", "agency_mentions_per_100_words",
    "urgency_mentions_per_100_words", "desc_sentiment_compound", "is_group_loan",
]
CATEGORICAL_COLS = ["gender_classification", "loan_size_band", "repaymentInterval", "sector", "region", "analysis_period"]

preprocessor = ColumnTransformer([
    ("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), NUMERIC_COLS),
    ("categorical", Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]), CATEGORICAL_COLS),
])

X_train = preprocessor.fit_transform(train_raw[NUMERIC_COLS + CATEGORICAL_COLS])
X_holdout = preprocessor.transform(holdout_raw[NUMERIC_COLS + CATEGORICAL_COLS])
y_train_log = train_raw["log_funding_speed"].to_numpy()
y_holdout_days = holdout_raw["funding_speed_days"].to_numpy()
```

== 5. Mô Hình Hồi Quy Dự Báo (Regression Modeling)

So sánh hai kiến trúc mô hình trên cùng tập dữ liệu kiểm thử:
1. *Mô hình hồi quy tuyến tính phạt Ridge*: Mô hình bảng điểm cộng gộp minh bạch, gán trọng số cố định cho từng biến số.
2. *Mô hình cây tăng cường (HistGradientBoostingRegressor)*: Mô hình phi tuyến linh hoạt, có khả năng tự học các quan hệ tương tác phức tạp giữa các yếu tố.

```python
# 1. Huấn luyện Ridge
ridge = Ridge(alpha=1.0, random_state=SEED)
ridge.fit(X_train, y_train_log)
ridge_holdout_days = np.expm1(np.clip(ridge.predict(X_holdout), a_min=0, a_max=None))
print(f"Ridge holdout MAE (days): {mean_absolute_error(y_holdout_days, ridge_holdout_days):.2f}")

# 2. Huấn luyện HistGradientBoostingRegressor
boosted = HistGradientBoostingRegressor(random_state=SEED)
boosted.fit(X_train.toarray() if hasattr(X_train, "toarray") else X_train, y_train_log)
X_holdout_dense = X_holdout.toarray() if hasattr(X_holdout, "toarray") else X_holdout
boosted_holdout_days = np.expm1(np.clip(boosted.predict(X_holdout_dense), a_min=0, a_max=None))
print(f"Boosted holdout MAE (days): {mean_absolute_error(y_holdout_days, boosted_holdout_days):.2f}")
print(f"Boosted holdout R2: {r2_score(y_holdout_days, boosted_holdout_days):.3f}")
```

```output
Ridge holdout MAE (days): 6.76
Boosted holdout MAE (days): 5.56
Boosted holdout R2: 0.490
```

#align(center)[
  #image("/docs/presentation/charts/notebook/mod_21_5_regression_modeling.png", width: 75%)
]

#insight_box([
Kiểm định trên các khoản vay mà mô hình hoàn toàn chưa từng nhìn thấy (năm 2024–2025):
- Mô hình cộng gộp tuyến tính đơn giản (Ridge) có sai số MAE là *6,76 ngày*.
- Mô hình cây tăng cường phi tuyến (Boosted trees) rút ngắn sai số xuống còn *5,56 ngày* và giải thích được tới *49,0% phương sai dự báo* của tốc độ gọi vốn ($R^2 = 0.490$). 
- Gần một nửa mức độ khác biệt về tốc độ gọi vốn giữa các khoản vay có thể được giải thích bằng thông tin đã biết tại thời điểm đăng tải; nửa còn lại thuộc về các yếu tố dữ liệu không ghi nhận được (độ hấp dẫn chủ quan đối với từng cá nhân, sự may mắn về thời điểm, v.v.). Việc mô hình phi tuyến vượt trội hơn bảng điểm tuyến tính hơn 1 ngày sai số chứng minh rằng: *tốc độ gọi vốn không phải là một danh sách cộng dồn đơn giản — một số yếu tố phát huy tác dụng mạnh hơn khi kết hợp cùng nhau.*
])

== 6. Mô Hình Phân Loại Khoản Vay Gọi Vốn Nhanh (Funding Classification)

Dự báo chính xác số ngày gọi vốn là một bài toán khó và mang tính biến thiên cao. Một bài toán thực tiễn và dễ hành động hơn đối với đội ngũ vận hành sản phẩm: *Liệu khoản vay này có hoàn thành huy động vốn trong vòng 24 giờ hay không (Có / Không)?* Việc gắn cờ cảnh báo sớm cho các khoản vay có nguy cơ bị chậm trễ là một tính năng vận hành có giá trị trực tiếp.

```python
y_train_binary = train_raw["funded_within_24h"].to_numpy()
y_holdout_binary = holdout_raw["funded_within_24h"].to_numpy()

classifier = HistGradientBoostingClassifier(random_state=SEED)
classifier.fit(X_train_dense, y_train_binary)
holdout_proba = classifier.predict_proba(X_holdout_dense)[:, 1]

print(f"Holdout ROC AUC: {roc_auc_score(y_holdout_binary, holdout_proba):.4f}")
print(f"Holdout average precision: {average_precision_score(y_holdout_binary, holdout_proba):.4f}")
```

```output
Holdout ROC AUC: 0.9053
Holdout average precision: 0.8374
```

#insight_box([
*Kết quả ứng dụng thực tiễn mạnh mẽ nhất của toàn bộ nghiên cứu:*
Chỉ số *ROC AUC đạt 0,905* (so với 0,5 là đoán ngẫu nhiên) và *Average Precision đạt 0,837* trên tập kiểm thử giữ lại độc lập. Cần lưu ý rằng tỷ lệ khoản vay hoàn thành trong 24 giờ ở giai đoạn này chỉ chiếm khoảng 30%, do đó việc đoán mò ngẫu nhiên sẽ có hiệu suất rất kém. 

Điều này khẳng định: *Một công cụ được xây dựng thuần túy từ thông tin sẵn có tại thời điểm đăng tải (quy mô vay, ngành nghề, khu vực, văn bản) có thể phân loại và gắn cờ cảnh báo rủi ro cực kỳ chuẩn xác cho các khoản vay chậm gọi vốn* — hoàn toàn độc lập với việc phong cách kể chuyện có tạo ra hiệu ứng nhân quả hay không.
])

== 7. Mô Hình Giải Thích Đa Biến (Explanatory Modeling)

Mô hình học máy ở trên dự báo rất tốt, nhưng nó không giải thích lý do *tại sao*. Phần này sử dụng hồi quy OLS đa biến để đo lường mức độ liên hệ của từng yếu tố với tốc độ gọi vốn khi giữ cố định tất cả các yếu tố còn lại.

```python
FORMULA = (
    "log_funding_speed ~ log_loan_amount + lenderRepaymentTerm + is_group_loan + "
    "C(gender_classification) + family_mentions_per_100_words + agency_mentions_per_100_words + "
    "urgency_mentions_per_100_words + desc_sentiment_compound + C(repaymentInterval) + "
    "C(sector_group) + C(region_group) + C(analysis_period) + C(loan_size_band) + "
    "family_mentions_per_100_words:C(analysis_period) + "
    "family_mentions_per_100_words:C(region_group) + "
    "family_mentions_per_100_words:C(loan_size_band)"
)
y, X = patsy.dmatrices(FORMULA, data=valid, return_type="dataframe")
with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    duration_model = sm.OLS(y, X).fit(cov_type="HC3")
print(duration_model.summary())
```

```output
                            OLS Regression Results                            
==============================================================================
Dep. Variable:      log_funding_speed   R-squared:                       0.426
Model:                            OLS   Adj. R-squared:                  0.425
No. Observations:             1453840   AIC:                         4.037e+06
Df Residuals:                 1453794   BIC:                         4.037e+06
Df Model:                          45                                         
Covariance Type:                  HC3                                         
==================================================================================================================
                                                                     coef   std err         z      P>|z|  [0.025  0.975]
------------------------------------------------------------------------------------------------------------------
Intercept                                                         -1.2630     0.021   -61.478      0.000  -1.303  -1.223
C(gender_classification)[T.male]                                   0.4336     0.002   177.927      0.000   0.429   0.438
C(repaymentInterval)[T.irregularly]                               -0.3776     0.006   -68.617      0.000  -0.388  -0.367
C(repaymentInterval)[T.monthly]                                   -0.1058     0.004   -27.795      0.000  -0.113  -0.098
C(sector_group)[T.Education]                                      -1.0702     0.006  -188.773      0.000  -1.081  -1.059
C(sector_group)[T.Water]                                          -1.1152     0.032   -35.166      0.000  -1.177  -1.053
C(sector_group)[T.Clean Energy]                                   -0.8024     0.005  -159.708      0.000  -0.812  -0.793
C(sector_group)[T.Clothing]                                        0.2592     0.005    50.466      0.000   0.249   0.269
C(sector_group)[T.Retail]                                          0.2009     0.003    73.407      0.000   0.196   0.206
C(region_group)[T.Middle East]                                    -1.0710     0.021   -50.709      0.000  -1.112  -1.030
C(loan_size_band)[T.small]                                        -0.5758     0.007   -81.917      0.000  -0.590  -0.562
log_loan_amount                                                    0.4285     0.003   154.717      0.000   0.423   0.434
lenderRepaymentTerm                                                0.0676     0.000   189.233      0.000   0.067   0.068
urgency_mentions_per_100_words                                    -0.0795     0.009    -8.917      0.000  -0.097  -0.062
desc_sentiment_compound                                            0.1116     0.003    37.367      0.000   0.106   0.117
agency_mentions_per_100_words                                      0.0007     0.001     0.739      0.460  -0.001   0.002
==================================================================================================================
```

```output
Danh mục tham chiếu (bị lược bỏ trong ma trận dummy):
  gender_classification: ['female']
  repaymentInterval:     ['at_end']
  sector_group:          ['Agriculture']
  region_group:          ['Africa']
  analysis_period:       ['pandemic_disruption']
  loan_size_band:        ['large']
```

=== 7.1 Kiểm định Độ nhạy với Sai số Phân cụm theo Quốc gia (Cluster-Robust Sensitivity Check)

Sai số chuẩn HC3 điều chỉnh cho hiện tượng phương sai sai số thay đổi giữa các khoản vay, nhưng vẫn giả định mọi khoản vay là quan sát độc lập. Trong thực tế, các khoản vay từ cùng một quốc gia chịu ảnh hưởng chung bởi các yếu tố tiềm ẩn không quan sát được (mẫu viết của đối tác địa phương, điều kiện kinh tế vi mô, tập quán văn hóa). 

Thử nghiệm này chạy lại chính xác mô hình trên với *sai số chuẩn phân cụm theo quốc gia (`country_name`)*:

```python
duration_model_clustered = sm.OLS(y, X).fit(
    cov_type="cluster", cov_kwds={"groups": valid.loc[X.index, "country_name"]}
)
```

```output
So sánh các biến diễn ngôn & cảm xúc: HC3 thông thường vs. Phân cụm theo quốc gia (Clustered):
  family_mentions_per_100_words:                             HC3 p=0.0000, clustered p=0.7638 [KẾT LUẬN THAY ĐỔI]
  family:analysis_period[T.post_pandemic]:                   HC3 p=0.0000, clustered p=0.5298 [KẾT LUẬN THAY ĐỔI]
  family:analysis_period[T.pre_pandemic]:                    HC3 p=0.0000, clustered p=0.2269 [KẾT LUẬN THAY ĐỔI]
  family:region_group[T.Asia]:                               HC3 p=0.0000, clustered p=0.1248 [KẾT LUẬN THAY ĐỔI]
  family:region_group[T.Central America]:                    HC3 p=0.0000, clustered p=0.0070 [CÙNG KẾT LUẬN]
  family:region_group[T.Middle East]:                        HC3 p=0.0000, clustered p=0.0002 [CÙNG KẾT LUẬN]
  family:region_group[T.North America]:                      HC3 p=0.0000, clustered p=0.2365 [KẾT LUẬN THAY ĐỔI]
  family:region_group[T.Oceania]:                            HC3 p=0.0000, clustered p=0.4406 [KẾT LUẬN THAY ĐỔI]
  family:loan_size_band[T.medium]:                           HC3 p=0.0000, clustered p=0.4389 [KẾT LUẬN THAY ĐỔI]
  family:loan_size_band[T.small]:                            HC3 p=0.1719, clustered p=0.9039 [CÙNG KẾT LUẬN]
  agency_mentions_per_100_words:                             HC3 p=0.4597, clustered p=0.9412 [CÙNG KẾT LUẬN]
  urgency_mentions_per_100_words:                            HC3 p=0.0000, clustered p=0.4442 [KẾT LUẬN THAY ĐỔI]
  desc_sentiment_compound:                                   HC3 p=0.0000, clustered p=0.2544 [KẾT LUẬN THAY ĐỔI]

Trên tổng số 45 hệ số của mô hình, có 20 hệ số (44%) THAY ĐỔI KẾT LUẬN Ý NGHĨA THỐNG KÊ khi phân cụm!
```

#warning_box([
*Đây là bài học phương pháp luận quan trọng nhất:* 
1. *Ảo tưởng về tính cấp bách (Urgency):* Dưới mô hình HC3 đơn giản, tính cấp bách có vẻ là một phát hiện thắng thế rực rỡ ($p < 0.001$, hệ số âm thể hiện gọi vốn nhanh hơn). Tuy nhiên, khi tính đến sự tương quan nội tại giữa các khoản vay trong cùng quốc gia, $p$-value vọt lên tới *0,44* — hoàn toàn không còn ý nghĩa thống kê!
2. *Hiệu ứng gia đình theo thời gian và quy mô vay sụp đổ:* Mọi tương tác của yếu tố gia đình với thời kỳ đại dịch và quy mô khoản vay đều tăng $p > 0.20$.
3. *Tập trung sự thay đổi:* 20 trên 45 hệ số thay đổi kết luận, tập trung toàn bộ ở nhóm biến diễn ngôn và cảm xúc. Trong khi đó, các biến cấu trúc cứng (ngành nghề, khu vực, số tiền vay, giới tính, kỳ hạn) vẫn giữ nguyên ý nghĩa thống kê tuyệt đối.
])

=== 7.2 Mối Liên Hệ Của Yếu Tố Gia Đình Trong Từng Khu Vực (Within-Region Slopes)

Hệ số tương tác `family:region[T.X]` ở trên chỉ kiểm định xem độ dốc của khu vực X có khác với khu vực cơ sở (Châu Phi) hay không, chứ *không kiểm định xem bản thân độ dốc bên trong khu vực X có khác 0 hay không*. 

Để biết chính xác ngôn ngữ gia đình có liên hệ với tốc độ gọi vốn bên trong từng khu vực hay không, ta tính *độ dốc trung bình nội vùng (average within-region slope)* bằng phép tương phản tuyến tính (linear contrast qua `t_test`), lấy trọng số theo phân phối thực tế của từng khu vực về thời kỳ và quy mô khoản vay:

```output
Khu vực           Quốc gia   Số khoản vay   Hệ số ước lượng   HC3 p-val   Clustered p   Đối chuẩn phân phối t cụm nhỏ      Kết luận
------------------------------------------------------------------------------------------------------------------------------------
Africa                 27        610,368        -0.0101         0.0000        0.5536    few-cluster t(26) p=0.5587         Không có ý nghĩa
Asia                   12        738,191        +0.0338         0.0000        0.0535    few-cluster t(11) p=0.0797         Không có ý nghĩa
Central America         2         59,391        -0.0618         0.0000        0.0000    few-cluster t(1)  p=0.0650         Chỉ có ý nghĩa chuẩn; KHÔNG đạt t cụm nhỏ
Middle East             2         14,946        -0.1236         0.0000        0.0000    few-cluster t(1)  p=0.0753         Chỉ có ý nghĩa chuẩn; KHÔNG đạt t cụm nhỏ
North America           1          7,559        +0.0109         0.0011        0.0621    không ước lượng được (1 nước)      Không có ý nghĩa
Oceania                 4         23,385        +0.0162         0.0000        0.6305    few-cluster t(3)  p=0.6634         Không có ý nghĩa
```

#insight_box([
*Bản chất thực sự là mô tả (Descriptive pattern), không phải quy luật phổ quát:*
- Nếu chỉ dùng phép kiểm định phân cụm thông thường dựa trên xấp xỉ phân phối chuẩn, có 2 khu vực đạt $p < 0.05$ theo chiều hướng gọi vốn nhanh hơn: Trung Đông (-0.124) và Trung Mỹ (-0.062). 
- Tuy nhiên, mỗi khu vực này thực chất chỉ bao gồm *đúng 2 quốc gia* (Trung Đông là Palestine & Yemen; Trung Mỹ là Honduras & Nicaragua). Việc cộng dồn hàng nghìn khoản vay trong 2 quốc gia không tạo ra thêm bằng chứng độc lập!
- Khi đối chiếu với phân phối $t$ có bậc tự do bằng $G - 1 = 1$ (giá trị tới hạn ở mức 95% vọt lên tới 12,7 thay vì 1,96), *cả hai khu vực đều không vượt qua ngưỡng ý nghĩa thống kê*. Khoảng tin cậy đều bao trùm giá trị 0.
- *Kết luận:* Đây là một *giả thuyết cần kiểm định A/B phân tầng theo quốc gia*, không phải là một phát hiện đã được chứng minh để triển khai thành quy tắc viết bài cho toàn bộ nền tảng.
])

== 8. Tầm Quan Trọng Của Các Đặc Trưng (Feature Importance với SHAP)

Mô hình OLS ở Phần 7 chỉ kiểm tra các mối liên hệ tuyến tính định trước. Mô hình cây tăng cường (Boosted trees) tự học mọi mối quan hệ trong dữ liệu mà không bị giới hạn. Phương pháp SHAP (SHapley Additive exPlanations) bóc tách mô hình hộp đen này, tính toán chính xác mức độ đóng góp của từng đặc trưng trên mẫu 2.000 khoản vay kiểm thử:

```output
Top 15 đặc trưng có giá trị trung bình |SHAP| cao nhất (mô hình Boosted):
 1. numeric__log_loan_amount                            0.446165
 2. numeric__lenderRepaymentTerm                        0.337281
 3. categorical__analysis_period_pre_pandemic           0.220126
 4. categorical__loan_size_band_small                   0.149013
 5. categorical__sector_Retail                          0.077729
 6. categorical__gender_classification_female           0.064640
 7. categorical__analysis_period_pandemic_disruption    0.053453
 8. categorical__region_Asia                            0.044537
 9. categorical__sector_Food                            0.043646
10. categorical__sector_Education                       0.039283
11. numeric__desc_sentiment_compound                    0.036779
12. categorical__gender_classification_male             0.036215
13. categorical__analysis_period_post_pandemic          0.026283
14. categorical__region_Africa                          0.023729
15. categorical__sector_Sanitation & Hygiene            0.020011
```

#align(center)[
  #image("/docs/presentation/charts/notebook/mod_39_8_feature_importance.png", width: 85%)
]

- *Quy mô vay và kỳ hạn hoàn trả hoàn toàn áp đảo:* Hai yếu tố cấu trúc này là những biến số mà mô hình linh hoạt dựa vào nhiều nhất để đưa ra quyết định dự báo.
- *Các phong cách kể chuyện (gia đình, năng lực, cấp bách) hoàn toàn vắng bóng trong Top 15:* Điều này tái khẳng định phát hiện ở Phần 7.1 rằng các đặc trưng diễn ngôn có đóng góp dự báo thực tế rất nhỏ bé. Chỉ duy nhất điểm cảm xúc tổng thể lọt vào vị trí thứ 11, nhưng vẫn đứng sau hàng loạt danh mục ngành nghề và khu vực.

== 9. Những Phát Hiện Cốt Lõi (Key Findings)

=== 9.1 Diễn Giải Kỹ Thuật (Technical Interpretation)
1. *Khả năng dự báo vượt trội từ thông tin ban đầu:* Mô hình đạt $R^2 = 0.49$, MAE 5,6 ngày trên tập kiểm thử giữ lại theo trình tự thời gian 2024–2025, và mô hình phân loại nhị phân 24 giờ đạt ROC AUC 0,91.
2. *Cấu trúc cứng chi phối:* Quy mô vay, kỳ hạn hoàn trả, ngành nghề, khu vực và giới tính người vay có độ lớn hệ số gấp nhiều lần so với bất kỳ biến số diễn ngôn nào.
3. *Kiểm định sai số phân cụm phủ nhận các kết luận đơn giản:* 44% hệ số thay đổi ý nghĩa thống kê khi phân cụm theo quốc gia. Tính cấp bách và hầu hết các tương tác điều kiện của yếu tố gia đình không còn ý nghĩa.
4. *Bản chất của hiệu ứng khu vực:* Tác động tích cực của ngôn ngữ gia đình ở Trung Đông và Trung Mỹ chỉ xuất phát từ 2 quốc gia mỗi vùng và không vượt qua được kiểm định số lượng cụm nhỏ ($t(1)$).
5. *Sự bất định của biến cảm xúc:* Điểm cảm xúc có ý nghĩa trong một số cấu trúc mô hình phức tạp hơn nhưng không bền vững trong mô hình đơn giản này.

=== 9.2 Tác Động Quản Trị & Kinh Doanh (Business Impact)
- *Bộ phân loại 24 giờ là một nguyên mẫu xếp hạng hồi cứu (retrospective prototype):* Mô hình đạt ROC AUC 0,91 nhưng chỉ được xác thực trên các khoản vay sau cùng đã gọi vốn thành công. Để đưa vào vận hành cảnh báo sớm thời gian thực, cần tích hợp cả dữ liệu khoản vay bị hết hạn/hủy bỏ và kiểm định tiền khả thi (prospective test).
- *Tuyệt đối không khuyến nghị dùng ngôn ngữ cấp bách trên toàn sàn:* Hiệu ứng này là một hiện tượng thống kê giả tạo do sai số chưa được phân cụm đúng mức.
- *Không ban hành hướng dẫn chung \"nhắc đến gia đình\":* Trên 95% dữ liệu (Châu Phi, Châu Á, Bắc Mỹ, Châu Đại Dương), yếu tố này không có liên hệ ý nghĩa với tốc độ gọi vốn.
- *Ưu tiên tối ưu hóa cấu trúc hơn là câu chữ:* Thay vì tập trung huấn luyện người vay cách viết bài, Kiva và các đối tác nên xem xét lại cấu trúc hiển thị theo ngành nghề, kỳ hạn và quy mô vốn — những yếu tố thực sự quyết định sự thành bại và tốc độ của dòng vốn vi mô.
