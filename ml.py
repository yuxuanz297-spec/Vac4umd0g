import zipfile
import xml.etree.ElementTree as ET
import re
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO


def extract_text_from_docx(file_path):
    """
    Extract text from a .docx file by parsing the document.xml inside the zip archive.
    """
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


# Assume the file is in the current directory or accessible path
file_path = '转速配置.docx'
content = extract_text_from_docx(file_path)

# Parse the content
lines = [line.strip() for line in content.split('\n') if line.strip()]

configs = []
current_duties = None
current_velocities = [[], [], [], []]  # For four wheels
wheel_names = ['left rear wheel', 'left front wheel', 'right front wheel', 'right rear wheel']

i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith('占空比') and '：' in line:
        if current_duties is not None:
            # Save previous config if exists
            configs.append({
                'duties': current_duties,
                'velocities': current_velocities
            })
        duties_str = re.findall(r'\d+', line)
        current_duties = [int(d) for d in duties_str]
        current_velocities = [[], [], [], []]
        i += 1  # Skip '数据：' or next
        continue
    if '组数据' in line:
        # Next 4 lines are velocities
        for j in range(4):
            i += 1
            if i >= len(lines):
                break
            vel_line = lines[i]
            # Extract float from '：' to 'cm/s'
            match = re.search(r'：([\d\.]+)cm/s', vel_line)
            if match:
                vel = float(match.group(1))
                current_velocities[j].append(vel)
    i += 1

# Append the last config
if current_duties is not None:
    configs.append({
        'duties': current_duties,
        'velocities': current_velocities
    })

# Now, for each wheel, collect duty and average velocity
wheel_data = [[] for _ in range(4)]  # List of (duty, avg_vel) for each wheel

for config in configs:
    duties = config['duties']
    velocities = config['velocities']
    for wheel_idx in range(4):
        if velocities[wheel_idx]:  # If data exists
            avg_vel = np.mean(velocities[wheel_idx])
            wheel_data[wheel_idx].append((duties[wheel_idx], avg_vel))

# Sort each wheel's data by duty cycle
for wheel_idx in range(4):
    wheel_data[wheel_idx].sort(key=lambda x: x[0])

# Use machine learning: polynomial regression (degree 2 for curve) with numpy.polyfit
# Plot for each wheel
fig, axs = plt.subplots(2, 2, figsize=(12, 10))
axs = axs.flatten()

for wheel_idx in range(4):
    duties, avgs = zip(*wheel_data[wheel_idx])
    duties = np.array(duties)
    avgs = np.array(avgs)

    # Fit a quadratic polynomial (machine learning regression)
    if len(duties) >= 3:  # Need at least 3 points for deg=2
        coeffs = np.polyfit(duties, avgs, deg=2)
        p = np.poly1d(coeffs)
        x_fit = np.linspace(min(duties), max(duties), 100)
        y_fit = p(x_fit)
    else:
        # Fallback to linear if few points
        coeffs = np.polyfit(duties, avgs, deg=1)
        p = np.poly1d(coeffs)
        x_fit = np.linspace(min(duties), max(duties), 100)
        y_fit = p(x_fit)

    # Plot
    ax = axs[wheel_idx]
    ax.scatter(duties, avgs, color='blue', label='Data Points')
    ax.plot(x_fit, y_fit, color='red', label='Fitted Curve')
    ax.set_title(f'{wheel_names[wheel_idx]} empty-occupy-velocity curve')
    ax.set_xlabel('empty occupy (%)')
    ax.set_ylabel('averge line velocity (cm/s)')
    ax.legend()
    ax.grid(True)

plt.tight_layout()
plt.show()

# Optionally, print the coefficients for each wheel
for wheel_idx in range(4):
    duties, avgs = zip(*wheel_data[wheel_idx])
    coeffs = np.polyfit(duties, avgs, deg=2 if len(duties) >= 3 else 1)
    print(f'{wheel_names[wheel_idx]} fitted coefficients (highest degree first): {coeffs}')
print(configs)
