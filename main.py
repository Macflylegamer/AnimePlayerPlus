import os
import sys
import platform
import logging
from typing import Optional
import time

from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QIcon, QGuiApplication, QAction, QPixmap, QCursor, QPalette, QColor
from PySide6.QtWidgets import QMainWindow, QApplication, QDialog, QMenu, QFileDialog, QWidget, QStyleFactory

import about_window
import android_config_window
import anime4k
import icons
import launch_parameters_window
import localization
import main_window
import open_folder_window
import open_url_window
import reference_window
import screenshot_window
import settings_window
from config import ConfigManager
from mpv import MPV
import aniskip
from aniskip import SkipType, SkipSegment

name_program = 'Anime Player'
version = '2.1.2'
video_formats = ('mp4', 'mkv', 'webm', 'avi', 'mov', 'wmv', '3gp', 'ts', 'mpeg')
audio_formats = ('m4a', 'mp3', 'flac', 'ogg', 'aac', 'opus', 'wav')
subtitles_formats = ('ass', 'idx', 'srt', 'ssa', 'sub', 'ttml', 'vtt')
formats = video_formats + audio_formats

config = ConfigManager('config.json')
localization.set_locale(config.get('language'))
loc = localization.strings

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AndroidConfigWindow(QDialog):
    def __init__(self):
        super(AndroidConfigWindow, self).__init__()
        self.ui = android_config_window.Ui_AndroidConfigWindow()
        self.ui.setupUi(self)

        self.setWindowIcon(QIcon(f'{os.path.dirname(__file__) + os.sep}favicon.ico'))

        self.setWindowTitle(loc['Create config for Android'])
        self.ui.label.setText(loc['You can use this config to use the Anime4K algorithm in the mpv video player on android'])
        self.ui.label_2.setText(loc['Enter the path to the shaders'])
        self.ui.label_3.setText(loc['Select the algorithm configuration'])
        self.ui.selected.setText(loc['Selected'])
        self.ui.all.setText(loc['All'])

        self.ui.selected.clicked.connect(self.selected)
        self.ui.all.clicked.connect(self.all)

        self.modes = []
        for quality in anime4k.qualities:
            self.modes += [f'{loc["Mode"]} {mode} ({quality})' for mode in anime4k.modes]

        self.ui.comboBox.addItems(self.modes)

    def selected(self):
        quality = self.ui.comboBox.currentText().replace(')', '').split('(')[1]
        mode = self.ui.comboBox.currentText().split(' ')[1]
        self.ui.plainTextEdit.setPlainText(f'# {self.ui.comboBox.currentText()}\n' + anime4k.android_config(anime4k.create_preset(quality, mode), self.ui.lineEdit.text()))

    def all(self):
        mods = []
        for mod in self.modes:
            quality = mod.replace(')', '').split('(')[1]
            mode = mod.split(' ')[1]
            mods.append(f'# {mod}\n' + '# ' + anime4k.android_config(anime4k.create_preset(quality, mode), self.ui.lineEdit.text()))
        self.ui.plainTextEdit.setPlainText('\n\n'.join(mods))


class LaunchParametersWindow(QDialog):
    def __init__(self):
        super(LaunchParametersWindow, self).__init__()
        self.ui = launch_parameters_window.Ui_LaunchParemetersWindow()
        self.ui.setupUi(self)

        self.setWindowIcon(QIcon(f'{os.path.dirname(__file__) + os.sep}favicon.ico'))

        self.setWindowTitle(loc['Launch parameters'])
        self.ui.label.setText(loc['Manual launch parameters'])
        self.ui.buttonBox.buttons()[0].setText(loc['Save'])
        self.ui.buttonBox.buttons()[1].setText(loc['Cancel'])
        self.ui.buttonBox.buttons()[2].setText(loc['Apply'])

        self.ui.plainTextEdit.setPlainText(config.get('launchParameters', ''))

        self.ui.buttonBox.buttons()[0].clicked.connect(self.save)
        self.ui.buttonBox.buttons()[2].clicked.connect(self.apply)

    def save(self):
        config.set('launchParameters', self.ui.plainTextEdit.toPlainText())

    def apply(self):
        try:
            exec(self.ui.plainTextEdit.toPlainText())
            config.set('launchParameters', self.ui.plainTextEdit.toPlainText())
            Player.volume_update(mpv.volume)
            self.setWindowTitle(loc['Success'])
        except Exception:
            self.setWindowTitle(loc['Error'])


class ReferenceWindow(QDialog):
    def __init__(self):
        super(ReferenceWindow, self).__init__()
        self.ui = reference_window.Ui_ReferenceWindow()
        self.ui.setupUi(self)

        self.setWindowIcon(QIcon(f'{os.path.dirname(__file__) + os.sep}favicon.ico'))

        self.setWindowTitle(loc['Reference'])
        self.ui.buttonBox.buttons()[0].setText(loc['Close'])

        if loc['lang'] == 'Русский':
            reference_file_name = 'GLSL_Instructions_Advanced_ru.txt'
        else:
            reference_file_name = 'GLSL_Instructions_Advanced.txt'

        with open(f'{os.path.dirname(__file__) + os.sep}docs{os.sep}{reference_file_name}', 'r', encoding='utf-8') as ref_data:
            reference = ref_data.read()
            self.ui.plainTextEdit.setPlainText(reference)


class ScreenshotWindow(QDialog):
    def __init__(self):
        super(ScreenshotWindow, self).__init__()
        self.ui = screenshot_window.Ui_ScreenshotWindow()
        self.ui.setupUi(self)

        self.setFixedSize(520, 120)
        self.setWindowIcon(QIcon(f'{os.path.dirname(__file__) + os.sep}favicon.ico'))

        self.ui.lineEdit.setText(screenshot_path)

        self.setWindowTitle(loc['Screenshot'])
        self.ui.label.setText(loc['Enter folder path for screenshots'])
        self.ui.select.setText(loc['Select'])
        self.ui.paste.setText(loc['Paste'])
        self.ui.buttonBox.buttons()[0].setText(loc['Save'])
        self.ui.buttonBox.buttons()[1].setText(loc['Close'])

        self.ui.paste.clicked.connect(lambda: self.ui.lineEdit.setText(QGuiApplication.clipboard().text()))
        self.ui.select.clicked.connect(self.select)
        self.ui.buttonBox.accepted.connect(self.save)

    def select(self):
        folder_name = QFileDialog.getExistingDirectory()
        if folder_name is not None and folder_name != '':
            self.ui.lineEdit.setText(folder_name)

    def save(self):
        global screenshot_path
        screenshot_path = self.ui.lineEdit.text().strip()
        if screenshot_path is not None and screenshot_path != '':
            mpv.screenshot_directory = screenshot_path
            mpv.screenshot_jpeg_quality = 100
            try:
                mpv.screenshot()
            except SystemError:
                self.ui.label.setText(loc['Error'])


class AboutWindow(QDialog):
    def __init__(self):
        super(AboutWindow, self).__init__()
        self.ui = about_window.Ui_AboutWindow()
        self.ui.setupUi(self)

        self.setWindowIcon(QIcon(f'{os.path.dirname(__file__) + os.sep}favicon.ico'))
        self.ui.image.setPixmap(QPixmap(f'{os.path.dirname(__file__) + os.sep}images{os.sep}anime-player-icon.png'))

        self.setWindowTitle(loc['About'])
        self.ui.label_2.setText(f'Anime Player v{version}')
        self.ui.label_3.setText(f'{mpv.mpv_version}\n\n{loc["About program"]}')
        self.ui.buttonBox.buttons()[0].setText(loc['Close'])


