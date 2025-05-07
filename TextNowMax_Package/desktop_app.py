"""
TextNow Max Creator - Desktop Application

A PyQt5-based desktop application for managing TextNow ghost accounts,
sending messages, and managing campaigns.
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime

# Set QT_QPA_PLATFORM to offscreen for headless environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"
# Set XDG_RUNTIME_DIR for Linux environments
if not os.environ.get("XDG_RUNTIME_DIR"):
    os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-dir"
    if not os.path.exists("/tmp/runtime-dir"):
        os.makedirs("/tmp/runtime-dir", exist_ok=True)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit,
                            QComboBox, QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QFileDialog, QProgressBar, QMessageBox, QGroupBox,
                            QFormLayout, QScrollArea, QFrame, QSplitter, QStatusBar, QAction,
                            QMenu, QMenuBar)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QTextCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl

# Set up logging
logging.basicConfig(
    filename='desktop_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global application styling
STYLESHEET = """
QMainWindow, QDialog {
    background-color: #1E1E1E;
    color: #EEE;
}
QTabWidget {
    background-color: #1E1E1E;
}
QTabWidget::pane {
    border: 1px solid #3A3A3A;
    background-color: #252525;
}
QTabBar::tab {
    background-color: #2A2A2A;
    color: #CCC;
    padding: 8px 16px;
    border: 1px solid #3A3A3A;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #FF6600;
    color: white;
}
QTabBar::tab:!selected {
    margin-top: 2px;
}
QPushButton {
    background-color: #FF6600;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #FF8533;
}
QPushButton:pressed {
    background-color: #E65C00;
}
QPushButton:disabled {
    background-color: #5A5A5A;
    color: #999;
}
QPushButton.secondary {
    background-color: #444;
    color: #EEE;
}
QPushButton.secondary:hover {
    background-color: #555;
}
QPushButton.secondary:pressed {
    background-color: #333;
}
QPushButton.danger {
    background-color: #E74C3C;
    color: white;
}
QPushButton.danger:hover {
    background-color: #F15B4A;
}
QPushButton.success {
    background-color: #27AE60;
    color: white;
}
QPushButton.success:hover {
    background-color: #2ECC71;
}
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background-color: #333;
    color: #EEE;
    border: 1px solid #444;
    padding: 6px;
    border-radius: 4px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #FF6600;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: url(assets/dropdown-arrow.png);
    width: 12px;
    height: 12px;
}
QTableWidget {
    background-color: #252525;
    color: #EEE;
    gridline-color: #3A3A3A;
    border: 1px solid #3A3A3A;
}
QTableWidget::item {
    padding: 5px;
}
QTableWidget::item:selected {
    background-color: #FF6600;
    color: white;
}
QHeaderView::section {
    background-color: #2A2A2A;
    color: #CCC;
    padding: 5px;
    border: 1px solid #3A3A3A;
}
QScrollBar:vertical {
    border: none;
    background: #2A2A2A;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #555;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QGroupBox {
    border: 1px solid #3A3A3A;
    border-radius: 4px;
    margin-top: 1em;
    padding-top: 10px;
    color: #CCC;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 5px;
}
QProgressBar {
    border: 1px solid #3A3A3A;
    border-radius: 4px;
    text-align: center;
    background-color: #333;
}
QProgressBar::chunk {
    background-color: #FF6600;
    width: 1px;
}
QLabel {
    color: #EEE;
}
QStatusBar {
    background-color: #252525;
    color: #CCC;
}
QMenuBar {
    background-color: #252525;
    color: #CCC;
}
QMenuBar::item {
    padding: 5px 10px;
}
QMenuBar::item:selected {
    background-color: #333;
}
QMenu {
    background-color: #252525;
    color: #CCC;
    border: 1px solid #3A3A3A;
}
QMenu::item {
    padding: 5px 30px 5px 20px;
}
QMenu::item:selected {
    background-color: #333;
}
"""

class DeviceStatusWidget(QWidget):
    """Widget that displays the current status of connected mobile devices"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.phone_connected = False
        self.updateDeviceStatus()
        
        # Update device status every 5 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateDeviceStatus)
        self.timer.start(5000)
        
    def initUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        self.statusLabel = QLabel("Device Status:")
        self.statusValue = QLabel("No Device Connected")
        self.statusValue.setStyleSheet("color: white; background-color: #000; padding: 4px 8px; border-radius: 4px;")
        
        self.refreshButton = QPushButton("Refresh IP")
        self.refreshButton.setEnabled(False)
        self.refreshButton.clicked.connect(self.refreshDeviceIP)
        
        layout.addWidget(self.statusLabel)
        layout.addWidget(self.statusValue)
        layout.addWidget(self.refreshButton)
        layout.addStretch()
        
    def updateDeviceStatus(self):
        """Check for connected devices and update status display"""
        # In a real implementation, this would check ADB for connected devices
        try:
            # Simulate device detection
            # In real implementation: 
            # result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            # devices = [line.split('\t')[0] for line in result.stdout.splitlines()[1:] if '\tdevice' in line]
            
            # For demo purposes:
            devices = []  # Simulating no connected device
            
            if devices:
                self.phone_connected = True
                ip = self.getCurrentIP()
                self.statusValue.setText(f"Connected: {ip}")
                self.statusValue.setStyleSheet("color: white; background-color: #27AE60; padding: 4px 8px; border-radius: 4px;")
                self.refreshButton.setEnabled(True)
            else:
                self.phone_connected = False
                self.statusValue.setText("No Device Connected")
                self.statusValue.setStyleSheet("color: white; background-color: #E74C3C; padding: 4px 8px; border-radius: 4px;")
                self.refreshButton.setEnabled(False)
                
        except Exception as e:
            logger.error(f"Error checking device status: {e}")
            self.phone_connected = False
            self.statusValue.setText("Error Checking Device")
            self.statusValue.setStyleSheet("color: white; background-color: #E74C3C; padding: 4px 8px; border-radius: 4px;")
            self.refreshButton.setEnabled(False)
    
    def getCurrentIP(self):
        """Get the current IP address of the connected device"""
        # In a real implementation, this would check the device's IP
        # For demo purposes:
        return "192.168.1.100"
    
    def refreshDeviceIP(self):
        """Toggle airplane mode to refresh the device's IP address"""
        if not self.phone_connected:
            return
            
        self.statusValue.setText("Refreshing IP...")
        self.statusValue.setStyleSheet("color: white; background-color: #F39C12; padding: 4px 8px; border-radius: 4px;")
        self.refreshButton.setEnabled(False)
        
        # In a real implementation, this would toggle airplane mode
        # For demo purposes, just simulate a delay
        QTimer.singleShot(3000, self.finishIPRefresh)
    
    def finishIPRefresh(self):
        """Update status after IP refresh completes"""
        if self.phone_connected:
            ip = self.getCurrentIP()
            self.statusValue.setText(f"Connected: {ip}")
            self.statusValue.setStyleSheet("color: white; background-color: #27AE60; padding: 4px 8px; border-radius: 4px;")
        else:
            self.statusValue.setText("No Device Connected")
            self.statusValue.setStyleSheet("color: white; background-color: #E74C3C; padding: 4px 8px; border-radius: 4px;")
        
        self.refreshButton.setEnabled(self.phone_connected)


