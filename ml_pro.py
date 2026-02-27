import zipfile
import xml.etree.ElementTree as ET
import re
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import pandas as pd  # 新增：用于生成表格和保存CSV

def extract_text_from_docx(file_path):
    with zipfile.ZipFile(file_path) as docx:
        xml_content = docx.read('word/document.xml')
    tree = ET.parse(BytesIO(xml_content))
    root = tree.getroot()
    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text = []
    for paragraph in root.findall('.//w:p', namespaces):
        para_text = ''
        for t in paragraph.findall('.//w:t', namespaces):
            if t.text:
                para_text += t.text
        if para_text.strip():
            text.append(para_text.strip())
    return '\n'.join(text)

# ====================== 读取并解析 docx ======================
file_path = '转速配置.docx'
content = extract_text_from_docx(file_path)
lines = [line.strip() for line in content.split('\n') if line.strip()]

configs = []
current_duties = None
current_velocities = [[], [], [], []]  # 四个轮子

i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith('占空比') and '：' in line:
        if current_duties is not None:
            configs.append({
                'duties': current_duties,
                'velocities': current_velocities
            })
        duties_str = re.findall(r'\d+', line)
        current_duties = [int(d) for d in duties_str]
        current_velocities = [[], [], [], []]
        i += 1
        continue
    if '组数据' in line:
        for j in range(4):
            i += 1
            if i >= len(lines):
                break
            vel_line = lines[i]
            match = re.search(r'：([\d\.]+)cm/s', vel_line)
            if match:
                vel = float(match.group(1))
                current_velocities[j].append(vel)
    i += 1

if current_duties is not None:
    configs.append({
        'duties': current_duties,
        'velocities': current_velocities
    })

# ====================== 汇总每个轮子的统计数据 ======================
wheel_names_cn = ['左后轮', '左前轮', '右前轮', '右后轮']
wheel_names_en = ['Left Rear', 'Left Front', 'Right Front', 'Right Rear']

# 用于存储每个轮子的所有原始数据：{占空比: [速度列表]}
raw_data_dict = [{}, {}, {}, {}]

for config in configs:
    duties = config['duties']
    velocities = config['velocities']
    for w in range(4):
        duty = duties[w]
        if velocities[w]:  # 有数据
            if duty not in raw_data_dict[w]:
                raw_data_dict[w][duty] = []
            raw_data_dict[w][duty].extend(velocities[w])

# 转为统计表格用的列表
stats_rows = []
for w in range(4):
    duties = sorted(raw_data_dict[w].keys())
    for duty in duties:
        speeds = np.array(raw_data_dict[w][duty])
        stats_rows.append({
            '轮子': wheel_names_cn[w],
            '英文名': wheel_names_en[w],
            '占空比 (%)': duty,
            '样本数 N': len(speeds),
            '平均速度 (cm/s)': speeds.mean(),
            '最大速度 (cm/s)': speeds.max(),
            '最小速度 (cm/s)': speeds.min(),
            '标准差 (cm/s)': speeds.std()
        })

# 创建 DataFrame 并美化显示
df_stats = pd.DataFrame(stats_rows)
df_stats = df_stats.round(3)  # 保留3位小数
df_stats = df_stats.sort_values(['轮子', '占空比 (%)'])  # 按轮子和占空比排序


# 保存为 CSV 文件
csv_filename = 'wheel_velocity_stats.csv'
df_stats.to_csv(csv_filename, index=False, encoding='utf-8-sig')  # utf-8-sig 兼容中文Excel
print(f"\n统计表格已保存至：{csv_filename}")

# ====================== 用于拟合的平均值点 ======================
wheel_avg_data = [[] for _ in range(4)]  # (duty, mean_vel)
for w in range(4):
    duties = sorted(raw_data_dict[w].keys())
    for duty in duties:
        mean_vel = np.mean(raw_data_dict[w][duty])
        wheel_avg_data[w].append((duty, mean_vel))

# ====================== 绘图 ======================
fig, axs = plt.subplots(2, 2, figsize=(14, 10))
axs = axs.flatten()

for w in range(4):
    if not wheel_avg_data[w]:
        continue
    duties, means = zip(*wheel_avg_data[w])
    duties = np.array(duties)
    means = np.array(means)

    # 二次拟合（如果点数足够）
    deg = 2 if len(duties) >= 3 else 1
    coeffs = np.polyfit(duties, means, deg)
    x_fit = np.linspace(duties.min(), duties.max(), 200)
    y_fit = np.polyval(coeffs, x_fit)

    ax = axs[w]
    ax.scatter(duties, means, color='blue', s=80, label='averge velocity points')
    ax.plot(x_fit, y_fit, color='red', linewidth=2, label=f'{deg}power fitting curve')
    ax.set_title(f' {wheel_names_en[w]}')
    ax.set_xlabel('empty occupy (%)')
    ax.set_ylabel('line velocity (cm/s)')
    ax.legend()
    ax.grid(True, alpha=0.4)

    # 在图上标注每个点的平均值
    for d, m in zip(duties, means):
        ax.text(d, m + 1, f'{m:.1f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.show()

# ====================== 输出拟合系数 ======================
print("\n=== 拟合多项式系数（从高次到低次）===\n")
for w in range(4):
    duties, means = zip(*wheel_avg_data[w])
    deg = 2 if len(duties) >= 3 else 1
    coeffs = np.polyfit(duties, means, deg)
    print(f"{wheel_names_cn[w]} ({wheel_names_en[w]}): {coeffs}")