class SettingsWindow(QDialog):
    def __init__(self):
        super(SettingsWindow, self).__init__()
        self.ui = settings_window.Ui_SettingsWindow()
        self.ui.setupUi(self)

        self.setWindowIcon(QIcon(f'{os.path.dirname(__file__) + os.sep}favicon.ico'))

        # Load language from config
        lang = config.get('language', 'Auto')
        self.ui.language.clear()
        self.ui.language.addItems(['Auto', 'Русский', 'English', 'Japanese', 'Français'])
        self.ui.language.setCurrentText(lang)

        match lang:
            case 'Русский':
                self.lang = 'Русский'
            case 'English':
                self.lang = 'English'
            case 'Japanese':
                self.lang = 'Japanese'
            case 'Français':
                self.lang = 'Français'
            case _:
                self.lang = 'Auto'

        match config.get('theme'):
            case 'Light':
                self.theme = 'Light'
            case 'Dark':
                self.theme = 'Dark'
            case _:
                self.theme = 'System'

        self.ui.language.clear()
        self.ui.language.addItems(['Auto', 'Русский', 'English', 'Japanese', 'Français'])
        self.ui.language.setCurrentText(self.lang)
        self.ui.openLastFile.setChecked(config.get('onOpenLastFile', True))
        self.ui.posLastFile.setChecked(config.get('onPosLastFile', True))
        self.ui.volumePlus.setChecked(config.get('volumePlus', False))
        self.ui.svp.setChecked(config.get('SVP', False))
        self.ui.appTheme.setCurrentText(self.theme)
        styles = QStyleFactory.keys()
        for i in range(len(styles)):
            styles[i] = styles[i].lower()
        self.ui.comboBox_style.addItems(styles)
        self.ui.comboBox_style.setCurrentText(config.get('style', app.style().name()))

        self.ui.labelAppTheme.setVisible(True)
        self.ui.appTheme.setVisible(True)

        # Load AniSkip settings
        aniskip_settings = config.get('aniskip', {
            'auto_skip_op': False,
            'auto_skip_ed': False,
            'auto_skip_recap': False,
            'auto_skip_preview': False,
            'skip_button_size': 100
        })
        self.ui.auto_skip_op.setChecked(aniskip_settings.get('auto_skip_op', False))
        self.ui.auto_skip_ed.setChecked(aniskip_settings.get('auto_skip_ed', False))
        self.ui.auto_skip_recap.setChecked(aniskip_settings.get('auto_skip_recap', False))
        self.ui.auto_skip_preview.setChecked(aniskip_settings.get('auto_skip_preview', False))
        self.ui.skip_button_size.setValue(aniskip_settings.get('skip_button_size', 100))

        self.ui.buttonBox.accepted.connect(self.ok)

        self.setWindowTitle(loc['Settings'])
        self.ui.label.setText(loc['Language selection'])
        self.ui.openLastFile.setText(loc['On startup open the last opened file'])
        self.ui.posLastFile.setText(loc['Set the position of the last opened file'])
        self.ui.volumePlus.setText(loc['Increase maximum volume up to 150%'])
        self.ui.svp.setText(loc['Activate SVP'])
        self.ui.buttonBox.buttons()[1].setText(loc['Cancel'])
        self.ui.labelAppTheme.setText(loc['App theme'])
        self.ui.label_style.setText(loc['Theme'])

        # Set localized text for AniSkip checkboxes
        self.ui.auto_skip_op.setText(loc['Auto-skip Opening'])
        self.ui.auto_skip_ed.setText(loc['Auto-skip Ending'])
        self.ui.auto_skip_recap.setText(loc['Auto-skip Recap'])
        self.ui.auto_skip_preview.setText(loc['Auto-skip Preview'])

        # Set localized text for AniSkip Settings label
        self.ui.aniskip_label.setText(loc['AniSkip Settings'])

    def ok(self):
        config.set('language', self.ui.language.currentText())
        config.set('onOpenLastFile', self.ui.openLastFile.isChecked())
        config.set('onPosLastFile', self.ui.posLastFile.isChecked())
        config.set('SVP', self.ui.svp.isChecked())
        config.set('volumePlus', self.ui.volumePlus.isChecked())
        config.set('style', self.ui.comboBox_style.currentText())
        config.set('theme', self.ui.appTheme.currentText())
        app.setStyle(self.ui.comboBox_style.currentText())
        # Save AniSkip settings
        aniskip_settings = {
            'auto_skip_op': self.ui.auto_skip_op.isChecked(),
            'auto_skip_ed': self.ui.auto_skip_ed.isChecked(),
            'auto_skip_recap': self.ui.auto_skip_recap.isChecked(),
            'auto_skip_preview': self.ui.auto_skip_preview.isChecked(),
            'skip_button_size': self.ui.skip_button_size.value()
        }
        config.set('aniskip', aniskip_settings)
        config.save_config()
        apply_theme()


class OpenURLWindow(QDialog):
    def __init__(self):
        super(OpenURLWindow, self).__init__()
        self.ui = open_url_window.Ui_OpenURLWindow()
        self.ui.setupUi(self)

        self.setFixedSize(550, 120)
        self.setWindowIcon(QIcon(f'{os.path.dirname(__file__) + os.sep}favicon.ico'))

        self.links_history = config.get('linksHistory', [])

        self.ui.comboBox.addItems(self.links_history)

        self.ui.paste.clicked.connect(lambda: self.ui.comboBox.setCurrentText(QGuiApplication.clipboard().text()))
        self.ui.clear.clicked.connect(self.clear)
        self.ui.buttonBox.accepted.connect(self.ok)

        self.setWindowTitle(loc['Opening a link'])
        self.ui.label.setText(loc['Enter the URL'])
        self.ui.paste.setText(loc['Paste'])
        self.ui.clear.setText(loc['Clear'])
        self.ui.buttonBox.buttons()[1].setText(loc['Cancel'])

    def clear(self):
        self.links_history = []
        self.ui.comboBox.clear()
        self.ui.comboBox.clearEditText()
        config.set('linksHistory', [])

    def ok(self):
        new_link = self.ui.comboBox.currentText().strip()
        if new_link is not None and new_link != '':
            if self.links_history.count(new_link) > 0:
                self.links_history.remove(new_link)
            self.links_history.insert(0, new_link)
            config.set('linksHistory', self.links_history)
            player.open_url(new_link)


