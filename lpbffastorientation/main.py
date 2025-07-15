import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
from stl import mesh
import math
import threading
import time

class STLSupportOptimizer(qtw.QMainWindow):
    def __init__(self):
        super().__init__()
        self.stl_mesh = None
        self.vertices = None
        self.faces = None
        self.support_structures = []
        self.current_orientation = [0, 0, 0]  # x, y, z rotations
        self.best_orientation = [0, 0, 0]
        self.min_support_volume = float('inf')
        self.optimization_running = False
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('3D Printing Support Optimizer')
        self.setGeometry(100, 100, 1400, 800)
        
        # Ana widget ve layout
        central_widget = qtw.QWidget()
        self.setCentralWidget(central_widget)
        layout = qtw.QHBoxLayout(central_widget)
        
        # Sol panel - kontroller
        control_panel = qtw.QWidget()
        control_panel.setFixedWidth(300)
        control_layout = qtw.QVBoxLayout(control_panel)
        
        # STL dosya yükleme
        load_group = qtw.QGroupBox("STL Dosya Yükleme")
        load_layout = qtw.QVBoxLayout(load_group)
        
        self.load_btn = qtw.QPushButton("STL Dosyası Yükle")
        self.load_btn.clicked.connect(self.load_stl_file)
        load_layout.addWidget(self.load_btn)
        
        self.file_info_label = qtw.QLabel("Dosya yüklenmedi")
        load_layout.addWidget(self.file_info_label)
        
        # Manuel oryantasyon kontrolleri
        orientation_group = qtw.QGroupBox("Manuel Oryantasyon")
        orientation_layout = qtw.QVBoxLayout(orientation_group)
        
        # X ekseni rotasyonu
        x_layout = qtw.QHBoxLayout()
        x_layout.addWidget(qtw.QLabel("X Rotasyon:"))
        self.x_slider = qtw.QSlider(qtc.Qt.Horizontal)
        self.x_slider.setRange(-180, 180)
        self.x_slider.setValue(0)
        self.x_slider.valueChanged.connect(self.update_orientation)
        self.x_value_label = qtw.QLabel("0°")
        x_layout.addWidget(self.x_slider)
        x_layout.addWidget(self.x_value_label)
        orientation_layout.addLayout(x_layout)
        
        # Y ekseni rotasyonu
        y_layout = qtw.QHBoxLayout()
        y_layout.addWidget(qtw.QLabel("Y Rotasyon:"))
        self.y_slider = qtw.QSlider(qtc.Qt.Horizontal)
        self.y_slider.setRange(-180, 180)
        self.y_slider.setValue(0)
        self.y_slider.valueChanged.connect(self.update_orientation)
        self.y_value_label = qtw.QLabel("0°")
        y_layout.addWidget(self.y_slider)
        y_layout.addWidget(self.y_value_label)
        orientation_layout.addLayout(y_layout)
        
        # Z ekseni rotasyonu
        z_layout = qtw.QHBoxLayout()
        z_layout.addWidget(qtw.QLabel("Z Rotasyon:"))
        self.z_slider = qtw.QSlider(qtc.Qt.Horizontal)
        self.z_slider.setRange(-180, 180)
        self.z_slider.setValue(0)
        self.z_slider.valueChanged.connect(self.update_orientation)
        self.z_value_label = qtw.QLabel("0°")
        z_layout.addWidget(self.z_slider)
        z_layout.addWidget(self.z_value_label)
        orientation_layout.addLayout(z_layout)
        
        # Optimizasyon kontrolleri
        optimization_group = qtw.QGroupBox("Optimizasyon")
        optimization_layout = qtw.QVBoxLayout(optimization_group)
        
        self.optimize_btn = qtw.QPushButton("Optimizasyonu Başlat")
        self.optimize_btn.clicked.connect(self.start_optimization)
        optimization_layout.addWidget(self.optimize_btn)
        
        self.progress_bar = qtw.QProgressBar()
        optimization_layout.addWidget(self.progress_bar)
        
        self.optimization_info = qtw.QTextEdit()
        self.optimization_info.setFixedHeight(150)
        optimization_layout.addWidget(self.optimization_info)
        
        # Destek ayarları
        support_group = qtw.QGroupBox("Destek Ayarları")
        support_layout = qtw.QVBoxLayout(support_group)
        
        overhang_layout = qtw.QHBoxLayout()
        overhang_layout.addWidget(qtw.QLabel("Overhang Açısı:"))
        self.overhang_spin = qtw.QSpinBox()
        self.overhang_spin.setRange(0, 90)
        self.overhang_spin.setValue(45)
        self.overhang_spin.setSuffix("°")
        overhang_layout.addWidget(self.overhang_spin)
        support_layout.addLayout(overhang_layout)
        
        self.auto_support_btn = qtw.QPushButton("Destek Yapıları Oluştur")
        self.auto_support_btn.clicked.connect(self.generate_supports)
        support_layout.addWidget(self.auto_support_btn)
        
        self.support_info_label = qtw.QLabel("Destek hacmi: 0 mm³")
        support_layout.addWidget(self.support_info_label)
        
        # Layout'a grupları ekle
        control_layout.addWidget(load_group)
        control_layout.addWidget(orientation_group)
        control_layout.addWidget(optimization_group)
        control_layout.addWidget(support_group)
        control_layout.addStretch()
        
        # Sağ panel - 3D görüntü
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111, projection='3d')
        
        # Layout'a ekle
        layout.addWidget(control_panel)
        layout.addWidget(self.canvas)
        
        # Timer for live updates
        self.update_timer = qtc.QTimer()
        self.update_timer.timeout.connect(self.update_visualization)
        
    def load_stl_file(self):
        file_path, _ = qtw.QFileDialog.getOpenFileName(self, "STL Dosyası Seç", "", "STL Files (*.stl)")
        if file_path:
            try:
                self.stl_mesh = mesh.Mesh.from_file(file_path)
                self.vertices = self.stl_mesh.vectors
                self.faces = np.arange(len(self.vertices))
                
                # Mesh bilgilerini göster
                num_faces = len(self.stl_mesh.vectors)
                self.file_info_label.setText(f"Yüklendi: {num_faces} üçgen")
                
                # İlk görselleştirme
                self.update_visualization()
                
            except Exception as e:
                qtw.QMessageBox.critical(self, "Hata", f"STL dosyası yüklenirken hata: {str(e)}")
    
    def rotate_mesh(self, vertices, rx, ry, rz):
        """Mesh'i verilen açılarla döndür"""
        # Açıları radyana çevir
        rx, ry, rz = np.radians(rx), np.radians(ry), np.radians(rz)
        
        # Rotasyon matrisleri
        Rx = np.array([[1, 0, 0],
                       [0, np.cos(rx), -np.sin(rx)],
                       [0, np.sin(rx), np.cos(rx)]])
        
        Ry = np.array([[np.cos(ry), 0, np.sin(ry)],
                       [0, 1, 0],
                       [-np.sin(ry), 0, np.cos(ry)]])
        
        Rz = np.array([[np.cos(rz), -np.sin(rz), 0],
                       [np.sin(rz), np.cos(rz), 0],
                       [0, 0, 1]])
        
        # Toplam rotasyon matrisi
        R = Rz @ Ry @ Rx
        
        # Tüm vertexleri döndür
        rotated_vertices = np.zeros_like(vertices)
        for i in range(len(vertices)):
            for j in range(3):
                rotated_vertices[i, j] = vertices[i, j] @ R
        
        return rotated_vertices
    
    def calculate_face_normal(self, triangle):
        """Üçgen yüzün normal vektörünü hesapla"""
        v1 = triangle[1] - triangle[0]
        v2 = triangle[2] - triangle[0]
        normal = np.cross(v1, v2)
        norm = np.linalg.norm(normal)
        if norm > 0:
            return normal / norm
        return np.array([0, 0, 1])
    
    def needs_support(self, triangle, overhang_angle=45):
        """Üçgenin destek gerekip gerekmediğini kontrol et"""
        normal = self.calculate_face_normal(triangle)
        # Z ekseni ile açıyı hesapla
        z_axis = np.array([0, 0, 1])
        angle = np.arccos(np.clip(np.dot(normal, z_axis), -1, 1))
        angle_degrees = np.degrees(angle)
        
        # Eğer yüzey aşağı bakıyorsa ve açı overhang açısından büyükse destek gerekir
        return angle_degrees > (90 - overhang_angle) and normal[2] < 0
    
    def generate_supports(self):
        """Destek yapılarını oluştur"""
        if self.vertices is None:
            return
        
        # Mevcut oryantasyonla mesh'i döndür
        rotated_vertices = self.rotate_mesh(self.vertices, *self.current_orientation)
        
        self.support_structures = []
        overhang_angle = self.overhang_spin.value()
        
        total_support_volume = 0
        
        for triangle in rotated_vertices:
            if self.needs_support(triangle, overhang_angle):
                # Destek yapısı oluştur
                center = np.mean(triangle, axis=0)
                
                # Build platform'a kadar destek
                if center[2] > 0:  # Sadece platform üstündeki noktalar için
                    support_height = center[2]
                    support_volume = 0.5 * 0.5 * support_height  # Basit dikdörtgen destek
                    total_support_volume += support_volume
                    
                    # Destek çubuğu
                    support_points = np.array([
                        [center[0]-0.25, center[1]-0.25, 0],
                        [center[0]+0.25, center[1]-0.25, 0],
                        [center[0]+0.25, center[1]+0.25, 0],
                        [center[0]-0.25, center[1]+0.25, 0],
                        [center[0]-0.25, center[1]-0.25, center[2]],
                        [center[0]+0.25, center[1]-0.25, center[2]],
                        [center[0]+0.25, center[1]+0.25, center[2]],
                        [center[0]-0.25, center[1]+0.25, center[2]]
                    ])
                    
                    self.support_structures.append(support_points)
        
        self.support_info_label.setText(f"Destek hacmi: {total_support_volume:.2f} mm³")
        self.update_visualization()
        
        return total_support_volume
    
    def update_orientation(self):
        """Oryantasyon slider'ları değiştiğinde çağrılır"""
        self.current_orientation = [
            self.x_slider.value(),
            self.y_slider.value(),
            self.z_slider.value()
        ]
        
        # Label'ları güncelle
        self.x_value_label.setText(f"{self.current_orientation[0]}°")
        self.y_value_label.setText(f"{self.current_orientation[1]}°")
        self.z_value_label.setText(f"{self.current_orientation[2]}°")
        
        # Canlı güncelleme
        if hasattr(self, 'stl_mesh') and self.stl_mesh is not None:
            self.update_visualization()
            # Otomatik destek oluştur
            self.generate_supports()
    
    def update_visualization(self):
        """3D görselleştirmeyi güncelle"""
        if self.vertices is None:
            return
        
        self.ax.clear()
        
        # Mesh'i döndür
        rotated_vertices = self.rotate_mesh(self.vertices, *self.current_orientation)
        
        # Ana mesh'i çiz
        collection = Poly3DCollection(rotated_vertices, alpha=0.7, facecolor='lightblue', edgecolor='black')
        self.ax.add_collection3d(collection)
        
        # Destek yapılarını çiz
        for support in self.support_structures:
            # Destek çubuğu yüzleri
            faces = [
                [support[0], support[1], support[2], support[3]],  # alt yüz
                [support[4], support[5], support[6], support[7]],  # üst yüz
                [support[0], support[1], support[5], support[4]],  # yan yüz 1
                [support[1], support[2], support[6], support[5]],  # yan yüz 2
                [support[2], support[3], support[7], support[6]],  # yan yüz 3
                [support[3], support[0], support[4], support[7]]   # yan yüz 4
            ]
            
            support_collection = Poly3DCollection(faces, alpha=0.5, facecolor='red', edgecolor='darkred')
            self.ax.add_collection3d(support_collection)
        
        # Eksenleri ayarla
        all_points = rotated_vertices.reshape(-1, 3)
        if len(self.support_structures) > 0:
            support_points = np.array(self.support_structures).reshape(-1, 3)
            all_points = np.vstack([all_points, support_points])
        
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
        # Eşit ölçekleme
        max_range = np.array([all_points[:, 0].max()-all_points[:, 0].min(),
                             all_points[:, 1].max()-all_points[:, 1].min(),
                             all_points[:, 2].max()-all_points[:, 2].min()]).max() / 2.0
        
        mid_x = (all_points[:, 0].max() + all_points[:, 0].min()) * 0.5
        mid_y = (all_points[:, 1].max() + all_points[:, 1].min()) * 0.5
        mid_z = (all_points[:, 2].max() + all_points[:, 2].min()) * 0.5
        
        self.ax.set_xlim(mid_x - max_range, mid_x + max_range)
        self.ax.set_ylim(mid_y - max_range, mid_y + max_range)
        self.ax.set_zlim(mid_z - max_range, mid_z + max_range)
        
        # Build platform'u göster
        platform_size = max_range * 2
        xx, yy = np.meshgrid(np.linspace(mid_x - platform_size/2, mid_x + platform_size/2, 2),
                           np.linspace(mid_y - platform_size/2, mid_y + platform_size/2, 2))
        zz = np.zeros_like(xx)
        self.ax.plot_surface(xx, yy, zz, alpha=0.3, color='gray')
        
        self.canvas.draw()
    
    def start_optimization(self):
        """Optimizasyon işlemini başlat"""
        if self.vertices is None:
            qtw.QMessageBox.warning(self, "Uyarı", "Önce bir STL dosyası yükleyin!")
            return
        
        if self.optimization_running:
            qtw.QMessageBox.warning(self, "Uyarı", "Optimizasyon zaten çalışıyor!")
            return
        
        self.optimization_running = True
        self.optimize_btn.setText("Optimizasyon Durduruluyor...")
        self.optimize_btn.setEnabled(False)
        
        # Threading ile optimizasyon çalıştır
        self.optimization_thread = threading.Thread(target=self.run_optimization)
        self.optimization_thread.start()
    
    def run_optimization(self):
        """Optimizasyon algoritmasını çalıştır"""
        self.min_support_volume = float('inf')
        self.best_orientation = [0, 0, 0]
        
        orientations = []
        # 100 farklı oryantasyon oluştur
        for i in range(100):
            rx = np.random.uniform(-180, 180)
            ry = np.random.uniform(-180, 180)
            rz = np.random.uniform(-180, 180)
            orientations.append([rx, ry, rz])
        
        for i, orientation in enumerate(orientations):
            if not self.optimization_running:
                break
                
            # Oryantasyonu ayarla
            self.current_orientation = orientation
            
            # UI'yi güncelle (ana thread'de)
            qtc.QMetaObject.invokeMethod(self, "update_orientation_ui", qtc.Qt.QueuedConnection)
            
            # Destek hacmini hesapla
            support_volume = self.calculate_support_volume(orientation)
            
            # En iyi oryantasyonu güncelle
            if support_volume < self.min_support_volume:
                self.min_support_volume = support_volume
                self.best_orientation = orientation.copy()
            
            # Progress bar'ı güncelle
            progress = int((i + 1) / 100 * 100)
            qtc.QMetaObject.invokeMethod(self.progress_bar, "setValue", qtc.Qt.QueuedConnection, qtc.Q_ARG(int, progress))
            
            # Bilgi güncellemesi
            info_text = f"Optimizasyon: {i+1}/100\n"
            info_text += f"Mevcut destek hacmi: {support_volume:.2f} mm³\n"
            info_text += f"En iyi destek hacmi: {self.min_support_volume:.2f} mm³\n"
            info_text += f"En iyi oryantasyon: X={self.best_orientation[0]:.1f}°, Y={self.best_orientation[1]:.1f}°, Z={self.best_orientation[2]:.1f}°"
            
            qtc.QMetaObject.invokeMethod(self, "update_optimization_info", qtc.Qt.QueuedConnection, qtc.Q_ARG(str, info_text))
            
            time.sleep(0.1)  # Görselleştirme için kısa bekleme
        
        # Optimizasyon tamamlandı
        self.optimization_running = False
        qtc.QMetaObject.invokeMethod(self, "optimization_finished", qtc.Qt.QueuedConnection)
    
    def calculate_support_volume(self, orientation):
        """Verilen oryantasyon için destek hacmini hesapla"""
        rotated_vertices = self.rotate_mesh(self.vertices, *orientation)
        
        total_support_volume = 0
        overhang_angle = self.overhang_spin.value()
        
        for triangle in rotated_vertices:
            if self.needs_support(triangle, overhang_angle):
                center = np.mean(triangle, axis=0)
                if center[2] > 0:
                    support_height = center[2]
                    support_volume = 0.5 * 0.5 * support_height
                    total_support_volume += support_volume
        
        return total_support_volume
    
    @qtc.pyqtSlot()
    def update_orientation_ui(self):
        """UI oryantasyon kontrollerini güncelle"""
        self.x_slider.setValue(int(self.current_orientation[0]))
        self.y_slider.setValue(int(self.current_orientation[1]))
        self.z_slider.setValue(int(self.current_orientation[2]))
    
    @qtc.pyqtSlot(str)
    def update_optimization_info(self, text):
        """Optimizasyon bilgilerini güncelle"""
        self.optimization_info.setText(text)
    
    @qtc.pyqtSlot()
    def optimization_finished(self):
        """Optimizasyon tamamlandığında çağrılır"""
        self.optimize_btn.setText("Optimizasyonu Başlat")
        self.optimize_btn.setEnabled(True)
        
        # En iyi oryantasyona geç
        self.current_orientation = self.best_orientation.copy()
        self.update_orientation_ui()
        
        qtw.QMessageBox.information(self, "Optimizasyon Tamamlandı", 
                                   f"En iyi oryantasyon bulundu!\n"
                                   f"Destek hacmi: {self.min_support_volume:.2f} mm³\n"
                                   f"X: {self.best_orientation[0]:.1f}°\n"
                                   f"Y: {self.best_orientation[1]:.1f}°\n"
                                   f"Z: {self.best_orientation[2]:.1f}°")

if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    window = STLSupportOptimizer()
    window.show()
    sys.exit(app.exec_())