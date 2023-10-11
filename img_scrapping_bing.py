import os
import sys
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QSpinBox, QProgressBar, QMessageBox
import requests
from bs4 import BeautifulSoup
import json
import time
import threading

class ImageFetcher(QWidget):

    def __init__(self):
        super().__init__()

        # GUI
        self.init_ui()
        
        # Variável de controle para parar o processo
        self.stop_process = False

    def init_ui(self):
        self.item_pos_label = QLabel('Nome do Item Positivo:')
        self.item_pos_entry = QLineEdit(self)
        
        self.item_neg_label = QLabel('Nome do Item Negativo:')
        self.item_neg_entry = QLineEdit(self)
        
        self.num_imgs_label = QLabel('Número de imagens:')
        self.num_imgs_spinbox = QSpinBox(self)
        self.num_imgs_spinbox.setRange(1, 100)
        
        self.root_folder_label = QLabel('Pasta Raiz:')
        self.root_folder_entry = QLineEdit(self)
        
        self.fetch_button = QPushButton('Iniciar', self)
        self.fetch_button.clicked.connect(self.fetch_images)
        
        self.stop_button = QPushButton('Parar', self)
        self.stop_button.clicked.connect(self.stop_fetching_images)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)  
        
        layout = QVBoxLayout()
        layout.addWidget(self.item_pos_label)
        layout.addWidget(self.item_pos_entry)
        layout.addWidget(self.item_neg_label)
        layout.addWidget(self.item_neg_entry)
        layout.addWidget(self.num_imgs_label)
        layout.addWidget(self.num_imgs_spinbox)
        layout.addWidget(self.root_folder_label)
        layout.addWidget(self.root_folder_entry)
        layout.addWidget(self.fetch_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.setWindowTitle('Image Fetcher')
        self.show()

    def update_progress(self, current, total):
        percent_complete = (current / total) * 100
        self.progress_bar.setValue(int(percent_complete))
        QCoreApplication.processEvents() 

    def stop_fetching_images(self):
        self.stop_process = True

    def fetch_images_from_bing(self, query, folder, num_imgs, current_count):
        base_url = f"https://www.bing.com/images/search?q={query}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        
        try:
            response = requests.get(base_url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            QMessageBox.warning(self, "Erro", f"Erro ao acessar o Bing: {e}")
            return 0

        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all("a", class_="iusc")
        img_links = []
        for tag in img_tags:
            img_info = tag.get("m")
            if img_info:
                try:
                    m = json.loads(img_info.replace("\\", ""))
                    link = m["murl"]
                    if ".jpg" in link:
                        img_links.append(link)
                except:
                    continue

        valid_downloads = 0
        for link in img_links:
            if valid_downloads >= num_imgs:
                break

            if self.stop_process:
                break  

            
            for _ in range(2): 
                try:
                    img_data = requests.get(link, timeout=10).content
                    if len(img_data) > 5000 and img_data[:2] == b'\xff\xd8':
                        filename = os.path.join(folder, f"{os.path.basename(folder)}_{valid_downloads + 1}.jpg")
                        with open(filename, 'wb') as f:
                            f.write(img_data)
                        valid_downloads += 1
                        break  
                except requests.RequestException:
                    time.sleep(2) 

            self.update_progress(valid_downloads + current_count, 2 * num_imgs)

        return valid_downloads

    def fetch_images(self):
        self.stop_process = False  
        item_pos = self.item_pos_entry.text()
        num_imgs = self.num_imgs_spinbox.value()
        
        folder_pos = os.path.join(self.root_folder_entry.text(), f"{item_pos}_positive")
        os.makedirs(folder_pos, exist_ok=True)
        downloaded_pos = self.fetch_images_from_bing(item_pos, folder_pos, num_imgs, 0)

        item_neg = self.item_neg_entry.text()
        folder_neg = os.path.join(self.root_folder_entry.text(), f"{item_pos}_negative")
        os.makedirs(folder_neg, exist_ok=True)
        _ = self.fetch_images_from_bing(item_neg, folder_neg, num_imgs, downloaded_pos)

        QMessageBox.information(self, "Sucesso", "Download das imagens concluído com sucesso!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageFetcher()
    sys.exit(app.exec_())
