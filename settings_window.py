# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings_window.ui'
##
## Created by: Qt User Interface Compiler version 6.8.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
    QSizePolicy, QVBoxLayout, QWidget, QSlider)

class Ui_SettingsWindow(object):
    def setupUi(self, SettingsWindow):
        if not SettingsWindow.objectName():
            SettingsWindow.setObjectName(u"SettingsWindow")
        SettingsWindow.resize(254, 242)
        icon = QIcon()
        icon.addFile(u"../favicon.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        SettingsWindow.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(SettingsWindow)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(SettingsWindow)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.language = QComboBox(SettingsWindow)
        self.language.addItem("")
        self.language.addItem("")
        self.language.addItem("")
        self.language.addItem("")
        self.language.setObjectName(u"language")

        self.horizontalLayout.addWidget(self.language)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.labelAppTheme = QLabel(SettingsWindow)
        self.labelAppTheme.setObjectName(u"labelAppTheme")
        self.labelAppTheme.setText("App theme")
        self.horizontalLayout_2.addWidget(self.labelAppTheme)

        self.appTheme = QComboBox(SettingsWindow)
        self.appTheme.setObjectName(u"appTheme")
        self.appTheme.addItem("System")
        self.appTheme.addItem("Light")
        self.appTheme.addItem("Dark")
        try:
            import main
            self.appTheme.setCurrentText(main.config.get('theme', 'System'))
        except Exception:
            self.appTheme.setCurrentText("System")
        self.horizontalLayout_2.addWidget(self.appTheme)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_style = QLabel(SettingsWindow)
        self.label_style.setObjectName(u"label_style")

        self.horizontalLayout_3.addWidget(self.label_style)

        self.comboBox_style = QComboBox(SettingsWindow)
        self.comboBox_style.setObjectName(u"comboBox_style")

        self.horizontalLayout_3.addWidget(self.comboBox_style)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.openLastFile = QCheckBox(SettingsWindow)
        self.openLastFile.setObjectName(u"openLastFile")

        self.verticalLayout.addWidget(self.openLastFile)

        self.posLastFile = QCheckBox(SettingsWindow)
        self.posLastFile.setObjectName(u"posLastFile")

        self.verticalLayout.addWidget(self.posLastFile)

        self.volumePlus = QCheckBox(SettingsWindow)
        self.volumePlus.setObjectName(u"volumePlus")

        self.verticalLayout.addWidget(self.volumePlus)

        self.svp = QCheckBox(SettingsWindow)
        self.svp.setObjectName(u"svp")

        self.verticalLayout.addWidget(self.svp)

        # Add AniSkip settings group
        self.aniskip_group = QWidget(SettingsWindow)
        self.aniskip_group.setObjectName(u"aniskip_group")
        self.aniskip_layout = QVBoxLayout(self.aniskip_group)
        self.aniskip_layout.setObjectName(u"aniskip_layout")
        
        self.aniskip_label = QLabel(SettingsWindow)
        self.aniskip_label.setObjectName(u"aniskip_label")
        self.aniskip_label.setText("AniSkip Settings")
        self.aniskip_layout.addWidget(self.aniskip_label)
        
        self.auto_skip_op = QCheckBox(SettingsWindow)
        self.auto_skip_op.setObjectName(u"auto_skip_op")
        self.auto_skip_op.setText("Auto-skip openings")
        self.aniskip_layout.addWidget(self.auto_skip_op)
        
        self.auto_skip_ed = QCheckBox(SettingsWindow)
        self.auto_skip_ed.setObjectName(u"auto_skip_ed")
        self.auto_skip_ed.setText("Auto-skip endings")
        self.aniskip_layout.addWidget(self.auto_skip_ed)
        
        self.auto_skip_recap = QCheckBox(SettingsWindow)
        self.auto_skip_recap.setObjectName(u"auto_skip_recap")
        self.auto_skip_recap.setText("Auto-skip recaps")
        self.aniskip_layout.addWidget(self.auto_skip_recap)
        
        self.auto_skip_preview = QCheckBox(SettingsWindow)
        self.auto_skip_preview.setObjectName(u"auto_skip_preview")
        self.auto_skip_preview.setText("Auto-skip previews")
        self.aniskip_layout.addWidget(self.auto_skip_preview)
        
        # Add skip button size control
        self.skip_button_size_label = QLabel(SettingsWindow)
        self.skip_button_size_label.setObjectName(u"skip_button_size_label")
        self.skip_button_size_label.setText("Skip button size")
        self.aniskip_layout.addWidget(self.skip_button_size_label)
        
        self.skip_button_size = QSlider(SettingsWindow)
        self.skip_button_size.setObjectName(u"skip_button_size")
        self.skip_button_size.setOrientation(Qt.Orientation.Horizontal)
        self.skip_button_size.setMinimum(50)  # 50% of default size
        self.skip_button_size.setMaximum(200)  # 200% of default size
        self.skip_button_size.setValue(100)  # Default to 100%
        self.skip_button_size.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.skip_button_size.setTickInterval(25)
        self.aniskip_layout.addWidget(self.skip_button_size)
        
        self.verticalLayout.addWidget(self.aniskip_group)

        self.buttonBox = QDialogButtonBox(SettingsWindow)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(SettingsWindow)
        self.buttonBox.accepted.connect(SettingsWindow.accept)
        self.buttonBox.rejected.connect(SettingsWindow.reject)

        QMetaObject.connectSlotsByName(SettingsWindow)

        self.labelAppTheme.setVisible(True)
        self.appTheme.setVisible(True)
        self.appTheme.clear()
        self.appTheme.addItem("System")
        self.appTheme.addItem("Light")
        self.appTheme.addItem("Dark")
        try:
            import main
            self.appTheme.setCurrentText(main.config.get('theme', 'System'))
        except Exception:
            self.appTheme.setCurrentText("System")

    def retranslateUi(self, SettingsWindow):
        SettingsWindow.setWindowTitle(QCoreApplication.translate("SettingsWindow", u"Settings", None))
        self.label.setText(QCoreApplication.translate("SettingsWindow", u"Language selection", None))
        self.language.setItemText(0, QCoreApplication.translate("SettingsWindow", u"Auto", None))
        self.language.setItemText(1, QCoreApplication.translate("SettingsWindow", u"English", None))
        self.language.setItemText(2, QCoreApplication.translate("SettingsWindow", u"\u0420\u0443\u0441\u0441\u043a\u0438\u0439", None))
        self.language.setItemText(3, QCoreApplication.translate("SettingsWindow", u"Japanese", None))
        self.label_style.setText(QCoreApplication.translate("SettingsWindow", u"Style", None))
        self.openLastFile.setText(QCoreApplication.translate("SettingsWindow", u"On startup open the last opened file", None))
        self.posLastFile.setText(QCoreApplication.translate("SettingsWindow", u"Set the position of the last opened file", None))
        self.volumePlus.setText(QCoreApplication.translate("SettingsWindow", u"Increase maxumum volume up to 150%", None))
        self.svp.setText(QCoreApplication.translate("SettingsWindow", u"Activate SVP", None))

    def ok(self):
        # ... existing code ...
        config.set('onOpenLastFile', self.openLastFile.isChecked())
        config.set('onPosLastFile', self.posLastFile.isChecked())
        config.set('SVP', self.svp.isChecked())
        config.set('volumePlus', self.volumePlus.isChecked())
        config.set('style', self.comboBox_style.currentText())
        config.set('theme', self.appTheme.currentText())
        # ... existing code ...
        app.setStyle(self.comboBox_style.currentText())
        # ... existing code ...
        apply_theme()

