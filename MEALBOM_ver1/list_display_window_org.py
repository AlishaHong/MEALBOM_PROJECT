from PyQt5 import QtCore, QtWidgets, QtGui
import threading
import cv2
from camera import DepthVolumeCalculator
from get_weight import GetWeight
from food_processor import FoodProcessor
import traceback
from summary import NutritionSummary


class ListDisplayWindow(QtWidgets.QWidget):
    def __init__(self, main_app, parent=None):
        super().__init__(parent)
        self.main_app = main_app  # MainApp 참조 저장
        self.customer_id = None  # Customer ID를 저장하는 속성 추가
        self.setup_ui()

        # Camera and Weight Components
        self.volume_calculator = DepthVolumeCalculator(
            model_path="model/large_epoch200.pt",
            roi_points=[(130, 15), (1020, 665)],
            cls_name_color={
                '01011001': ('Rice', (255, 0, 255), 0),
                '04017001': ('Soybean Soup', (0, 255, 255), 1),
                '06012004': ('Tteokgalbi', (0, 255, 0), 2),
                '07014001': ('Egg Roll', (0, 0, 255), 3),
                '11013007': ('Spinach Namul', (255, 255, 0), 4),
                '12011008': ('Kimchi', (100, 100, 100), 5),
                '01012006': ('Black Rice', (255, 0, 255), 6),
                '04011005': ('Seaweed Soup', (0, 255, 255), 7),
                '04011007': ('Beef Stew', (0, 255, 255), 8),
                '06012008': ('Beef Bulgogi', (0, 255, 0), 9),
                '08011003': ('Stir-fried Anchovies', (0, 0, 255), 10),
                '10012001': ('Chicken Gangjeong', (0, 0, 255), 11),
                '11013002': ('Fernbrake Namul', (255, 255, 0), 12),
                '12011003': ('Radish Kimchi', (100, 100, 100), 13),
                '01012002': ('Bean Rice', (255, 0, 255), 14),
                '04011011': ('Fish Cake Soup', (0, 255, 255), 15),
                '07013003': ('Kimchi Pancake', (0, 0, 255), 16),
                '11013010': ('Bean Sprouts Namul', (255, 255, 0), 17),
                '03011011': ('Pumpkin Soup', (255, 0, 255), 18),
                '08012001': ('Stir-fried Potatoes', (255, 255, 0), 19)
            },
            food_processor=FoodProcessor(
                food_data_path='FOOD_DB/food_project_food_info.csv',
                real_time_csv_path='FOOD_DB/real_time_food_info.csv',
                customer_diet_csv_path='FOOD_DB/customer_diet_detail.csv',
                min_max_table='FOOD_DB/quantity_min_max.csv'
            ),
            total_calories=0
        )

        self.is_running = False

    def setup_ui(self):
        self.setObjectName("window2")
        self.resize(1200, 700)

        self.camera_frame = QtWidgets.QLabel(self)
        self.camera_frame.setGeometry(QtCore.QRect(20, 40, 880, 640))
        self.camera_frame.setAlignment(QtCore.Qt.AlignCenter)

        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setGeometry(QtCore.QRect(920, 40, 250, 521))

        self.btn_complete = QtWidgets.QPushButton("Complete", self)
        self.btn_complete.setGeometry(QtCore.QRect(920, 580, 250, 50))
        self.btn_complete.clicked.connect(self.save_results)

        # "대시보드 보러가기" 버튼 추가
        self.btn_go_dashboard = QtWidgets.QPushButton("대시보드 보러가기", self)
        self.btn_go_dashboard.setGeometry(QtCore.QRect(920, 630, 250, 50))
        self.btn_go_dashboard.clicked.connect(self.go_to_dashboard)
        
        self.label_customer_id = QtWidgets.QLabel("Customer ID: Not Set", self)
        self.label_customer_id.setGeometry(QtCore.QRect(20, 10, 400, 30))

    def set_customer_id(self, user_id):
        """Customer ID를 설정하고 UI를 업데이트합니다."""
        self.customer_id = user_id
        self.label_customer_id.setText(f"Customer ID: {self.customer_id} ")
        print(f"[DEBUG] Customer ID set in ListDisplayWindow: {self.customer_id}")  # 디버깅 로그


    def showEvent(self, event):
        super().showEvent(event)
        print(f"[DEBUG] ListDisplayWindow displayed with Customer ID: {self.customer_id}")  # 디버깅 로그
        if not self.customer_id:
            self.label_customer_id.setText("Customer ID: Not Set")
            print("[ERROR] Customer ID not set before showing ListDisplayWindow.")
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self.run_main_loop, daemon=True).start()
            
    def run_main_loop(self):
        if not self.customer_id:
            print("Error: Customer ID is not set. Exiting main loop.")
            return
        try:
            for blend_image, current_frame_objects in self.volume_calculator.main_loop(self.customer_id):
                rgb_image = cv2.cvtColor(blend_image, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                q_image = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(q_image)
                self.camera_frame.setPixmap(pixmap)

                # Update Object List
                self.list_widget.clear()
                for obj_id, obj_data in current_frame_objects.items():
                    obj_name = obj_data[0]
                    region = obj_data[1]
                    volume = obj_data[2]
                    weight = self.volume_calculator.confirmed_objects.get(obj_id, {}).get("weight", 0)
                    self.list_widget.addItem(f"{obj_name}: {volume:.1f}cm³, {weight}g in region {region}")
        except Exception as e:
            print(f"Error in volume_calculator.main_loop: {e}")
            print(traceback.format_exc())

    def save_results(self):
        """Complete 버튼 클릭 시 저장 호출"""
        try:
            success = self.volume_calculator.save_results()
            print(f"[DEBUG] save_results returned: {success}")  # 반환값 로그 출력

            self.is_running = False  # 메인 루프 종료 플래그 설정

            if success:
                QtWidgets.QMessageBox.information(self, "Complete", "Results saved successfully!")
            else:
                QtWidgets.QMessageBox.warning(self, "Incomplete", "No results were saved.")
        except Exception as e:
            print(f"Error in save_results: {e}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save results: {e}")
    
    def go_to_dashboard(self):
        """대시보드 화면으로 이동"""
        try:
            # 새 NutritionSummary 객체 생성
            nutrition_summary = NutritionSummary(
                "user_info.csv",  # 유저 정보 파일 경로
                "FOOD_DB/customer_diet_detail.csv",  # 새로운 데이터가 반영된 파일 경로
                self.customer_id  # 현재 고객 ID
            )

            # 대시보드 업데이트
            self.main_app.nutrition_dashboard.update_dashboard(nutrition_summary)

            # 화면 전환
            self.main_app.switch_window(3)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load updated data: {e}")
            
    def closeEvent(self, event):
        self.is_running = False
        super().closeEvent(event)