class AccountCreatorTab(QWidget):
    """Tab for creating new TextNow accounts"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title and description
        titleLabel = QLabel("TextNow Account Creator")
        titleLabel.setFont(QFont("Arial", 14, QFont.Bold))
        descLabel = QLabel("Create new TextNow accounts with randomly generated names and credentials.")
        descLabel.setWordWrap(True)
        
        layout.addWidget(titleLabel)
        layout.addWidget(descLabel)
        layout.addSpacing(10)
        
        # Settings form
        settingsGroup = QGroupBox("Creation Settings")
        settingsLayout = QFormLayout()
        settingsGroup.setLayout(settingsLayout)
        
        self.countSpinBox = QSpinBox()
        self.countSpinBox.setRange(1, 1000)
        self.countSpinBox.setValue(10)
        self.countSpinBox.setFixedWidth(100)
        
        self.areaCodeInput = QLineEdit()
        self.areaCodeInput.setPlaceholderText("e.g. 305, 786, 954 (comma-separated)")
        
        self.stateCombo = QComboBox()
        states = ["All States", "Florida", "New York", "California", "Texas", "Illinois"]
        self.stateCombo.addItems(states)
        
        self.regionCombo = QComboBox()
        regions = ["All Regions", "Northeast", "Southeast", "Midwest", "Southwest", "West"]
        self.regionCombo.addItems(regions)
        
        self.pauseCheck = QCheckBox("Pause between accounts")
        self.pauseCheck.setChecked(True)
        
        self.randomizeCheck = QCheckBox("Randomize user agent and fingerprint")
        self.randomizeCheck.setChecked(True)
        
        settingsLayout.addRow("Number of Accounts:", self.countSpinBox)
        settingsLayout.addRow("Area Codes:", self.areaCodeInput)
        settingsLayout.addRow("State:", self.stateCombo)
        settingsLayout.addRow("Region:", self.regionCombo)
        settingsLayout.addRow("", self.pauseCheck)
        settingsLayout.addRow("", self.randomizeCheck)
        
        layout.addWidget(settingsGroup)
        layout.addSpacing(10)
        
        # Advanced settings
        advancedGroup = QGroupBox("Advanced Settings")
        advancedLayout = QFormLayout()
        advancedGroup.setLayout(advancedLayout)
        
        self.delaySpinBox = QSpinBox()
        self.delaySpinBox.setRange(1, 300)
        self.delaySpinBox.setValue(30)
        self.delaySpinBox.setSuffix(" sec")
        self.delaySpinBox.setFixedWidth(100)
        
        self.retrySpinBox = QSpinBox()
        self.retrySpinBox.setRange(0, 10)
        self.retrySpinBox.setValue(3)
        self.retrySpinBox.setFixedWidth(100)
        
        self.rotateIPCheck = QCheckBox("Rotate IP after each account")
        self.rotateIPCheck.setChecked(True)
        
        self.voicemailCheck = QCheckBox("Set up voicemail automatically")
        self.voicemailCheck.setChecked(True)
        
        advancedLayout.addRow("Delay Between Accounts:", self.delaySpinBox)
        advancedLayout.addRow("Max Retries:", self.retrySpinBox)
        advancedLayout.addRow("", self.rotateIPCheck)
        advancedLayout.addRow("", self.voicemailCheck)
        
        layout.addWidget(advancedGroup)
        layout.addSpacing(10)
        
        # Progress section
        progressGroup = QGroupBox("Creation Progress")
        progressLayout = QVBoxLayout()
        progressGroup.setLayout(progressLayout)
        
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        
        self.statusLabel = QLabel("Ready to create accounts")
        
        self.logText = QTextEdit()
        self.logText.setReadOnly(True)
        self.logText.setFixedHeight(100)
        
        progressLayout.addWidget(self.progressBar)
        progressLayout.addWidget(self.statusLabel)
        progressLayout.addWidget(self.logText)
        
        layout.addWidget(progressGroup)
        layout.addSpacing(20)
        
        # Action buttons
        buttonLayout = QHBoxLayout()
        
        self.startButton = QPushButton("Start Creation")
        self.startButton.clicked.connect(self.startCreation)
        
        self.pauseButton = QPushButton("Pause")
        self.pauseButton.setEnabled(False)
        self.pauseButton.clicked.connect(self.pauseCreation)
        
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.setEnabled(False)
        self.cancelButton.clicked.connect(self.cancelCreation)
        self.cancelButton.setProperty("class", "danger")
        
        buttonLayout.addWidget(self.startButton)
        buttonLayout.addWidget(self.pauseButton)
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addStretch()
        
        layout.addLayout(buttonLayout)
        layout.addStretch()
        
    def startCreation(self):
        """Start the account creation process"""
        count = self.countSpinBox.value()
        area_codes = self.areaCodeInput.text()
        state = self.stateCombo.currentText()
        
        # Check if required fields are filled
        if not area_codes:
            QMessageBox.warning(self, "Missing Information", "Please enter at least one area code")
            return
            
        # Check if device is connected (in a real implementation)
        # For demo purposes, show a warning
        device_connected = False  # In a real app, this would check ADB connection
        if not device_connected:
            response = QMessageBox.question(
                self, 
                "No Device Connected",
                "No Android device detected. Account creation requires a connected phone for IP rotation.\n\n"
                "Would you like to continue in simulation mode?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if response == QMessageBox.No:
                return
        
        # Update UI
        self.startButton.setEnabled(False)
        self.pauseButton.setEnabled(True)
        self.cancelButton.setEnabled(True)
        self.progressBar.setValue(0)
        self.statusLabel.setText(f"Creating accounts (0/{count})...")
        
        # Log start of creation
        self.logMessage(f"Starting creation of {count} accounts with area codes: {area_codes}")
        self.logMessage(f"State: {state}, IP Rotation: {'Enabled' if self.rotateIPCheck.isChecked() else 'Disabled'}")
        
        # In a real implementation, this would start a worker thread to create accounts
        # For demo purposes, we'll simulate progress
        self.current_account = 0
        self.total_accounts = count
        self.creation_timer = QTimer()
        self.creation_timer.timeout.connect(self.simulateProgress)
        self.creation_timer.start(1000)  # Update every second
        
    def simulateProgress(self):
        """Simulate account creation progress for demo purposes"""
        self.current_account += 1
        progress = int((self.current_account / self.total_accounts) * 100)
        self.progressBar.setValue(progress)
        
        # Create a simulated phone number based on area codes
        area_codes_list = [code.strip() for code in self.areaCodeInput.text().split(",")]
        import random
        area_code = random.choice(area_codes_list)
        phone_number = f"({area_code}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        self.statusLabel.setText(f"Creating accounts ({self.current_account}/{self.total_accounts})...")
        self.logMessage(f"Created account with number {phone_number}")
        
        if self.current_account >= self.total_accounts:
            self.creation_timer.stop()
            self.statusLabel.setText(f"Creation completed: {self.total_accounts} accounts created")
            self.progressBar.setValue(100)
            self.startButton.setEnabled(True)
            self.pauseButton.setEnabled(False)
            self.cancelButton.setEnabled(False)
            self.logMessage("Account creation completed successfully")
    
    def pauseCreation(self):
        """Pause the account creation process"""
        if hasattr(self, 'creation_timer') and self.creation_timer.isActive():
            self.creation_timer.stop()
            self.pauseButton.setText("Resume")
            self.statusLabel.setText("Creation paused")
            self.logMessage("Account creation paused")
        else:
            self.creation_timer.start(1000)
            self.pauseButton.setText("Pause")
            self.statusLabel.setText(f"Creating accounts ({self.current_account}/{self.total_accounts})...")
            self.logMessage("Account creation resumed")
    
    def cancelCreation(self):
        """Cancel the account creation process"""
        if hasattr(self, 'creation_timer'):
            self.creation_timer.stop()
        
        self.startButton.setEnabled(True)
        self.pauseButton.setEnabled(False)
        self.cancelButton.setEnabled(False)
        self.statusLabel.setText("Creation cancelled")
        self.logMessage("Account creation cancelled")
        
    def logMessage(self, message):
        """Add a message to the log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logText.append(f"[{timestamp}] {message}")
        # Auto-scroll to the bottom
        self.logText.moveCursor(QTextCursor.End)


