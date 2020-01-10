# Hollow 图片（视频）信息隐藏加解密软件 V1.0
# 编程语言：Python 3
from PIL import Image
import sys
import os
import time
import numpy as np
import math
import random
import threading
import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore, QtGui, QtWidgets
import res_rc

# 对图像的红绿蓝三通道合并, 处理变换中的异常像素值，并且输出文件


def output_file(picname, red, green, blue, width, height):
    for i in range(width):
        for j in range(height):
            if red[i, j] > 255:
                red[i, j] = 255
            elif red[i, j] < 0:
                red[i, j] *= -1
    for i in range(width):
        for j in range(height):
            if green[i, j] > 255:
                green[i, j] = 255
            elif green[i, j] < 0:
                green[i, j] *= -1
    for i in range(width):
        for j in range(height):
            if blue[i, j] > 255:
                blue[i, j] = 255
            elif blue[i, j] < 0:
                blue[i, j] *= -1
    red = red.T
    green = green.T
    blue = blue.T
    source = Image.new("RGB", (width, height))
    img = np.array(source)
    img[:, :, 0] = red[:, :]
    img[:, :, 1] = green[:, :]
    img[:, :, 2] = blue[:, :]
    fo = Image.fromarray(img, 'RGB')
    fo.save(picname)

# 进行离散小波变换处理


