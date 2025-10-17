import pandas as pd

file_path = '/Users/minhtan/Documents/GitHub/Law_in_Tech/outputs/discussions/index.parquet'

try:
    # Dùng pandas để đọc file parquet
    # Pandas sẽ tự động dùng pyarrow nếu bạn đã cài đặt nó
    df = pd.read_parquet(file_path, engine='pyarrow')

    # In ra 5 dòng đầu tiên của DataFrame
    print("5 dòng đầu tiên của dữ liệu:")
    print(df.head())

    # In thông tin tổng quan về DataFrame
    print("\nThông tin tổng quan về dữ liệu:")
    df.info()
    df.to_csv("../outputs/discussions/index_2.csv")

except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file tại đường dẫn '{file_path}'")
except Exception as e:
    print(f"Đã xảy ra lỗi khi đọc file Parquet: {e}")