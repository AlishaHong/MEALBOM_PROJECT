import pandas as pd
import numpy as np
from datetime import datetime

class FoodProcessor:
    def __init__(self, food_data_path, real_time_csv_path, customer_diet_csv_path, min_max_table):
        # food_data_path: 음식 데이터가 저장된 CSV 파일 경로
        # real_time_csv_path: 실시간 음식 정보를 저장할 CSV 파일 경로
        # customer_diet_csv_path: 고객 식단 정보를 저장할 CSV 파일 경로
        # min_max_table: 음식별 최소/최대 섭취량 정보를 포함하는 데이터
        
        # 음식 데이터를 pandas DataFrame으로 불러오기 (food_id를 문자열 타입으로 저장)
        self.food_data = pd.read_csv(food_data_path, dtype={'food_id': str})
        self.real_time_csv_path = real_time_csv_path  # 실시간 CSV 파일 경로 저장
        self.customer_diet_csv_path = customer_diet_csv_path  # 고객 식단 CSV 파일 경로 저장
        self.min_max_table = min_max_table  # 최소/최대 섭취량 데이터 저장
        
    def get_food_info(self, food_id):
        # 주어진 food_id에 해당하는 음식 정보를 검색하여 반환
        food_info = self.food_data[self.food_data['food_id'] == food_id]  # food_id 일치하는 데이터 검색
        if not food_info.empty:
            return food_info.to_dict(orient='records')[0]  # 첫 번째 레코드(딕셔너리 형태) 반환
        else:
            print(f"[ERROR] Food ID {food_id} not found in data.")  # 오류 메시지 출력
            return None  # 검색 결과 없을 경우 None 반환
        
    def calculate_nutrient(self, base_weight, base_value, consumed_weight):
        # 영양소 계산: 기준 중량(base_weight) 대비 소비된 중량(consumed_weight)에 따른 영양소 값을 계산
        return base_value * (consumed_weight / base_weight)  # 비율을 적용하여 영양소 값 계산

    def load_min_max_table(file_path):
        # 음식별 최소/최대 섭취량 정보를 포함하는 CSV 파일을 로드하는 함수
        try:
            min_max_table = pd.read_csv(file_path, encoding='utf-8', dtype={'food_id': str})
            return min_max_table  # CSV 데이터를 DataFrame으로 반환
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV 파일 {file_path}을(를) 찾을 수 없습니다.")  # 파일이 없을 경우 오류 발생

    def calculate_q_ranges(self, food_id, min_max_table):
        # 음식 ID에 대한 최소/최대 섭취량 정보를 기반으로 Q1~Q5 범위를 계산하는 함수
        food_info = min_max_table[min_max_table['food_id'] == str(food_id)]  # 해당 food_id에 대한 정보 검색
        if food_info.empty:
            raise ValueError(f"음식 ID {food_id}에 대한 정보를 찾을 수 없습니다.")  # 데이터 없을 경우 오류 발생
        min_quantity = food_info['min'].values[0]  # 최소 섭취량
        max_quantity = food_info['max'].values[0]  # 최대 섭취량
        quantities = np.linspace(min_quantity, max_quantity, 5)  # 최소~최대 값을 5단계(Q1~Q5)로 나눔
        return {f"Q{i+1}": quantities[i] for i in range(len(quantities))}  # Q1~Q5 범위를 딕셔너리로 반환

    def determine_q_category(self, measured_weight, q_ranges):
        # 측정된 중량(measured_weight)이 Q1~Q5 중 어느 범위에 속하는지 판별하는 함수
        q_values = list(q_ranges.values())  # Q 값 리스트 생성
        for i in range(len(q_values) - 1):  # 범위를 순차적으로 비교
            if q_values[i] <= measured_weight <= q_values[i + 1]:
                return f"Q{i+1}"  # 해당하는 Q값 반환
        return "Q5" if measured_weight > q_values[-1] else "Q1"  # 범위를 벗어난 경우 처리

    def save_to_csv(self, file_path, data):
        # 데이터프레임을 CSV 파일로 저장하는 함수 (기존 데이터가 있으면 추가)
        try:
            existing_df = pd.read_csv(file_path)  # 기존 데이터 로드
            updated_df = pd.concat([existing_df, data], ignore_index=True)  # 기존 데이터와 병합
        except FileNotFoundError:
            updated_df = data  # 파일이 없으면 새로운 데이터 사용
        updated_df.to_csv(file_path, index=False)  # CSV 파일로 저장
        print(f"[INFO] Data saved to {file_path}.")  # 저장 완료 메시지 출력

    def save_customer_diet_detail(self, customer_id, total_weight, total_nutrients):
        # 고객의 식단 정보를 기록하고 CSV 파일에 저장하는 함수
        today_date = datetime.now().strftime('%Y%m%d')  # 현재 날짜(YYYYMMDD) 가져오기
        try:
            existing_data = pd.read_csv(self.customer_diet_csv_path)  # 기존 데이터 로드
            same_date_data = existing_data[
                (existing_data['customer_id'] == customer_id) &
                (existing_data['log_id'].str.startswith(f"{today_date}_{customer_id}"))
            ]
            log_number = len(same_date_data) + 1  # 동일 고객의 로그 개수를 기반으로 새로운 log_id 생성
        except FileNotFoundError:
            log_number = 1  # 파일이 없으면 첫 번째 로그로 설정
        
        log_id = f"{today_date}_{customer_id}_{log_number}"  # log_id 생성
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 현재 시간 기록

        new_data = {
            "log_id": [log_id],
            "customer_id": [customer_id],
            "total_weight": [total_weight],
            **{f"total_{key}": [round(value, 2)] for key, value in total_nutrients.items()},  # 영양소 값 추가
            "timestamp": [timestamp]
        }
        self.save_to_csv(self.customer_diet_csv_path, pd.DataFrame(new_data))  # CSV 저장

    def process_food_data(self, plate_food_data, customer_id, min_max_table):
        # 접시 위 음식 데이터를 분석하여 총 영양소 및 카테고리를 계산하는 함수
        if isinstance(min_max_table, str):
            min_max_table = pd.read_csv(min_max_table, dtype={'food_id': str})  # 문자열 경로이면 CSV 파일 로드

        # 총 영양소 저장을 위한 딕셔너리 초기화
        total_nutrients = {
            'calories': 0, 'carb': 0, 'fat': 0, 'protein': 0,
            'ca': 0, 'p': 0, 'k': 0, 'fe': 0, 'zn': 0, 'mg': 0
        }
        total_weight = 0  # 총 중량 초기화

        for item in plate_food_data:
            try:
                food_id, measured_weight, measured_volume, region = item  # 데이터 언패킹
            except ValueError:
                print(f"[ERROR] Failed to unpack item: {item}")  # 오류 메시지 출력
                continue

        return total_nutrients