def dwt(colour, width, height):
    TEMP1 = np.zeros((width, height), int)
    TEMP2 = np.zeros((width, height), int)
    for i in range(width):
        for j in range(height//2):
            tmp = (colour[i, j*2] + colour[i, j * 2 + 1])
            if((tmp < 0 or (tmp == (-1) or tmp // 2 == (-1))) and ((colour[i, j * 2] + colour[i, j * 2+1]) % 2) != 0):
                TEMP1[i, j] = tmp // 2 - 1
            else:
                TEMP1[i, j] = tmp // 2
        ct = height // 2
        for j in range(height//2):
            TEMP1[i, ct] = (colour[i, j * 2] - colour[i, j * 2 + 1])
            ct += 1
    for j in range(height):
        for i in range(width//2):
            tmp = (TEMP1[i * 2, j] + TEMP1[i * 2 + 1, j])
            if ((tmp < 0 or tmp == (-1) or tmp // 2 == (-1)) and ((TEMP1[i * 2, j] + TEMP1[i * 2 + 1, j]) % 2) != 0):
                TEMP2[i, j] = tmp // 2 - 1
            else:
                TEMP2[i, j] = tmp // 2
        ct = width // 2
        for i in range(width//2):
            TEMP2[ct, j] = (TEMP1[i * 2, j] - TEMP1[i * 2 + 1, j])
            ct += 1
    return TEMP2

# 对图片的隐藏信息进行提取


def extract_watermark(TEMP2, width, height, mwidth, mheight, complex, passwd):
    outputwm = np.zeros((mwidth*mheight), int)
    order = np.zeros((mwidth*mheight), int)
    tmp = np.zeros((mwidth*mheight), int)
    k = 5
    position_pixel = 0
    for i in range(width // 2, width):
        for j in range(height // 2, height):
            p = math.fabs(TEMP2[i, j])
            k = p % 10
            outputwm[position_pixel] = p % 10
            p = int(p//10)
            if(p % 2 == 0):
                outputwm[position_pixel] = 9+outputwm[position_pixel]
            outputwm[position_pixel] = math.pow(
                outputwm[position_pixel]+complex[position_pixel], 2)
            if(outputwm[position_pixel] > 255 and(k >= 7 and k < 10)):
                outputwm[position_pixel] = math.pow(
                    k+complex[position_pixel], 2)
            else:
                outputwm[position_pixel] = outputwm[position_pixel]
            position_pixel += 1
            if position_pixel == mwidth*mheight:
                break
        if position_pixel == mwidth*mheight:
            break
    random.seed(passwd)
    for i in range(position_pixel):
        order[i] = i
    random.shuffle(order)
    for i in range(position_pixel):
        tmp[order[i]] = outputwm[i]
    for i in range(position_pixel):
        outputwm[i] = tmp[i]
    return outputwm

# 向图片写入隐藏信息


def hiding_data(TEMP2, filename, flag, writedata, passwd):
    width = TEMP2.shape[0]
    height = TEMP2.shape[1]
    watermark = Image.open(filename)
    if len(watermark.split()) < 3:
        watermark = watermark.convert("RGB")
    mk = watermark.load()
    wm_width, wm_height = watermark.size
    outputwm = np.zeros((wm_width*wm_height), int)
    wm_pixel = np.zeros((wm_width*wm_height), int)
    complex = np.zeros((wm_width*wm_height), float)
    k = 5
    position_pixel = 0
    for i in range(wm_width):
        for j in range(wm_height):
            wm_pixel[position_pixel] = int(mk[i, j][flag])
            position_pixel += 1
    random.seed(passwd)
    random.shuffle(wm_pixel)
    position_pixel = 0
    for i in range(width // 2, width):
        for j in range(height // 2, height):
            a = math.fabs(TEMP2[i, j])
            flag = 1
            if(TEMP2[i, j] < 0):
                flag = -1
            diwm = round(math.sqrt(wm_pixel[position_pixel]))
            complex[position_pixel] = math.sqrt(wm_pixel[position_pixel])-diwm
            if(diwm >= 10):
                g = a - (a % 10)
                p = g//10
                if(p % 2 == 1):
                    g = g-10+(diwm//10) + (diwm % 10)
                else:
                    g = g+(diwm//10) + (diwm % 10)
            else:
                g = a - (a % 10)
                p = g//10
                if(p % 2 == 0):
                    if(g == 240):
                        g = g-20
                    g = g+10+diwm
                else:
                    g = g+diwm
            g = g*flag
            if(writedata):
                TEMP2[i, j] = g
            position_pixel += 1
            if position_pixel == wm_width*wm_height:
                break
        if position_pixel == wm_width*wm_height:
            break
    return complex

# 离散小波反变换


def idwt(TEMP2, pixel, width, height):
    for j in range(height):
        ct = 0
        for i in range(width//2):
            tmp = (TEMP2[i + (width // 2), j]) + 1
            if ((tmp < 0 or tmp == (-1) or tmp // 2 == (-1)) and ((TEMP2[i + (width // 2), j] + 1) % 2) != 0):
                pixel[ct, j] = TEMP2[i, j] + (tmp // 2 - 1)
            else:
                pixel[ct, j] = TEMP2[i, j] + tmp // 2
            pixel[ct + 1, j] = pixel[ct, j] - TEMP2[i + (width // 2), j]
            ct += 2
    for i in range(width):
        ct = 0
        for j in range(height//2):
            tmp = (pixel[i, j + (height // 2)]) + 1
            if ((tmp < 0 or tmp == (-1) or tmp // 2 == (-1)) and((pixel[i, j + (height // 2)] + 1) % 2) != 0):
                TEMP2[i, ct] = pixel[i, j] + (tmp // 2 - 1)
            else:
                TEMP2[i, ct] = pixel[i, j] + tmp // 2
            TEMP2[i, ct + 1] = TEMP2[i, ct] - pixel[i, j + (height // 2)]
            ct += 2

# 重写线程类，使得其能获取计算结果返回值


class MyThread(threading.Thread):
    def __init__(self, func, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None

# 作者信息窗口类


class AuInfo(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(408, 305)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(90, 100, 271, 51))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(80, 160, 251, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setGeometry(QtCore.QRect(10, 200, 391, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(Dialog)
        self.label_5.setGeometry(QtCore.QRect(10, 220, 371, 20))
        self.label_5.setObjectName("label_5")
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(50, 260, 93, 28))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(Dialog)
        self.pushButton_2.setGeometry(QtCore.QRect(250, 260, 93, 28))
        self.pushButton_2.setObjectName("pushButton_2")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(40, -40, 291, 191))
        self.label.setStyleSheet("image:url(:/mark.png)")
        self.label.setText("")
        self.label.setObjectName("label")

        self.retranslateUi(Dialog)
        self.pushButton.clicked.connect(self.openHome)
        self.pushButton_2.clicked.connect(self.openFund)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "关于作者"))
        Dialog.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        Dialog.setWindowIcon(QIcon('icon.png'))
        self.label_2.setText(_translate("Dialog", "作者：Hollow Man"))
        self.label_3.setText(_translate("Dialog", "兰州大学 信息科学与工程学院"))
        self.label_4.setText(_translate(
            "Dialog", "在这里，我需要感谢蔡銘峯（parkmftsai）等人的研究成果，他们的"))
        self.label_5.setText(_translate(
            "Dialog", "论文所述算法是此软件所用图片信息隐藏加密算法的基础。"))
        self.pushButton.setText(_translate("Dialog", "我的网站"))
        self.pushButton_2.setText(_translate("Dialog", "捐助我！"))

    def openHome(self):
        if QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://hollowman6.github.io/")):
            pass

    def openFund(self):
        if QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://hollowman6.github.io/fund.html")):
            pass

# 软件帮助使用说明窗口类


class helpw(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 308)
        Dialog.setFixedSize(400, 308)
        self.textBrowser = QtWidgets.QTextBrowser(Dialog)
        self.textBrowser.setGeometry(QtCore.QRect(10, 10, 381, 241))
        self.textBrowser.setObjectName("textBrowser")
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(160, 260, 93, 28))
        self.pushButton.setObjectName("pushButton")

        self.retranslateUi(Dialog)
        self.pushButton.clicked.connect(Dialog.close)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        Dialog.setWindowIcon(QIcon('icon.png'))
        Dialog.setWindowTitle(_translate("Dialog", "帮助"))
        self.textBrowser.setHtml(_translate("Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                                            "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
                                            "p, li { white-space: pre-wrap; }\n"
                                            "</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:7.8pt; font-weight:400; font-style:normal;\">\n"
                                            "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">· 注意：要隐藏图片尺寸越小，要附加隐藏信息的目标图片尺寸越大，效果越好。在给视频进行隐藏信息处理时，由于视频编码的压缩，效果可能并不是很明显。在加密时请不要使要隐藏图片的宽和高超过要附加隐藏信息的图片宽和高的二分之一。如果你这样做了，虽然不会有任何错误提示，但这会导致在隐藏解密时图片还原的必然失败！</p>\n"
                                            "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"
                                            "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">· 本软件基于蔡銘峯(parkmftsai)等人的研究成果，使用整数小波域变换实现图片信息隐藏功能, 能够抵御一定各种程度的图片压缩以及剪切，添加噪声，旋转等降低图片质量的攻击手段，具有高健壮性，并且加密得到的图片与原图片画质几乎一致看不出区别，适用于版权保护或其它特殊领域需要。</p>\n"
                                            "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
                                            "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">· 在加密时，你需要设定一个加密密码，你还可以选择是否保存图片还原辅助信息，如果选择保存，该信息将会以npy文件扩展名保存，文件名为图片的文件名（不包括扩展名）。如果选择不保存，则在还原图片时，缺少这一信息会导致图片部分细节丢失。如果需要批量加密图片，请在\"要附加隐藏信息的图片（文件夹）\"处选择要处理图片所存放的文件夹。</p>\n"
                                            "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
                                            "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">· 在解密时，你需要选择被附加隐藏信息的图片，如果存在图片还原辅助信息，你可以选择图片还原辅助信息文件或者文件夹，如果你选择的是存放图片还原辅助信息文件文件夹，程序将会自动搜寻该文件夹下和你选择的被附加隐藏信息图片同名的文件，如果不存在则不能（在批量状态下）加载图片还原辅助信息。同时，你需要正确地输入被隐藏图片的宽与高，并且输入正确的解密密码。如果你输入的信息与加密时的不符，将会导致解密的失败，即解密出来的图片为一堆杂乱的像素点。如果需要批量解密图片，请在“被附加隐藏信息的图片（文件夹）”处选择要处理图片所存放的文件夹。</p>\n"
                                            "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
                                            "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">· 对于视频，你可以选择软件提供的视频处理工具，将视频按帧拆解成图片，然后再对图片进行批量信息隐藏加密。视频拆解出来的图片默认保存为png格式,同时自动显示视频帧率fps，方便再次合成。完成后，你可以对保存的文件夹下的图片进行信息隐藏加密（注意不要改动拆解的原始图片名称，并且在后续加密和合成视频过程中再次使用此文件夹，方便合成视频），此时需要输入原视频的视频帧率（如果软件在拆解视频时已经帮你填好则可以不变），选择图片存放的文件夹（注意不要改动图片加密后的名称）重新合成原视频。默认保存为avi格式，XviD编码。对于视频的隐藏还原，同理，将视频按帧拆解成图片，然后"
                                            "可以从中随机挑选一张或者更多的图片解密来进行视频的加密隐藏信息的获取。</p>\n"
                                            "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.pushButton.setText(_translate("Dialog", "关闭"))

# 设定线程最大值窗口类


class ThrNum(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(333, 208)
        Dialog.setFixedSize(333, 208)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(120, 20, 211, 16))
        self.label.setObjectName("label")
        self.lineEdit = QtWidgets.QLineEdit(Dialog)
        self.lineEdit.setGeometry(QtCore.QRect(70, 50, 201, 21))
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setText(str(threadNum))
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(70, 90, 93, 28))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(Dialog)
        self.pushButton_2.setGeometry(QtCore.QRect(180, 90, 93, 28))
        self.pushButton_2.setObjectName("pushButton_2")
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setGeometry(QtCore.QRect(20, 130, 391, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(Dialog)
        self.label_5.setGeometry(QtCore.QRect(90, 140, 421, 21))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(Dialog)
        self.label_6.setGeometry(QtCore.QRect(70, 170, 421, 21))
        self.label_6.setObjectName("label_6")

        self.retranslateUi(Dialog)
        self.pushButton.clicked.connect(lambda: self.setThr(Dialog))
        self.pushButton_2.clicked.connect(Dialog.close)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def setThr(self, Dialog):
        try:
            temp = int(self.lineEdit.text())
            if temp > 0:
                threadNum = temp
                threadmax = threading.BoundedSemaphore(threadNum)
                Dialog.close()
            else:
                QMessageBox.critical(Dialog, "线程设定错误", "请输入一个正整数！")
        except Exception:
            QMessageBox.critical(Dialog, "线程设定错误", "请输入一个正整数！")

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        Dialog.setWindowIcon(QIcon('icon.png'))
        Dialog.setWindowTitle(_translate("Dialog", "设定线程数"))
        self.label.setText(_translate("Dialog", "最大线程数："))
        self.pushButton.setText(_translate("Dialog", "确认"))
        self.pushButton_2.setText(_translate("Dialog", "取消"))
        self.label_4.setText(_translate("Dialog", "注意："))
        self.label_5.setText(_translate("Dialog", "仅在批量处理图片时有效！"))
        self.label_6.setText(_translate("Dialog", "请按电脑实际性能设置，以免死机！"))

# 程序主界面窗口类


class Ui_MainWindow(QtCore.QObject):
    signal = QtCore.pyqtSignal(str)
    progressChanged = QtCore.pyqtSignal(int)
    progressChanged2 = QtCore.pyqtSignal(int)
    progressChanged3 = QtCore.pyqtSignal(int)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(651, 438)
        MainWindow.setFixedSize(651, 438)
        self.cwd = os.getcwd()
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStatusTip("已处理文件："+str(countw)+"个")
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 651, 411))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.lineEdit = QtWidgets.QLineEdit(self.tab)
        self.lineEdit.setGeometry(QtCore.QRect(10, 50, 491, 21))
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setClearButtonEnabled(True)
        self.checkBox = QtWidgets.QCheckBox(self.tab)
        self.checkBox.setGeometry(QtCore.QRect(10, 250, 161, 20))
        self.checkBox.setChecked(True)
        self.checkBox.setObjectName("checkBox")
        self.pushButton = QtWidgets.QPushButton(self.tab)
        self.pushButton.setGeometry(QtCore.QRect(540, 30, 93, 28))
        self.pushButton.setObjectName("pushButton")
        self.label = QtWidgets.QLabel(self.tab)
        self.label.setGeometry(QtCore.QRect(10, 20, 211, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.tab)
        self.label_2.setGeometry(QtCore.QRect(10, 100, 91, 16))
        self.label_2.setObjectName("label_2")
        self.lineEdit_2 = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_2.setGeometry(QtCore.QRect(10, 130, 491, 21))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.lineEdit_2.setClearButtonEnabled(True)
        self.pushButton_2 = QtWidgets.QPushButton(self.tab)
        self.pushButton_2.setGeometry(QtCore.QRect(540, 130, 93, 28))
        self.pushButton_2.setObjectName("pushButton_2")
        self.lineEdit_3 = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_3.setGeometry(QtCore.QRect(10, 210, 151, 21))
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.lineEdit_3.setClearButtonEnabled(True)
        self.label_3 = QtWidgets.QLabel(self.tab)
        self.label_3.setGeometry(QtCore.QRect(10, 180, 61, 16))
        self.label_3.setObjectName("label_3")
        self.pushButton_3 = QtWidgets.QPushButton(self.tab)
        self.pushButton_3.setGeometry(QtCore.QRect(360, 200, 141, 61))
        self.pushButton_3.setObjectName("pushButton_3")
        self.progressBar = QtWidgets.QProgressBar(self.tab)
        self.progressBar.setGeometry(QtCore.QRect(10, 310, 621, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.label_11 = QtWidgets.QLabel(self.tab)
        self.label_11.setGeometry(QtCore.QRect(260, 280, 81, 16))
        self.label_11.setText("")
        self.label_11.setObjectName("label_11")
        self.pushButton_10 = QtWidgets.QPushButton(self.tab)
        self.pushButton_10.setGeometry(QtCore.QRect(540, 60, 93, 28))
        self.pushButton_10.setObjectName("pushButton_10")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.label_4 = QtWidgets.QLabel(self.tab_2)
        self.label_4.setGeometry(QtCore.QRect(10, 20, 241, 16))
        self.label_4.setObjectName("label_4")
        self.lineEdit_4 = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_4.setGeometry(QtCore.QRect(10, 50, 491, 21))
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.lineEdit_4.setClearButtonEnabled(True)
        self.pushButton_4 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_4.setGeometry(QtCore.QRect(540, 60, 93, 28))
        self.pushButton_4.setObjectName("pushButton_4")
        self.label_5 = QtWidgets.QLabel(self.tab_2)
        self.label_5.setGeometry(QtCore.QRect(200, 180, 91, 16))
        self.label_5.setObjectName("label_5")
        self.lineEdit_5 = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_5.setGeometry(QtCore.QRect(200, 200, 91, 21))
        self.lineEdit_5.setObjectName("lineEdit_5")
        self.lineEdit_5.setClearButtonEnabled(True)
        self.label_6 = QtWidgets.QLabel(self.tab_2)
        self.label_6.setGeometry(QtCore.QRect(200, 230, 91, 16))
        self.label_6.setObjectName("label_6")
        self.lineEdit_6 = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_6.setGeometry(QtCore.QRect(200, 250, 91, 21))
        self.lineEdit_6.setObjectName("lineEdit_6")
        self.lineEdit_6.setClearButtonEnabled(True)
        self.label_7 = QtWidgets.QLabel(self.tab_2)
        self.label_7.setGeometry(QtCore.QRect(10, 180, 101, 16))
        self.label_7.setObjectName("label_7")
        self.lineEdit_7 = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_7.setGeometry(QtCore.QRect(10, 210, 151, 21))
        self.lineEdit_7.setObjectName("lineEdit_7")
        self.lineEdit_7.setClearButtonEnabled(True)
        self.checkBox_2 = QtWidgets.QCheckBox(self.tab_2)
        self.checkBox_2.setGeometry(QtCore.QRect(10, 250, 161, 20))
        self.checkBox_2.setChecked(True)
        self.checkBox_2.setObjectName("checkBox_2")
        self.pushButton_5 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_5.setGeometry(QtCore.QRect(360, 200, 141, 61))
        self.pushButton_5.setObjectName("pushButton_5")
        self.label_8 = QtWidgets.QLabel(self.tab_2)
        self.label_8.setGeometry(QtCore.QRect(10, 100, 181, 16))
        self.label_8.setObjectName("label_8")
        self.lineEdit_8 = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_8.setGeometry(QtCore.QRect(10, 130, 491, 21))
        self.lineEdit_8.setObjectName("lineEdit_8")
        self.lineEdit_8.setClearButtonEnabled(True)
        self.progressBar_2 = QtWidgets.QProgressBar(self.tab_2)
        self.progressBar_2.setGeometry(QtCore.QRect(10, 310, 621, 23))
        self.progressBar_2.setProperty("value", 0)
        self.progressBar_2.setObjectName("progressBar_2")
        self.label_12 = QtWidgets.QLabel(self.tab_2)
        self.label_12.setGeometry(QtCore.QRect(260, 280, 81, 16))
        self.label_12.setText("")
        self.label_12.setObjectName("label_12")
        self.pushButton_11 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_11.setGeometry(QtCore.QRect(540, 30, 93, 28))
        self.pushButton_11.setObjectName("pushButton_11")
        self.pushButton_12 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_12.setGeometry(QtCore.QRect(540, 110, 93, 28))
        self.pushButton_12.setObjectName("pushButton_12")
        self.pushButton_6 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_6.setGeometry(QtCore.QRect(540, 140, 93, 28))
        self.pushButton_6.setObjectName("pushButton_6")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.label_9 = QtWidgets.QLabel(self.tab_3)
        self.label_9.setGeometry(QtCore.QRect(10, 20, 241, 16))
        self.label_9.setObjectName("label_9")
        self.label_10 = QtWidgets.QLabel(self.tab_3)
        self.label_10.setGeometry(QtCore.QRect(10, 100, 250, 16))
        self.label_10.setObjectName("label_10")
        self.lineEdit_9 = QtWidgets.QLineEdit(self.tab_3)
        self.lineEdit_9.setGeometry(QtCore.QRect(10, 50, 491, 21))
        self.lineEdit_9.setObjectName("lineEdit_9")
        self.lineEdit_9.setClearButtonEnabled(True)
        self.pushButton_7 = QtWidgets.QPushButton(self.tab_3)
        self.pushButton_7.setGeometry(QtCore.QRect(540, 50, 93, 28))
        self.pushButton_7.setObjectName("pushButton_7")
        self.lineEdit_10 = QtWidgets.QLineEdit(self.tab_3)
        self.lineEdit_10.setGeometry(QtCore.QRect(10, 130, 491, 21))
        self.lineEdit_10.setObjectName("lineEdit_10")
        self.lineEdit_10.setClearButtonEnabled(True)
        self.pushButton_8 = QtWidgets.QPushButton(self.tab_3)
        self.pushButton_8.setGeometry(QtCore.QRect(540, 130, 93, 28))
        self.pushButton_8.setObjectName("pushButton_8")
        self.pushButton_9 = QtWidgets.QPushButton(self.tab_3)
        self.pushButton_9.setGeometry(QtCore.QRect(360, 200, 141, 61))
        self.pushButton_9.setObjectName("pushButton_9")
        self.progressBar_3 = QtWidgets.QProgressBar(self.tab_3)
        self.progressBar_3.setGeometry(QtCore.QRect(10, 310, 621, 23))
        self.progressBar_3.setProperty("value", 0)
        self.progressBar_3.setObjectName("progressBar_3")
        self.radioButton = QtWidgets.QRadioButton(self.tab_3)
        self.radioButton.setGeometry(QtCore.QRect(10, 200, 95, 20))
        self.radioButton.setChecked(True)
        self.radioButton.setObjectName("radioButton")
        self.radioButton_2 = QtWidgets.QRadioButton(self.tab_3)
        self.radioButton_2.setGeometry(QtCore.QRect(10, 240, 95, 20))
        self.radioButton_2.setObjectName("radioButton_2")
        self.label_13 = QtWidgets.QLabel(self.tab_3)
        self.label_13.setGeometry(QtCore.QRect(180, 200, 101, 16))
        self.label_13.setObjectName("label_13")
        self.lineEdit_11 = QtWidgets.QLineEdit(self.tab_3)
        self.lineEdit_11.setGeometry(QtCore.QRect(180, 230, 101, 21))
        self.lineEdit_11.setObjectName("lineEdit_11")
        self.lineEdit_11.setClearButtonEnabled(True)
        self.tabWidget.addTab(self.tab_3, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 651, 26))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menu)
        self.menu_2.setObjectName("menu_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action_3 = QtWidgets.QAction(MainWindow)
        self.action_3.setObjectName("action_3")
        self.action_4 = QtWidgets.QAction(MainWindow)
        self.action_4.setObjectName("action_4")
        self.action_5 = QtWidgets.QAction(MainWindow)
        self.action_5.setObjectName("action_5")
        self.action_6 = QtWidgets.QAction(MainWindow)
        self.action_6.setObjectName("action_6")
        self.action_7 = QtWidgets.QAction(MainWindow)
        self.action_7.setObjectName("action_7")
        self.label_14 = QtWidgets.QLabel(self.tab_3)
        self.label_14.setGeometry(QtCore.QRect(260, 280, 81, 16))
        self.label_14.setText("")
        self.label_14.setObjectName("label_14")
        self.menu_2.addAction(self.action_4)
        self.menu_2.addAction(self.action_6)
        self.menu_2.addAction(self.action_5)
        self.menu.addAction(self.menu_2.menuAction())
        self.menu.addAction(self.action_7)
        self.menu.addAction(self.action_3)
        self.menubar.addAction(self.menu.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        self.checkBox_2.stateChanged.connect(self.setState)
        self.radioButton.toggled.connect(self.btnstate)
        self.radioButton_2.toggled.connect(self.btnstate1)
        self.pushButton.clicked.connect(self.showPicCho2)
        self.pushButton_2.clicked.connect(self.showPicCho3)
        self.pushButton_3.clicked.connect(self.beginencrypt)
        self.pushButton_4.clicked.connect(self.showDirCho1)
        self.pushButton_5.clicked.connect(self.begindecrypt)
        self.pushButton_6.clicked.connect(self.showDirCho2)
        self.pushButton_7.clicked.connect(self.showMovCho1)
        self.pushButton_8.clicked.connect(self.showDirCho4)
        self.pushButton_9.clicked.connect(self.beginvihand)
        self.pushButton_10.clicked.connect(self.showDirCho3)
        self.pushButton_11.clicked.connect(self.showPicCho1)
        self.pushButton_12.clicked.connect(self.showFileCho1)
        self.action_3.triggered.connect(MainWindow.close)
        self.action_4.triggered.connect(self.openWeb)
        self.signal.connect(self.wrongd)
        self.progressChanged.connect(self.progressBar.setValue)
        self.progressChanged2.connect(self.progressBar_2.setValue)
        self.progressChanged3.connect(self.progressBar_3.setValue)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def beginencrypt(self):
        self.progressChanged.emit(0)
        if self.lineEdit_3.text() == "":
            QMessageBox.information(MainWindow, '加密密码', '请输入加密密码！')
            return
        if self.lineEdit.text() == "":
            QMessageBox.information(MainWindow, '选择', '请选择要附加隐藏信息的图片或文件夹！')
            return
        if self.lineEdit_2.text() == "":
            QMessageBox.information(MainWindow, '选择', '请选择要隐藏的图片！')
            return
        if not os.path.exists(self.lineEdit.text()):
            QMessageBox.critical(MainWindow, "文件或文件夹不存在",
                                 "你输入的要附加隐藏信息的图片或文件夹不存在！请重新选择！")
            return
        if not os.path.exists(self.lineEdit_2.text()):
            QMessageBox.critical(MainWindow, "文件不存在", "你输入的要隐藏的图片不存在！请重新选择！")
            return
        if not os.path.isfile(self.lineEdit_2.text()):
            QMessageBox.critical(MainWindow, "请选择一个文件",
                                 "请为要隐藏的图片选择一个图片文件而不是文件夹！")
            return
        self.label_11.setText("请稍后···")
        self.pushButton_3.setEnabled(False)
        self.tab_2.setEnabled(False)
        self.tab_3.setEnabled(False)
        t = threading.Thread(target=self.Thren, args=(self.lineEdit.text(
        ), self.lineEdit_2.text(), self.lineEdit_3.text(), self.checkBox.isChecked()))
        t.setDaemon(True)
        t.start()

    def begindecrypt(self):
        self.progressChanged2.emit(0)
        if self.lineEdit_7.text() == "":
            QMessageBox.information(MainWindow, '解密密码', '请输入解密密码！')
            return
        if self.lineEdit_5.text() == "":
            QMessageBox.information(MainWindow, '被隐藏图片宽', '请输入被隐藏图片宽度！')
            return
        if self.lineEdit_6.text() == "":
            QMessageBox.information(MainWindow, '被隐藏图片高', '请输入被隐藏图片高度！')
            return
        if self.lineEdit_4.text() == "":
            QMessageBox.information(MainWindow, '选择', '请选择被附加隐藏信息的图片或文件夹：')
            return
        if self.checkBox_2.isChecked() and self.lineEdit_8.text() == "":
            QMessageBox.information(MainWindow, '选择', '请选择图片还原辅助信息文件或文件夹！')
            return
        if not os.path.exists(self.lineEdit_4.text()):
            QMessageBox.critical(MainWindow, "文件或文件夹不存在",
                                 "被附加隐藏信息的图片或文件夹不存在！请重新选择！")
            return
        if self.checkBox_2.isChecked() and not os.path.exists(self.lineEdit_8.text()):
            QMessageBox.critical(MainWindow, "文件或文件夹不存在",
                                 "图片还原辅助信息文件或文件夹不存在！请重新选择！")
            return
        try:
            temp = int(self.lineEdit_5.text())
            if temp > 0:
                pass
            else:
                QMessageBox.critical(MainWindow, "被隐藏图片宽", "请为被隐藏图片宽度输入一个正整数！")
                return
        except Exception:
            QMessageBox.critical(MainWindow, "被隐藏图片宽", "请为被隐藏图片宽度输入一个正整数！")
            return
        try:
            temp = int(self.lineEdit_6.text())
            if temp > 0:
                pass
            else:
                QMessageBox.critical(MainWindow, "被隐藏图片宽", "请为被隐藏图片高度输入一个正整数！")
                return
        except Exception:
            QMessageBox.critical(MainWindow, "被隐藏图片宽", "请为被隐藏图片高度输入一个正整数！")
            return
        self.label_12.setText("请稍后···")
        self.pushButton_5.setEnabled(False)
        self.tab.setEnabled(False)
        self.tab_3.setEnabled(False)
        t = threading.Thread(target=self.Thrde, args=(self.lineEdit_4.text(), self.lineEdit_5.text(
        ), self.lineEdit_6.text(), self.lineEdit_7.text(), self.checkBox_2.isChecked(), self.lineEdit_8.text()))
        t.setDaemon(True)
        t.start()

    def beginvihand(self):
        self.progressChanged3.emit(0)
        if self.radioButton.isChecked():
            if self.lineEdit_9.text() == "":
                QMessageBox.information(MainWindow, '视频文件', '请输入视频文件！')
                return
            if self.lineEdit_10.text() == "":
                QMessageBox.information(MainWindow, '选择文件夹', '请选择拆解的图片保存文件夹！')
                return
            if not os.path.exists(self.lineEdit_9.text()):
                QMessageBox.critical(
                    MainWindow, "文件或文件夹不存在", "你输入的视频文件不存在！请重新选择！")
                return
            if not os.path.isfile(self.lineEdit_9.text()):
                QMessageBox.critical(MainWindow, '选择文件', '请输入视频文件而并非一个文件夹！')
                return
            if not os.path.exists(self.lineEdit_10.text()):
                QMessageBox.critical(
                    MainWindow, "文件或文件夹不存在", "你输入的拆解图片保存文件夹不存在！请重新选择！")
                return
            if os.path.isfile(self.lineEdit_10.text()):
                QMessageBox.critical(MainWindow, "选择文件夹",
                                     "请输入拆解图片保存文件夹而并非一个文件！")
                return
            self.label_14.setText("请稍后···")
            self.pushButton_9.setEnabled(False)
            self.tab_2.setEnabled(False)
            self.tab.setEnabled(False)
            t = threading.Thread(target=self.video2pic, args=(
                self.lineEdit_9.text(), self.lineEdit_10.text()))
            t.setDaemon(True)
            t.start()
        elif self.radioButton_2.isChecked():
            if self.lineEdit_9.text() == "":
                QMessageBox.information(
                    MainWindow, '选择文件夹', '请选择要保存生成视频文件的目标文件夹')
                return
            if self.lineEdit_10.text() == "":
                QMessageBox.information(
                    MainWindow, '选择文件夹', '请选择要合成的图片所在的文件夹！')
                return
            if not os.path.exists(self.lineEdit_9.text()):
                QMessageBox.critical(
                    MainWindow, "文件或文件夹不存在", "你输入的要保存生成视频文件的目标文件夹不存在！请重新选择！")
                return
            if os.path.isfile(self.lineEdit_9.text()):
                QMessageBox.critical(MainWindow, "选择文件夹",
                                     "请输入要保存生成视频文件的目标文件夹而并非一个文件！")
                return
            if not os.path.exists(self.lineEdit_10.text()):
                QMessageBox.critical(
                    MainWindow, "文件或文件夹不存在", "你输入的要合成的图片所在的文件夹不存在！请重新选择！")
                return
            if os.path.isfile(self.lineEdit_10.text()):
                QMessageBox.critical(MainWindow, "选择文件夹",
                                     "请输入要合成的图片所在的文件夹而并非一个文件！")
                return
            try:
                temp = float(self.lineEdit_11.text())
                if temp > 0:
                    pass
                else:
                    QMessageBox.critical(
                        MainWindow, "被隐藏图片宽", "请为视频帧率（fps）输入一个正整数！")
                    return
            except Exception:
                QMessageBox.critical(MainWindow, "被隐藏图片宽",
                                     "请为视频帧率（fps）输入一个正整数！")
                return
            self.label_14.setText("请稍后···")
            self.pushButton_9.setEnabled(False)
            self.tab_2.setEnabled(False)
            self.tab.setEnabled(False)
            t = threading.Thread(target=self.pic2video, args=(
                self.lineEdit_9.text(), self.lineEdit_10.text(), float(self.lineEdit_11.text())))
            t.setDaemon(True)
            t.start()

    def Thren(self, hidepath, markpath, passwd, info):
        flist = []
        if os.path.isfile(hidepath):
            flist.append(hidepath)
        else:
            listl = os.listdir(hidepath)
            for i in range(len(listl)):
                path = os.path.join(hidepath, listl[i])
                if os.path.isfile(path):
                    flist.append(path)
        l = []
        for i in flist:
            filepath, tempfilename = os.path.split(i)
            savefile = os.path.join(
                filepath, "ec"+os.path.splitext(tempfilename)[0]+".png")
            threadmax.acquire()
            t = threading.Thread(target=self.encrypt, args=(
                i, os.path.abspath(markpath), savefile, passwd, info))
            t.setDaemon(True)
            t.start()
            l.append(t)
        for t in l:
            t.join()
        self.label_11.setText("")
        self.pushButton_3.setEnabled(True)
        self.tab_2.setEnabled(True)
        self.tab_3.setEnabled(True)

    def Thrde(self, entimage, mwidth, mheight, passwd, NKey, keyfile):
        flist = []
        if os.path.isfile(entimage):
            flist.append(entimage)
        else:
            listl = os.listdir(entimage)
            for i in range(len(listl)):
                path = os.path.join(entimage, listl[i])
                if os.path.isfile(path) and os.path.splitext(path)[1] != '.npy':
                    flist.append(path)
        l = []
        for i in flist:
            filepath, tempfilename = os.path.split(i)
            realfile = ""
            if NKey == True:
                if not os.path.isfile(keyfile) and os.path.isfile(os.path.abspath(keyfile)+"/"+os.path.splitext(tempfilename)[0]+'.npy'):
                    realfile = os.path.abspath(
                        keyfile)+"/"+os.path.splitext(tempfilename)[0]+'.npy'
                elif os.path.isfile(keyfile):
                    realfile = os.path.abspath(keyfile)
                else:
                    self.signal.emit("在指定文件夹中无法找到"+tempfilename +
                                     "的图片还原辅助信息，请确保指定文件夹下存在"+os.path.splitext(tempfilename)[0]+'.npy文件！')
                    continue
            savefile = os.path.join(
                filepath, "de"+os.path.splitext(tempfilename)[0]+".png")
            threadmax.acquire()
            t = threading.Thread(target=self.decrypt, args=(
                i, savefile, int(mwidth), int(mheight), passwd, NKey, realfile))
            t.setDaemon(True)
            t.start()
            l.append(t)
        for t in l:
            t.join()
        self.label_12.setText("")
        self.pushButton_5.setEnabled(True)
        self.tab.setEnabled(True)
        self.tab_3.setEnabled(True)

    def btnstate(self):
        self.label_9.setText("选择视频文件：")
        self.label_10.setText("选择拆解的图片保存文件夹：")
        self.lineEdit_9.setText("")
        self.lineEdit_10.setText("")

    def btnstate1(self):
        self.label_9.setText("选择要保存生成视频文件的目标文件夹：")
        self.label_10.setText("选择要合成的图片所在的文件夹：")
        self.lineEdit_9.setText("")
        self.lineEdit_10.setText("")

    def setState(self):
        if self.checkBox_2.isChecked():
            self.lineEdit_8.setEnabled(True)
            self.pushButton_12.setEnabled(True)
            self.pushButton_6.setEnabled(True)
        else:
            self.lineEdit_8.setEnabled(False)
            self.pushButton_12.setEnabled(False)
            self.pushButton_6.setEnabled(False)

    def wrongd(self, info):
        QMessageBox.critical(MainWindow, "错误", info)

    def openWeb(self):
        if QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://raw.githubusercontent.com/parkmftsai/digital_watermarking/master/paper/High-capacity%20Robust%20Watermarking%20Approach%20for%20Protecting%20Ownership%20Right.pdf")):
            pass

    def showPicCho1(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(
            None,  "选取图片",  self.cwd, "图片文件 (*.png;*.jpg;*.jpeg;*.bmp;*.dib;*.jpeg;*.jpe;*.tif;*.tiff)")
        if fileName_choose == "":
            return
        else:
            self.lineEdit_4.setText(fileName_choose)

    def showPicCho3(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(
            None,  "选取图片",  self.cwd, "图片文件 (*.png;*.jpg;*.jpeg;*.bmp;*.dib;*.jpeg;*.jpe;*.tif;*.tiff)")
        if fileName_choose == "":
            return
        else:
            self.lineEdit_2.setText(fileName_choose)

    def showPicCho2(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(
            None,  "选取图片",  self.cwd, "图片文件 (*.png;*.jpg;*.jpeg;*.bmp;*.dib;*.jpeg;*.jpe;*.tif;*.tiff)")
        if fileName_choose == "":
            return
        else:
            self.lineEdit.setText(fileName_choose)

    def showDirCho1(self):
        dir_choose = QFileDialog.getExistingDirectory(None, "选取文件夹", self.cwd)
        if dir_choose == "":
            return
        else:
            self.lineEdit_4.setText(dir_choose)

    def showFileCho1(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(
            None,  "选取图片",  self.cwd, "文件 (*.npy)")
        if fileName_choose == "":
            return
        else:
            self.lineEdit_8.setText(fileName_choose)

    def showMovCho1(self):
        if self.radioButton.isChecked():
            fileName_choose, filetype = QFileDialog.getOpenFileName(
                None,  "选取视频",  self.cwd, "视频文件 (*.mp4;*.avi;*.mkv)")
            if fileName_choose == "":
                return
            else:
                self.lineEdit_9.setText(fileName_choose)
        if self.radioButton_2.isChecked():
            dir_choose = QFileDialog.getExistingDirectory(
                None, "选取文件夹", self.cwd)
            if dir_choose == "":
                return
            else:
                self.lineEdit_9.setText(dir_choose)

    def showDirCho2(self):
        dir_choose = QFileDialog.getExistingDirectory(None, "选取文件夹", self.cwd)
        if dir_choose == "":
            return
        else:
            self.lineEdit_8.setText(dir_choose)

    def showDirCho3(self):
        dir_choose = QFileDialog.getExistingDirectory(None, "选取文件夹", self.cwd)
        if dir_choose == "":
            return
        else:
            self.lineEdit.setText(dir_choose)

    def showDirCho4(self):
        dir_choose = QFileDialog.getExistingDirectory(None, "选取文件夹", self.cwd)
        if dir_choose == "":
            return
        else:
            self.lineEdit_10.setText(dir_choose)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate(
            "MainWindow", "Hollow 图片（视频）信息隐藏加解密软件 V1.0"))
        MainWindow.setWindowIcon(QIcon('icon.png'))
        self.checkBox.setText(_translate("MainWindow", "保存图片还原辅助信息"))
        self.pushButton.setText(_translate("MainWindow", "选择图片"))
        self.label.setText(_translate("MainWindow", "要附加隐藏信息的图片（文件夹）："))
        self.label_2.setText(_translate("MainWindow", "要隐藏的图片："))
        self.pushButton_2.setText(_translate("MainWindow", "选择图片"))
        self.label_3.setText(_translate("MainWindow", "加密密码："))
        self.pushButton_3.setText(_translate("MainWindow", "开始加密！"))
        self.pushButton_10.setText(_translate("MainWindow", "选择文件夹"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(
            self.tab), _translate("MainWindow", "隐藏加密"))
        self.label_4.setText(_translate("MainWindow", "选择被附加隐藏信息的图片（文件夹）："))
        self.pushButton_4.setText(_translate("MainWindow", "选择文件夹"))
        self.label_5.setText(_translate("MainWindow", "被隐藏图片宽："))
        self.label_6.setText(_translate("MainWindow", "被隐藏图片高："))
        self.label_7.setText(_translate("MainWindow", "解密密码："))
        self.checkBox_2.setText(_translate("MainWindow", "有图片还原辅助信息"))
        self.pushButton_5.setText(_translate("MainWindow", "开始解密！"))
        self.label_8.setText(_translate("MainWindow", "图片还原辅助信息文件（夹）："))
        self.pushButton_11.setText(_translate("MainWindow", "选择图片"))
        self.pushButton_12.setText(_translate("MainWindow", "选择文件"))
        self.pushButton_6.setText(_translate("MainWindow", "选择文件夹"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(
            self.tab_2), _translate("MainWindow", "隐藏解密"))
        self.label_9.setText(_translate("MainWindow", "选择视频文件："))
        self.label_10.setText(_translate("MainWindow", "选择拆解的图片保存文件夹："))
        self.pushButton_7.setText(_translate("MainWindow", "浏览"))
        self.pushButton_8.setText(_translate("MainWindow", "浏览"))
        self.pushButton_9.setText(_translate("MainWindow", "开始！"))
        self.radioButton.setText(_translate("MainWindow", "视频拆解"))
        self.radioButton_2.setText(_translate("MainWindow", "视频合成"))
        self.label_13.setText(_translate("MainWindow", "视频帧率（fps）："))
        self.tabWidget.setTabText(self.tabWidget.indexOf(
            self.tab_3), _translate("MainWindow", "视频处理"))
        self.menu.setTitle(_translate("MainWindow", "选项"))
        self.menu_2.setTitle(_translate("MainWindow", "关于"))
        self.action_3.setText(_translate("MainWindow", "退出"))
        self.action_4.setText(_translate("MainWindow", "原理"))
        self.action_5.setText(_translate("MainWindow", "作者"))
        self.action_6.setText(_translate("MainWindow", "帮助"))
        self.action_7.setText(_translate("MainWindow", "设定线程数"))

    def encrypt(self, srcimage, markimage, outimage, passwd, NKey):
        global countw, threadmax, lock
        try:
            lock.acquire()
            source = Image.open(srcimage)
            if len(source.split()) < 3:
                source = source.convert("RGB")
            self.progressChanged.emit(10)
            img = np.array(source)
            width, height = source.size
            lock.release()
        except Exception:
            lock.release()
            self.signal.emit(srcimage+"的图片格式不受支持！")
            self.progressChanged.emit(0)
            threadmax.release()
            return
        pixelred = np.zeros((img.shape[0], img.shape[1]), int)
        pixelgreen = np.zeros((img.shape[0], img.shape[1]), int)
        pixelblue = np.zeros((img.shape[0], img.shape[1]), int)
        pixelred[:, :] = img[:, :, 0]
        pixelred = pixelred.T
        pixelgreen[:, :] = img[:, :, 1]
        pixelgreen = pixelgreen.T
        pixelblue[:, :] = img[:, :, 2]
        pixelblue = pixelblue.T
        threads = []
        for i in [pixelred, pixelgreen, pixelblue]:
            t = MyThread(dwt, (i, width, height))
            threads.append(t)
        for i in range(3):
            threads[i].start()
        for i in range(3):
            threads[i].join()
        self.progressChanged.emit(20)
        dwtred = threads[0].get_result()
        dwtgreen = threads[1].get_result()
        dwtblue = threads[2].get_result()
        try:
            lock.acquire()
            mark = Image.open(markimage)
            if len(mark.split()) < 3:
                mark = mark.convert("RGB")
            mwidth, mheight = mark.size
            lock.release()
        except Exception:
            lock.release()
            self.signal.emit(markimage+"的图片格式不受支持！")
            self.progressChanged.emit(0)
            threadmax.release()
            return
        threads = []
        flag = 0
        self.progressChanged.emit(30)
        lock.acquire()
        for i in [dwtred, dwtgreen, dwtblue]:
            t = MyThread(hiding_data, (i, markimage, flag, True, passwd))
            flag += 1
            threads.append(t)
        for i in range(3):
            threads[i].start()
        for i in range(3):
            threads[i].join()
        lock.release()
        self.progressChanged.emit(40)
        complex1 = threads[0].get_result()
        complex2 = threads[1].get_result()
        complex3 = threads[2].get_result()
        pixel = np.zeros((width, height), int)
        self.progressChanged.emit(50)
        idwt(dwtred, pixel, width, height)
        self.progressChanged.emit(65)
        idwt(dwtgreen, pixel, width, height)
        self.progressChanged.emit(78)
        idwt(dwtblue, pixel, width, height)
        self.progressChanged.emit(90)
        output_file(outimage, dwtred, dwtgreen, dwtblue, width, height)
        if NKey == True:
            complexd = np.zeros((mwidth*mheight, 3), float)
            complexd[:, 0] = complex1[:]
            complexd[:, 1] = complex2[:]
            complexd[:, 2] = complex3[:]
            np.save(os.path.splitext(outimage)[0], complexd)
        countw += 1
        self.progressChanged.emit(100)
        self.centralwidget.setStatusTip("已处理文件："+str(countw)+"个")
        threadmax.release()

    def decrypt(self, entimage, outimage, mwidth, mheight, passwd, NKey, keyfile=''):
        global countw, threadmax, lock
        complex1 = 0
        complex2 = 0
        complex3 = 0
        if NKey == True:
            try:
                lock.acquire()
                complexd = np.load(keyfile)
                lock.release()
            except Exception:
                lock.release()
                self.progressChanged2.emit(0)
                self.signal.emit(keyfile+"图片还原辅助信息加载错误，请确认是否为正确的文件！")
                threadmax.release()
                return
            complex1 = np.zeros((complexd.shape[0]), float)
            complex2 = np.zeros((complexd.shape[0]), float)
            complex3 = np.zeros((complexd.shape[0]), float)
            complex1[:] = complexd[:, 0]
            complex2[:] = complexd[:, 1]
            complex3[:] = complexd[:, 2]
        else:
            complex1 = np.zeros((mwidth*mheight), float)
            complex2 = np.zeros((mwidth*mheight), float)
            complex3 = np.zeros((mwidth*mheight), float)
        self.progressChanged2.emit(10)
        try:
            lock.acquire()
            source = Image.open(entimage)
            if len(source.split()) < 3:
                source = source.convert("RGB")
            img = np.array(source)
            lock.release()
        except Exception:
            lock.release()
            self.progressChanged2.emit(0)
            self.signal.emit(entimage+"的图片格式不受支持！")
            threadmax.release()
            return
        self.progressChanged2.emit(10)
        width, height = source.size
        pixelred = np.zeros((img.shape[0], img.shape[1]), int)
        pixelgreen = np.zeros((img.shape[0], img.shape[1]), int)
        pixelblue = np.zeros((img.shape[0], img.shape[1]), int)
        pixelred[:, :] = img[:, :, 0]
        pixelred = pixelred.T
        pixelgreen[:, :] = img[:, :, 1]
        pixelgreen = pixelgreen.T
        pixelblue[:, :] = img[:, :, 2]
        pixelblue = pixelblue.T
        self.progressChanged2.emit(20)
        outdata = Image.new("RGB", (mwidth, mheight))
        threads = []
        for i in [pixelred, pixelgreen, pixelblue]:
            t = MyThread(dwt, (i, width, height))
            threads.append(t)
        for i in range(3):
            threads[i].start()
        for i in range(3):
            threads[i].join()
        self.progressChanged2.emit(50)
        dwtred = threads[0].get_result()
        dwtgreen = threads[1].get_result()
        dwtblue = threads[2].get_result()
        threads = []
        l = [complex1, complex2, complex3]
        count = 0
        lock.acquire()
        try:
            for i in [dwtred, dwtgreen, dwtblue]:
                t = MyThread(extract_watermark, (i, width, height,
                                                 mwidth, mheight, l[count], passwd))
                count += 1
                threads.append(t)
            for i in range(3):
                threads[i].start()
            for i in range(3):
                threads[i].join()
            lock.release()
        except Exception:
            lock.release()
            self.progressChanged2.emit(0)
            self.signal.emit(entimage+"图片还原辅助信息与实际不符！")
            threadmax.release()
            return
        self.progressChanged2.emit(70)
        red_wm = threads[0].get_result()
        green_wm = threads[1].get_result()
        blue_wm = threads[2].get_result()
        position_pixel = 0
        self.progressChanged2.emit(90)
        for i in range(mwidth):
            for j in range(mheight):
                outdata.putpixel(
                    (i, j), (red_wm[position_pixel], green_wm[position_pixel], blue_wm[position_pixel]))
                position_pixel += 1
        outdata.save(outimage)
        countw += 1
        self.progressChanged2.emit(100)
        self.centralwidget.setStatusTip("已处理文件："+str(countw)+"个")
        threadmax.release()

    def video2pic(self, video, pic_path):
        global countw
        try:
            vc = cv2.VideoCapture(video)
            c = 0
            rval = vc.isOpened()
            while rval:
                c = c + 1
                rval, frame = vc.read()
                if rval:
                    cv2.imencode('.png', frame)[1].tofile(
                        pic_path + '/'+str(c) + '.png')
                    cv2.waitKey(1)
                else:
                    break
            self.lineEdit_11.setText(str(vc.get(cv2.CAP_PROP_FPS)))
            vc.release()
        except Exception:
            self.progressChanged2.emit(0)
            self.signal.emit(video+"的格式不受支持！")
        self.label_14.setText("")
        self.pushButton_9.setEnabled(True)
        self.tab_2.setEnabled(True)
        self.tab.setEnabled(True)
        countw += 1
        self.progressChanged3.emit(100)
        self.centralwidget.setStatusTip("已处理文件："+str(countw)+"个")

    def pic2video(self, savepath, path, fps):
        global countw
        try:
            file_path = os.path.abspath(
                savepath) + '/' + str(int(time.time())) + ".avi"
            fourcc = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
            size = (0, 0)
            item = os.path.abspath(path) + '/ec1.png'
            img = cv2.imdecode(np.fromfile(
                item, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img.shape[0] < img.shape[1]:
                size = (img.shape[1], img.shape[0])
            else:
                size = img.shape[:2]
            video = cv2.VideoWriter(file_path, fourcc, fps, size)
            i = 1
            while os.path.isfile(os.path.abspath(path) + '/ec' + str(i)+'.png'):
                item = os.path.abspath(path) + '/ec' + str(i)+'.png'
                img = cv2.imdecode(np.fromfile(
                    item, dtype=np.uint8), cv2.IMREAD_COLOR)
                video.write(img)
                i += 1
            video.release()
        except Exception:
            self.progressChanged2.emit(0)
            self.signal.emit(
                "无法找到图片，请确认文件夹下存放着文件名为‘ecX.png’（X为连续的从1开始的数字）的图片集！")
        self.label_14.setText("")
        self.pushButton_9.setEnabled(True)
        self.tab_2.setEnabled(True)
        self.tab.setEnabled(True)
        countw += 1
        self.progressChanged3.emit(100)
        self.centralwidget.setStatusTip("已处理文件："+str(countw)+"个")


if __name__ == "__main__":
    threadNum = 4
    threadmax = threading.BoundedSemaphore(threadNum)
    lock = threading.Lock()
    countw = 0
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    helpwd = QtWidgets.QDialog()
    ThrNumd = QtWidgets.QDialog()
    AuInford = QtWidgets.QDialog()
    helpwr = helpw()
    helpwr.setupUi(helpwd)
    ThrNumr = ThrNum()
    ThrNumr.setupUi(ThrNumd)
    AuInfor = AuInfo()
    AuInfor.setupUi(AuInford)
    MainWindow.show()
    ui.action_5.triggered.connect(AuInford.show)
    ui.action_6.triggered.connect(helpwd.show)
    ui.action_7.triggered.connect(ThrNumd.show)
    sys.exit(app.exec_())
