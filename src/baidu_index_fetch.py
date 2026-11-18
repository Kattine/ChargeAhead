import time
import pandas as pd
from datetime import datetime, timedelta
from qdata.baidu_index import get_search_index

COOKIES = "Your Baidu Search Index Cookie"
# Cleaning Cookies: Remove invisible characters, then convert to latin-1 safe byte strings
_clean = "".join(ch for ch in COOKIES if ch.isprintable() and ord(ch) < 128)
COOKIES = _clean.encode("utf-8").decode("latin-1")

# BATCHES = [
#     [["混动车"], ["插电式混合动力车"], ["新能源汽车技术"], ["燃油车"], ["纯电车"]],
#     [["比亚迪"], ["特斯拉"], ["小米"], ["理想"], ["蔚来"], ["小鹏"], ["零跑"]],
#     [["极氪"], ["问界"], ["埃安"], ["领克"], ["吉利银河"], ["深蓝"], ["阿维塔"]],
#     [["Model Y"], ["比亚迪宋"], ["海鸥"], ["小米SU7"], ["理想L6"]],
# ]

# BATCHES = [
#     # 动力类型层：覆盖 BEV / PHEV / EREV / HEV / 燃油车
#     [
#         ["纯电车"],
#         ["燃油车"],
#         ["插电式混合动力车"],
#         ["混动车"],
#         ["增程式混动和插电式混动的区别"],
#         ["增程式电动车是什么意思"],
#         ["新能源车"],
#         ["新能源汽车"],
#     ],
#     # 品牌层：覆盖主流新能源品牌 + 母品牌 + 华为系
#     [
#         ["比亚迪"],
#         ["特斯拉"],
#         ["小米汽车"],
#         ["理想"],
#         ["蔚来"],
#         ["小鹏"],
#         ["零跑"],
#         ["吉利"],
#         ["奇瑞"],
#         ["鸿蒙智行"],
#     ],
#     # 品牌层（续）：新势力 + 传统车企子品牌
#     [
#         ["极氪"],
#         ["问界"],
#         ["埃安"],
#         ["领克"],
#         ["吉利银河"],
#         ["深蓝"],
#         ["阿维塔"],
#     ],
#     # 车型层：覆盖 CPCA 月度 Top 20 + EREV 主力车型
#     [
#         ["Model Y"],
#         ["Model 3"],
#         ["比亚迪宋"],
#         ["比亚迪秦PLUS"],
#         ["比亚迪海豚"],
#         ["海鸥"],
#         ["小米SU7"],
#         ["理想L6"],
#         ["理想L7"],
#         ["理想L9"],
#         ["问界M7"],
#         ["问界M9"],
#         ["零跑C10"],
#         ["零跑B11"],
#         ["零跑C11"],
#         ["小鹏MONA M03"],
#         ["吉利星愿"],
#         ["元UP"],
#     ],
# ]

# ============================================================
# TIER 1  主信号保底    先跑完这块
# 覆盖所有动力类型 + Top 10 NEV 品牌 + 8 款旗舰车型
# 只要这些拿到，Transition Index 和品牌/车型三层验证都能跑
# ============================================================
BATCHES_CORE = [
    # 动力类型层  每个 CPCA 类别一个最干净的词
    [
        ["纯电车"],                      # BEV
        ["插电式混合动力车"],             # PHEV  短词不在库里就用这个
        ["增程式电动车是什么意思"],       # EREV  长尾教育词作代理
        ["燃油车"],                      # ICE
        ["新能源车"],                    # NEV 总盘
    ],
    # 头部 NEV 品牌  按 2026 批发排名  覆盖 NEV 市场约 75%
    [
        ["比亚迪"],
        ["特斯拉"],
        ["理想"],
        ["问界"],
        ["蔚来"],
    ],
    [
        ["小鹏"],
        ["零跑"],
        ["小米汽车"],
        ["极氪"],
        ["埃安"],
    ],
    # 旗舰车型  CPCA 月度 Top + EREV 龙头
    [
        ["Model Y"],
        ["比亚迪宋"],
        ["吉利星愿"],
        ["元UP"],
        ["海鸥"],
    ],
    [
        ["小米SU7"],
        ["理想L6"],
        ["问界M9"],
    ],
]