class OpenFolderWindow(QDialog):
    def __init__(self):
        super(OpenFolderWindow, self).__init__()
        self.ui = open_folder_window.Ui_OpenFolderWindow()
        self.ui.setupUi(self)

        self.setFixedSize(550, 120)
        self.setWindowIcon(QIcon(f'{os.path.dirname(__file__) + os.sep}favicon.ico'))

        self.folders_history = config.get('foldersHistory', [])

        self.ui.comboBox.addItems(self.folders_history)

        self.ui.paste.clicked.connect(lambda: self.ui.comboBox.setCurrentText(QGuiApplication.clipboard().text()))
        self.ui.clear.clicked.connect(self.clear)
        self.ui.buttonBox.accepted.connect(self.ok)
        self.ui.select.clicked.connect(self.select)

        self.setWindowTitle(loc['Opening a folder'])
        self.ui.label.setText(loc['Select a folder'])
        self.ui.select.setText(loc['Select'])
        self.ui.paste.setText(loc['Paste'])
        self.ui.clear.setText(loc['Clear'])
        self.ui.buttonBox.buttons()[1].setText(loc['Cancel'])

    def clear(self):
        self.folders_history = []
        self.ui.comboBox.clear()
        self.ui.comboBox.clearEditText()
        config.set('foldersHistory', [])

    def ok(self):
        new_folder = self.ui.comboBox.currentText().strip()
        if new_folder is not None and new_folder != '':
            if self.folders_history.count(new_folder) > 0:
                self.folders_history.remove(new_folder)
            self.folders_history.insert(0, new_folder)
            config.set('foldersHistory', self.folders_history)
            player.open_folder(new_folder)

    def select(self):
        folder_name = QFileDialog.getExistingDirectory()
        if folder_name is not None and folder_name != '':
            self.ui.comboBox.setCurrentText(folder_name)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = main_window.Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowIcon(QIcon(f'{os.path.dirname(__file__) + os.sep}favicon.ico'))

        self.ui.rightPanel.setVisible(False)

        # Fix icon paths to use relative paths
        icons_dir = os.path.join(os.path.dirname(__file__), 'images', 'icons')
        self.ui.play.setIcon(QIcon(os.path.join(icons_dir, 'play_arrow_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg')))
        self.ui.prev.setIcon(QIcon(os.path.join(icons_dir, 'skip_previous_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg')))
        self.ui.next.setIcon(QIcon(os.path.join(icons_dir, 'skip_next_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg')))
        self.ui.fullscreen.setIcon(QIcon(os.path.join(icons_dir, 'fullscreen_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg')))
        self.ui.audio.setIcon(QIcon(os.path.join(icons_dir, 'music_note_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg')))
        self.ui.sub.setIcon(QIcon(os.path.join(icons_dir, 'subtitles_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg')))
        self.ui.menu.setIcon(QIcon(os.path.join(icons_dir, 'format_list_bulleted_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg')))
        self.ui.video.setPixmap(QPixmap(os.path.join(os.path.dirname(__file__), 'images', 'play-button.png')))

        self.ui.rightPanel.setTitleBarWidget(QWidget())
        self.ui.controlPanel.setTitleBarWidget(QWidget())

        self.ui.play.setToolTip(f'{loc['Play']} / {loc['Pause']}')
        self.ui.prev.setToolTip(loc['Previous file'])
        self.ui.next.setToolTip(loc['Next file'])
        self.ui.fullscreen.setToolTip(loc['Fullscreen'])
        self.ui.audio.setToolTip(loc['Soundtrack'])
        self.ui.sub.setToolTip(loc['Subtitles'])
        self.ui.menu.setToolTip(loc['Menu'])
        self.ui.volume.setToolTip(loc['Volume level'])

        self.ui.play.clicked.connect(lambda: player.play())
        self.ui.prev.clicked.connect(lambda: player.prev())
        self.ui.next.clicked.connect(lambda: player.next())
        self.ui.fullscreen.clicked.connect(lambda: player.fullscreen_switch())
        self.ui.menu.clicked.connect(self.right_panel_visible)
        self.ui.sub.clicked.connect(lambda: player.sub_view())
        self.ui.audio.clicked.connect(lambda: player.audio_view())
        self.ui.volume.valueChanged.connect(lambda: player.volume_update(self.ui.volume.value()))
        self.ui.time.valueChanged.connect(lambda: self.change_time())

        self.ui.video.setMouseTracking(True)
        self.setMouseTracking(True)
        self.centralWidget().setMouseTracking(True)

        self.timer = QTimer(interval=500)
        self.timer.timeout.connect(self.timer_update)
        self.timer.start()

        self.timer_click = QTimer(interval=300)
        self.timer_click.timeout.connect(self.timer_click.stop)

        self.ui.fileList.clicked.connect(lambda: player.update_filelist(self.ui.fileList.currentIndex().row()))

        # Верхнее меню
        self.ui.action_Exit.triggered.connect(lambda: self.close())
        self.ui.action_Close.triggered.connect(lambda: player.close())
        self.ui.action_Open_file.triggered.connect(self.open_file)
        self.ui.action_Open_folder.triggered.connect(self.open_folder)
        self.ui.action_Open_URL.triggered.connect(self.open_url)
        self.ui.action_Settings.triggered.connect(self.settings)
        self.ui.action_Reference.triggered.connect(self.reference)
        self.ui.action_Launch_parameters.triggered.connect(self.launch_parameters)
        self.ui.action_Create_config_Android.triggered.connect(self.android_config)
        self.ui.action_Fullscreen.triggered.connect(lambda: player.fullscreen_switch())
        self.ui.action_Play_Pause.triggered.connect(lambda: player.play())
        self.ui.action_Disable.triggered.connect(lambda: player.disable_anime4k())
        self.ui.action_Volume_plus.triggered.connect(self.volume_plus)
        self.ui.action_Volume_minus.triggered.connect(self.volume_minus)
        self.ui.action_Rewind_plus.triggered.connect(self.rewind_plus)
        self.ui.action_Rewind_minus.triggered.connect(self.rewind_minus)
        self.ui.action_About.triggered.connect(self.about)
        self.ui.action_Playlist.triggered.connect(self.right_panel_visible)
        self.ui.action_Take_a_screenshot.triggered.connect(self.screenshot)
        self.ui.action_Zoom_in.triggered.connect(lambda: self.zoom(0.01))
        self.ui.action_Zoom_out.triggered.connect(lambda: self.zoom(-0.01))

        self.ui.action_x025.triggered.connect(lambda: self.speed(0.25))
        self.ui.action_x05.triggered.connect(lambda: self.speed(0.5))
        self.ui.action_x075.triggered.connect(lambda: self.speed(0.75))
        self.ui.action_x10.triggered.connect(lambda: self.speed(1.0))
        self.ui.action_x125.triggered.connect(lambda: self.speed(1.25))
        self.ui.action_x15.triggered.connect(lambda: self.speed(1.5))
        self.ui.action_x175.triggered.connect(lambda: self.speed(1.75))
        self.ui.action_x20.triggered.connect(lambda: self.speed(2.0))
        self.ui.action_x225.triggered.connect(lambda: self.speed(2.25))
        self.ui.action_x25.triggered.connect(lambda: self.speed(2.5))
        self.ui.action_x275.triggered.connect(lambda: self.speed(2.75))
        self.ui.action_x30.triggered.connect(lambda: self.speed(3.0))

        self.ui.action_Settings.setText(loc['Settings'])
        self.ui.menu_File.setTitle(loc['File'])
        self.ui.action_Open_file.setText(loc['Open file'])
        self.ui.action_Open_URL.setText(loc['Open URL'])
        self.ui.action_Open_folder.setText(loc['Open folder'])
        self.ui.action_Close.setText(loc['Close'])
        self.ui.action_Exit.setText(loc['Exit'])
        self.ui.menu_Playback.setTitle(loc['Playback'])
        self.ui.action_Play_Pause.setText(loc['Play | Pause'])
        self.ui.action_Fullscreen.setText(loc['Fullscreen'])
        self.ui.menu_Increasing_image_quality.setTitle(loc['Increasing image quality'])
        self.ui.action_Disable.setText(loc['Disable'])
        self.ui.menu_Other.setTitle(loc['Other'])
        self.ui.action_About.setText(loc['About'])
        self.ui.action_Launch_parameters.setText(loc['Launch parameters'])
        self.ui.action_Take_a_screenshot.setText(loc['Take a screenshot'])
        self.ui.action_Create_config_Android.setText(loc['Create config for Android'])
        self.ui.action_Reference.setText(loc['Reference'])
        self.ui.menu_Playback_speed.setTitle(loc['Playback speed'])
        self.ui.action_Volume_plus.setText(loc['Volume +10'])
        self.ui.action_Volume_minus.setText(loc['Volume -10'])
        self.ui.action_Rewind_plus.setText(loc['Rewind +5 sec'])
        self.ui.action_Rewind_minus.setText(loc['Rewind -5 sec'])
        self.ui.action_Zoom_in.setText(loc['Zoom in'])
        self.ui.action_Zoom_out.setText(loc['Zoom out'])
        self.ui.action_Playlist.setText(loc['Playlist'])
        self.ui.sourceInfo.setText('')

        modes = []
        for quality in anime4k.qualities:
            modes += [f'{loc["Mode"]} {mode} ({quality})' for mode in anime4k.modes]

        tabs = {}
        for quality in anime4k.qualities:
            if f'{loc["Quality"]} {quality}' not in tabs.keys():
                tabs[f'{loc["Quality"]} {quality}'] = []
            tabs[f'{loc["Quality"]} {quality}'] += [f'{loc["Mode"]} {mode}' for mode in anime4k.modes]
        tabs[f'{loc["Quality"]} HQ'] = [f'{loc["Mode"]} {mode}' for mode in list(anime4k.ultra_hq_presets.keys())]

        for quality in tabs.keys():
            menu = QMenu(self.menuBar())
            menu.setTitle(quality)
            self.ui.menu_Increasing_image_quality.addMenu(menu)
            for mode in tabs[quality]:
                action = QAction(self)
                action.setText(mode)
                action.triggered.connect(lambda ignore=False, q=quality, m=mode: player.set_preset_quality(q, m))
                menu.addAction(action)

        self.customContextMenuRequested.connect(self.show_context_menu)

        self.setAcceptDrops(True)

        # Connect skip button
        self.ui.skip_button.clicked.connect(lambda: player.skip_current_segment())

    def mouseMoveEvent(self, event):
        if player.fullscreen:
            player.update_fullscreen_layout(event.position().x(), event.position().y())

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()

    def dropEvent(self, event):
        is_new = True
        for url in event.mimeData().urls():
            file_name = url.toLocalFile()
            if os.path.isfile(file_name):
                if is_new:
                    player.open_file(file_name)
                    is_new = False
                else:
                    player.add_file(file_name)
            elif os.path.isdir(file_name):
                player.open_folder(file_name)
                break
            elif os.path.islink(file_name):
                player.open_url(file_name)
                break

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            player.play()
            if self.timer_click.isActive():
                Player.fullscreen_switch()
                self.timer_click.stop()
            else:
                self.timer_click.start()

    @staticmethod
    def screenshot():
        screenshot_win = ScreenshotWindow()
        screenshot_win.setModal(True)
        screenshot_win.exec()

    @staticmethod
    def zoom(value):
        mpv.video_zoom += value

    @staticmethod
    def speed(speed):
        mpv.speed = speed

    @staticmethod
    def timer_update():
        player.update_info()
        player.update_cursor()
        # --- AUTO SKIP BUTTON VIDEO SIZE UPDATE ---
        # Always update the video frame size for the skip button
        if hasattr(window.ui, 'video'):
            try:
                window.ui.video_frame_width = mpv.width
                window.ui.video_frame_height = mpv.height
                # If the skip button and update function exist, update position
                if hasattr(window.ui, 'skip_button') and hasattr(window.ui, 'video_container'):
                    for child in window.ui.video_container.children():
                        if callable(getattr(child, 'move', None)) and child.objectName() == 'skip_button':
                            # Call the update function if it exists in the closure
                            if 'update_skip_button' in window.ui.video_container.__dict__:
                                window.ui.video_container.update_skip_button()
                            break
            except Exception:
                pass

    def change_time(self):
        if mpv.time_pos is not None and int(mpv.time_pos) != self.ui.time.value():
            player.new_position(self.ui.time.value())
            # Force update skip button state after seeking
            if hasattr(window.ui, 'skip_button'):
                current_segment = player.aniskip.get_current_segment(self.ui.time.value())
                if current_segment:
                    skip_type = current_segment.skip_type.value
                    auto_skip_types = []
                    if config.get('aniskip', {}).get('auto_skip_op', False):
                        auto_skip_types.append('op')
                    if config.get('aniskip', {}).get('auto_skip_ed', False):
                        auto_skip_types.append('ed')
                    if config.get('aniskip', {}).get('auto_skip_recap', False):
                        auto_skip_types.append('recap')
                    if config.get('aniskip', {}).get('auto_skip_preview', False):
                        auto_skip_types.append('preview')
                    if skip_type in auto_skip_types:
                        window.ui.skip_button.setVisible(False)
                    else:
                        window.ui.skip_button.setVisible(True)
                        skip_type_text = {
                            'op': loc['Skip Opening'],
                            'ed': loc['Skip Ending'],
                            'recap': loc['Skip Recap'],
                            'mixed-op': loc['Skip Mixed Opening'],
                            'mixed-ed': loc['Skip Mixed Ending'],
                            'preview': loc['Skip Preview']
                        }.get(skip_type, f'Skip {skip_type}')
                        window.ui.skip_button.setText(skip_type_text)
                else:
                    window.ui.skip_button.setVisible(False)

    def closeEvent(self, event):
        try:
            # Save current parameters
            player.save_parameters()
            
            # Terminate MPV
            if mpv:
                mpv.terminate()
            
            # Accept the close event
            event.accept()
            
            # Force quit the application
            QApplication.quit()
        except Exception as e:
            logger.error(f"Error during window close: {e}")
            # Force quit even if there's an error
            QApplication.quit()

    def open_file(self):
        file_name = QFileDialog.getOpenFileName(self,
                                                filter=f"{loc['All supported files']} ({' '.join(['*.' + f for f in formats])});;{loc['Video']} ({' '.join(['*.' + f for f in video_formats])});;{loc['Audio']} ({' '.join(['*.' + f for f in audio_formats])});;{loc['All files']} (*.*)")
        if file_name[0] is not None and file_name[0] != '':
            player.open_file(file_name[0])

    @staticmethod
    def open_folder():
        open_folder_win = OpenFolderWindow()
        open_folder_win.setModal(True)
        open_folder_win.exec()

    @staticmethod
    def open_url():
        open_url_win = OpenURLWindow()
        open_url_win.setModal(True)
        open_url_win.exec()

    def settings(self):
        settings_win = SettingsWindow()
        settings_win.setModal(True)
        settings_win.exec()
        if not config.get('volumePlus', False):
            self.ui.volume.setValue(mpv.volume)
            self.ui.volume.setMaximum(100)
        else:
            self.ui.volume.setMaximum(150)

    @staticmethod
    def about():
        about_win = AboutWindow()
        about_win.setModal(True)
        about_win.exec()

    @staticmethod
    def reference():
        reference_win = ReferenceWindow()
        reference_win.setModal(True)
        reference_win.exec()

    def launch_parameters(self):
        launch_parameters_win = LaunchParametersWindow()
        launch_parameters_win.setModal(True)
        launch_parameters_win.exec()
        self.ui.volume.setValue(mpv.volume)

    @staticmethod
    def android_config():
        android_config_win = AndroidConfigWindow()
        android_config_win.setModal(True)
        android_config_win.exec()

    def right_panel_visible(self):
        if Player.fullscreen:
            Player.is_menu_visible = not Player.is_menu_visible
        else:
            self.ui.rightPanel.setVisible(not self.ui.rightPanel.isVisible())

    def show_context_menu(self):
        menu = QMenu()
        menu.addAction(self.ui.action_Open_file)
        menu.addAction(self.ui.action_Open_folder)
        menu.addAction(self.ui.action_Open_URL)
        menu.addAction(self.ui.action_Close)
        menu.addSeparator()
        menu.addMenu(self.ui.menu_Increasing_image_quality)
        menu.addSeparator()
        menu.addAction(self.ui.action_Play_Pause)
        menu.addMenu(self.ui.menu_Playback_speed)
        menu.addAction(self.ui.action_Playlist)
        menu.addAction(self.ui.action_Zoom_in)
        menu.addAction(self.ui.action_Zoom_out)
        menu.addAction(self.ui.action_Take_a_screenshot)
        menu.addAction(self.ui.action_Fullscreen)
        menu.addSeparator()
        menu.addAction(self.ui.action_Settings)
        menu.addAction(self.ui.action_About)
        menu.addSeparator()
        menu.addAction(self.ui.action_Exit)
        menu.exec(QCursor.pos())

    def volume_plus(self):
        if mpv.volume > 95 and self.ui.volume.maximum() == 100:
            mpv.volume = 100
        elif mpv.volume > 145 and self.ui.volume.maximum() == 150:
            mpv.volume = 150
        else:
            mpv.volume += 5
        self.ui.volume.setValue(mpv.volume)
        Player.volume_update(mpv.volume)

    def volume_minus(self):
        if mpv.volume < 5:
            mpv.volume = 0
        else:
            mpv.volume -= 5
        self.ui.volume.setValue(mpv.volume)
        Player.volume_update(mpv.volume)

    @staticmethod
    def rewind_plus():
        if mpv.time_pos is not None:
            mpv.seek(5)
            window.ui.time.setValue(mpv.time_pos)
            window.ui.currentTime.setText('{:02d}:{:02d}'.format(*divmod(int(mpv.time_pos), 60)))

    @staticmethod
    def rewind_minus():
        if mpv.time_pos is not None:
            if mpv.time_pos > 5:
                mpv.seek(-5)
            else:
                mpv.time_pos = 0
            window.ui.time.setValue(mpv.time_pos)
            window.ui.currentTime.setText('{:02d}:{:02d}'.format(*divmod(int(mpv.time_pos), 60)))