class AccountDashboardTab(QWidget):
    """Tab for managing existing TextNow accounts"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title and description
        titleLabel = QLabel("Account Dashboard")
        titleLabel.setFont(QFont("Arial", 14, QFont.Bold))
        descLabel = QLabel("Manage your TextNow accounts and monitor their status.")
        descLabel.setWordWrap(True)
        
        layout.addWidget(titleLabel)
        layout.addWidget(descLabel)
        layout.addSpacing(15)
        
        # Search and filter controls
        filterLayout = QHBoxLayout()
        
        self.searchInput = QLineEdit()
        self.searchInput.setPlaceholderText("Search accounts...")
        
        self.filterCombo = QComboBox()
        filters = ["All Accounts", "Active", "Inactive", "Warning", "Blocked"]
        self.filterCombo.addItems(filters)
        
        self.searchButton = QPushButton("Search")
        self.searchButton.clicked.connect(self.searchAccounts)
        
        filterLayout.addWidget(QLabel("Filter:"))
        filterLayout.addWidget(self.searchInput)
        filterLayout.addWidget(self.filterCombo)
        filterLayout.addWidget(self.searchButton)
        
        layout.addLayout(filterLayout)
        layout.addSpacing(10)
        
        # Account table
        self.accountTable = QTableWidget()
        self.accountTable.setColumnCount(8)
        self.accountTable.setHorizontalHeaderLabels([
            "Phone Number", "Name", "Email", "Created", "Last Active", 
            "Status", "Health", "Actions"
        ])
        self.accountTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.accountTable.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.accountTable, 1)
        
        # Action buttons
        buttonLayout = QHBoxLayout()
        
        self.refreshButton = QPushButton("Refresh List")
        self.refreshButton.clicked.connect(self.refreshAccountList)
        
        self.exportButton = QPushButton("Export Accounts")
        self.exportButton.clicked.connect(self.exportAccounts)
        
        self.deleteButton = QPushButton("Delete Selected")
        self.deleteButton.clicked.connect(self.deleteAccounts)
        self.deleteButton.setProperty("class", "danger")
        
        buttonLayout.addWidget(self.refreshButton)
        buttonLayout.addWidget(self.exportButton)
        buttonLayout.addWidget(self.deleteButton)
        buttonLayout.addStretch()
        
        layout.addLayout(buttonLayout)
        
        # Load initial data
        self.refreshAccountList()
        
    def refreshAccountList(self):
        """Refresh the account list from the database"""
        # Clear existing data
        self.accountTable.setRowCount(0)
        
        try:
            # In a real implementation, this would load from the database
            # For demo purposes, add sample accounts
            sample_accounts = [
                {
                    "phone": "(305) 123-4567",
                    "name": "John Smith",
                    "email": "john.smith.583@gmail.com",
                    "created": "2025-03-15",
                    "last_active": "2025-04-22",
                    "status": "Active",
                    "health": "Good"
                },
                {
                    "phone": "(786) 987-6543",
                    "name": "Mary Johnson",
                    "email": "mary.j.1990@outlook.com",
                    "created": "2025-03-20",
                    "last_active": "2025-04-10",
                    "status": "Warning",
                    "health": "Borderline"
                },
                {
                    "phone": "(954) 456-7890",
                    "name": "Robert Williams",
                    "email": "robert.w.2023@gmail.com",
                    "created": "2025-02-28",
                    "last_active": "2025-04-25",
                    "status": "Active",
                    "health": "Good"
                },
                {
                    "phone": "(407) 321-6549",
                    "name": "Sarah Miller",
                    "email": "sarahm_84@yahoo.com",
                    "created": "2025-04-01",
                    "last_active": "2025-04-20",
                    "status": "Active",
                    "health": "Good"
                },
                {
                    "phone": "(561) 789-4561",
                    "name": "David Brown",
                    "email": "david.brown.official@gmail.com",
                    "created": "2025-03-10",
                    "last_active": "2025-03-25",
                    "status": "Inactive",
                    "health": "Poor"
                }
            ]
            
            # Add accounts to table
            for account in sample_accounts:
                row = self.accountTable.rowCount()
                self.accountTable.insertRow(row)
                
                self.accountTable.setItem(row, 0, QTableWidgetItem(account["phone"]))
                self.accountTable.setItem(row, 1, QTableWidgetItem(account["name"]))
                self.accountTable.setItem(row, 2, QTableWidgetItem(account["email"]))
                self.accountTable.setItem(row, 3, QTableWidgetItem(account["created"]))
                self.accountTable.setItem(row, 4, QTableWidgetItem(account["last_active"]))
                
                status_item = QTableWidgetItem(account["status"])
                if account["status"] == "Active":
                    status_item.setForeground(QColor("#27AE60"))
                elif account["status"] == "Warning":
                    status_item.setForeground(QColor("#F39C12"))
                elif account["status"] == "Inactive":
                    status_item.setForeground(QColor("#7F8C8D"))
                elif account["status"] == "Blocked":
                    status_item.setForeground(QColor("#E74C3C"))
                self.accountTable.setItem(row, 5, status_item)
                
                health_item = QTableWidgetItem(account["health"])
                if account["health"] == "Good":
                    health_item.setForeground(QColor("#27AE60"))
                elif account["health"] == "Borderline":
                    health_item.setForeground(QColor("#F39C12"))
                elif account["health"] == "Poor":
                    health_item.setForeground(QColor("#E74C3C"))
                self.accountTable.setItem(row, 6, health_item)
                
                # Action buttons in cell
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                
                login_btn = QPushButton("Login")
                login_btn.setFixedSize(60, 25)
                login_btn.setProperty("class", "secondary")
                
                send_btn = QPushButton("Send")
                send_btn.setFixedSize(60, 25)
                send_btn.setProperty("class", "secondary")
                
                actions_layout.addWidget(login_btn)
                actions_layout.addWidget(send_btn)
                
                self.accountTable.setCellWidget(row, 7, actions_widget)
            
        except Exception as e:
            logger.error(f"Error loading accounts: {e}")
            QMessageBox.critical(self, "Database Error", f"Error loading accounts: {str(e)}")
    
    def searchAccounts(self):
        """Search accounts based on filter criteria"""
        search_text = self.searchInput.text().lower()
        filter_option = self.filterCombo.currentText()
        
        # Hide rows that don't match search criteria
        for row in range(self.accountTable.rowCount()):
            show_row = True
            
            # Check filter by status
            if filter_option != "All Accounts":
                status_item = self.accountTable.item(row, 5)
                if status_item and status_item.text() != filter_option:
                    show_row = False
            
            # Check search text
            if search_text and show_row:
                match_found = False
                for col in range(3):  # Check in first 3 columns (phone, name, email)
                    item = self.accountTable.item(row, col)
                    if item and search_text in item.text().lower():
                        match_found = True
                        break
                
                show_row = match_found
            
            self.accountTable.setRowHidden(row, not show_row)
    
    def exportAccounts(self):
        """Export accounts to CSV file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Accounts", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w') as f:
                # Write header
                headers = [self.accountTable.horizontalHeaderItem(i).text() 
                           for i in range(self.accountTable.columnCount() - 1)]  # Skip Actions column
                f.write(','.join(headers) + '\n')
                
                # Write data
                for row in range(self.accountTable.rowCount()):
                    if not self.accountTable.isRowHidden(row):
                        row_data = []
                        for col in range(self.accountTable.columnCount() - 1):  # Skip Actions column
                            item = self.accountTable.item(row, col)
                            row_data.append(item.text() if item else "")
                        f.write(','.join(row_data) + '\n')
                
            QMessageBox.information(self, "Export Successful", f"Accounts exported to {file_path}")
            
        except Exception as e:
            logger.error(f"Error exporting accounts: {e}")
            QMessageBox.critical(self, "Export Error", f"Error exporting accounts: {str(e)}")
    
    def deleteAccounts(self):
        """Delete selected accounts"""
        selected_rows = set(item.row() for item in self.accountTable.selectedItems())
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select accounts to delete")
            return
            
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_rows)} account(s)?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # In a real implementation, this would delete from the database
            # For demo purposes, just remove from the table
            for row in sorted(selected_rows, reverse=True):
                self.accountTable.removeRow(row)
            
            QMessageBox.information(self, "Deletion Complete", f"{len(selected_rows)} account(s) deleted")


