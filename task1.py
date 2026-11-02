import pandas as pd
import os

# ========== 1. 读取数据到DataFrame ==========
# 确保 Online Retail.xlsx 和 task1.py 在同一个文件夹
df = pd.read_excel("Online Retail.xlsx")

# 目标国家列表
target_countries = ['United Kingdom', 'Germany', 'France', 'Spain']

# 按国家筛选数据
uk_data = df[df["Country"] == "United Kingdom"]
germany_data = df[df["Country"] == "Germany"]
france_data = df[df["Country"] == "France"]
spain_data = df[df["Country"] == "Spain"]

# 自动创建 data 文件夹（如果不存在）
os.makedirs("data", exist_ok=True)

# ========== 2. 保存为4个CSV文件 ==========
uk_data.to_csv("data/United Kingdom.csv", index=False)
germany_data.to_csv("data/Germany.csv", index=False)
france_data.to_csv("data/France.csv", index=False)
spain_data.to_csv("data/Spain.csv", index=False)

print("✅ 已生成4个CSV文件，存放在 data/ 文件夹中")

# ========== 3. 把德、法、西的数据写入同一个Excel的不同工作表 ==========
# 处理Note：去掉冗余的 Country 列
germany_no_country = germany_data.drop(columns=["Country"])
france_no_country = france_data.drop(columns=["Country"])
spain_no_country = spain_data.drop(columns=["Country"])

# 写入Excel（注意with语句的缩进和冒号）
with pd.ExcelWriter("data/Online Retail Sheets.xlsx", engine="openpyxl") as writer:
    germany_no_country.to_excel(writer, sheet_name="Germany", index=False)
    france_no_country.to_excel(writer, sheet_name="France", index=False)
    spain_no_country.to_excel(writer, sheet_name="Spain", index=False)

print("✅ 已生成 Online Retail Sheets.xlsx，存放在 data/ 文件夹中")
print("ℹ️  已按Note要求移除了每个工作表的 Country 列")