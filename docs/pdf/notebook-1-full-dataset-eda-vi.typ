// ============================================================================
// UNSW MARKETING ANALYTICS HACKATHON 2026
// Sổ tay Kaggle 1: Phân tích Khám phá Dữ liệu Toàn diện (Full-Dataset EDA)
// Bản dịch tiếng Việt đầy đủ và chuẩn hóa học thuật
// ============================================================================

#set page(
  paper: "a4",
  margin: (x: 2cm, top: 2.5cm, bottom: 2.5cm),
  header: [
    #grid(
      columns: (1fr, auto),
      align(left)[#text(fill: rgb("#205493"), weight: "bold", size: 8pt)[UNSW MARKETING ANALYTICS HACKATHON 2026]],
      align(right)[#text(fill: rgb("#6b7280"), size: 8pt)[Kaggle notebook — Notebook 1 - Full-Dataset EDA (Bản tiếng Việt)]]
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
  text(font: ("Menlo", "Courier New"), size: 7.8pt, it)
)

#show raw.where(lang: "output"): it => block(
  fill: rgb("#fbfcfd"),
  inset: 7pt,
  radius: 3pt,
  width: 100%,
  stroke: 0.5pt + rgb("#d1d5db"),
  text(font: ("Menlo", "Courier New"), size: 7.5pt, it.text)
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

= Kiva Loans: Khám phá Dữ liệu Toàn diện (1.45 triệu khoản vay)

#link("https://www.kiva.org")[*Kiva*] là một nền tảng cho vay vi mô phi lợi nhuận: những người bình thường trên khắp thế giới ("người cho vay" - lenders) mỗi người đóng góp một khoản tiền nhỏ hướng tới một khoản vay dành cho người đi vay ở một nơi nào đó trên thế giới, thường nhằm mục đích phát triển kinh doanh nhỏ hoặc trang trải nhu cầu thiết yếu của gia đình. Khi có đủ số lượng người cho vay góp vốn, khoản vay sẽ được huy động vốn hoàn toàn và số tiền được giải ngân.

Phân tích này đặt ra câu hỏi trọng tâm: *cách viết và kể câu chuyện của một khoản vay* có liên hệ như thế nào với *tốc độ khoản vay đó được huy động vốn*? Cụ thể, liệu việc nhấn mạnh vào các lời kêu gọi hướng về gia đình/cộng đồng, việc xây dựng câu chuyện theo hướng năng lực/độc lập kinh doanh, hay ngôn ngữ tạo tính cấp bách có tương quan với tốc độ huy động vốn nhanh hơn hay không — và liệu câu trả lời đó có thay đổi tùy thuộc vào bối cảnh kinh tế hoặc loại hình khoản vay hay không. 

Một khoản vay nằm chờ gọi vốn càng lâu thì trải nghiệm của người đi vay càng khó khăn và việc tận dụng sự chú ý của người cho vay càng kém hiệu quả. Do đó, một mối liên hệ thực chất, nhất quán giữa khung diễn ngôn (narrative framing) và tốc độ gọi vốn sẽ là một *đòn bẩy có thể can thiệp trong thực tiễn (actionable lever)* — loại phát hiện có thể định hình các hướng dẫn viết và truyền thông câu chuyện cho người đi vay. Ngược lại, nếu phong cách viết hầu như không mang lại tác động nào đáng kể so với các yếu tố mang tính cấu trúc cứng của khoản vay, thì đó cũng là một sự thật vô cùng hữu ích để Kiva và các đối tác địa phương nhận biết.

Sổ tay này đảm nhận phần *nền tảng mô tả* trên toàn bộ tập dữ liệu thực tế đầy đủ (không phải mẫu thử nghiệm 100 dòng được dùng trong đề xuất ban đầu); tài liệu tiếp theo `2_full_dataset_modeling.ipynb` sẽ kế thừa nền tảng này bằng các mô hình thống kê kiểm soát đồng thời tất cả các yếu tố.

== 1. Cài đặt môi trường (Setup)

```python
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

SEED = 42
MIN_REGION_OBSERVATIONS = 10
MIN_SECTOR_OBSERVATIONS = 1000

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

sns.set_theme(style="whitegrid", palette="viridis")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 12
```

== 2. Tải Dữ liệu (Load Data)

```python
# Tệp pickle là danh sách các từ điển hàng (list of row dicts), không phải một DataFrame 
# được pickle trực tiếp (pd.read_pickle sẽ báo lỗi) - sử dụng pickle.load tiêu chuẩn
import pickle  # noqa: E402
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

27 trường dữ liệu thô, gần như tất cả đều được điền đầy đủ — phần lớn các cột ghi nhận gần 1.453.846 giá trị không rỗng, chỉ có một số ít trường địa lý (`latitude`, `longitude`) có dữ liệu khuyết thiếu đáng kể. Đây là một tập dữ liệu sạch, gần như hoàn chỉnh để xây dựng phân tích.

```python
# Xem trước một mẫu hàng thực tế, giới hạn ở các cột mô tả bản chất của *khoản vay* 
# thay vì thông tin định danh cá nhân của *người đi vay* - có chủ đích loại trừ name/id/image_url 
# và văn bản tự do/dấu thời gian chính xác để bảo mật quyền riêng tư.
preview_cols = [
    "gender", "borrowerCount", "loanAmount", "sector", "activity",
    "region", "country_name", "repaymentInterval",
]
df[preview_cols].head(8)
```

Mỗi hàng đại diện cho một khoản vay có thật, với đầy đủ các thuộc tính chuẩn: đối tượng vay (giới tính, số lượng người vay), quy mô vay (số tiền vay bằng USD), mục đích vay (ngành nghề, hoạt động), vị trí địa lý (khu vực, quốc gia) và cơ cấu kỳ hạn hoàn trả. Hai nhóm trường quan trọng khác tồn tại trong tập dữ liệu nhưng không được hiển thị từng dòng vì lý do bảo mật: văn bản mô tả tự do (`description`) được viết cho người cho vay, và hai mốc thời gian — thời điểm đăng tải (`fundraisingDate`) và thời điểm hoàn tất gọi vốn (`raisedDate`) — khoảng cách giữa hai mốc này chính là chủ đề nghiên cứu xuyên suốt của sổ tay.

== 3. Biến Mục Tiêu (Target Variable)

Mỗi khoản vay có một ngày đăng tải và một ngày hoàn tất gọi vốn. Khoảng cách giữa hai mốc này, `funding_speed_days`, thể hiện số ngày người cho vay cần để tài trợ đủ khoản tiền — xấp xỉ 0 đối với khoản vay hoàn tất trong ngày, và 21 ngày đối với khoản vay mất ba tuần. Giá trị âm hoặc khuyết thiếu thể hiện bản ghi không hợp lệ và bị loại bỏ, tuyệt đối không suy đoán. Biến `funded_within_24h` là một phiên bản nhị phân đơn giản hơn (Có/Không: hoàn tất trong 24 giờ). Cả hai chỉ số này chỉ tồn tại đối với các khoản vay *đã thực sự hoàn thành gọi vốn* — dữ liệu này không đánh giá việc một khoản vay có gọi vốn thành công hay không, mà chỉ đánh giá *tốc độ hoàn thành khi đã thành công*.

```python
fundraising = pd.to_datetime(df["fundraisingDate"], errors="coerce", utc=True)
raised = pd.to_datetime(df["raisedDate"], errors="coerce", utc=True)
df["funding_speed_days"] = (raised - fundraising).dt.total_seconds() / 86400
df["log_funding_speed"] = np.log1p(df["funding_speed_days"].clip(lower=0))
df["funded_within_24h"] = (df["funding_speed_days"] <= 1).astype("Int64")
year = fundraising.dt.year
df["analysis_period"] = pd.cut(
    year, bins=[-np.inf, 2019, 2021, np.inf],
    labels=["pre_pandemic", "pandemic_disruption", "post_pandemic"],
)
valid = df.loc[df["funding_speed_days"].notna() & (df["funding_speed_days"] >= 0)].copy()

print(f"Rows loaded: {len(df)}")
print(f"Rows with a valid completed outcome: {len(valid)}")
print(f"Rows excluded: {len(df) - len(valid)}")
print(f"Status among valid rows:\n{valid['status'].value_counts().to_string()}")
```

```output
Rows loaded: 1453846
Rows with a valid completed outcome: 1453840
Rows excluded: 6
Status among valid rows:
status
funded      1452203
refunded       1637
```

- *Tập dữ liệu gần như sử dụng được trọn vẹn*: 1.453.840 trên tổng số 1.453.846 khoản vay (99,9996%) có thời gian gọi vốn hợp lệ và không âm — chỉ 6 dòng bị loại do lỗi chất lượng dữ liệu (ngày hoàn tất lại diễn ra trước ngày đăng tải), không phải do bị bỏ sót.
- *Trong số các hàng hợp lệ*, 1.452.203 khoản vay (99,89%) ở trạng thái đã gọi vốn (`funded`) và 1.637 khoản vay (0,11%) được hoàn trả lại (`refunded`) — các khoản hoàn trả vẫn được giữ nguyên vai trò vì việc hoàn tiền là sự kiện phát sinh sau đó; khoản vay vốn đã được gọi đủ tiền trên sàn.
- Với quy mô dữ liệu gấp 14.500 lần mẫu thử nghiệm tuần đầu tiên, độ phủ gần như tuyệt đối này đảm bảo các kết luận dưới đây không phải là hiện tượng ngẫu nhiên của mẫu nhỏ.

#align(center)[
  #image("/docs/presentation/charts/notebook/eda_13_3_target_variable.png", width: 88%)
]

*Nhận định về phân phối:* Phần lớn các khoản vay được huy động vốn rất nhanh (cột cao vọt gần mốc 0 ở biểu đồ bên trái), với một phần đuôi dài kéo dài nhiều tuần cho các khoản vay chậm. Biểu đồ bên phải áp dụng phép biến đổi logarit (`log1p`), giúp thu gọn phần đuôi dài này để phân phối tiệm cận dạng hình chuông đối xứng hơn — các kỹ thuật mô hình hóa (được triển khai ở Notebook 2) hoạt động tốt hơn rất nhiều trên dữ liệu có phân phối dạng logarit này; cả hai biểu đồ đều mô tả cùng một hiện tượng bản chất.

== 4. Xu hướng theo Nhóm Phân loại (Categorical Trends)

Tốc độ gọi vốn khác biệt như thế nào qua hai phép phân nhóm cơ bản: *thời điểm đăng tải khoản vay* và *giới tính của người đi vay*?

```python
period_counts = df["analysis_period"].value_counts(dropna=False).sort_index()
print("Rows per analysis period:")
print(period_counts.to_string())

within_24h_by_period = valid.dropna(subset=["funded_within_24h"]).groupby(
    "analysis_period", observed=True
)["funded_within_24h"].mean()
print("\nShare funded within 24 hours, by period:")
print(within_24h_by_period.to_string())
```

```output
Rows per analysis period:
analysis_period
pre_pandemic           589823
pandemic_disruption    298549
post_pandemic          565474

Share funded within 24 hours, by period:
analysis_period
pre_pandemic            0.46028
pandemic_disruption     0.30321
post_pandemic           0.299945
```

#align(center)[
  #image("/docs/presentation/charts/notebook/eda_17_4_categorical_trends.png", width: 88%)
]

#insight_box([
*Phát hiện tiêu đề quan trọng nhất của sổ tay này:* Tỷ lệ các khoản vay được huy động vốn trong vòng 24 giờ *đã giảm gần một nửa và không hề phục hồi* cho đến hết khoảng thời gian dữ liệu (năm 2025) — cụ thể: *46,0% thời kỳ tiền đại dịch $arrow.r$ 30,3% trong giai đoạn xáo trộn đại dịch $arrow.r$ 30,0% thời kỳ hậu đại dịch*. 

Trước năm 2020, gần một nửa số khoản vay hoàn tất gọi vốn trong vòng một ngày kể từ khi đăng tải; từ năm 2020 trở đi, con số này sụt giảm xuống dưới một phần ba và giữ nguyên ở mức đó trong suốt 4 năm sau khi giai đoạn biến động đại dịch kết thúc. Đây không phải là một biến động nhỏ ngẫu nhiên — có 589.823 khoản vay ở nhóm "trước" và 565.474 khoản vay ở nhóm "sau". Bất kể yếu tố nào làm thay đổi cơ chế tài trợ vốn của thị trường Kiva quanh năm 2020, nó đã tồn tại dai dẳng cho đến nay. Dữ liệu ghi nhận sự tồn tại này một cách khách quan, không đưa ra khẳng định nhân quả mang tính chủ quan.
])

```python
# Tốc độ gọi vốn theo giới tính người đi vay
fig, ax = plt.subplots(figsize=(8, 5))
sns.boxplot(data=valid, x="gender", y="funding_speed_days", hue="gender", 
            legend=False, palette="viridis", ax=ax)
ax.set_title("Funding speed by borrower gender")
plt.tight_layout()
plt.show()

print("Median funding speed (days), by gender:")
print(valid.groupby("gender", observed=True)["funding_speed_days"].median().to_string())
```

```output
Median funding speed (days), by gender:
gender
female    2.332182
male      7.713970
```

#align(center)[
  #image("/docs/presentation/charts/notebook/eda_19_4_categorical_trends.png", width: 65%)
]

Các khoản vay được đăng dưới tên người đi vay là *nam giới* mất nhiều thời gian hơn rõ rệt để huy động đủ vốn so với người đi vay là *nữ giới* (trung vị: 7,71 ngày so với 2,33 ngày), ngay cả trong góc nhìn đơn biến giản dị này. Cần đặc biệt lưu ý điểm này khi bước sang sổ tay mô hình hóa: khoảng cách chênh lệch này vẫn tồn tại sau khi đã kiểm soát toàn bộ các đặc trưng khác của khoản vay — tuy nhỏ hơn hiệu ứng của ngành nghề và khu vực lớn nhất, nhưng lớn hơn hiệu ứng của chính quy mô số tiền vay, và lớn hơn tất cả các biến số về phong cách kể chuyện cộng lại!

== 5. Các Đặc Trưng Phân Loại (Categorical Features)

Khảo sát mở rộng trên các trường phân loại còn lại: *ngành nghề* (sector), *khu vực địa lý* (region) và *kỳ hạn hoàn trả* (repayment interval). Ngành nghề và khu vực được gộp nhóm trước để bất kỳ danh mục nào có quá ít khoản vay — dưới `MIN_SECTOR_OBSERVATIONS` (1.000) cho ngành nghề và `MIN_REGION_OBSERVATIONS` (10) cho khu vực — sẽ được gộp vào danh mục "Other" thay vì vẽ riêng lẻ; quy tắc này tương tự quy tắc trong mô hình hóa để tránh việc một nhóm nhỏ gây nhiễu tạo ra các cột ước lượng sai lệch.

```python
overall_avg_speed = valid["funding_speed_days"].mean()

def _barh_avg_speed_with_counts(series_grouped_by: pd.Series, ax, title: str, 
                                show_legend: bool = False) -> None:
    """Vẽ biểu đồ thanh ngang thể hiện tốc độ gọi vốn trung bình kèm số lượng quan sát n."""
    stats = valid.groupby(series_grouped_by, observed=True)["funding_speed_days"].agg(["mean", "count"]).sort_values("mean")
    stats["mean"].plot(kind="barh", color=plt.cm.viridis(np.linspace(0.1, 0.9, len(stats))), legend=False, ax=ax)
    avg_line = ax.axvline(overall_avg_speed, color="red", linestyle="--", linewidth=1, label="Overall average")
    for i, (mean_val, count_val) in enumerate(zip(stats["mean"], stats["count"])):
        ax.text(mean_val, i, f"  n={count_val:,}", va="center", fontsize=8, color="dimgray")
    ax.set_xlabel("Average funding speed (days)")
    ax.set_title(title)
    if show_legend:
        ax.legend(handles=[avg_line])

for col, min_obs, new_col in [("sector", MIN_SECTOR_OBSERVATIONS, "sector_group"), 
                              ("region", MIN_REGION_OBSERVATIONS, "region_group")]:
    counts = valid[col].value_counts()
    major = counts[counts >= min_obs].index
    valid[new_col] = valid[col].where(valid[col].isin(major), "Other")
```

#align(center)[
  #image("/docs/presentation/charts/notebook/eda_22_5_categorical_features.png", width: 78%)
]

#align(center)[
  #image("/docs/presentation/charts/notebook/eda_23_5_categorical_features.png", width: 88%)
]

- *Ngành nghề (Sector) có ảnh hưởng cực kỳ lớn*: khoảng cách giữa các ngành được tài trợ nhanh nhất (Năng lượng sạch, Y tế, Giáo dục) và chậm nhất (Bán buôn/Bán lẻ, Vận tải) áp đảo hoàn toàn bất kỳ hiệu ứng nào mà khung diễn ngôn có thể mang lại. Mọi ngành nghề hiển thị đều có hơn 1.000 quan sát, loại trừ khả năng do nhiễu mẫu nhỏ.
- *Khu vực địa lý (Region) cũng thể hiện biên độ phân hóa lớn*: tốc độ gọi vốn thay đổi mạnh mẽ tùy thuộc vào nơi người vay sinh sống, độc lập với cách viết văn bản câu chuyện.
- *Kỳ hạn hoàn trả (Repayment interval) cho thấy mô thức rõ nét*: các khoản vay hoàn trả một lần vào cuối kỳ (`at_end`) mất thời gian lâu hơn đáng kể so với các khoản vay hoàn trả hàng tháng (`monthly`) hoặc không định kỳ (`irregularly`).

Tất cả các yếu tố trên đều là *thuộc tính cấu trúc cứng* của khoản vay. Sự biến thiên khổng lồ từ các biến cấu trúc trước khi mô hình hóa là dấu hiệu báo trước cho kết luận cốt lõi: *Cấu trúc khoản vay quan trọng hơn nhiều so với nghệ thuật kể chuyện.*

== 6. Khung Diễn Ngôn Câu Chuyện (Narrative Framing)

Mỗi mô tả khoản vay được chấm điểm trên ba phong cách thuyết phục, dựa trên các nghiên cứu về tâm lý thuyết phục trong gây quỹ:
- *Gia đình / Cộng đồng (Family/communal)*: nhắc đến trẻ em, vai trò gia đình (mẹ, cha, vợ, chồng, con cái, trường học) — kêu gọi sự đồng cảm hướng về gia đình.
- *Năng lực / Tự chủ (Agency/competence)*: nhắc đến quyết định, lập kế hoạch, quản lý, chăm chỉ, độc lập, điều hành — phát tín hiệu về năng lực quản lý kinh doanh.
- *Tính cấp bách (Urgency)*: ngôn ngữ khẩn cấp, thời gian gấp rút ("ngay lập tức", "khủng hoảng", "nhanh chóng", "càng sớm càng tốt").

Mỗi phong cách được chuẩn hóa thành *tỷ lệ trên 100 từ* thay vì đếm số lần thô, để một câu chuyện dài không bị chấm điểm khẩn cấp hơn chỉ vì nó chứa nhiều chữ.

```python
FAMILY_PATTERN = re.compile(r"\b(child|children|family|son|daughter|mother|father|wife|husband|school)\b", re.I)
AGENCY_PATTERN = re.compile(r"\b(decide|plan|manage|responsible|hard.?working|independent|own|run|lead)\w*\b", re.I)
URGENCY_PATTERN = re.compile(r"\b(urgent|immediately|emergency|crisis|desperate|asap|quickly)\w*\b", re.I)

# Làm sạch các thẻ HTML thô (<br />) để không làm méo mó độ dài từ hoặc tạo từ rác
valid["description"] = (
    valid["description"].fillna("")
    .str.replace(r"<[^>]+>", " ", regex=True)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)
description = valid["description"]
word_count = description.str.split().str.len().clip(lower=1)

def _rate_per_100_words(pattern: re.Pattern, text: pd.Series, words: pd.Series) -> pd.Series:
    return text.str.count(pattern) / words * 100

valid["family_mentions_per_100_words"] = _rate_per_100_words(FAMILY_PATTERN, description, word_count)
valid["agency_mentions_per_100_words"] = _rate_per_100_words(AGENCY_PATTERN, description, word_count)
valid["urgency_mentions_per_100_words"] = _rate_per_100_words(URGENCY_PATTERN, description, word_count)
```

== 7. Phân Tích Cảm Xúc (Sentiment Analysis)

Cùng với phong cách diễn ngôn, mỗi đoạn mô tả được tính điểm cảm xúc thông qua VADER — công cụ chuẩn hóa đánh giá mức độ tích cực từ $-1$ (rất tiêu cực) đến $+1$ (rất tích cực). Phân tích được thực hiện trên mẫu ngẫu nhiên 20.000 văn bản để tối ưu tốc độ xử lý.

```python
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()
sentiment_sample = valid.sample(min(20_000, len(valid)), random_state=SEED).copy()
sentiment_sample["sentiment_compound"] = sentiment_sample["description"].fillna("").apply(
    lambda text: analyzer.polarity_scores(text)["compound"]
)
print("Sentiment (compound score) summary, 20K-row sample:")
print(sentiment_sample["sentiment_compound"].describe().to_string())
```

```output
Sentiment (compound score) summary, 20K-row sample:
count    20000.000000
mean         0.779637
std          0.286086
min         -0.929000
25%          0.743000
50%          0.886000
75%          0.954500
max          0.998600
```

*Hiệu ứng trần (Ceiling effect) trong cảm xúc:* Các bài mô tả khoản vay Kiva mang *tông giọng tích cực áp đảo*: điểm trung bình là 0,78 (trên thang 1.0), và điểm trung vị đạt tới 0,89; ngay cả nhóm một phần tư có điểm khiêm tốn nhất vẫn đạt mức tích cực 0,74. Hầu như mọi mô tả trên nền tảng này đều được viết bằng giọng văn lạc quan, hy vọng, hiếm khi có văn bản trung tính hoặc tiêu cực thực sự. Khi hầu hết mọi văn bản đều đã tập trung ở cận trên của thang đo, phương sai giữa các khoản vay còn lại rất nhỏ — điều này lý giải tại sao tác động của điểm cảm xúc trong mô hình hồi quy lại rất hạn chế.

== 8. Mô Hình Hóa Chủ Đề (Topic Modeling)

Ba chỉ số phong cách kể chuyện ở trên chỉ đếm các từ từ một danh sách cố định do con người thiết lập. Mô hình hóa chủ đề sử dụng hướng tiếp cận ngược lại: đọc văn bản và để các cụm từ xuất hiện tự nhiên mà không cần danh sách định trước. Quy trình sử dụng TF-IDF kết hợp phân tích nhân tử ma trận không âm NMF (Non-Negative Matrix Factorization) để tách thành 8 chủ đề chính trên mẫu 20.000 khoản vay.

```python
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
N_TOPICS = 8
N_TOP_WORDS = 8
vectorizer = TfidfVectorizer(max_features=1000, stop_words="english", min_df=5)
tfidf_matrix = vectorizer.fit_transform(sentiment_sample["description"].fillna(""))
nmf_model = NMF(n_components=N_TOPICS, random_state=SEED, max_iter=300)
topic_weights = nmf_model.fit_transform(tfidf_matrix)
sentiment_sample["dominant_topic"] = topic_weights.argmax(axis=1)

feature_names = vectorizer.get_feature_names_out()
topic_labels = {}
for topic_idx, topic in enumerate(nmf_model.components_):
    top_words = [feature_names[i] for i in topic.argsort()[-N_TOP_WORDS:][::-1]]
    topic_labels[topic_idx] = ", ".join(top_words)
    print(f"Topic {topic_idx}: {', '.join(top_words)}")
```

```output
Topic 0: pigs, pig, raise, supplies, nwtf, fattening, years, raising
Topic 1: business, loan, income, children, years, family, kiva, old
Topic 2: sanitary, toilet, risks, hazard, health, using, aware, reducing
Topic 3: water, village, filter, clean, drinking, boiling, fuel, safeguard
Topic 4: store, general, items, canned, goods, like, personal, products
Topic 5: farm, farming, inputs, quality, farmer, high, seeds, smallholder
Topic 6: group, solar, acre, total, fund, farmers, light, acres
Topic 7: business, nwtf, philippines, php, entrepreneur, fish, additional, 000
```

```python
topic_speed = sentiment_sample.groupby("dominant_topic")["funding_speed_days"].agg(["mean", "count"]).sort_values("mean")
topic_speed["top_words"] = [topic_labels[i] for i in topic_speed.index]
print(topic_speed.to_string())
```

```output
                 mean  count                                                            top_words
dominant_topic                                                                                    
2            1.455901   1029              sanitary, toilet, risks, hazard, health, using, aware, reducing
3            1.814373    673            water, village, filter, clean, drinking, boiling, fuel, safeguard
0            7.258376   1590                  pigs, pig, raise, supplies, nwtf, fattening, years, raising
7            7.803372   2362        business, nwtf, philippines, php, entrepreneur, fish, additional, 000
4            8.964443   1838               store, general, items, canned, goods, like, personal, products
1           10.700803   8883                   business, loan, income, children, years, family, kiva, old
5           12.513396   2739             farm, farming, inputs, quality, farmer, high, seeds, smallholder
6           13.492799    886                       group, solar, acre, total, fund, farmers, light, acres
```

#align(center)[
  #image("/docs/presentation/charts/notebook/eda_32_8_topic_modeling.png", width: 85%)
]

#insight_box([
Các chủ đề xuất hiện phản ánh rất rõ ràng các lĩnh vực thực tế trong đời sống chứ không phải các cụm từ ngẫu nhiên: chăn nuôi (lợn), vệ sinh & sức khỏe (nhà vệ sinh/nguy cơ bệnh tật), nước sạch, cửa hàng tạp hóa, nông nghiệp trồng trọt, và năng lượng mặt trời/cho vay theo nhóm.

*Chênh lệch tốc độ gọi vốn giữa các chủ đề là cực kỳ lớn:* Chủ đề vệ sinh/sức khỏe gọi vốn trung bình trong 1,5 ngày — *nhanh hơn gấp 9 lần* so với chủ đề năng lượng mặt trời/cho vay nhóm (13,5 ngày). Đây là mức chênh lệch lớn hơn bất kỳ tín hiệu phong cách diễn ngôn đơn lẻ nào. Tuy nhiên, mỗi chủ đề gắn liền với các ngành nghề và quy mô vốn cụ thể, do đó đây là tín hiệu mở đường cho phân tích sâu hơn chứ chưa phải là kết luận độc lập.
])

== 9. Tương Quan Giữa Các Đặc Trưng (Feature Correlations)

Kiểm tra tương quan tuyến tính đơn biến giữa tốc độ gọi vốn với các biến diễn ngôn và biến cấu trúc khoản vay:

```python
narrative_cols = ["family_mentions_per_100_words", "agency_mentions_per_100_words", "urgency_mentions_per_100_words"]
valid["log_loan_amount"] = np.log1p(valid["loanAmount"])
structural_cols = ["log_loan_amount", "lenderRepaymentTerm"]
corr_table = valid[narrative_cols + structural_cols + ["funding_speed_days"]].corr()["funding_speed_days"].drop("funding_speed_days")
print("Correlation with funding speed (days):")
print(corr_table.sort_values().to_string())
```

```output
Correlation with funding speed (days):
family_mentions_per_100_words    -0.018791
urgency_mentions_per_100_words    0.010423
agency_mentions_per_100_words     0.058013
lenderRepaymentTerm               0.284895
log_loan_amount                   0.429447
```

#align(center)[
  #image("/docs/presentation/charts/notebook/eda_36_9_feature_correlations.png", width: 80%)
]

- *Cấu trúc khoản vay áp đảo phong cách diễn ngôn:* Số tiền vay lớn hơn ($r = +0.43$) và kỳ hạn hoàn trả dài hơn ($r = +0.28$) là những biến tương quan mạnh nhất với tốc độ gọi vốn chậm — số tiền yêu cầu càng lớn thì thời gian góp vốn càng dài, thể hiện quan hệ đơn điệu rõ ràng theo từng phân vị quy mô vốn.
- *Cả ba phong cách diễn ngôn đều có tương quan cực kỳ mờ nhạt:* yếu hơn hẳn một bậc độ lớn (order of magnitude). Lời kêu gọi gia đình có $r = -0.019$ (liên hệ rất mỏng với tốc độ nhanh hơn), tính cấp bách $r = +0.010$ (gần như bằng 0), và năng lực tự chủ $r = +0.058$ (thậm chí hơi nghiêng về việc gọi vốn chậm hơn — trái ngược hoàn toàn với giả định ngây thơ rằng "viết có vẻ tự tin thì sẽ được góp vốn nhanh hơn").
- *Bài học cảnh báo về phương pháp:* Tính cấp bách tưởng chừng như là một biến mạnh khi kiểm soát OLS thông thường ($p < 0.001$), nhưng khi kiểm định lại với sai số chuẩn phân cụm theo quốc gia (country-clustered standard errors) ở Notebook 2, mối liên hệ này hoàn toàn biến mất ($p approx 0.44$). Tương tự, hiệu ứng gia đình chỉ còn lại dấu hiệu mô tả ở Trung Đông và Trung Mỹ, nhưng không vượt qua được kiểm định số cụm nhỏ (few-cluster t).

== 10. Những Phát Hiện Cốt Lõi (Key Findings)

=== 10.1 Diễn Giải Kỹ Thuật (Technical Interpretation)
- *Dữ liệu hoàn chỉnh và chuẩn xác:* 1.453.840 trên 1.453.846 khoản vay (99,9996%) có thời gian gọi vốn hợp lệ, đảm bảo độ tin cậy tuyệt đối cho các kết luận thống kê.
- *Thời gian gọi vốn bước vào giai đoạn trì trệ dai dẳng sau năm 2019:* Tỷ lệ hoàn thành trong 24 giờ giảm từ 46% xuống ~30% và chưa từng hồi phục đến hết năm 2025.
- *Văn bản mô tả có hiệu ứng trần cảm xúc:* Trung vị điểm cảm xúc là 0,89/1.0, làm giảm đáng kể khả năng phân hóa của biến cảm xúc.
- *Cấu trúc khoản vay vượt trội hoàn toàn:* Quy mô vay và kỳ hạn có mức độ tương quan lớn hơn hẳn một bậc độ lớn so với mọi biến phong cách viết. Giới tính của người đi vay tạo ra khoảng cách rõ rệt ngay cả trước khi kiểm soát các biến khác.
- *Kiểm định sai số phân cụm thay đổi căn bản bức tranh diễn ngôn:* Tính cấp bách và hầu hết các tương tác điều kiện của yếu tố gia đình không đứng vững trước sai số chuẩn phân cụm theo quốc gia.

=== 10.2 Tác Động Quản Trị & Kinh Doanh (Business Impact)
- *Sự chậm lại thời kỳ đại dịch là một thực tế mang tính cấu trúc:* Cần có giải pháp vận hành thực chất thay vì giả định rằng "thị trường sẽ tự động hồi phục về mức cũ".
- *Không nên tập trung hướng dẫn người vay "viết tích cực hơn":* Hầu hết văn bản đã ở mức rất lạc quan; việc cố gắng nâng tông giọng không tạo ra lợi thế cạnh tranh.
- *Quy mô vay và kỳ hạn là yếu tố chi phối lớn nhất:* Hữu ích để Kiva thiết lập kỳ vọng thời gian gọi vốn thực tế cho người vay và đối tác.
- *Ngành nghề và địa lý quan trọng hơn cách viết:* Các chương trình xem xét lại cơ chế phân bổ hiển thị cho từng ngành nghề và khu vực sẽ mang lại hiệu quả cao hơn nhiều so với việc chỉ tập trung đào tạo kỹ năng viết mô tả.
- *Thận trọng với các khuyến nghị về phong cách kể chuyện:* Không có cơ sở thực nghiệm để khuyến khích dùng từ ngữ cấp bách trên toàn sàn. Mô thức hỗ trợ gia đình ở một số thị trường cần được thử nghiệm A/B có phân tầng theo quốc gia thay vì áp dụng thành quy chuẩn chung.