class CampaignTab(QWidget):
    """Tab for managing message campaigns"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title and description
        titleLabel = QLabel("Campaign Manager")
        titleLabel.setFont(QFont("Arial", 14, QFont.Bold))
        descLabel = QLabel("Create and manage messaging campaigns to send messages from your accounts.")
        descLabel.setWordWrap(True)
        
        layout.addWidget(titleLabel)
        layout.addWidget(descLabel)
        layout.addSpacing(15)
        
        # Split view with campaign list on left, details on right
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Campaign list
        leftWidget = QWidget()
        leftLayout = QVBoxLayout(leftWidget)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        
        # Campaign controls
        controlLayout = QHBoxLayout()
        
        self.newCampaignButton = QPushButton("New Campaign")
        self.newCampaignButton.clicked.connect(self.createNewCampaign)
        
        self.importButton = QPushButton("Import")
        self.importButton.setProperty("class", "secondary")
        
        controlLayout.addWidget(self.newCampaignButton)
        controlLayout.addWidget(self.importButton)
        controlLayout.addStretch()
        
        leftLayout.addLayout(controlLayout)
        leftLayout.addSpacing(10)
        
        # Campaign list
        self.campaignList = QTableWidget()
        self.campaignList.setColumnCount(4)
        self.campaignList.setHorizontalHeaderLabels(["Name", "Status", "Progress", "Created"])
        self.campaignList.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.campaignList.setSelectionBehavior(QTableWidget.SelectRows)
        self.campaignList.setSelectionMode(QTableWidget.SingleSelection)
        self.campaignList.setEditTriggers(QTableWidget.NoEditTriggers)
        self.campaignList.itemSelectionChanged.connect(self.campaignSelected)
        
        leftLayout.addWidget(self.campaignList)
        
        # Right panel - Campaign details
        rightWidget = QWidget()
        self.rightLayout = QVBoxLayout(rightWidget)
        self.rightLayout.setContentsMargins(10, 0, 0, 0)
        
        # Default right panel content (empty state)
        self.setupEmptyDetailsPanel()
        
        # Add panels to splitter
        splitter.addWidget(leftWidget)
        splitter.addWidget(rightWidget)
        splitter.setSizes([300, 700])  # Set initial sizes
        
        layout.addWidget(splitter)
        
        # Load sample campaigns
        self.loadSampleCampaigns()
        
    def setupEmptyDetailsPanel(self):
        """Set up empty state for campaign details panel"""
        # Clear existing widgets
        for i in reversed(range(self.rightLayout.count())): 
            widget = self.rightLayout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        # Add empty state message
        emptyLabel = QLabel("Select a campaign to view details or create a new campaign")
        emptyLabel.setAlignment(Qt.AlignCenter)
        emptyLabel.setStyleSheet("color: #999; font-size: 14px;")
        
        self.rightLayout.addWidget(emptyLabel)
        self.rightLayout.addStretch()
        
    def setupCampaignDetailsPanel(self, campaign):
        """Set up campaign details panel for the selected campaign"""
        # Clear existing widgets
        for i in reversed(range(self.rightLayout.count())): 
            widget = self.rightLayout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        # Campaign header
        headerLayout = QHBoxLayout()
        
        nameLabel = QLabel(campaign["name"])
        nameLabel.setFont(QFont("Arial", 14, QFont.Bold))
        
        statusLabel = QLabel(campaign["status"])
        if campaign["status"] == "Running":
            statusLabel.setStyleSheet("background-color: #27AE60; color: white; padding: 4px 8px; border-radius: 4px;")
        elif campaign["status"] == "Paused":
            statusLabel.setStyleSheet("background-color: #F39C12; color: white; padding: 4px 8px; border-radius: 4px;")
        elif campaign["status"] == "Completed":
            statusLabel.setStyleSheet("background-color: #3498DB; color: white; padding: 4px 8px; border-radius: 4px;")
        elif campaign["status"] == "Scheduled":
            statusLabel.setStyleSheet("background-color: #9B59B6; color: white; padding: 4px 8px; border-radius: 4px;")
        
        headerLayout.addWidget(nameLabel)
        headerLayout.addStretch()
        headerLayout.addWidget(statusLabel)
        
        self.rightLayout.addLayout(headerLayout)
        
        # Campaign details
        detailsGroup = QGroupBox("Campaign Details")
        detailsLayout = QFormLayout()
        detailsGroup.setLayout(detailsLayout)
        
        createdLabel = QLabel(campaign["created"])
        messagesLabel = QLabel(f"{campaign['sent']}/{campaign['total']} messages sent")
        accountsLabel = QLabel(f"{campaign['accounts']} accounts used")
        
        detailsLayout.addRow("Created:", createdLabel)
        detailsLayout.addRow("Messages:", messagesLabel)
        detailsLayout.addRow("Accounts:", accountsLabel)
        
        if "schedule" in campaign:
            scheduleLabel = QLabel(campaign["schedule"])
            detailsLayout.addRow("Schedule:", scheduleLabel)
        
        self.rightLayout.addWidget(detailsGroup)
        
        # Progress
        if campaign["status"] == "Running" or campaign["status"] == "Paused":
            progressGroup = QGroupBox("Progress")
            progressLayout = QVBoxLayout()
            progressGroup.setLayout(progressLayout)
            
            progressBar = QProgressBar()
            progress = int((campaign['sent'] / campaign['total']) * 100)
            progressBar.setValue(progress)
            
            progressLayout.addWidget(progressBar)
            
            self.rightLayout.addWidget(progressGroup)
        
        # Message preview
        previewGroup = QGroupBox("Message Preview")
        previewLayout = QVBoxLayout()
        previewGroup.setLayout(previewLayout)
        
        messageText = QTextEdit()
        messageText.setReadOnly(True)
        messageText.setPlainText(campaign["message_preview"])
        messageText.setFixedHeight(100)
        
        previewLayout.addWidget(messageText)
        
        if "media" in campaign and campaign["media"]:
            mediaLabel = QLabel("Media attachments: " + campaign["media"])
            previewLayout.addWidget(mediaLabel)
        
        self.rightLayout.addWidget(previewGroup)
        
        # Action buttons
        buttonLayout = QHBoxLayout()
        
        if campaign["status"] == "Running":
            pauseButton = QPushButton("Pause Campaign")
            pauseButton.setProperty("class", "secondary")
            buttonLayout.addWidget(pauseButton)
        elif campaign["status"] == "Paused":
            resumeButton = QPushButton("Resume Campaign")
            buttonLayout.addWidget(resumeButton)
        elif campaign["status"] == "Scheduled":
            startNowButton = QPushButton("Start Now")
            buttonLayout.addWidget(startNowButton)
        
        if campaign["status"] != "Completed":
            stopButton = QPushButton("Stop Campaign")
            stopButton.setProperty("class", "danger")
            buttonLayout.addWidget(stopButton)
        
        editButton = QPushButton("Edit Campaign")
        duplicateButton = QPushButton("Duplicate")
        duplicateButton.setProperty("class", "secondary")
        deleteButton = QPushButton("Delete")
        deleteButton.setProperty("class", "danger")
        
        buttonLayout.addWidget(editButton)
        buttonLayout.addWidget(duplicateButton)
        buttonLayout.addWidget(deleteButton)
        
        self.rightLayout.addLayout(buttonLayout)
        
        # Add spacing and stretch at the end
        self.rightLayout.addSpacing(20)
        self.rightLayout.addStretch()
        
    def loadSampleCampaigns(self):
        """Load sample campaign data for demo purposes"""
        self.campaigns = [
            {
                "id": 1,
                "name": "April Promotion",
                "status": "Running",
                "progress": 65,
                "created": "2025-04-15",
                "sent": 6500,
                "total": 10000,
                "accounts": 15,
                "message_preview": "Hi there! Check out our special April promotion. Get 20% off your next purchase with code SPRING20.",
                "media": "spring_promo.jpg"
            },
            {
                "id": 2,
                "name": "Customer Follow-up",
                "status": "Completed",
                "progress": 100,
                "created": "2025-04-01",
                "sent": 5000,
                "total": 5000,
                "accounts": 10,
                "message_preview": "Thank you for your recent purchase! We hope you're enjoying your new product. Please let us know if you have any questions."
            },
            {
                "id": 3,
                "name": "Weekend Flash Sale",
                "status": "Scheduled",
                "progress": 0,
                "created": "2025-04-20",
                "sent": 0,
                "total": 7500,
                "accounts": 20,
                "message_preview": "FLASH SALE this weekend only! Save up to 50% on selected items. Shop now before they're gone!",
                "media": "flash_sale.jpg, promo_video.mp4",
                "schedule": "Starts Apr 27, 2025 at 08:00"
            },
            {
                "id": 4,
                "name": "Restock Notification",
                "status": "Paused",
                "progress": 35,
                "created": "2025-04-18",
                "sent": 1750,
                "total": 5000,
                "accounts": 8,
                "message_preview": "Good news! The item you were interested in is back in stock. Order now while supplies last."
            }
        ]
        
        # Populate campaign list
        self.campaignList.setRowCount(len(self.campaigns))
        for i, campaign in enumerate(self.campaigns):
            # Name
            self.campaignList.setItem(i, 0, QTableWidgetItem(campaign["name"]))
            
            # Status
            status_item = QTableWidgetItem(campaign["status"])
            if campaign["status"] == "Running":
                status_item.setForeground(QColor("#27AE60"))
            elif campaign["status"] == "Paused":
                status_item.setForeground(QColor("#F39C12"))
            elif campaign["status"] == "Completed":
                status_item.setForeground(QColor("#3498DB"))
            elif campaign["status"] == "Scheduled":
                status_item.setForeground(QColor("#9B59B6"))
            self.campaignList.setItem(i, 1, status_item)
            
            # Progress
            progress_item = QTableWidgetItem(f"{campaign['progress']}%")
            self.campaignList.setItem(i, 2, progress_item)
            
            # Created
            self.campaignList.setItem(i, 3, QTableWidgetItem(campaign["created"]))
    
    def campaignSelected(self):
        """Handle selection of a campaign in the list"""
        selected_items = self.campaignList.selectedItems()
        if not selected_items:
            self.setupEmptyDetailsPanel()
            return
            
        row = selected_items[0].row()
        selected_campaign = self.campaigns[row]
        self.setupCampaignDetailsPanel(selected_campaign)
    
    def createNewCampaign(self):
        """Create a new campaign"""
        QMessageBox.information(
            self,
            "Create New Campaign",
            "This would open the campaign creation wizard.\nNot implemented in this demo."
        )


class VoicemailTab(QWidget):
    """Tab for managing voicemail greetings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title and description
        titleLabel = QLabel("Voicemail Manager")
        titleLabel.setFont(QFont("Arial", 14, QFont.Bold))
        descLabel = QLabel("Manage voicemail greetings for your TextNow accounts. Upload recordings or generate new ones.")
        descLabel.setWordWrap(True)
        
        layout.addWidget(titleLabel)
        layout.addWidget(descLabel)
        layout.addSpacing(15)
        
        # Split view - Voicemail library and assignments
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Voicemail library
        leftWidget = QWidget()
        leftLayout = QVBoxLayout(leftWidget)
        
        libraryLabel = QLabel("Voicemail Library")
        libraryLabel.setFont(QFont("Arial", 12, QFont.Bold))
        
        uploadButton = QPushButton("Upload Voicemail")
        uploadButton.clicked.connect(self.uploadVoicemail)
        
        generateButton = QPushButton("Generate New")
        generateButton.setProperty("class", "secondary")
        
        controlLayout = QHBoxLayout()
        controlLayout.addWidget(uploadButton)
        controlLayout.addWidget(generateButton)
        controlLayout.addStretch()
        
        leftLayout.addWidget(libraryLabel)
        leftLayout.addLayout(controlLayout)
        leftLayout.addSpacing(10)
        
        # Voicemail list
        voicemailLayout = QVBoxLayout()
        voicemailLayout.setSpacing(10)
        
        # Sample voicemail entries
        voicemails = [
            {"name": "Female_Professional_1.mp3", "duration": "12s", "used": 22},
            {"name": "Male_Casual_2.mp3", "duration": "10s", "used": 18},
            {"name": "Female_Casual_1.mp3", "duration": "15s", "used": 30},
            {"name": "Male_Business_1.mp3", "duration": "14s", "used": 25},
            {"name": "Male_Casual_1.mp3", "duration": "8s", "used": 15}
        ]
        
        for vm in voicemails:
            vmWidget = QFrame()
            vmWidget.setFrameShape(QFrame.StyledPanel)
            vmWidget.setStyleSheet("background-color: #2A2A2A; border-radius: 4px;")
            
            vmLayout = QVBoxLayout(vmWidget)
            
            nameLabel = QLabel(vm["name"])
            nameLabel.setFont(QFont("Arial", 10, QFont.Bold))
            
            infoLabel = QLabel(f"Duration: {vm['duration']} • Used: {vm['used']} times")
            infoLabel.setStyleSheet("color: #CCC; font-size: 12px;")
            
            buttonLayout = QHBoxLayout()
            
            playButton = QPushButton("▶ Play")
            playButton.setFixedWidth(60)
            playButton.setProperty("class", "secondary")
            
            assignButton = QPushButton("Assign")
            assignButton.setFixedWidth(60)
            assignButton.setProperty("class", "secondary")
            
            deleteButton = QPushButton("Delete")
            deleteButton.setFixedWidth(60)
            deleteButton.setProperty("class", "danger")
            
            buttonLayout.addWidget(playButton)
            buttonLayout.addWidget(assignButton)
            buttonLayout.addWidget(deleteButton)
            buttonLayout.addStretch()
            
            vmLayout.addWidget(nameLabel)
            vmLayout.addWidget(infoLabel)
            vmLayout.addLayout(buttonLayout)
            
            voicemailLayout.addWidget(vmWidget)
        
        # Scrollable area for voicemails
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollContainer = QWidget()
        scrollContainer.setLayout(voicemailLayout)
        scrollArea.setWidget(scrollContainer)
        
        leftLayout.addWidget(scrollArea)
        
        # Right panel - Voicemail assignments
        rightWidget = QWidget()
        rightLayout = QVBoxLayout(rightWidget)
        
        assignmentLabel = QLabel("Voicemail Assignments")
        assignmentLabel.setFont(QFont("Arial", 12, QFont.Bold))
        
        # Search and filter
        searchLayout = QHBoxLayout()
        
        searchInput = QLineEdit()
        searchInput.setPlaceholderText("Search accounts...")
        
        filterCombo = QComboBox()
        filterCombo.addItems(["All Accounts", "With Voicemail", "Without Voicemail"])
        
        searchButton = QPushButton("Filter")
        searchButton.setFixedWidth(70)
        searchButton.setProperty("class", "secondary")
        
        searchLayout.addWidget(searchInput)
        searchLayout.addWidget(filterCombo)
        searchLayout.addWidget(searchButton)
        
        rightLayout.addWidget(assignmentLabel)
        rightLayout.addLayout(searchLayout)
        rightLayout.addSpacing(10)
        
        # Assignment table
        assignmentTable = QTableWidget()
        assignmentTable.setColumnCount(6)
        assignmentTable.setHorizontalHeaderLabels([
            "", "Phone Number", "Account Name", "Current Voicemail", "Last Changed", "Actions"
        ])
        assignmentTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        assignmentTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        assignmentTable.setColumnWidth(0, 30)
        
        # Sample data
        accounts = [
            {"phone": "(954) 123-4567", "name": "John Smith", "voicemail": "Male_Greeting_1.mp3", "changed": "2 weeks ago"},
            {"phone": "(786) 987-6543", "name": "Jane Doe", "voicemail": "Female_Casual_2.mp3", "changed": "1 week ago"},
            {"phone": "(305) 456-7890", "name": "Robert Johnson", "voicemail": "Male_Business_3.mp3", "changed": "3 days ago"},
            {"phone": "(407) 789-0123", "name": "Lisa Williams", "voicemail": None, "changed": "N/A"},
            {"phone": "(561) 234-5678", "name": "Michael Brown", "voicemail": "Male_Casual_1.mp3", "changed": "5 days ago"}
        ]
        
        assignmentTable.setRowCount(len(accounts))
        for i, account in enumerate(accounts):
            # Checkbox
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Unchecked)
            assignmentTable.setItem(i, 0, checkbox)
            
            # Account info
            assignmentTable.setItem(i, 1, QTableWidgetItem(account["phone"]))
            assignmentTable.setItem(i, 2, QTableWidgetItem(account["name"]))
            
            # Voicemail
            if account["voicemail"]:
                assignmentTable.setItem(i, 3, QTableWidgetItem(account["voicemail"]))
                assignmentTable.setItem(i, 4, QTableWidgetItem(account["changed"]))
            else:
                no_vm = QTableWidgetItem("No voicemail set")
                no_vm.setForeground(QColor("#999"))
                assignmentTable.setItem(i, 3, no_vm)
                assignmentTable.setItem(i, 4, QTableWidgetItem("N/A"))
            
            # Actions
            actionsWidget = QWidget()
            actionsLayout = QHBoxLayout(actionsWidget)
            actionsLayout.setContentsMargins(2, 2, 2, 2)
            
            if account["voicemail"]:
                playButton = QPushButton("▶ Play")
                playButton.setFixedSize(50, 25)
                playButton.setProperty("class", "secondary")
                actionsLayout.addWidget(playButton)
            
            changeButton = QPushButton("Change")
            changeButton.setFixedSize(60, 25)
            changeButton.setProperty("class", "secondary")
            actionsLayout.addWidget(changeButton)
            
            actionsLayout.addStretch()
            
            assignmentTable.setCellWidget(i, 5, actionsWidget)
        
        rightLayout.addWidget(assignmentTable)
        
        # Bulk actions
        bulkLayout = QHBoxLayout()
        
        bulkAssignButton = QPushButton("Assign to Selected")
        bulkAssignButton.setProperty("class", "secondary")
        
        bulkLayout.addWidget(bulkAssignButton)
        bulkLayout.addStretch()
        
        rightLayout.addLayout(bulkLayout)
        
        # Add panels to splitter
        splitter.addWidget(leftWidget)
        splitter.addWidget(rightWidget)
        splitter.setSizes([400, 600])  # Set initial sizes
        
        layout.addWidget(splitter)
        
    def uploadVoicemail(self):
        """Upload new voicemail greeting files"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Upload Voicemail Greetings", "", "Audio Files (*.mp3 *.wav *.m4a);;All Files (*)"
        )
        
        if not file_paths:
            return
            
        message = f"Selected {len(file_paths)} file(s) for upload:\n\n"
        for path in file_paths:
            message += f"- {os.path.basename(path)}\n"
            
        QMessageBox.information(self, "Upload Voicemail", message + "\n\nFiles would be processed and added to the library.")


class ImageManagerTab(QWidget):
    """Tab for managing images and media for messages"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title and description
        titleLabel = QLabel("Media Manager")
        titleLabel.setFont(QFont("Arial", 14, QFont.Bold))
        descLabel = QLabel("Manage images, videos, and other media files for your campaigns and messages.")
        descLabel.setWordWrap(True)
        
        layout.addWidget(titleLabel)
        layout.addWidget(descLabel)
        layout.addSpacing(15)
        
        # Tabs for different media types
        mediaTabs = QTabWidget()
        
        # Images tab
        imagesTab = QWidget()
        imagesLayout = QVBoxLayout(imagesTab)
        
        # Image controls
        imageControlLayout = QHBoxLayout()
        
        uploadImageButton = QPushButton("Upload Images")
        uploadImageButton.clicked.connect(lambda: self.uploadMedia("images"))
        
        createFolderButton = QPushButton("Create Folder")
        createFolderButton.setProperty("class", "secondary")
        
        deleteImageButton = QPushButton("Delete Selected")
        deleteImageButton.setProperty("class", "danger")
        
        imageControlLayout.addWidget(uploadImageButton)
        imageControlLayout.addWidget(createFolderButton)
        imageControlLayout.addWidget(deleteImageButton)
        imageControlLayout.addStretch()
        
        imagesLayout.addLayout(imageControlLayout)
        
        # Image grid
        # This would use a custom widget in a real implementation
        # For demo purposes, just show a placeholder
        imagesPlaceholder = QLabel("Image grid would be displayed here\n(12 sample images in 3x4 grid)")
        imagesPlaceholder.setAlignment(Qt.AlignCenter)
        imagesPlaceholder.setStyleSheet("background-color: #252525; padding: 100px; border-radius: 4px;")
        
        imagesLayout.addWidget(imagesPlaceholder)
        
        # Videos tab
        videosTab = QWidget()
        videosLayout = QVBoxLayout(videosTab)
        
        # Video controls
        videoControlLayout = QHBoxLayout()
        
        uploadVideoButton = QPushButton("Upload Videos")
        uploadVideoButton.clicked.connect(lambda: self.uploadMedia("videos"))
        
        deleteVideoButton = QPushButton("Delete Selected")
        deleteVideoButton.setProperty("class", "danger")
        
        videoControlLayout.addWidget(uploadVideoButton)
        videoControlLayout.addWidget(deleteVideoButton)
        videoControlLayout.addStretch()
        
        videosLayout.addLayout(videoControlLayout)
        
        # Video list
        videosTable = QTableWidget()
        videosTable.setColumnCount(5)
        videosTable.setHorizontalHeaderLabels(["Name", "Duration", "Size", "Added", "Actions"])
        videosTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Sample videos
        videos = [
            {"name": "product_demo.mp4", "duration": "0:45", "size": "8.2 MB", "added": "2025-04-10"},
            {"name": "testimonial_1.mp4", "duration": "1:30", "size": "12.5 MB", "added": "2025-04-15"},
            {"name": "promo_spring.mp4", "duration": "0:30", "size": "5.8 MB", "added": "2025-04-20"}
        ]
        
        videosTable.setRowCount(len(videos))
        for i, video in enumerate(videos):
            videosTable.setItem(i, 0, QTableWidgetItem(video["name"]))
            videosTable.setItem(i, 1, QTableWidgetItem(video["duration"]))
            videosTable.setItem(i, 2, QTableWidgetItem(video["size"]))
            videosTable.setItem(i, 3, QTableWidgetItem(video["added"]))
            
            # Actions
            actionsWidget = QWidget()
            actionsLayout = QHBoxLayout(actionsWidget)
            actionsLayout.setContentsMargins(2, 2, 2, 2)
            
            playButton = QPushButton("▶ Play")
            playButton.setFixedSize(50, 25)
            playButton.setProperty("class", "secondary")
            
            infoButton = QPushButton("Info")
            infoButton.setFixedSize(50, 25)
            infoButton.setProperty("class", "secondary")
            
            actionsLayout.addWidget(playButton)
            actionsLayout.addWidget(infoButton)
            actionsLayout.addStretch()
            
            videosTable.setCellWidget(i, 4, actionsWidget)
        
        videosLayout.addWidget(videosTable)
        
        # Audio tab
        audioTab = QWidget()
        audioLayout = QVBoxLayout(audioTab)
        
        # Audio controls
        audioControlLayout = QHBoxLayout()
        
        uploadAudioButton = QPushButton("Upload Audio")
        uploadAudioButton.clicked.connect(lambda: self.uploadMedia("audio"))
        
        deleteAudioButton = QPushButton("Delete Selected")
        deleteAudioButton.setProperty("class", "danger")
        
        audioControlLayout.addWidget(uploadAudioButton)
        audioControlLayout.addWidget(deleteAudioButton)
        audioControlLayout.addStretch()
        
        audioLayout.addLayout(audioControlLayout)
        
        # Audio list
        audioTable = QTableWidget()
        audioTable.setColumnCount(5)
        audioTable.setHorizontalHeaderLabels(["Name", "Duration", "Size", "Added", "Actions"])
        audioTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Sample audio files
        audioFiles = [
            {"name": "ringtone_1.mp3", "duration": "0:30", "size": "2.8 MB", "added": "2025-04-05"},
            {"name": "notification.mp3", "duration": "0:05", "size": "0.5 MB", "added": "2025-04-12"},
            {"name": "greeting.mp3", "duration": "0:15", "size": "1.2 MB", "added": "2025-04-22"}
        ]
        
        audioTable.setRowCount(len(audioFiles))
        for i, audio in enumerate(audioFiles):
            audioTable.setItem(i, 0, QTableWidgetItem(audio["name"]))
            audioTable.setItem(i, 1, QTableWidgetItem(audio["duration"]))
            audioTable.setItem(i, 2, QTableWidgetItem(audio["size"]))
            audioTable.setItem(i, 3, QTableWidgetItem(audio["added"]))
            
            # Actions
            actionsWidget = QWidget()
            actionsLayout = QHBoxLayout(actionsWidget)
            actionsLayout.setContentsMargins(2, 2, 2, 2)
            
            playButton = QPushButton("▶ Play")
            playButton.setFixedSize(50, 25)
            playButton.setProperty("class", "secondary")
            
            infoButton = QPushButton("Info")
            infoButton.setFixedSize(50, 25)
            infoButton.setProperty("class", "secondary")
            
            actionsLayout.addWidget(playButton)
            actionsLayout.addWidget(infoButton)
            actionsLayout.addStretch()
            
            audioTable.setCellWidget(i, 4, actionsWidget)
        
        audioLayout.addWidget(audioTable)
        
        # Add tabs
        mediaTabs.addTab(imagesTab, "Images")
        mediaTabs.addTab(videosTab, "Videos")
        mediaTabs.addTab(audioTab, "Audio")
        
        layout.addWidget(mediaTabs)
        
    def uploadMedia(self, media_type):
        """Upload media files of specified type"""
        file_filter = "All Files (*)"
        title = "Upload Media"
        
        if media_type == "images":
            file_filter = "Image Files (*.jpg *.jpeg *.png *.gif *.bmp);;All Files (*)"
            title = "Upload Images"
        elif media_type == "videos":
            file_filter = "Video Files (*.mp4 *.mov *.avi *.wmv);;All Files (*)"
            title = "Upload Videos"
        elif media_type == "audio":
            file_filter = "Audio Files (*.mp3 *.wav *.m4a *.ogg);;All Files (*)"
            title = "Upload Audio"
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, title, "", file_filter
        )
        
        if not file_paths:
            return
            
        message = f"Selected {len(file_paths)} {media_type} file(s) for upload:\n\n"
        for path in file_paths:
            message += f"- {os.path.basename(path)}\n"
            
        QMessageBox.information(self, f"Upload {media_type.capitalize()}", message + "\n\nFiles would be processed and added to the library.")


