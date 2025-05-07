import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QComboBox, QProgressBar, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pytube

class DownloaderThread(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, url, save_path, download_type):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.download_type = download_type
        
    def progress_callback(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = int(bytes_downloaded / total_size * 100)
        self.progress_signal.emit(percentage)
        
    def run(self):
        try:
            self.status_signal.emit("Fetching video information...")
            yt = pytube.YouTube(self.url)
            yt.register_on_progress_callback(self.progress_callback)
            
            # Get video title and clean it for filename
            title = yt.title
            for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
                title = title.replace(char, '')
            
            if self.download_type == "Video (MP4)":
                self.status_signal.emit("Downloading video...")
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                file_path = stream.download(output_path=self.save_path, filename=f"{title}.mp4")
                self.finished_signal.emit(True, file_path)
                
            elif self.download_type == "Audio (MP3)":
                self.status_signal.emit("Extracting audio...")
                stream = yt.streams.filter(only_audio=True).first()
                mp4_file = stream.download(output_path=self.save_path, filename=f"{title}_temp")
                mp3_file = os.path.join(self.save_path, f"{title}.mp3")
                
                # Convert to MP3 (just rename since we're not actually converting)
                os.rename(mp4_file, mp3_file)
                self.finished_signal.emit(True, mp3_file)
                
        except Exception as e:
            self.status_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False, str(e))


class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("YouTube Downloader")
        self.setMinimumSize(600, 300)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Title label
        title_label = QLabel("YouTube Video Downloader")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("Video URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)
        
        # Download type
        type_layout = QHBoxLayout()
        type_label = QLabel("Download Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Video (MP4)", "Audio (MP3)"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        main_layout.addLayout(type_layout)
        
        # Save location
        save_layout = QHBoxLayout()
        save_label = QLabel("Save to:")
        self.save_path = QLineEdit()
        self.save_path.setReadOnly(True)
        self.save_path.setText(os.path.expanduser("~/Downloads"))
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_folder)
        save_layout.addWidget(save_label)
        save_layout.addWidget(self.save_path)
        save_layout.addWidget(browse_btn)
        main_layout.addLayout(save_layout)
        
        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.setStyleSheet("font-size: 16px; height: 40px;")
        self.download_btn.clicked.connect(self.start_download)
        main_layout.addWidget(self.download_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Initialize variables
        self.downloader = None
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if folder:
            self.save_path.setText(folder)
    
    def start_download(self):
        url = self.url_input.text().strip()
        save_location = self.save_path.text()
        download_type = self.type_combo.currentText()
        
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a YouTube URL")
            return
        
        if not url.startswith(("https://www.youtube.com/", "https://youtu.be/")):
            QMessageBox.warning(self, "Input Error", "Please enter a valid YouTube URL")
            return
        
        # Disable UI elements during download
        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Create and start download thread
        self.downloader = DownloaderThread(url, save_location, download_type)
        self.downloader.progress_signal.connect(self.update_progress)
        self.downloader.status_signal.connect(self.update_status)
        self.downloader.finished_signal.connect(self.download_finished)
        self.downloader.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        self.status_label.setText(message)
    
    def download_finished(self, success, message):
        self.download_btn.setEnabled(True)
        
        if success:
            self.status_label.setText("Download completed!")
            QMessageBox.information(self, "Success", f"Download completed successfully!\nSaved to: {message}")
        else:
            self.status_label.setText(f"Error: {message}")
            QMessageBox.warning(self, "Error", f"Download failed: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())