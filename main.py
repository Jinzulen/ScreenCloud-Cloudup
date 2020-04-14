import ScreenCloud

from PythonQt.QtUiTools import QUiLoader
from PythonQt.QtCore import QFile, QSettings
from PythonQt.QtGui import QFont, QWidget, QDialog, QMessageBox

class Cloudup:
    def __init__(self):
        # Load the settings here to provide global access and avoid redundancy.
        self.loadSettings()

    def updateUi(self):
        if self.Key:
            # Set the logged in user to bold.
            Font = QFont()
            Font.setBold(True)
            self.settingsDialog.group_account.widget_user.label_username.setFont(Font)
            
            # Show the username display and hide the login button.
            self.settingsDialog.group_account.widget_user.show()
            self.settingsDialog.group_account.widget_loggedIn.show()
            self.settingsDialog.group_account.button_authenticate.hide()

            # Hide the username and password input fields.
            self.settingsDialog.group_account.label_username.hide()
            self.settingsDialog.group_account.input_username.hide()

            self.settingsDialog.group_account.label_password.hide()
            self.settingsDialog.group_account.input_password.hide()

            # Inject the username into the display.
            self.settingsDialog.group_account.widget_user.label_username.setText(self.Username)
        else:
            # Hide the username display and show the login button.
            self.settingsDialog.group_account.widget_user.hide()
            self.settingsDialog.group_account.widget_loggedIn.hide()
            self.settingsDialog.group_account.button_authenticate.show()
        
        # Inject the default image title into the name field.
        self.settingsDialog.group_upload.input_name.setText(self.Format)

        self.settingsDialog.adjustSize()

    def showSettingsUI(self, parentWidget):
        self.settingsDialog = QUiLoader().load(QFile(workingDir + "/settings.ui"), parentWidget)

        # Inject the image title format
        self.settingsDialog.group_upload.input_name.connect("textChanged(QString)", self.nameFormatEdited)
        self.settingsDialog.connect("accepted()", self.saveSettings)

        # Inject default values
        self.settingsDialog.group_upload.input_name.text      = self.Format
        self.settingsDialog.group_account.input_username.text = self.Username
        self.settingsDialog.group_account.input_password.text = self.Password

        self.settingsDialog.group_clipboard.radio_direct.setChecked(not self.copyDirect)
        self.settingsDialog.group_clipboard.radio_nothing.setChecked(not self.copyNothing)

        self.updateUi()
        self.settingsDialog.open()

    def loadSettings(self):
        Settings = QSettings()

        Settings.beginGroup("uploaders")
        Settings.beginGroup("cloudup")

        # Account
        self.Key      = Settings.value("token", "")
        self.Username = Settings.value("username", "")
        self.Password = Settings.value("password", "")

        # Image title
        self.Format = Settings.value("name-format", "Screenshot at %H-%M-%S")

        # Clipboard
        self.copyDirect  = Settings.value("copy-direct", "true") in ["true", True]
        self.copyNothing = Settings.value("copy-nothing", "true") in ["true", True]

        Settings.endGroup()
        Settings.endGroup()

    def saveSettings(self):
        Settings = QSettings()
        
        Settings.beginGroup("uploaders")
        Settings.beginGroup("cloudup")

        # Account
        Settings.setValue("username", self.settingsDialog.group_account.input_username.text)
        Settings.setValue("password", self.settingsDialog.group_account.input_password.text)

        # Image title
        Settings.setValue("name-format", self.settingsDialog.group_upload.input_name.text)

        # Clipboard
        Settings.setValue("copy-direct", not self.settingsDialog.group_clipboard.radio_direct.checked)
        Settings.setValue("copy-nothing", not self.settingsDialog.group_clipboard.radio_nothing.checked)

        Settings.endGroup()
        Settings.endGroup()

    def getFilename(self):
        return ScreenCloud.formatFilename(self.Format)

    def nameFormatEdited(self, nameFormat):
        self.settingsDialog.group_upload.label_example.setText(ScreenCloud.formatFilename(nameFormat))

    def isConfigured(self):
        return not(not self.Username or not self.Password)