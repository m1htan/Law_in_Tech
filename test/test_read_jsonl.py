import json
import pandas as pd

file_path = '/Users/minhtan/Documents/GitHub/Law_in_Tech/outputs/discussions/index.jsonl'
data_list = []

try:
    # Bước 1: Đọc file JSONL vào một danh sách (list) các dictionary
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data_list.append(json.loads(line))

    # Bước 2: Chuyển danh sách đó thành một Pandas DataFrame
    df = pd.DataFrame(data_list)

    # In ra DataFrame để kiểm tra
    print("Dữ liệu đã được lưu vào DataFrame:")
    print(df)
    df.to_csv("../outputs/discussions/index_1.csv")

except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file tại đường dẫn '{file_path}'")
except Exception as e:
    print(f"Đã có lỗi xảy ra: {e}")