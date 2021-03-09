import os, time, json, requests, ScreenCloud

from PythonQt.QtUiTools import QUiLoader
from PythonQt.QtCore import QFile, QSettings, QStandardPaths
from PythonQt.QtGui import QFont, QWidget, QDialog, QDesktopServices, QMessageBox

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

            self.settingsDialog.group_account.label_username.show()
            self.settingsDialog.group_account.input_username.show()

            self.settingsDialog.group_account.label_password.show()
            self.settingsDialog.group_account.input_password.show()

            # Hide the upload and clipboard configuration
            self.settingsDialog.group_upload.hide()
            self.settingsDialog.group_clipboard.hide()
        
        # Inject the default image title into the name field.
        self.settingsDialog.group_upload.input_name.setText(self.Format)

        self.settingsDialog.adjustSize()

    def getFilename(self):
        return ScreenCloud.formatFilename(self.Format)

    def nameFormatEdited(self, nameFormat):
        self.settingsDialog.group_upload.label_example.setText(ScreenCloud.formatFilename(nameFormat))

    def loadSettings(self):
        Settings = QSettings()

        Settings.beginGroup("uploaders")
        Settings.beginGroup("cloudup")

        # Account
        self.Key      = Settings.value("token", "")
        self.Username = Settings.value("username", "")
        self.Password = Settings.value("password", "")

        # Image title and stream
        self.Stream = Settings.value("stream", "")
        self.Format = Settings.value("name-format", "Screenshot at %H-%M-%S")

        # Clipboard
        self.copyDirect  = Settings.value("copy-direct", "true") in ["true", True]
        self.copyCloudup = Settings.value("copy-cloudup", "true") in ["true", True]
        self.copyNothing = Settings.value("copy-nothing", "true") in ["true", True]

        Settings.endGroup()
        Settings.endGroup()

    def showSettingsUI(self, parentWidget):
        self.settingsDialog = QUiLoader().load(QFile(workingDir + "/settings.ui"), parentWidget)

        # Inject the image title format.
        self.settingsDialog.group_upload.input_name.connect("textChanged(QString)", self.nameFormatEdited)
        self.settingsDialog.connect("accepted()", self.saveSettings)

        # Inject the upload stream
        self.settingsDialog.group_upload.input_stream.text = self.Stream

        # Inject default values.
        self.loadSettings()

        self.settingsDialog.group_upload.input_name.text      = self.Format
        self.settingsDialog.group_account.input_username.text = self.Username
        self.settingsDialog.group_account.input_password.text = self.Password

        self.settingsDialog.group_clipboard.radio_direct.setChecked(not self.copyDirect)
        self.settingsDialog.group_clipboard.radio_nothing.setChecked(not self.copyNothing)

        # Wait for login/out button activation.
        self.settingsDialog.group_account.widget_loggedIn.connect("clicked()", self.Logout)
        self.settingsDialog.group_account.button_authenticate.connect("clicked()", self.Login)

        self.updateUi()
        self.settingsDialog.open()

    def saveSettings(self):
        Settings = QSettings()

        Settings.beginGroup("uploaders")
        Settings.beginGroup("cloudup")

        # Account
        Settings.setValue("token", self.Key)
        Settings.setValue("username", self.settingsDialog.group_account.input_username.text)
        Settings.setValue("password", self.settingsDialog.group_account.input_password.text)

        # Image title and stream
        Settings.setValue("name-format", self.settingsDialog.group_upload.input_name.text)
        Settings.setValue("stream", self.settingsDialog.group_upload.input_stream.text)

        # Clipboard
        Settings.setValue("copy-cloudup", not self.settingsDialog.group_clipboard.radio_cloudup.checked)
        Settings.setValue("copy-direct", not self.settingsDialog.group_clipboard.radio_direct.checked)
        Settings.setValue("copy-nothing", not self.settingsDialog.group_clipboard.radio_nothing.checked)

        Settings.endGroup()
        Settings.endGroup()

        self.updateUi()
        self.settingsDialog.open()

    # Login.
    def Login(self):
        self.saveSettings()

        # Grab credentials from the currently available fields, not saved settings.
        if self.settingsDialog.group_account:
            Username = self.settingsDialog.group_account.input_username.text
            Password = self.settingsDialog.group_account.input_password.text

            # Headers and payload.
            Headers = {"User-Agent": "ScreenCloud-Cloudup"}

            Payload = {
                "client_id": "ah5Oa7F3hT8",
                "grant_type": "password",
                "username": Username,
                "password": Password
            }

            try:
                r = requests.post("https://cloudup.com/oauth/access_token", data = Payload, headers = Headers)
                j = json.loads(r.text)

                if r.status_code == 400:
                    QMessageBox.critical(self.settingsDialog, "Cloudup Login Error", j["error_description"])

                self.Key = j["access_token"]

                self.saveSettings()
                self.loadSettings()
                self.updateUi()

                QMessageBox.information(self.settingsDialog, "Success!", "You have successfully signed into your Cloudup account.")
            except Exception as e:
                QMessageBox.critical(self.settingsDialog, "Cloudup Login Error", "Error occurred during login. " + e.message)

    # Logout.
    def Logout(self):
        Settings = QSettings()

        Settings.beginGroup("uploaders")
        Settings.beginGroup("cloudup")

        Settings.remove("token")

        Settings.endGroup()
        Settings.endGroup()

        self.loadSettings()
        self.updateUi()

        QMessageBox.information(self.settingsDialog, "Success!", "You have successfully signed out of your Cloudup account.")

    # UPLOAD!
    def upload(self, screenshot, name):
        Headers = {"User-Agent": "ScreenCloud-Cloudup"}

        try:
            FilePath = QStandardPaths.writableLocation(QStandardPaths.TempLocation) + "/" + ScreenCloud.formatFilename(str(time.time()))
            screenshot.save(QFile(FilePath), ScreenCloud.getScreenshotFormat())

            # Has a stream been specified or should we create on?
            if self.Stream:
                Stream = self.Stream
            else:
                # Create stream
                s = requests.post("https://api.cloudup.com/1/streams?access_token=" + self.Key, data = {"title": name}, headers = Headers)
                c = s.json()

                Stream = c["id"]

            # Create item inside the stream
            i = requests.post("https://api.cloudup.com/1/items?access_token=" + self.Key, data = {"filename": FilePath, "stream_id": Stream}, headers = Headers)
            j = json.loads(i.text)

            # Upload
            requests.post(j["s3_url"], files = {"file": open(FilePath, "rb")}, data = {
                "key": j["s3_key"],
                "acl": "public-read",
                "policy": j["s3_policy"],
                "signature": j["s3_signature"],
                "AWSAccessKeyId": j["s3_access_key"],

                "Content-Type": "image/png",
                "Content-Length": os.path.getsize(FilePath)
            }, headers = Headers)

            # Completion signal
            requests.patch("https://api.cloudup.com/1/items/" + j["id"] + "?access_token=" + self.Key, json.dumps({u"complete": True}), headers = {
                "Content-Type": "application/json",
                "User-Agent": "ScreenCloud-Cloudup"
            })

            # Does the user want the Cloudup item link?
            if self.copyCloudup:
                ScreenCloud.setUrl(j["url"])

            # Does the user want the direct link?
            if self.copyDirect:
                ScreenCloud.setUrl(j["direct_url"])
        except requests.exceptions.RequestException as E:
            ScreenCloud.setError("Failued to upload to Cloudup: " + E.message)
            return False

        return True

    def isConfigured(self):
        return not(not self.Key)