class Player:
    """
    Управление плеером
    """
    files: list = []
    filenames_only: list = []
    fullscreen: bool = False
    is_menu_visible: bool = True
    is_maximized: bool = False
    audio: dict = {}
    sub: dict = {}
    duration: int = 0
    info: dict = {
        'preset': '',
        'codec': '',
        'resolution': '',
        'fps': 0,
        'frame_drop': 0
    }
    cursor_last: tuple = (0, 0)
    cursor_timer: int = 0
    aniskip = None  # Will be initialized in __init__
    current_segment: Optional[SkipSegment] = None

    def __init__(self):
        self.aniskip = aniskip.AniSkip(mpv_instance=mpv)

    @staticmethod
    def list_files(folder: str):
        return [os.path.join(folder, f) for f in os.listdir(folder) if (f.split('.')[-1].lower() in formats)]

    @staticmethod
    def list_filenames(folder: str):
        filenames = [f for f in os.listdir(folder) if (f.split('.')[-1].lower() in formats)]
        return [f'{i + 1}) ' + filenames[i] for i in range(len(filenames))]

    def sub_view(self):
        self.sub = {}
        if mpv.track_list is not None:
            for track in mpv.track_list:
                if track['type'] == 'sub':
                    if 'title' in track.keys():
                        self.sub[track['id']] = f'{track["title"]}'
                        if 'lang' in track.keys():
                            self.sub[track['id']] = f'{track["lang"]} - ' + self.sub[track['id']]
                    elif 'lang' in track.keys():
                        self.sub[track['id']] = f'{track["lang"]} - {track["codec"]}'
                    else:
                        self.sub[track['id']] = track['codec']

            def set_sub(index: int):
                mpv.sid = index

            def add_subtitles():
                file_name = QFileDialog.getOpenFileName(filter=f"{loc['Subtitles']} ({' '.join(['*.' + f for f in subtitles_formats])});;{loc['All files']} (*.*)")
                if file_name[0] is not None and file_name[0] != '':
                    mpv.sub_add(file_name[0])

            menu_sub = QMenu()
            if len(self.sub) > 0:
                action = QAction(window)
                action.setText(loc['Disable'])
                action.triggered.connect(lambda: set_sub(0))
                menu_sub.addAction(action)

                action = QAction(window)
                action.setText(loc['Add subtitles'])
                action.triggered.connect(add_subtitles)
                menu_sub.addAction(action)

                menu_sub.addSeparator()
                for key, value in self.sub.items():
                    action = QAction(window)
                    action.setText(f'{key}) {value}')
                    action.triggered.connect(lambda ignore=False, x=key: set_sub(x))
                    menu_sub.addAction(action)
            else:
                action = QAction(window)
                action.setText(loc['Add subtitles'])
                action.triggered.connect(add_subtitles)
                menu_sub.addAction(action)

            menu_sub.exec(window.ui.sub.mapToGlobal(QPoint(0, 0)))

    def audio_view(self):
        self.audio = {}
        if mpv.track_list is not None:
            for track in mpv.track_list:
                if track['type'] == 'audio':
                    self.audio[track['id']] = f'{track['codec']} {track['audio-channels']}ch {track['demux-samplerate']} Hz'
                    if 'title' in track.keys():
                        self.audio[track['id']] = f'{track["title"]} (' + self.audio[track['id']] + ')'
                        if 'lang' in track.keys():
                            self.audio[track['id']] = f'{track["lang"]} - ' + self.audio[track['id']]
                    elif 'lang' in track.keys():
                        self.audio[track['id']] = f'{track["lang"]} - {self.audio[track['id']]}'

            def set_audio(index: int):
                mpv.aid = index

            menu_audio = QMenu()
            if len(self.audio) > 0:
                action = QAction(window)
                action.setText(loc['Disable'])
                action.triggered.connect(lambda: set_audio(0))
                menu_audio.addAction(action)
                menu_audio.addSeparator()
                for key, value in self.audio.items():
                    action = QAction(window)
                    action.setText(f'{key}) {value}')
                    action.triggered.connect(lambda ignore=False, a=key: set_audio(a))
                    menu_audio.addAction(action)
            else:
                action = QAction(window)
                action.setText(loc['No audio tracks'])
                menu_audio.addAction(action)
            menu_audio.exec(window.ui.audio.mapToGlobal(QPoint(0, 0)))

    def update_info(self, no_update_fps=True):
        try:
            # Use the global mpv instance instead of self.mpv
            if not mpv:
                return

            # duration = player.duration
            time_pos = mpv.time_pos
            if time_pos is None:
                return

            Player.info['codec'] = mpv.video_format if mpv.video_format is not None else mpv.audio_codec_name
            Player.info['resolution'] = (mpv.width, mpv.height)
            if no_update_fps:
                Player.info['fps'] = mpv.estimated_vf_fps
            Player.info['frame_drop'] = mpv.frame_drop_count

            # Обновление информации о разрешении, FPS, кодеке и потерянных кадрах
            str_info = {
                'preset': Player.info['preset'],
                'codec': f'{Player.info["codec"].upper()}' if Player.info["codec"] is not None else '',
                'resolution': f'{Player.info["resolution"][0]}x{Player.info["resolution"][1]}' if Player.info["resolution"] != (None, None) else '',
                'fps': f'{round(Player.info["fps"], 1) if Player.info["fps"] is not None else "0.0"} FPS' if Player.info["resolution"] != (None, None) else '',
                'frame_drop': f'{loc["Frames lost"]}: {Player.info["frame_drop"]}' if Player.info["frame_drop"] is not None else ''
            }

            window.ui.mediaInfo.setText(' | '.join([string for string in str_info.values() if string != '']))
            # Обновление кнопки ИГРАТЬ
            if mpv.duration is not None and mpv.pause:
                window.ui.play.setIcon(QIcon(icons.play))
            # Обновление ползунка прокрутки и времени
            if mpv.duration is not None:
                if self.duration != mpv.duration:
                    self.duration = mpv.duration
                    window.ui.time.setMaximum(self.duration)
                    window.ui.allTime.setText('{:02d}:{:02d}'.format(*divmod(int(self.duration), 60)))
            else:
                window.ui.time.setMaximum(0)
                window.ui.allTime.setText('00:00')

            if time_pos is not None:
                window.ui.time.setValue(time_pos)
                window.ui.currentTime.setText('{:02d}:{:02d}'.format(*divmod(int(time_pos), 60)))
            else:
                window.ui.currentTime.setText('00:00')
                window.ui.time.setValue(0)

            # Add AniSkip debug logging
            if mpv.time_pos is not None:
                current_segment = self.aniskip.get_current_segment(mpv.time_pos)
                if current_segment != self.current_segment:
                    logger.debug(f"Current segment changed: {current_segment}")
                    self.current_segment = current_segment
                    # AniSkip auto-skip logic
                    if current_segment:
                        skip_type = current_segment.skip_type.value
                        auto_skip_types = []
                        if config.get('aniskip', {}).get('auto_skip_op', False):
                            auto_skip_types.append('op')
                        if config.get('aniskip', {}).get('auto_skip_ed', False):
                            auto_skip_types.append('ed')
                        if config.get('aniskip', {}).get('auto_skip_recap', False):
                            auto_skip_types.append('recap')
                        if config.get('aniskip', {}).get('auto_skip_preview', False):
                            auto_skip_types.append('preview')
                        # If auto-skip is enabled for this type, skip automatically
                        if skip_type in auto_skip_types:
                            logger.info(f"AniSkip auto-skipping {skip_type} to {current_segment.end}")
                            mpv.seek(current_segment.end, reference="absolute")
                            window.ui.skip_button.setVisible(False)
                            return
                        # Update skip button visibility and text (auto/hide logic)
                        if current_segment:
                            skip_type = current_segment.skip_type.value
                            auto_skip_types = []
                            if config.get('aniskip', {}).get('auto_skip_op', False):
                                auto_skip_types.append('op')
                            if config.get('aniskip', {}).get('auto_skip_ed', False):
                                auto_skip_types.append('ed')
                            if config.get('aniskip', {}).get('auto_skip_recap', False):
                                auto_skip_types.append('recap')
                            if config.get('aniskip', {}).get('auto_skip_preview', False):
                                auto_skip_types.append('preview')
                            # If auto-skip is enabled for this type, hide the button
                            if skip_type in auto_skip_types:
                                window.ui.skip_button.setVisible(False)
                            else:
                                window.ui.skip_button.setVisible(True)
                                skip_type_text = {
                                    'op': loc['Skip Opening'],
                                    'ed': loc['Skip Ending'],
                                    'recap': loc['Skip Recap'],
                                    'mixed-op': loc['Skip Mixed Opening'],
                                    'mixed-ed': loc['Skip Mixed Ending'],
                                    'preview': loc['Skip Preview']
                                }.get(skip_type, f'Skip {skip_type}')
                                window.ui.skip_button.setText(skip_type_text)
                                logger.debug(f"Skip button updated - Type: {skip_type_text}")
                        else:
                            window.ui.skip_button.setVisible(False)
                            logger.debug("Skip button hidden")

        except Exception as e:
            # Handle all exceptions, including MPV shutdown
            logger.debug(f"Error in update_info: {e}")
            return

    def play_file(self, file: str, timeout=3, position: float = 0):
        # Clear skip segments before playing new file
        player.current_segment = None
        player.aniskip.skip_segments = []  # Clear the skip segments list
        window.ui.skip_button.setVisible(False)
        mpv.play(file)
        if position > 0:
            try:
                mpv.wait_for_property('duration', lambda val: val is not None, timeout=timeout)
            except TimeoutError:
                pass
            else:
                self.new_position(position, slider_update=True)

    def play(self):
        """Воспроизведение / Пауза"""
        if window.ui.fileList.currentIndex().row() >= 0:
            if mpv.duration is None:
                self.play_file(self.files[window.ui.fileList.currentIndex().row()])
                mpv.pause = False
                window.ui.play.setIcon(QIcon(icons.pause))
            elif not mpv.pause:
                mpv.pause = True
                window.ui.play.setIcon(QIcon(icons.play))
            else:
                mpv.pause = False
                window.ui.play.setIcon(QIcon(icons.pause))

    def next(self):
        """Переход к следующему файлу"""
        current_index = window.ui.fileList.currentIndex().row()
        if current_index < len(self.files) - 1:
            window.ui.fileList.setCurrentRow(current_index + 1)
            window.setWindowTitle(f'{self.filenames_only[current_index]} - {name_program}')
            self.play_file(self.files[current_index])

    def prev(self):
        """Переход к предыдущему файлу"""
        if window.ui.fileList.currentIndex().row() > 0:
            file_num = window.ui.fileList.currentIndex().row() - 1
            file = self.files[file_num]
            window.ui.fileList.setCurrentRow(file_num)
            window.setWindowTitle(f'{file.rsplit(os.sep, 1)[-1]} - {name_program}')
            self.play_file(file)
        elif window.ui.fileList.count() > 0:
            window.ui.fileList.setCurrentRow(0)
            window.setWindowTitle(f'{self.files[0].rsplit(os.sep, 1)[-1]} - {name_program}')

    def open_file(self, file: str, pause: bool = False, position: float = 0):
        """
        Открытие файла
        :param file: путь к файлу
        :param pause: должна ли стоять пауза после открытия
        :param position: позиция
        """
        logger.debug(f"Opening file: {file}")
        file = file.replace('/', os.sep)
        mpv.stop()
        mpv.pause = pause
        if pause:
            window.ui.play.setIcon(QIcon(icons.play))
        else:
            window.ui.play.setIcon(QIcon(icons.pause))
        folder = file.rsplit(os.sep, 1)[0]
        self.files = [file]
        self.filenames_only = [file.split(os.sep)[-1]]
        window.ui.fileList.clear()
        window.ui.fileList.addItems(self.filenames_only)
        window.ui.fileList.setCurrentRow(0)
        window.ui.sourceInfo.setText(folder)
        window.setWindowTitle(f'{self.filenames_only[window.ui.fileList.currentIndex().row()]} - {name_program}')
        self.play_file(self.files[window.ui.fileList.currentIndex().row()], position=position)
        config.set('opened', ['file', file])

        # Fetch AniSkip segments
        logger.debug("Fetching AniSkip segments...")
        segments = self.aniskip.fetch_skip_segments(file)
        logger.debug(f"Found {len(segments)} skip segments: {segments}")
        if segments:
            logger.debug(f"First segment: {segments[0]}")
            logger.debug(f"Last segment: {segments[-1]}")

    def add_file(self, file: str):
        file = file.replace('/', os.sep)
        self.files.append(file)
        self.filenames_only.append(file.split(os.sep)[-1])
        window.ui.fileList.addItem(file.split(os.sep)[-1])

    def open_url(self, link: str, pause: bool = False, position: float = 0):
        """
        Открытие с помощью URL-адреса
        :param link: URL-адрес
        :param pause: должна ли стоять пауза после открытия
        :param position: позиция
        """
        mpv.stop()
        mpv.pause = pause
        if pause:
            window.ui.play.setIcon(QIcon(icons.play))
        else:
            window.ui.play.setIcon(QIcon(icons.pause))
        folder = 'URL'
        self.files = [link]
        self.filenames_only = [link.rsplit("/", 1)[-1]]
        window.ui.fileList.clear()
        window.ui.fileList.addItems(self.files)
        window.ui.fileList.setCurrentRow(0)
        window.ui.sourceInfo.setText(folder)
        window.setWindowTitle(f'{link.rsplit("/", 1)[-1]} - {name_program}')
        self.play_file(link, position=position, timeout=5)
        config.set('opened', ['url', link])

    def open_folder(self, folder: str, pause: bool = True, file: str = '', position: float = 0):
        """
        Открытие папки
        :param file:
        :param folder: путь к папке
        :param pause: должна ли стоять пауза после открытия
        :param file: полное имя файла
        :param position: позиция
        """
        folder = folder.replace('/', os.sep)
        mpv.stop()
        mpv.pause = pause
        if pause:
            window.ui.play.setIcon(QIcon(icons.play))
        else:
            window.ui.play.setIcon(QIcon(icons.pause))
        self.files = self.list_files(folder)
        self.filenames_only = self.list_filenames(folder)
        if file != '' and os.path.exists(file):
            file_num = self.files.index(file)
        else:
            file_num = 0
        if len(self.files) != 0:
            file_name = self.files[file_num]
            window.setWindowTitle(f'{file_name.rsplit(os.sep, 1)[-1]} - {name_program}')
            self.play_file(file_name, position=position)
        else:
            window.setWindowTitle(name_program)
        window.ui.fileList.clear()
        window.ui.fileList.addItems(self.filenames_only)
        window.ui.fileList.setCurrentRow(file_num)
        window.ui.rightPanel.setVisible(True)
        window.ui.sourceInfo.setText(folder)
        config.set('opened', ['folder', folder])

    def close(self):
        """
        Закрытие открытых фалов и переход в изначальное состояние
        """
        mpv.stop()
        mpv.pause = False
        window.ui.play.setIcon(QIcon(icons.play))
        self.files = []
        self.filenames_only = []
        self.duration = 0
        window.ui.fileList.clear()
        window.ui.sourceInfo.setText('')
        window.setWindowTitle(name_program)
        config.set('opened', ['', ''])

    def update_filelist(self, index: int):
        """
        Обновление списка файлов
        :param index: Номер файла в списке файлов
        """
        if len(self.filenames_only) >= 1:
            # if cls.filename != filename_temp or cls.filenum < 0:
            self.play_file(self.files[index])
            window.setWindowTitle(f'{self.files[index].rsplit(os.sep, 1)[-1]} - {name_program}')

    @classmethod
    def fullscreen_switch(cls):
        """
        Переключение полноэкранного режима
        """
        if not cls.fullscreen:
            cls.fullscreen = True
            cls.is_maximized = window.isMaximized()
            window.showFullScreen()
            window.ui.menubar.setFixedHeight(0)
            window.ui.controlPanel.setFloating(True)
            window.ui.controlPanel.setVisible(False)
            cls.is_menu_visible = window.ui.rightPanel.isVisible()
            window.ui.rightPanel.setVisible(False)
        else:
            cls.fullscreen = False
            window.ui.rightPanel.setFloating(False)
            if cls.is_maximized:
                window.showMaximized()
            else:
                window.showNormal()
            window.ui.menubar.setFixedHeight(window.ui.menubar.sizeHint().height() + 1)
            window.ui.controlPanel.setVisible(True)
            window.ui.rightPanel.setVisible(cls.is_menu_visible)
            window.ui.video.unsetCursor()
            cls.cursor_timer = 0
            window.ui.controlPanel.setFloating(False)

    def update_fullscreen_layout(self, x: float, y: float):
        if y > window.ui.centralwidget.size().height() - window.ui.controlPanel.height():
            window.ui.controlPanel.setVisible(True)
            window.ui.controlPanel.activateWindow()
        elif x > window.ui.centralwidget.size().width() - window.ui.rightPanel.width() - 20 and Player.is_menu_visible and not window.ui.rightPanel.isVisible():
            window.ui.rightPanel.setVisible(True)
        elif x > window.ui.centralwidget.size().width() - 20 and Player.is_menu_visible and window.ui.rightPanel.isVisible():
            window.ui.rightPanel.setVisible(True)
        else:
            window.ui.rightPanel.setVisible(False)
            window.ui.controlPanel.setVisible(False)

        window.ui.video.unsetCursor()
        self.cursor_last = (x, y)
        self.cursor_timer = 0

    def update_cursor(self):
        if not window.ui.controlPanel.isVisible() and not window.ui.rightPanel.isVisible():
            self.cursor_timer += 1
            if self.cursor_timer > 3:
                window.ui.video.setCursor(Qt.CursorShape.BlankCursor)

    @staticmethod
    def new_position(position: float, slider_update: bool = False):
        """
        Установка новой позиции
        :param position: позиция
        :param slider_update: обновлять ли слайдер
        """
        if mpv.duration is not None:
            mpv.time_pos = position
            window.ui.currentTime.setText('{:02d}:{:02d}'.format(*divmod(int(mpv.time_pos), 60)))
            window.ui.allTime.setText('{:02d}:{:02d}'.format(*divmod(int(mpv.duration), 60)))
            if slider_update:
                window.ui.time.setMaximum(mpv.duration)
                window.ui.time.setValue(mpv.time_pos)

    @staticmethod
    def volume_update(volume: int):
        """Изменение громкости"""
        mpv.volume = volume
        window.ui.volume.setToolTip(f'{volume}%')
        config.set('volume', volume)

    def save_parameters(self):
        """Сохранение текущего открытого файла и позиции"""
        if window.ui.fileList.count() > 0:
            file = self.files[window.ui.fileList.currentIndex().row()]
        else:
            file = None
        position = mpv.time_pos
        config.set('file', file)
        if position is not None and position >= 10:
            config.set('position', position)
        else:
            config.set('position', None)
        config.save_config()

    def configuration(self, open_prev: bool = True):
        """
        Начальная настройка плеера
        :param open_prev: открывать ли предыдущий файл
        """
        try:
            volume = config.get('volume')
            opened = config.get('opened')
            file = config.get('file')
            position = config.get('position')
            open_last = config.get('onOpenLastFile')
            on_pos_last_file = config.get('onPosLastFile')
            volume_plus = config.get('volumePlus', False)
            svp = config.get('SVP')
            style = config.get('style')
            launch_parameters = config.get('launchParameters')
            if on_pos_last_file is not None and not on_pos_last_file or position is None:
                position = 0
            if volume is not None:
                mpv.volume = volume
                window.ui.volume.setValue(volume)
                window.ui.volume.setToolTip(f'{volume}%')
            if volume_plus:
                window.ui.volume.setMaximum(150)
            if opened is not None and open_prev and (open_last is None or open_last):
                match opened[0]:
                    case 'file':
                        if os.path.exists(opened[1]):
                            self.open_file(opened[1], pause=True, position=position)
                    case 'url':
                        if on_pos_last_file is None or on_pos_last_file:
                            self.open_url(opened[1], pause=True, position=position)
                    case 'folder':
                        if os.path.exists(opened[1]):
                            self.open_folder(opened[1], pause=True, file=file, position=position)
            if svp is not None and svp:
                mpv.input_ipc_server = 'mpvpipe'
                mpv.hwdec = 'auto-copy'
                mpv.hwdec_codecs = 'all'
                mpv.hr_seek_framedrop = False
            if launch_parameters is not None and launch_parameters != '':
                try:
                    exec(launch_parameters)
                    window.ui.volume.setValue(mpv.volume)
                    config.set('volume', mpv.volume)
                except Exception:
                    pass
            if style is not None:
                app.setStyle(style)

            # Load AniSkip settings
            aniskip_settings = config.get('aniskip', {
                'auto_skip_op': False,
                'auto_skip_ed': False,
                'auto_skip_recap': False,
                'auto_skip_preview': False,
                'skip_button_size': 100
            })
            logger.debug(f"Loaded AniSkip settings: {aniskip_settings}")
            config.set('aniskip', aniskip_settings)
        except ValueError as e:
            logger.error(f"Error in configuration: {e}")
            config.delete('opened')
            config.delete('file')
            config.delete('position')

    def start_player(self, args: list):
        """
        Начальные действия при открытии плеера
        :param args: аргументы командной строки
        """
        if len(args) > 1:
            self.configuration(open_prev=False)
            if os.path.isfile(args[1]):
                file = config.get('opened', [None, None])[1]
                position = config.get('position')

                if file is not None and file == args[1] and position is not None:
                    self.open_file(args[1], position=position)
                else:
                    self.open_file(args[1])
            elif os.path.isdir(args[1]):
                self.open_folder(args[1])
        else:
            self.configuration(open_prev=True)

    def set_preset_quality(self, quality: str, mode: str):
        if quality == f'{loc["Quality"]} HQ':
            mpv.glsl_shaders = anime4k.to_string(anime4k.ultra_hq_presets[mode.split(' ', 1)[-1]], mode + ' (HQ)')
            self.info['preset'] = anime4k.current_preset
        else:
            mpv.glsl_shaders = anime4k.to_string(anime4k.create_preset(quality.split(' ', 1)[-1], mode.split(' ', 1)[-1]), mode + f' ({quality.split(" ", 1)[-1]})')
            self.info['preset'] = anime4k.current_preset

    @staticmethod
    def disable_anime4k():
        anime4k.current_preset = ''
        mpv.glsl_shaders = ''
        Player.info['preset'] = ''

    def skip_current_segment(self):
        """Skip the current segment."""
        # Add debounce to prevent multiple skips
        if not hasattr(self, '_last_skip_time'):
            self._last_skip_time = 0
        
        current_time = time.time()
        if current_time - self._last_skip_time < 0.5:  # 500ms debounce
            return
            
        self._last_skip_time = current_time
        
        logger.debug(f"Skip button clicked. Current segment: {self.current_segment}")
        if self.current_segment:
            logger.debug(f"Skipping to time: {self.current_segment.end}")
            mpv.seek(self.current_segment.end)
            logger.debug("Skip completed")
            # Hide the button after skipping
            window.ui.skip_button.setVisible(False)