# ============================================================
# TIER 2 Candidates / Supplements Un-comment in batches after the main signals are run 
# Used for robustness testing, parent brand comparison, and long-tail model coverage
# ============================================================
BATCHES_SUPPLEMENT = [
    # Power Type  Synonyms/Contrast Words  Used to check consistency with the main term
    [
        ["混动车"],                        # 大混动 sanity check
        ["增程式混动和插电式混动的区别"],  # EREV 比较期搜索
        ["新能源汽车"],                    # NEV 正式写法对照
    ],

    # Second-tier Brand  Parent Brand + Huawei Ecosystem Overall + Sub-brand
    [
        ["吉利"],
        ["奇瑞"],
        ["鸿蒙智行"],
        ["领克"],
        ["吉利银河"],
    ],
    [
        ["深蓝"],
        ["阿维塔"],
    ],

    # Second-tier models Top 20 Others + EREV mid-range + Xpeng MONA
    [
        ["Model 3"],
        ["比亚迪秦PLUS"],
        ["比亚迪海豚"],
        ["理想L7"],
        ["理想L9"],
    ],
    [
        ["问界M7"],
        ["零跑C10"],
        ["零跑C11"],
        ["零跑B11"],
        ["小鹏MONA M03"],
    ],
]

BATCHES = BATCHES_CORE + BATCHES_SUPPLEMENT  # Change it after finishing the core run: BATCHES_CORE + BATCHES_SUPPLEMENT

DATE_RANGES = [
    ("2023-01-01", "2023-12-31"),
    ("2024-01-01", "2024-12-31"),
    ("2025-01-01", "2025-12-31"),
    ("2026-01-01", "2026-10-31"),
]

AREA = 0  # 0=全国


rows = []

total = len(BATCHES) * len(DATE_RANGES)
done = 0

for batch in BATCHES:
    for start_date, end_date in DATE_RANGES:
        done += 1
        print(f"[{done}/{total}] 跑 {batch} | {start_date} ~ {end_date} | 已取 {len(rows)} 行")

        for item in get_search_index(
            keywords_list=batch,
            start_date=start_date,
            end_date=end_date,
            cookies=COOKIES,
            area=AREA,
        ):
            keyword = item.get("keyword", "")
            date_str = item.get("date", "")
            idx = item.get("index")

            index_all = None
            if isinstance(idx, dict):
                all_data = idx.get("all")
                if isinstance(all_data, dict):
                    for d, v in all_data.items():
                        rows.append({"keyword": keyword, "date": d, "index_all": v})
                    continue
                elif isinstance(all_data, str) and all_data.replace(",", "").replace("-", "").isdigit():
                    index_all = all_data
            elif isinstance(idx, str) and idx.replace(",", "").replace("-", "").isdigit():
                index_all = idx

            if not date_str or index_all is None:
                print("  跳过：", keyword, "index =", repr(idx))
                continue

            rows.append({
                "keyword": keyword[0] if isinstance(keyword, list) else keyword,
                "date": date_str,
                "index_all": int(index_all.replace(",", "")),
            })

        time.sleep(1.2)

    time.sleep(1.5)

if not rows:
    print("Warning: No valid data was retrieved this time")
else:
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values(["keyword", "date"]).reset_index(drop=True)

    # Daily Original Table
    df.to_excel("baidu_index_daily.xlsx", index=False)

    # ---- weekly rollup ----
    df["iso_year"] = df["date"].dt.isocalendar().year.astype(int)
    df["iso_week"] = df["date"].dt.isocalendar().week.astype(int)

    weekly = (
        df.groupby(["keyword", "iso_year", "iso_week"], as_index=False)
        .agg(
            week_start=("date", "min"),
            week_end=("date", "max"),
            index_all_mean=("index_all", "mean"),
            index_all_sum=("index_all", "sum"),
            days=("date", "nunique"),
        )
    )

    weekly["is_partial_week"] = weekly["days"] != 7

    # month Assignment: A week belongs to the month in which it has 4 or more days; 
    # boundary weeks are clearly assigned to avoid misalignment in subsequent monthly aggregates.
    def _assign_month(row):
        dates = pd.date_range(row["week_start"], row["week_end"], freq="D")
        if len(dates) == 0:
            return pd.NaT
        month_counts = dates.to_series().dt.to_period("M").value_counts()
        return month_counts.idxmax().start_time

    weekly["month"] = weekly.apply(_assign_month, axis=1)

    weekly.to_excel("baidu_index_weekly.xlsx", index=False)

    # ---- monthly rollup：Align CPCA Panel ----
    df["month"] = df["date"].dt.to_period("M")

    monthly = (
        df.groupby(["keyword", "month"], as_index=False)
        .agg(
            index_all_mean=("index_all", "mean"),
            index_all_sum=("index_all", "sum"),
            days=("date", "nunique"),
        )
    )
    monthly["month"] = monthly["month"].astype(str)
    monthly.to_excel("baidu_index_monthly.xlsx", index=False)

    print("Exported：baidu_index_daily.xlsx / baidu_index_weekly.xlsx / baidu_index_monthly.xlsx")

