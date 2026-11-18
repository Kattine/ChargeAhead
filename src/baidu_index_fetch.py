import time
import pandas as pd
from datetime import datetime, timedelta
from qdata.baidu_index import get_search_index

# COOKIES = "你的百度指数Cookie"
COOKIES = "BIDUPSID=F2B2961085D25A0D082B589AF9C9982D; PSTM=1770601610; BAIDUID=9BC8CAFCDC1291AD6202BBA4BA3E4894:FG=1; BAIDUID_BFESS=9BC8CAFCDC1291AD6202BBA4BA3E4894:FG=1; ZFY=ccIrd4XNS:ANDEoeoaSaqGoGCgCVppxOD0pVQTh5xiO8:C; BDUSS=mxCb0t6TUVwdjVsTklLZElhTlM5WFdjVmdIck53dUFZY1d0clk4REV-Mm1xNzFwSVFBQUFBJCQAAAAAAAAAAAEAAADD369xxM~H5cuutvkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKYelmmmHpZpY; H_PS_PSSID=63141_67861_67890_68053_67986_68004_68149_68146_68144_68152_68140_68165_68230_68262_68266_68296_68308_68353_68370_68353_68419_68432_68447_68467_68539_68537_68546_68558_68506_68518_68621_68612_68604_68705_68680_68671_68714_68734_68726_68544_68799; H_WISE_SIDS=63141_67861_67986_68004_68149_68146_68144_68152_68140_68165_68230_68266_68296_68370_68419_68447_68539_68546_68558_68506_68518_68591_68616_68621_68612_68604_68705_68680_68671_68714_68734_68726_68544_68799_68872_68883_68902_68832_68922_68993_69000_69010_69017_69016_69021; HMACCOUNT=49256AD458ED270E; Hm_up_d101ea4d2a5c67dab98251f0b5de24dc=%7B%22uid_%22%3A%7B%22value%22%3A%221907351491%22%2C%22scope%22%3A1%7D%7D; SIGNIN_UC=70a2711cf1d3d9b1a82d2f87d633bd8a05395454900cYIqWIVgIEJIzpJxyeKAZUk3C8m2fKOkqKq0nPlby8dtkggAK9Crr%2FKT8wvMU%2Fjyu8FPVPhq94m03sw21ERiOtXDLHd30eWV1XRlbNAyv2da0kN1TiNDIsl%2BZBiCGDC5zR9zXhaycRC9jyov4jBlN%2F%2BmeucCBo0leupkgAHG2OA1tqBFEVT8MtGPkbbWeTfxYvr52SeugrKfc7dsv0FbBFYzteU%2F0imakKbCDL5d4TMgGG9QdUGFduPi3nu0mnZiWoLTApr%2FBwV9G4bfSQnPu8KQGavoIxsIw2Mgx%2B6vYadVFwny5s9SllrRCArx3SUM28159633400202598539926429911960; __cas__rn__=539545490; bdindexid=1s5ci2sar6tc1qdalqfg3aevu5; Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc=1789533042,1791878383; Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc=1791878383; __cas__st__212=9141b1c769eccb7f1a8411811c7be4b99c8dc2fe4f1ea0e184e0c17172465525ae648c444820b6ed282cd87a; __cas__id__212=43219807; CPTK_212=703663222; CPID_212=43219807; RT=\"z=1&dm=baidu.com&si=b8446b25-ab45-46ff-8d2c-cbd231dc1c4a&ss=mv6e4g5i&sl=13&tt=14rk&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf\"; BDUSS_BFESS=mxCb0t6TUVwdjVsTklLZElhTlM5WFdjVmdIck53dUFZY1d0clk4REV-Mm1xNzFwSVFBQUFBJCQAAAAAAAAAAAEAAADD369xxM~H5cuutvkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKYelmmmHpZpY; ab_sr=1.0.1_NjYzMDI3NDY1MWM0ZTE5NmNlMGNhNmNkYzE2N2YzZDM3ZjA2MWRjOWNlOGE0Y2IxNDI1MmJmOTFhNTNiNWM3Mzk4YTI3ZTUxOTEwN2VhNWYyOWRkZWUxZDliZGJmNDkxYmY3MjkxOTE4ZGRmOWZkYmE4NWU1ZWZjMTY1NGFmYzk4YzgyM2UxODYyN2U0NGViYmVlYWIyYTJlZGFlN2U1Yw=="

# 清洗 Cookie：去掉不可见字符，再转成 latin-1 安全的字节串
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
# TIER 2  候选 / 补充    主信号跑完再逐批解开注释
# 用于稳健性检验、母品牌对照、长尾车型覆盖
# ============================================================
BATCHES_SUPPLEMENT = [
    # 动力类型  同义/对照词  用来和主词做一致性检查
    [
        ["混动车"],                        # 大混动 sanity check
        ["增程式混动和插电式混动的区别"],  # EREV 比较期搜索
        ["新能源汽车"],                    # NEV 正式写法对照
    ],

    # 二线品牌  母品牌 + 华为系整体 + 子品牌
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

    # 第二梯队车型  Top 20 其余 + EREV 中段 + 小鹏 MONA
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

BATCHES = BATCHES_CORE + BATCHES_SUPPLEMENT  # 跑完核心后改成 BATCHES_CORE + BATCHES_SUPPLEMENT

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
    print("警告：本次未取到有效数据")
else:
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values(["keyword", "date"]).reset_index(drop=True)

    # 日度原始表
    df.to_excel("baidu_index_daily.xlsx", index=False)

    # ---- 周度 rollup ----
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

    # month 归属：哪个月占这周 >= 4 天就归哪个月；边界周明确归属，避免后续 monthly aggregate 对不齐
    def _assign_month(row):
        dates = pd.date_range(row["week_start"], row["week_end"], freq="D")
        if len(dates) == 0:
            return pd.NaT
        month_counts = dates.to_series().dt.to_period("M").value_counts()
        return month_counts.idxmax().start_time

    weekly["month"] = weekly.apply(_assign_month, axis=1)

    weekly.to_excel("baidu_index_weekly.xlsx", index=False)

    # ---- 月度 rollup：对齐 CPCA 面板 ----
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

    print("已导出：baidu_index_daily.xlsx / baidu_index_weekly.xlsx / baidu_index_monthly.xlsx")

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
#                 print("跳过：", item.get("keyword"), "index =", repr(idx))
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

#         # 控制频率，避免被限
#         time.sleep(1.2)

#     # 每个 batch 之间再缓冲一下
#     time.sleep(1.5)

# if not rows:
#     print("警告：本次未取到有效数据，请检查 Cookie、关键词或时间范围。")
#     # raise RuntimeError("未取到数据，请检查 Cookie、关键词或时间范围。")

# df = pd.DataFrame(rows)
# df["date"] = pd.to_datetime(df["date"])
# df = df.dropna(subset=["date"])
# df = df.sort_values(["keyword", "date"]).reset_index(drop=True)

# # 日度原始表
# df.to_excel("baidu_index_daily.xlsx", index=False)

# # 周度 rollup：按 ISO 周聚合
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

# # 月度 rollup：对齐 CPCA / CADA / 车值
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

# print("已导出：baidu_index_daily.xlsx / baidu_index_weekly.xlsx / baidu_index_monthly.xlsx")