# --- THEME SYSTEM ---
def apply_theme():
    global os
    theme = config.get('theme', 'System')
    # Detect system theme if needed
    if theme == 'System':
        import platform
        import os
        # Try to detect dark mode on Linux (KDE/GNOME)
        is_dark = False
        if platform.system() == 'Linux':
            # KDE
            kde_color_scheme = os.environ.get('KDE_COLOR_SCHEME', '').lower()
            if 'dark' in kde_color_scheme:
                is_dark = True
            # GNOME
            gtk_theme = os.environ.get('GTK_THEME', '').lower()
            if 'dark' in gtk_theme:
                is_dark = True
            # Try xdg settings
            try:
                import subprocess
                xdg_theme = subprocess.check_output(['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'], stderr=subprocess.DEVNULL).decode().strip()
                if 'dark' in xdg_theme:
                    is_dark = True
            except Exception:
                pass
        elif platform.system() == 'Windows':
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize') as key:
                    apps_use_light_theme = winreg.QueryValueEx(key, 'AppsUseLightTheme')[0]
                    is_dark = not bool(apps_use_light_theme)
            except Exception:
                pass
        elif platform.system() == 'Darwin':
            try:
                import subprocess
                result = subprocess.check_output(['defaults', 'read', '-g', 'AppleInterfaceStyle'], stderr=subprocess.DEVNULL).decode().strip()
                if 'dark' in result.lower():
                    is_dark = True
            except Exception:
                pass
        theme = 'Dark' if is_dark else 'Light'

    # Set palette and stylesheet
    if theme == 'Dark':
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(20, 20, 20))
        dark_palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(dark_palette)
        app.setStyleSheet('QToolTip { color: #ffffff; background-color: #2a2a2a; border: 1px solid white; }')
        icon_color = 'white'
    else:
        app.setPalette(QPalette())
        app.setStyleSheet('')
        icon_color = 'black'

    # Change icon color for single-color icons
    icons_dir = os.path.join(os.path.dirname(__file__), 'images', 'icons')
    def recolor_icon(svg_path, color):
        # Only recolor if it's a single-color SVG
        try:
            with open(svg_path, 'r') as f:
                svg = f.read()
            import re
            svg = re.sub(r'fill="#?[A-Fa-f0-9]{3,6}"', f'fill="{color}"', svg)
            temp_path = svg_path + f'.{color}.svg'
            with open(temp_path, 'w') as f:
                f.write(svg)
            return temp_path
        except Exception:
            return svg_path
    # Set icons
    color_hex = '#ffffff' if icon_color == 'white' else '#000000'
    window.ui.play.setIcon(QIcon(recolor_icon(os.path.join(icons_dir, 'play_arrow_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg'), color_hex)))
    window.ui.prev.setIcon(QIcon(recolor_icon(os.path.join(icons_dir, 'skip_previous_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg'), color_hex)))
    window.ui.next.setIcon(QIcon(recolor_icon(os.path.join(icons_dir, 'skip_next_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg'), color_hex)))
    window.ui.fullscreen.setIcon(QIcon(recolor_icon(os.path.join(icons_dir, 'fullscreen_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg'), color_hex)))
    window.ui.audio.setIcon(QIcon(recolor_icon(os.path.join(icons_dir, 'music_note_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg'), color_hex)))
    window.ui.sub.setIcon(QIcon(recolor_icon(os.path.join(icons_dir, 'subtitles_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg'), color_hex)))
    window.ui.menu.setIcon(QIcon(recolor_icon(os.path.join(icons_dir, 'format_list_bulleted_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg'), color_hex)))


if __name__ == '__main__':
    app = QApplication()
    window = MainWindow()

    screenshot_path = ''

    if os.name == 'nt':
        if platform.release() != '11':
            app.setStyle('windows11')
    else:
        import locale

        locale.setlocale(locale.LC_NUMERIC, 'C')

    mpv: MPV = MPV(wid=window.ui.video.winId(), keep_open=True, profile='gpu-hq', ytdl=True, terminal='yes')

    apply_theme()  # Apply theme on startup

    window.show()
    player = Player()
    player.start_player(sys.argv)

    # --- Ensure skip button is positioned correctly at startup ---
    def initial_skip_button_update():
        try:
            window.ui.video_frame_width = mpv.width
            window.ui.video_frame_height = mpv.height
            if hasattr(window.ui, 'video_container') and hasattr(window.ui.video_container, 'update_skip_button'):
                window.ui.video_container.update_skip_button()
        except Exception:
            pass
    QTimer.singleShot(100, initial_skip_button_update)

    sys.exit(app.exec())
