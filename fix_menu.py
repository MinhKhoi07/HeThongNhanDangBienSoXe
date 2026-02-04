#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

# Đọc file
with open(r'd:\xampp\htdocs\XLA_TTD\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Tìm dòng menu = st.radio
for i, line in enumerate(lines):
    if 'menu = st.radio' in line and i > 1980:
        print(f"Dòng {i+1}: {line.strip()}")
        print(f"Context:")
        for j in range(max(0, i-2), min(len(lines), i+12)):
            print(f"{j+1}: {lines[j]}", end='')
        break

# Thực hiện thay thế
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Tìm st.radio ở khoảng dòng 1984 (index 1983)
    if i >= 1983 and i <= 1995 and 'menu = st.radio' in line:
        # Tìm dòng kết thúc của st.radio call (tìm dấu ']')
        j = i
        bracket_count = 0
        found_start = False
        
        while j < len(lines):
            if '[' in lines[j]:
                bracket_count += 1
                found_start = True
            if found_start and ']' in lines[j] and 'label_visibility' in lines[j]:
                # Tìm được dòng kết thúc
                break
            j += 1
        
        # Thay thế các dòng từ i đến j
        if found_start and j > i:
            # Thêm dòng mới
            new_lines.append('        menu = st.radio("", [\n')
            new_lines.append('            "Quy trình",\n')
            new_lines.append('            "Quản lý xe",\n')
            new_lines.append('            "Nhận dạng",\n')
            new_lines.append('            "Tra cứu",\n')
            new_lines.append('            "Danh sách đen",\n')
            new_lines.append('            "Vi phạm",\n')
            new_lines.append('            "Thanh toán",\n')
            new_lines.append('            "Thống kê"\n')
            new_lines.append('        ], index=1, label_visibility="collapsed", format_func=lambda x: {\n')
            new_lines.append('            "Quy trình": "🎯 Quy trình",\n')
            new_lines.append('            "Quản lý xe": "🚗 Quản lý xe",\n')
            new_lines.append('            "Nhận dạng": "🎯 Nhận dạng",\n')
            new_lines.append('            "Tra cứu": "🔍 Tra cứu",\n')
            new_lines.append('            "Danh sách đen": "🚫 Danh sách đen",\n')
            new_lines.append('            "Vi phạm": "⚠️ Vi phạm",\n')
            new_lines.append('            "Thanh toán": "💳 Thanh toán",\n')
            new_lines.append('            "Thống kê": "📊 Thống kê"\n')
            new_lines.append('        }[x])\n')
            
            i = j + 1
            continue
    
    # Thay thế các điều kiện if/elif
    if i >= 2005 and i <= 2020:
        if 'if menu ==' in line:
            if 'Quy trình' in line:
                line = '    if menu == "Quy trình":\n'
        elif 'elif menu ==' in line:
            if 'Quản lý xe' in line:
                line = '    elif menu == "Quản lý xe":\n'
            elif 'Nhận dạng' in line:
                line = '    elif menu == "Nhận dạng":\n'
            elif 'Tra cứu' in line:
                line = '    elif menu == "Tra cứu":\n'
            elif 'Danh sách đen' in line:
                line = '    elif menu == "Danh sách đen":\n'
            elif 'Vi phạm' in line:
                line = '    elif menu == "Vi phạm":\n'
            elif 'Thanh toán' in line:
                line = '    elif menu == "Thanh toán":\n'
    
    new_lines.append(line)
    i += 1

# Ghi file
with open(r'd:\xampp\htdocs\XLA_TTD\app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("\n✓ File đã được sửa")
