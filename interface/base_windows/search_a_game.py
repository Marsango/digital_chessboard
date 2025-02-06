# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'search_a_game.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpinBox, QTabWidget,
    QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(388, 434)
        Form.setMaximumSize(QSize(388, 16777215))
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(Form)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setEnabled(True)
        self.tabWidget.setMaximumSize(QSize(370, 16777215))
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.North)
        self.tabWidget.setTabShape(QTabWidget.TabShape.Rounded)
        self.ai_tab = QWidget()
        self.ai_tab.setObjectName(u"ai_tab")
        self.verticalLayout_6 = QVBoxLayout(self.ai_tab)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.frame_13 = QFrame(self.ai_tab)
        self.frame_13.setObjectName(u"frame_13")
        self.frame_13.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_13.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.frame_13)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.frame = QFrame(self.frame_13)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.label)

        self.spin_minutes_ai = QSpinBox(self.frame)
        self.spin_minutes_ai.setObjectName(u"spin_minutes_ai")
        self.spin_minutes_ai.setMinimum(1)
        self.spin_minutes_ai.setMaximum(180)

        self.verticalLayout_2.addWidget(self.spin_minutes_ai)


        self.horizontalLayout_5.addWidget(self.frame)

        self.frame_2 = QFrame(self.frame_13)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_2 = QLabel(self.frame_2)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_2)

        self.spin_increments_ai = QSpinBox(self.frame_2)
        self.spin_increments_ai.setObjectName(u"spin_increments_ai")
        self.spin_increments_ai.setMaximum(60)

        self.verticalLayout_3.addWidget(self.spin_increments_ai)


        self.horizontalLayout_5.addWidget(self.frame_2)


        self.verticalLayout_6.addWidget(self.frame_13)

        self.frame_5 = QFrame(self.ai_tab)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.frame_5)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.label_4 = QLabel(self.frame_5)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_5.addWidget(self.label_4)

        self.frame_6 = QFrame(self.frame_5)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.random_color_ai = QPushButton(self.frame_6)
        self.random_color_ai.setObjectName(u"random_color_ai")
        self.random_color_ai.setCheckable(True)
        self.random_color_ai.setChecked(True)

        self.horizontalLayout_2.addWidget(self.random_color_ai)

        self.white_color_ai = QPushButton(self.frame_6)
        self.white_color_ai.setObjectName(u"white_color_ai")
        self.white_color_ai.setCheckable(True)

        self.horizontalLayout_2.addWidget(self.white_color_ai)

        self.black_color_ai = QPushButton(self.frame_6)
        self.black_color_ai.setObjectName(u"black_color_ai")
        self.black_color_ai.setCheckable(True)
        self.black_color_ai.setChecked(False)

        self.horizontalLayout_2.addWidget(self.black_color_ai)


        self.verticalLayout_5.addWidget(self.frame_6)


        self.verticalLayout_6.addWidget(self.frame_5)

        self.frame_4 = QFrame(self.ai_tab)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_4)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_3 = QLabel(self.frame_4)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_4.addWidget(self.label_3)

        self.frame_3 = QFrame(self.frame_4)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.strenght_1 = QPushButton(self.frame_3)
        self.strenght_1.setObjectName(u"strenght_1")
        self.strenght_1.setCheckable(True)
        self.strenght_1.setChecked(True)

        self.horizontalLayout.addWidget(self.strenght_1)

        self.strenght_2 = QPushButton(self.frame_3)
        self.strenght_2.setObjectName(u"strenght_2")
        self.strenght_2.setCheckable(True)

        self.horizontalLayout.addWidget(self.strenght_2)

        self.strenght_3 = QPushButton(self.frame_3)
        self.strenght_3.setObjectName(u"strenght_3")
        self.strenght_3.setCheckable(True)

        self.horizontalLayout.addWidget(self.strenght_3)

        self.strenght_4 = QPushButton(self.frame_3)
        self.strenght_4.setObjectName(u"strenght_4")
        self.strenght_4.setCheckable(True)

        self.horizontalLayout.addWidget(self.strenght_4)

        self.strenght_5 = QPushButton(self.frame_3)
        self.strenght_5.setObjectName(u"strenght_5")
        self.strenght_5.setCheckable(True)

        self.horizontalLayout.addWidget(self.strenght_5)

        self.strenght_6 = QPushButton(self.frame_3)
        self.strenght_6.setObjectName(u"strenght_6")
        self.strenght_6.setCheckable(True)

        self.horizontalLayout.addWidget(self.strenght_6)

        self.strenght_7 = QPushButton(self.frame_3)
        self.strenght_7.setObjectName(u"strenght_7")
        self.strenght_7.setCheckable(True)

        self.horizontalLayout.addWidget(self.strenght_7)

        self.strenght_8 = QPushButton(self.frame_3)
        self.strenght_8.setObjectName(u"strenght_8")
        self.strenght_8.setCheckable(True)

        self.horizontalLayout.addWidget(self.strenght_8)


        self.verticalLayout_4.addWidget(self.frame_3)


        self.verticalLayout_6.addWidget(self.frame_4)

        self.queue_ai = QPushButton(self.ai_tab)
        self.queue_ai.setObjectName(u"queue_ai")

        self.verticalLayout_6.addWidget(self.queue_ai)

        self.tabWidget.addTab(self.ai_tab, "")
        self.player_tab = QWidget()
        self.player_tab.setObjectName(u"player_tab")
        self.verticalLayout_11 = QVBoxLayout(self.player_tab)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.frame_14 = QFrame(self.player_tab)
        self.frame_14.setObjectName(u"frame_14")
        self.frame_14.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_14.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.frame_14)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.frame_7 = QFrame(self.frame_14)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_7.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_7 = QVBoxLayout(self.frame_7)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.label_5 = QLabel(self.frame_7)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_7.addWidget(self.label_5)

        self.spin_minutes_player = QSpinBox(self.frame_7)
        self.spin_minutes_player.setObjectName(u"spin_minutes_player")
        self.spin_minutes_player.setMinimum(10)
        self.spin_minutes_player.setMaximum(180)

        self.verticalLayout_7.addWidget(self.spin_minutes_player)


        self.horizontalLayout_6.addWidget(self.frame_7)

        self.frame_8 = QFrame(self.frame_14)
        self.frame_8.setObjectName(u"frame_8")
        self.frame_8.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_8.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_8 = QVBoxLayout(self.frame_8)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.label_6 = QLabel(self.frame_8)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_8.addWidget(self.label_6)

        self.spin_increments_player = QSpinBox(self.frame_8)
        self.spin_increments_player.setObjectName(u"spin_increments_player")
        self.spin_increments_player.setMaximum(60)

        self.verticalLayout_8.addWidget(self.spin_increments_player)


        self.horizontalLayout_6.addWidget(self.frame_8)


        self.verticalLayout_11.addWidget(self.frame_14)

        self.frame_9 = QFrame(self.player_tab)
        self.frame_9.setObjectName(u"frame_9")
        self.frame_9.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_9.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_9 = QVBoxLayout(self.frame_9)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.label_7 = QLabel(self.frame_9)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_9.addWidget(self.label_7)

        self.frame_10 = QFrame(self.frame_9)
        self.frame_10.setObjectName(u"frame_10")
        self.frame_10.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_10.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_10)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.yes_rated = QPushButton(self.frame_10)
        self.yes_rated.setObjectName(u"yes_rated")
        self.yes_rated.setCheckable(True)
        self.yes_rated.setChecked(True)

        self.horizontalLayout_3.addWidget(self.yes_rated)

        self.no_rated = QPushButton(self.frame_10)
        self.no_rated.setObjectName(u"no_rated")
        self.no_rated.setCheckable(True)

        self.horizontalLayout_3.addWidget(self.no_rated)


        self.verticalLayout_9.addWidget(self.frame_10)


        self.verticalLayout_11.addWidget(self.frame_9)

        self.frame_11 = QFrame(self.player_tab)
        self.frame_11.setObjectName(u"frame_11")
        self.frame_11.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_11.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_10 = QVBoxLayout(self.frame_11)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.label_8 = QLabel(self.frame_11)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_10.addWidget(self.label_8)

        self.frame_12 = QFrame(self.frame_11)
        self.frame_12.setObjectName(u"frame_12")
        self.frame_12.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_12.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frame_12)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.random_color_player = QPushButton(self.frame_12)
        self.random_color_player.setObjectName(u"random_color_player")
        self.random_color_player.setCheckable(True)

        self.horizontalLayout_4.addWidget(self.random_color_player)

        self.white_color_player = QPushButton(self.frame_12)
        self.white_color_player.setObjectName(u"white_color_player")
        self.white_color_player.setCheckable(True)

        self.horizontalLayout_4.addWidget(self.white_color_player)

        self.black_color_player = QPushButton(self.frame_12)
        self.black_color_player.setObjectName(u"black_color_player")
        self.black_color_player.setCheckable(True)

        self.horizontalLayout_4.addWidget(self.black_color_player)


        self.verticalLayout_10.addWidget(self.frame_12)


        self.verticalLayout_11.addWidget(self.frame_11)

        self.frame_15 = QFrame(self.player_tab)
        self.frame_15.setObjectName(u"frame_15")
        self.frame_15.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_15.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_15)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.queue_player = QPushButton(self.frame_15)
        self.queue_player.setObjectName(u"queue_player")

        self.horizontalLayout_7.addWidget(self.queue_player)

        self.cancel_queue = QPushButton(self.frame_15)
        self.cancel_queue.setObjectName(u"cancel_queue")

        self.horizontalLayout_7.addWidget(self.cancel_queue)


        self.verticalLayout_11.addWidget(self.frame_15)

        self.wait_time = QLabel(self.player_tab)
        self.wait_time.setObjectName(u"wait_time")
        self.wait_time.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_11.addWidget(self.wait_time)

        self.tabWidget.addTab(self.player_tab, "")

        self.verticalLayout.addWidget(self.tabWidget)


        self.retranslateUi(Form)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form", u"Minutes per side", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Increments per side", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Color", None))
        self.random_color_ai.setText(QCoreApplication.translate("Form", u"Random", None))
        self.white_color_ai.setText(QCoreApplication.translate("Form", u"White", None))
        self.black_color_ai.setText(QCoreApplication.translate("Form", u"Black", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Strenght", None))
        self.strenght_1.setText(QCoreApplication.translate("Form", u"1", None))
        self.strenght_2.setText(QCoreApplication.translate("Form", u"2", None))
        self.strenght_3.setText(QCoreApplication.translate("Form", u"3", None))
        self.strenght_4.setText(QCoreApplication.translate("Form", u"4", None))
        self.strenght_5.setText(QCoreApplication.translate("Form", u"5", None))
        self.strenght_6.setText(QCoreApplication.translate("Form", u"6", None))
        self.strenght_7.setText(QCoreApplication.translate("Form", u"7", None))
        self.strenght_8.setText(QCoreApplication.translate("Form", u"8", None))
        self.queue_ai.setText(QCoreApplication.translate("Form", u"Create game", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.ai_tab), QCoreApplication.translate("Form", u"vs AI", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"Minutes per side", None))
        self.label_6.setText(QCoreApplication.translate("Form", u"Increments per side", None))
        self.label_7.setText(QCoreApplication.translate("Form", u"Rated", None))
        self.yes_rated.setText(QCoreApplication.translate("Form", u"Yes", None))
        self.no_rated.setText(QCoreApplication.translate("Form", u"No", None))
        self.label_8.setText(QCoreApplication.translate("Form", u"Color", None))
        self.random_color_player.setText(QCoreApplication.translate("Form", u"Random", None))
        self.white_color_player.setText(QCoreApplication.translate("Form", u"White", None))
        self.black_color_player.setText(QCoreApplication.translate("Form", u"Black", None))
        self.queue_player.setText(QCoreApplication.translate("Form", u"Create game", None))
        self.cancel_queue.setText(QCoreApplication.translate("Form", u"Cancel queue", None))
        self.wait_time.setText(QCoreApplication.translate("Form", u"TextLabel", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.player_tab), QCoreApplication.translate("Form", u"vs Player", None))
    # retranslateUi