class AreaCodeManagerTab(QWidget):
    """Tab for managing area codes for account creation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title and description
        titleLabel = QLabel("Area Code Manager")
        titleLabel.setFont(QFont("Arial", 14, QFont.Bold))
        descLabel = QLabel("Manage area codes and presets for account creation across all US states and territories.")
        descLabel.setWordWrap(True)
        
        layout.addWidget(titleLabel)
        layout.addWidget(descLabel)
        layout.addSpacing(15)
        
        # Split view
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Area code presets
        leftWidget = QWidget()
        leftLayout = QVBoxLayout(leftWidget)
        
        presetLabel = QLabel("Area Code Presets")
        presetLabel.setFont(QFont("Arial", 12, QFont.Bold))
        
        # Preset controls
        presetControlLayout = QHBoxLayout()
        
        newPresetButton = QPushButton("New Preset")
        newPresetButton.clicked.connect(self.createNewPreset)
        
        deletePresetButton = QPushButton("Delete Preset")
        deletePresetButton.setProperty("class", "danger")
        
        presetControlLayout.addWidget(newPresetButton)
        presetControlLayout.addWidget(deletePresetButton)
        presetControlLayout.addStretch()
        
        leftLayout.addWidget(presetLabel)
        leftLayout.addLayout(presetControlLayout)
        leftLayout.addSpacing(10)
        
        # Preset list
        presetList = QTableWidget()
        presetList.setColumnCount(3)
        presetList.setHorizontalHeaderLabels(["Name", "Area Codes", "Default"])
        presetList.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        presetList.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Sample presets
        presets = [
            {"name": "Florida Main", "codes": "305, 786, 954, 561, 407", "default": True},
            {"name": "New York City", "codes": "212, 646, 917, 718", "default": False},
            {"name": "California", "codes": "213, 310, 323, 415, 510, 619", "default": False},
            {"name": "Texas Major", "codes": "214, 281, 512, 713, 817, 832", "default": False},
            {"name": "Northeast Region", "codes": "201, 203, 212, 215, 401, 516", "default": False}
        ]
        
        presetList.setRowCount(len(presets))
        for i, preset in enumerate(presets):
            presetList.setItem(i, 0, QTableWidgetItem(preset["name"]))
            presetList.setItem(i, 1, QTableWidgetItem(preset["codes"]))
            
            defaultItem = QTableWidgetItem("✓" if preset["default"] else "")
            defaultItem.setTextAlignment(Qt.AlignCenter)
            if preset["default"]:
                defaultItem.setForeground(QColor("#27AE60"))
            presetList.setItem(i, 2, defaultItem)
        
        leftLayout.addWidget(presetList)
        
        # Right side - Area code browser by state
        rightWidget = QWidget()
        rightLayout = QVBoxLayout(rightWidget)
        
        stateLabel = QLabel("Browse by State")
        stateLabel.setFont(QFont("Arial", 12, QFont.Bold))
        
        # State filter
        stateFilterLayout = QHBoxLayout()
        
        stateCombo = QComboBox()
        states = ["All States", "Alabama", "Alaska", "Arizona", "Arkansas", "California", 
                 "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", 
                 "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", 
                 "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", 
                 "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", 
                 "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", 
                 "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", 
                 "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", 
                 "West Virginia", "Wisconsin", "Wyoming"]
        stateCombo.addItems(states)
        stateCombo.setCurrentText("Florida")  # Default to Florida
        
        regionCombo = QComboBox()
        regions = ["All Regions", "Northeast", "Southeast", "Midwest", "Southwest", "West"]
        regionCombo.addItems(regions)
        
        filterButton = QPushButton("Filter")
        filterButton.setProperty("class", "secondary")
        
        stateFilterLayout.addWidget(QLabel("State:"))
        stateFilterLayout.addWidget(stateCombo)
        stateFilterLayout.addWidget(QLabel("Region:"))
        stateFilterLayout.addWidget(regionCombo)
        stateFilterLayout.addWidget(filterButton)
        
        rightLayout.addWidget(stateLabel)
        rightLayout.addLayout(stateFilterLayout)
        rightLayout.addSpacing(10)
        
        # Area code table
        areaCodeTable = QTableWidget()
        areaCodeTable.setColumnCount(4)
        areaCodeTable.setHorizontalHeaderLabels(["", "Area Code", "Location", "Availability"])
        areaCodeTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        areaCodeTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        areaCodeTable.setColumnWidth(0, 30)
        
        # Sample area codes for Florida
        areaCodes = [
            {"code": "305", "location": "Miami, Miami Beach, Key West", "availability": "High"},
            {"code": "786", "location": "Miami, Miami-Dade County", "availability": "Medium"},
            {"code": "954", "location": "Fort Lauderdale, Broward County", "availability": "High"},
            {"code": "561", "location": "West Palm Beach, Boca Raton", "availability": "Medium"},
            {"code": "407", "location": "Orlando, Orange County", "availability": "High"},
            {"code": "321", "location": "Orlando, Space Coast", "availability": "Medium"},
            {"code": "352", "location": "Gainesville, Ocala", "availability": "Low"},
            {"code": "850", "location": "Tallahassee, Pensacola", "availability": "Medium"},
            {"code": "904", "location": "Jacksonville, St. Augustine", "availability": "High"},
            {"code": "727", "location": "St. Petersburg, Clearwater", "availability": "Medium"},
            {"code": "813", "location": "Tampa", "availability": "High"},
            {"code": "941", "location": "Sarasota, Fort Myers", "availability": "Low"}
        ]
        
        areaCodeTable.setRowCount(len(areaCodes))
        for i, code in enumerate(areaCodes):
            # Checkbox
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Unchecked)
            areaCodeTable.setItem(i, 0, checkbox)
            
            areaCodeTable.setItem(i, 1, QTableWidgetItem(code["code"]))
            areaCodeTable.setItem(i, 2, QTableWidgetItem(code["location"]))
            
            availItem = QTableWidgetItem(code["availability"])
            if code["availability"] == "High":
                availItem.setForeground(QColor("#27AE60"))
            elif code["availability"] == "Medium":
                availItem.setForeground(QColor("#F39C12"))
            elif code["availability"] == "Low":
                availItem.setForeground(QColor("#E74C3C"))
            areaCodeTable.setItem(i, 3, availItem)
        
        rightLayout.addWidget(areaCodeTable)
        
        # Area code actions
        actionsLayout = QHBoxLayout()
        
        selectAllButton = QPushButton("Select All")
        selectAllButton.setProperty("class", "secondary")
        
        addToPresetButton = QPushButton("Add to Preset")
        
        createPresetButton = QPushButton("Create New Preset from Selected")
        
        actionsLayout.addWidget(selectAllButton)
        actionsLayout.addWidget(addToPresetButton)
        actionsLayout.addWidget(createPresetButton)
        actionsLayout.addStretch()
        
        rightLayout.addLayout(actionsLayout)
        
        # Add widgets to splitter
        splitter.addWidget(leftWidget)
        splitter.addWidget(rightWidget)
        splitter.setSizes([400, 600])  # Set initial sizes
        
        layout.addWidget(splitter)
        
    def createNewPreset(self):
        """Create a new area code preset"""
        name, ok = QInputDialog.getText(
            self, "New Area Code Preset", "Enter a name for the new preset:"
        )
        
        if ok and name:
            QMessageBox.information(
                self, 
                "Create Preset", 
                f"Preset '{name}' would be created here.\nNot implemented in this demo."
            )


class AccountHealthTab(QWidget):
    """Tab for monitoring account health and status"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title and description
        titleLabel = QLabel("Account Health Monitor")
        titleLabel.setFont(QFont("Arial", 14, QFont.Bold))
        descLabel = QLabel("Monitor the health and status of your TextNow accounts. Identify issues and replace problematic accounts.")
        descLabel.setWordWrap(True)
        
        layout.addWidget(titleLabel)
        layout.addWidget(descLabel)
        layout.addSpacing(15)
        
        # Dashboard cards
        dashboardLayout = QHBoxLayout()
        
        # Total Accounts card
        totalCard = QGroupBox("Total Accounts")
        totalLayout = QVBoxLayout(totalCard)
        
        totalCountLabel = QLabel("125")
        totalCountLabel.setAlignment(Qt.AlignCenter)
        totalCountLabel.setFont(QFont("Arial", 24, QFont.Bold))
        
        totalLayout.addWidget(totalCountLabel)
        
        # Healthy Accounts card
        healthyCard = QGroupBox("Healthy")
        healthyLayout = QVBoxLayout(healthyCard)
        
        healthyCountLabel = QLabel("102")
        healthyCountLabel.setAlignment(Qt.AlignCenter)
        healthyCountLabel.setFont(QFont("Arial", 24, QFont.Bold))
        healthyCountLabel.setStyleSheet("color: #27AE60;")
        
        healthyPercentLabel = QLabel("81.6%")
        healthyPercentLabel.setAlignment(Qt.AlignCenter)
        
        healthyLayout.addWidget(healthyCountLabel)
        healthyLayout.addWidget(healthyPercentLabel)
        
        # Warning Accounts card
        warningCard = QGroupBox("Warning")
        warningLayout = QVBoxLayout(warningCard)
        
        warningCountLabel = QLabel("18")
        warningCountLabel.setAlignment(Qt.AlignCenter)
        warningCountLabel.setFont(QFont("Arial", 24, QFont.Bold))
        warningCountLabel.setStyleSheet("color: #F39C12;")
        
        warningPercentLabel = QLabel("14.4%")
        warningPercentLabel.setAlignment(Qt.AlignCenter)
        
        warningLayout.addWidget(warningCountLabel)
        warningLayout.addWidget(warningPercentLabel)
        
        # Blocked Accounts card
        blockedCard = QGroupBox("Blocked")
        blockedLayout = QVBoxLayout(blockedCard)
        
        blockedCountLabel = QLabel("5")
        blockedCountLabel.setAlignment(Qt.AlignCenter)
        blockedCountLabel.setFont(QFont("Arial", 24, QFont.Bold))
        blockedCountLabel.setStyleSheet("color: #E74C3C;")
        
        blockedPercentLabel = QLabel("4.0%")
        blockedPercentLabel.setAlignment(Qt.AlignCenter)
        
        blockedLayout.addWidget(blockedCountLabel)
        blockedLayout.addWidget(blockedPercentLabel)
        
        dashboardLayout.addWidget(totalCard)
        dashboardLayout.addWidget(healthyCard)
        dashboardLayout.addWidget(warningCard)
        dashboardLayout.addWidget(blockedCard)
        
        layout.addLayout(dashboardLayout)
        layout.addSpacing(15)
        
        # Tab widget for different account lists
        accountTabs = QTabWidget()
        
        # Flagged Accounts tab
        flaggedTab = QWidget()
        flaggedLayout = QVBoxLayout(flaggedTab)
        
        flaggedTable = QTableWidget()
        flaggedTable.setColumnCount(7)
        flaggedTable.setHorizontalHeaderLabels([
            "Phone Number", "Account Name", "Created", "Last Check", 
            "Health Score", "Issues", "Actions"
        ])
        flaggedTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Sample flagged accounts
        flaggedAccounts = [
            {
                "phone": "(786) 987-6543", 
                "name": "Mary Johnson", 
                "created": "2025-03-20", 
                "last_check": "2025-04-25 09:15", 
                "score": 65, 
                "issues": "Slow message delivery"
            },
            {
                "phone": "(561) 789-4561", 
                "name": "David Brown", 
                "created": "2025-03-10", 
                "last_check": "2025-04-25 10:22", 
                "score": 58, 
                "issues": "Failed to send images"
            },
            {
                "phone": "(954) 345-6789", 
                "name": "Jennifer Wilson", 
                "created": "2025-02-15", 
                "last_check": "2025-04-25 08:45", 
                "score": 62, 
                "issues": "Login failures (2)"
            }
        ]
        
        flaggedTable.setRowCount(len(flaggedAccounts))
        for i, account in enumerate(flaggedAccounts):
            flaggedTable.setItem(i, 0, QTableWidgetItem(account["phone"]))
            flaggedTable.setItem(i, 1, QTableWidgetItem(account["name"]))
            flaggedTable.setItem(i, 2, QTableWidgetItem(account["created"]))
            flaggedTable.setItem(i, 3, QTableWidgetItem(account["last_check"]))
            
            scoreItem = QTableWidgetItem(str(account["score"]))
            scoreItem.setForeground(QColor("#F39C12"))  # Warning color
            flaggedTable.setItem(i, 4, scoreItem)
            
            flaggedTable.setItem(i, 5, QTableWidgetItem(account["issues"]))
            
            # Actions
            actionsWidget = QWidget()
            actionsLayout = QHBoxLayout(actionsWidget)
            actionsLayout.setContentsMargins(2, 2, 2, 2)
            
            checkButton = QPushButton("Check Now")
            checkButton.setFixedSize(80, 25)
            checkButton.setProperty("class", "secondary")
            
            replaceButton = QPushButton("Replace")
            replaceButton.setFixedSize(70, 25)
            replaceButton.setProperty("class", "danger")
            
            actionsLayout.addWidget(checkButton)
            actionsLayout.addWidget(replaceButton)
            actionsLayout.addStretch()
            
            flaggedTable.setCellWidget(i, 6, actionsWidget)
        
        flaggedLayout.addWidget(flaggedTable)
        
        # Blocked Accounts tab
        blockedTab = QWidget()
        blockedLayout = QVBoxLayout(blockedTab)
        
        blockedTable = QTableWidget()
        blockedTable.setColumnCount(7)
        blockedTable.setHorizontalHeaderLabels([
            "Phone Number", "Account Name", "Created", "Blocked Date", 
            "Health Score", "Reason", "Actions"
        ])
        blockedTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Sample blocked accounts
        blockedAccounts = [
            {
                "phone": "(305) 234-5678", 
                "name": "Robert Taylor", 
                "created": "2025-02-05", 
                "blocked_date": "2025-04-24", 
                "score": 20, 
                "reason": "Multiple login failures"
            },
            {
                "phone": "(786) 345-6789", 
                "name": "Sarah Miller", 
                "created": "2025-03-05", 
                "blocked_date": "2025-04-23", 
                "score": 15, 
                "reason": "Account suspended by TextNow"
            }
        ]
        
        blockedTable.setRowCount(len(blockedAccounts))
        for i, account in enumerate(blockedAccounts):
            blockedTable.setItem(i, 0, QTableWidgetItem(account["phone"]))
            blockedTable.setItem(i, 1, QTableWidgetItem(account["name"]))
            blockedTable.setItem(i, 2, QTableWidgetItem(account["created"]))
            blockedTable.setItem(i, 3, QTableWidgetItem(account["blocked_date"]))
            
            scoreItem = QTableWidgetItem(str(account["score"]))
            scoreItem.setForeground(QColor("#E74C3C"))  # Danger color
            blockedTable.setItem(i, 4, scoreItem)
            
            blockedTable.setItem(i, 5, QTableWidgetItem(account["reason"]))
            
            # Actions
            actionsWidget = QWidget()
            actionsLayout = QHBoxLayout(actionsWidget)
            actionsLayout.setContentsMargins(2, 2, 2, 2)
            
            replaceButton = QPushButton("Replace")
            replaceButton.setFixedSize(70, 25)
            replaceButton.setProperty("class", "danger")
            
            deleteButton = QPushButton("Delete")
            deleteButton.setFixedSize(70, 25)
            deleteButton.setProperty("class", "danger")
            
            actionsLayout.addWidget(replaceButton)
            actionsLayout.addWidget(deleteButton)
            actionsLayout.addStretch()
            
            blockedTable.setCellWidget(i, 6, actionsWidget)
        
        blockedLayout.addWidget(blockedTable)
        
        # Recent Health Checks tab
        checksTab = QWidget()
        checksLayout = QVBoxLayout(checksTab)
        
        checksTable = QTableWidget()
        checksTable.setColumnCount(6)
        checksTable.setHorizontalHeaderLabels([
            "Phone Number", "Check Time", "Check Type", "Result", "Score Change", "Details"
        ])
        checksTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Sample health checks
        healthChecks = [
            {
                "phone": "(954) 123-4567", 
                "time": "2025-04-25 10:30", 
                "type": "Login Test", 
                "result": "Success", 
                "change": "+2", 
                "details": "Login successful in 1.5s"
            },
            {
                "phone": "(786) 987-6543", 
                "time": "2025-04-25 10:15", 
                "type": "Message Test", 
                "result": "Warning", 
                "change": "-5", 
                "details": "Message delivery delayed (12s)"
            },
            {
                "phone": "(305) 456-7890", 
                "time": "2025-04-25 10:00", 
                "type": "Media Test", 
                "result": "Success", 
                "change": "+1", 
                "details": "Image upload and send successful"
            },
            {
                "phone": "(561) 789-4561", 
                "time": "2025-04-25 09:45", 
                "type": "Message Test", 
                "result": "Failure", 
                "change": "-10", 
                "details": "Message failed to send"
            },
            {
                "phone": "(954) 345-6789", 
                "time": "2025-04-25 09:30", 
                "type": "Login Test", 
                "result": "Warning", 
                "change": "-3", 
                "details": "Login delayed (5.2s)"
            }
        ]
        
        checksTable.setRowCount(len(healthChecks))
        for i, check in enumerate(healthChecks):
            checksTable.setItem(i, 0, QTableWidgetItem(check["phone"]))
            checksTable.setItem(i, 1, QTableWidgetItem(check["time"]))
            checksTable.setItem(i, 2, QTableWidgetItem(check["type"]))
            
            resultItem = QTableWidgetItem(check["result"])
            if check["result"] == "Success":
                resultItem.setForeground(QColor("#27AE60"))
            elif check["result"] == "Warning":
                resultItem.setForeground(QColor("#F39C12"))
            elif check["result"] == "Failure":
                resultItem.setForeground(QColor("#E74C3C"))
            checksTable.setItem(i, 3, resultItem)
            
            changeItem = QTableWidgetItem(check["change"])
            if check["change"].startswith("+"):
                changeItem.setForeground(QColor("#27AE60"))
            elif check["change"].startswith("-"):
                changeItem.setForeground(QColor("#E74C3C"))
            checksTable.setItem(i, 4, changeItem)
            
            checksTable.setItem(i, 5, QTableWidgetItem(check["details"]))
        
        checksLayout.addWidget(checksTable)
        
        # Add tabs
        accountTabs.addTab(flaggedTab, "Flagged Accounts (3)")
        accountTabs.addTab(blockedTab, "Blocked Accounts (2)")
        accountTabs.addTab(checksTab, "Recent Health Checks")
        
        layout.addWidget(accountTabs)
        
        # Action buttons
        buttonLayout = QHBoxLayout()
        
        checkAllButton = QPushButton("Check All Accounts")
        checkAllButton.clicked.connect(self.checkAllAccounts)
        
        replaceAllButton = QPushButton("Replace All Blocked")
        replaceAllButton.setProperty("class", "danger")
        
        exportReportButton = QPushButton("Export Health Report")
        exportReportButton.setProperty("class", "secondary")
        
        buttonLayout.addWidget(checkAllButton)
        buttonLayout.addWidget(replaceAllButton)
        buttonLayout.addWidget(exportReportButton)
        buttonLayout.addStretch()
        
        layout.addLayout(buttonLayout)
        
    def checkAllAccounts(self):
        """Check health of all accounts"""
        QMessageBox.information(
            self,
            "Check All Accounts",
            "This would scan all accounts and perform health checks.\nNot implemented in this demo."
        )


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Set up main window
        self.setWindowTitle("TextNow Max Creator")
        self.setWindowIcon(QIcon("assets/progress_logo.png"))
        self.setMinimumSize(1200, 800)
        
        # Create central widget and layout
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)
        
        # Create header with logo and device status
        headerLayout = QHBoxLayout()
        
        logoLabel = QLabel()
        # If logo exists, load it; otherwise use text
        logo_path = "assets/progress_logo.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logoLabel.setPixmap(pixmap.scaled(180, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logoLabel.setText("TextNow Max Creator")
            logoLabel.setFont(QFont("Arial", 16, QFont.Bold))
            logoLabel.setStyleSheet("color: #FF6600;")
        
        headerLayout.addWidget(logoLabel)
        headerLayout.addStretch()
        
        # Add device status widget
        self.deviceStatus = DeviceStatusWidget()
        headerLayout.addWidget(self.deviceStatus)
        
        mainLayout.addLayout(headerLayout)
        
        # Create tab widget
        self.tabWidget = QTabWidget()
        
        # Add tabs
        self.tabWidget.addTab(AccountCreatorTab(), "Account Creator")
        self.tabWidget.addTab(AccountDashboardTab(), "Account Dashboard")
        self.tabWidget.addTab(CampaignTab(), "Campaigns")
        self.tabWidget.addTab(VoicemailTab(), "Voicemail Manager")
        self.tabWidget.addTab(ImageManagerTab(), "Media Manager")
        self.tabWidget.addTab(AreaCodeManagerTab(), "Area Codes")
        self.tabWidget.addTab(AccountHealthTab(), "Account Health")
        
        mainLayout.addWidget(self.tabWidget)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Add status message
        self.statusBar.showMessage("TextNow Max Creator v1.2.0 - Ready")
        
        # Add application menu
        self.setupMenu()
        
        # Set stylesheet
        self.setStyleSheet(STYLESHEET)
        
    def setupMenu(self):
        """Set up application menu"""
        menuBar = self.menuBar()
        
        # File menu
        fileMenu = menuBar.addMenu("File")
        
        importAction = QAction("Import Data...", self)
        exportAction = QAction("Export Data...", self)
        settingsAction = QAction("Settings", self)
        exitAction = QAction("Exit", self)
        exitAction.triggered.connect(self.close)
        
        fileMenu.addAction(importAction)
        fileMenu.addAction(exportAction)
        fileMenu.addSeparator()
        fileMenu.addAction(settingsAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)
        
        # Accounts menu
        accountsMenu = menuBar.addMenu("Accounts")
        
        createAccountAction = QAction("Create New Account", self)
        importAccountsAction = QAction("Import Accounts", self)
        checkHealthAction = QAction("Check Account Health", self)
        
        accountsMenu.addAction(createAccountAction)
        accountsMenu.addAction(importAccountsAction)
        accountsMenu.addSeparator()
        accountsMenu.addAction(checkHealthAction)
        
        # Campaigns menu
        campaignsMenu = menuBar.addMenu("Campaigns")
        
        newCampaignAction = QAction("New Campaign", self)
        schedulerAction = QAction("Campaign Scheduler", self)
        templatesAction = QAction("Message Templates", self)
        
        campaignsMenu.addAction(newCampaignAction)
        campaignsMenu.addAction(schedulerAction)
        campaignsMenu.addSeparator()
        campaignsMenu.addAction(templatesAction)
        
        # Tools menu
        toolsMenu = menuBar.addMenu("Tools")
        
        deviceManagerAction = QAction("Device Manager", self)
        adbSetupAction = QAction("ADB Setup", self)
        backupAction = QAction("Backup Database", self)
        restoreAction = QAction("Restore Database", self)
        
        toolsMenu.addAction(deviceManagerAction)
        toolsMenu.addAction(adbSetupAction)
        toolsMenu.addSeparator()
        toolsMenu.addAction(backupAction)
        toolsMenu.addAction(restoreAction)
        
        # Help menu
        helpMenu = menuBar.addMenu("Help")
        
        docsAction = QAction("Documentation", self)
        updateAction = QAction("Check for Updates", self)
        aboutAction = QAction("About TextNow Max Creator", self)
        aboutAction.triggered.connect(self.showAboutDialog)
        
        helpMenu.addAction(docsAction)
        helpMenu.addAction(updateAction)
        helpMenu.addSeparator()
        helpMenu.addAction(aboutAction)
        
    def showAboutDialog(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About TextNow Max Creator",
            "TextNow Max Creator v1.2.0\n\n"
            "A comprehensive tool for creating and managing TextNow accounts,\n"
            "sending messages, and automating campaigns.\n\n"
            "© 2025 TextNow Max"
        )


def main():
    """Run the application"""
    # Force the platform to use VNC-compatible "vnc" platform plugin
    os.environ["QT_QPA_PLATFORM"] = "vnc"

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    print("======================================================")
    print("TextNow Max Creator - Desktop Application")
    print("Started in VNC mode. You can view it through the VNC viewer.")
    print("======================================================")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()