# rows = []

# for batch in BATCHES:
#     for start_date, end_date in DATE_RANGES:
#         for item in get_search_index(
#             keywords_list=batch,
#             start_date=start_date,
#             end_date=end_date,
#             cookies=COOKIES,
#             area=AREA,
#         ):
#             keyword = item.get("keyword", "")
#             date_str = item.get("date", "")
#             # index_all = item.get("index", {}).get("all")
#             idx = item.get("index")
#             if isinstance(idx, dict):
#                 index_all = idx.get("all")
#                 index_pc = idx.get("pc")
#                 index_wise = idx.get("wise")
#             else:
#                 print("Skip：", item.get("keyword"), "index =", repr(idx))
#                 continue

#             index_pc = item.get("index", {}).get("pc")
#             index_wise = item.get("index", {}).get("wise")

#             if not date_str:
#                 continue

#             rows.append(
#                 {
#                     "keyword": keyword,
#                     "date": date_str,
#                     "index_all": index_all,
#                     "index_pc": index_pc,
#                     "index_wise": index_wise,
#                 }
#             )

#         # Control the frequency to avoid being restricted
#         time.sleep(1.2)

#     # Buffer a bit between each batch
#     time.sleep(1.5)

# if not rows:
#     print("Warning: No valid data was retrieved this time. Please check the cookie, keywords, or time range.")
#     # raise RuntimeError("No data was retrieved, please check the cookie, keywords, or time range.")

# df = pd.DataFrame(rows)
# df["date"] = pd.to_datetime(df["date"])
# df = df.dropna(subset=["date"])
# df = df.sort_values(["keyword", "date"]).reset_index(drop=True)

# # Daily Raw Table
# df.to_excel("baidu_index_daily.xlsx", index=False)

# # Weekly Rollup: Aggregated by ISO Week
# df["year"] = df["date"].dt.isocalendar().year.astype(int)
# df["week"] = df["date"].dt.isocalendar().week.astype(int)

# weekly = (
#     df.groupby(["keyword", "year", "week"], as_index=False)
#     .agg(
#         week_start=("date", "min"),
#         index_all_mean=("index_all", "mean"),
#         index_pc_mean=("index_pc", "mean"),
#         index_wise_mean=("index_wise", "mean"),
#         index_all_sum=("index_all", "sum"),
#         index_pc_sum=("index_pc", "sum"),
#         index_wise_sum=("index_wise", "sum"),
#         days=("date", "nunique"),
#     )
# )

# weekly.to_excel("baidu_index_weekly.xlsx", index=False)

# # Monthly rollup: aligning CPCA / CADA / vehicle value
# df["month"] = df["date"].dt.to_period("M")

# monthly = (
#     df.groupby(["keyword", "month"], as_index=False)
#     .agg(
#         index_all_mean=("index_all", "mean"),
#         index_pc_mean=("index_pc", "mean"),
#         index_wise_mean=("index_wise", "mean"),
#         index_all_sum=("index_all", "sum"),
#         index_pc_sum=("index_pc", "sum"),
#         index_wise_sum=("index_wise", "sum"),
#         days=("date", "nunique"),
#     )
# )

# monthly["month"] = monthly["month"].astype(str)
# monthly.to_excel("baidu_index_monthly.xlsx", index=False)

# print("Exported：baidu_index_daily.xlsx / baidu_index_weekly.xlsx / baidu_index_monthly.xlsx")
