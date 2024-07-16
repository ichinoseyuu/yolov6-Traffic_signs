import webbrowser
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from AboutWindow import Ui_Form

class AboutWindow(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self) #建立窗口布局
        self.setWindowFlags(Qt.FramelessWindowHint) # 表示窗口没有边框
        self.setAttribute(Qt.WA_TranslucentBackground) # 表示窗口具有透明效果
        self.draggable = True #是否移动窗口
        self.old_pos = None #移动窗口，上一次鼠标指针位置

        # 关于窗口绑定按钮的点击事件
        self.button_min.clicked.connect(self.showMinimized) #最小化
        self.button_exit.clicked.connect(self.close)#关闭窗口
        self.button_blog.clicked.connect(self.openMyBlog)# 跳转的我的主页

    def maximize_window(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def openMyBlog(self):
        webbrowser.open('https://ichinoseyuu.github.io/')

    #拖动窗口相关函数 mousePressEvent mouseMoveEvent mouseReleaseEvent
    def mousePressEvent(self, event):
        if self.draggable and event.buttons() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.draggable and event.buttons() == Qt.LeftButton and self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None