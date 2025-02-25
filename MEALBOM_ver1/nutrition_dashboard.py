
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QFont, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt



# 대시보드 최종 구성 정리 
    # 영양 데이터 시각화
    # 1. 막대그래프 : 칼로리 소비량과 권장 칼로리를 비교 
    # 2. 파이차트 : 현재 영양소 섭취비율과(탄단지) 권장 비율을 비교
    # 3. 원형 진행바 : 주요 영양소(칼슘,아연등) 섭취 비율을 표현

    # 주요 사용자 인터페이스
    # 1. 사용자 이름 표시(왼쪽 상단) : 고객 이름을 표시
    # 2. 홈 버튼 : 홈 화면으로 이동 할 수 있도록 신호를 발생시킴
    

    # update_dashboard 메서드를 호출하면 NutritionSummary 객체를 기반으로 데이터가 갱신됨
    # NutritionSummary는 영양 데이터를 제공하는 클래스이며 이 코드에서는 해당 객체를 활용하여
    # 영양정보를 가져오도록 설계



# NutritionDashboard 클래스: 영양 정보를 시각적으로 표시하는 대시보드 역할을 수행
class NutritionDashboard(QMainWindow):
    go_home_signal = pyqtSignal()  # 홈 버튼이 클릭되었을 때 발생하는 신호

    def __init__(self):
        """
        NutritionDashboard 클래스의 생성자
        - UI를 설정하고 초기 NutritionSummary 데이터를 None으로 설정
        """
        super().__init__()  # 부모 클래스(QMainWindow)의 생성자 호출
        self.nutrition_summary = None  # 초기에는 NutritionSummary 데이터가 없음
        self.setup_ui()  # UI를 초기화하는 메서드 호출

    def setup_ui(self):
        """
        UI(사용자 인터페이스)를 설정하는 메서드
        - 윈도우 창의 제목, 크기, 스타일을 설정
        - 고객 정보 라벨, 차트, 영양소 진행 바 및 홈 버튼을 배치
        """
        self.setWindowTitle("Nutrition Dashboard")  # 윈도우 창의 제목 설정
        self.setGeometry(100, 100, 1200, 900)  # 창의 위치(100,100)와 크기(1200x900) 설정
        self.setStyleSheet("background-color: #282a36; color: #f8f8f2;")  # 다크 테마 스타일 적용

        # 메인 위젯 설정 (PyQt에서는 메인 레이아웃을 설정하려면 먼저 중앙 위젯을 지정해야 함)
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout()  # 세로 방향으로 위젯을 배치하는 레이아웃 생성
        self.main_widget.setLayout(self.layout)  # 메인 위젯에 레이아웃 적용

        # 고객 이름 라벨 (기본 메시지 출력)
        self.name_label = QLabel("고객 정보를 입력해주세요.")  # 기본 텍스트 설정
        self.name_label.setAlignment(Qt.AlignCenter)  # 텍스트 중앙 정렬
        self.name_label.setStyleSheet("""
            color: #f8f8f2;
            font-family: '맑은 고딕';
            font-size: 20px;
            font-weight: bold;
        """)
        self.layout.addWidget(self.name_label)  # 레이아웃에 추가

        # 상단 차트 레이아웃 (수평 정렬)
        self.top_layout = QHBoxLayout()
        self.layout.addLayout(self.top_layout, stretch=4)  # 상단 레이아웃 비율 설정

        # 칼로리 비교 막대 그래프 캔버스 (Matplotlib 활용)
        self.calorie_canvas = FigureCanvas(plt.figure())  # 빈 차트 생성
        self.top_layout.addWidget(self.calorie_canvas)  # 상단 레이아웃에 추가

        # 영양소 비율 파이 차트 캔버스
        self.nutrition_canvas = FigureCanvas(plt.figure())  # 빈 차트 생성
        self.top_layout.addWidget(self.nutrition_canvas)  # 상단 레이아웃에 추가

        # 하단 영역 제목 추가
        bottom_title = QLabel("Nutrient Intake Status")  # 제목 추가
        bottom_title.setAlignment(Qt.AlignCenter)  # 중앙 정렬
        bottom_title.setStyleSheet("color: #f8f8f2; font-size: 16px; font-weight: 1500;")  # 스타일 설정
        self.layout.addWidget(bottom_title)  # 레이아웃에 추가

        # 하단 영양소 진행 바를 위한 레이아웃 생성 (수평 정렬)
        self.bottom_layout = QHBoxLayout()
        self.layout.addLayout(self.bottom_layout, stretch=2)  # 하단 레이아웃 비율 설정

        # 홈 버튼 추가 (메인 화면으로 돌아가는 기능)
        self.add_home_button()

    def add_home_button(self):
        """
        홈 버튼을 추가하는 메서드
        - 버튼을 눌렀을 때 `go_home_signal`을 발생시켜 홈 화면으로 이동할 수 있도록 구현
        """
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)  # 여백 추가
        self.layout.addSpacerItem(spacer)

        home_button = QPushButton("Home")  # 버튼 생성
        home_button.setStyleSheet("""
            background-color: #6272a4;
            color: #f8f8f2;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
        """)
        home_button.clicked.connect(self.emit_go_home_signal)  # 버튼 클릭 시 `emit_go_home_signal` 실행
        self.layout.addWidget(home_button)  # 레이아웃에 추가

    def emit_go_home_signal(self):
        """
        홈 버튼이 눌렸을 때 `go_home_signal`을 발생시키는 메서드
        - 외부에서 해당 신호를 받아 홈 화면으로 이동 가능하도록 설계됨
        """
        self.go_home_signal.emit()  # 신호 발생 (홈 화면으로 이동하는 기능 연결 가능)

    def create_bar_chart(self):
        """
        소비된 칼로리와 권장 칼로리를 비교하는 막대 그래프 생성
        - NutritionSummary에서 데이터를 가져와 시각적으로 표현
        """
        if not self.nutrition_summary:
            return plt.figure()  # NutritionSummary가 없으면 빈 차트 반환

        consumed_calories, _, one_meal_recommend_calories = self.nutrition_summary.get_calories_data()
        fig, ax = plt.subplots()
        categories = ['Calories', 'Recommended Calories']  # X축 레이블
        values = [consumed_calories, one_meal_recommend_calories]  # Y축 데이터
        ax.bar(categories, values, color=['#6272a4', '#bd93f9'])  # 막대 그래프 색상 지정
        ax.set_title("Calorie Comparison", fontdict={'color': '#f8f8f2', 'weight': 'bold', 'size': 12})
        ax.tick_params(colors='#f8f8f2')  # 축 글자 색상 지정
        fig.patch.set_facecolor('#282a36')  # 차트 배경색 설정
        ax.set_facecolor('#282a36')  # 그래프 배경색 설정
        return fig  # 생성된 차트 반환


# if __name__ == "__main__":
#     user_csv_file_path = "FOOD_DB/user_info.csv"
#     diet_csv_file_path = "FOOD_DB/customer_diet_detail.csv"

#     nutrition_summary = NutritionSummary(user_csv_file_path, diet_csv_file_path)
#     app = QApplication(sys.argv)
#     window = NutritionDashboard(nutrition_summary)
#     window.show()
#     sys.exit(app.exec_())
