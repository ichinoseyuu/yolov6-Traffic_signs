import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from MainWindow import Ui_MainWindow
from AboutWindow_init import AboutWindow
from datetime import datetime
from Predict import Predict, Mode
from my_tool import Emoticon

class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self) #设定主窗口布局
        self.setWindowFlags(Qt.FramelessWindowHint) # 表示窗口没有边框
        self.setAttribute(Qt.WA_TranslucentBackground) # 表示窗口具有透明效果
        self.draggable = True #是否移动窗口
        self.old_pos = None #移动窗口，上一次鼠标指针位置
        # 主窗口绑定按钮的点击事件 
        self.button_min.clicked.connect(self.showMinimized) #最小化
        self.button_exit_1.clicked.connect(self.exitApplication) # 右上角退出 
        self.button_pic.clicked.connect(lambda:self.changeMode(Mode.pic)) # 图片模式    
        self.button_files.clicked.connect(lambda:self.changeMode(Mode.folder)) # 多图模式      
        self.button_heatmap.clicked.connect(lambda:self.changeMode(Mode.heatmap)) # 热力图模式       
        self.button_video.clicked.connect(lambda:self.changeMode(Mode.video))  # 视频模式       
        self.button_realtime.clicked.connect(lambda:self.changeMode(Mode.realTime)) # 摄像头模式
        self.button_select_file.clicked.connect(self.selectPredictFile) #选择文件
        self.button_handle.clicked.connect(self.startPredict) # 开始处理
        self.button_stop.clicked.connect(self.stopPredict) # 停止处理 
        self.button_confirm.clicked.connect(self.changeSavePath) # 保存路径
        self.button_display_result.clicked.connect(lambda:self.displayResult('pic')) # 选择图片显示
        self.button_display_result_2.clicked.connect(lambda:self.displayResult('video')) # 选择视频显示
        self.button_about.clicked.connect(lambda:aboutWindow.show()) # 关于
        self.button_exit_2.clicked.connect(self.exitApplication) # 右下角退出 
        # 主界面内容显示
        self.displayModeAndPath(predict.predict_file_path) #模式和当前文件路径显示
        self.readSavePath() #读取存储路径 
        self.showNotification("初始化已完成,欢迎使用"+emoticon.happy)


    def exitApplication(self):
        predict.stop_thread()
        QApplication.instance().quit()
        self.showNotification('欢迎下次使用'+emoticon.happy)

    # def maximize_window(window):
    #     if window.isMaximized():
    #         window.showNormal()
    #         window.showNotification('小窗模式已打开'+emoticon.happy)
    #     else:
    #         window.showMaximized()
    #         window.showNotification('窗口已最大化'+emoticon.happy)

    #用Label显示通知   
    def showNotification(self, message):
        time_title = '    --Time:'
        current_time = datetime.now().strftime("%H:%M:%S")
        self.label_message.setText(message + time_title + current_time)

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

    #变更模式
    def changeMode(self, mode):
        predict.setMode(mode)
        self.label_mode.setText(predict.getCurrentModeName())
        self.showNotification("模式已更改为："+ self.label_mode.text() + emoticon.happy)

    #选择需要处理的文件
    def selectPredictFile(self):
        if predict.mode in [Mode.heatmap, Mode.pic, Mode.fps]:
            file_dialog = QFileDialog()
            file_dialog.setWindowTitle("选择图片")
            file_dialog.setNameFilters(["图片 (*.png *.jpg *.jpeg *.bmp *.dib *.pbm *.pgm *.ppm *.tif *.tiff)"])
            # 打开文件对话框
            if file_dialog.exec_():
                    selected_files = file_dialog.selectedFiles()
                    predict.predict_file_path = selected_files[0]
                    self.displayModeAndPath(predict.predict_file_path)
                    self.showNotification('打开文件成功'+ emoticon.happy)
            else: self.showNotification('你取消了选择'+ emoticon.awk)

        elif predict.mode == Mode.video:
            file_dialog = QFileDialog()
            file_dialog.setWindowTitle("选择视频")
            file_dialog.setNameFilters(["视频 (*.mp4 *.avi *.mkv)"])
            # 打开文件对话框
            if file_dialog.exec_():
                    selected_files = file_dialog.selectedFiles()
                    predict.predict_file_path = selected_files[0]
                    self.displayModeAndPath(predict.predict_file_path)
                    self.showNotification('打开文件成功'+ emoticon.happy)
            else: self.showNotification('你取消了选择'+ emoticon.awk)

        elif predict.mode == Mode.folder:
            file_path , isCancel = self.selectFolder()
            if isCancel:
                self.showNotification(file_path+emoticon.awk)
            else:  
                predict.predict_file_path = file_path  
                self.displayModeAndPath(file_path)
                self.showNotification('选择文件夹成功'+ emoticon.happy)
        else: 
            self.showNotification('该模式不需要选择文件'+ emoticon.awk)
    #开始检测
    def startPredict(self):
        predict.predictFile(self.label_display_window,self.progressBar)

    #停止检测
    def stopPredict(self):
        predict.stop_thread()        

    # 选择文件显示
    def displayResult(self, filetype): 
        if filetype == 'pic':
            file_dialog = QFileDialog()
            file_dialog.setWindowTitle("选择图片")
            file_dialog.setNameFilters(["图片 (*.png *.jpg *.jpeg)"])
             # 打开文件对话框
            if file_dialog.exec_():
                selected_files = file_dialog.selectedFiles()
                self.label_currentPath.setText(selected_files[0])
                self.showPic(selected_files[0])
                self.showNotification('打开文件成功'+ emoticon.happy)
            else: self.showNotification('你取消了选择'+ emoticon.awk)
        if filetype == 'video':
            file_dialog = QFileDialog()
            file_dialog.setWindowTitle("选择视频")
            file_dialog.setNameFilters(["视频 (*.mp4 *.avi *.mkv)"])
            if file_dialog.exec_():
                selected_files = file_dialog.selectedFiles()
                self.label_display_path.setText(selected_files[0])
                predict.showVideo(selected_files[0],self.label_display_window,self.progressBar,)
                self.showNotification('打开文件成功'+ emoticon.happy)
            else: self.showNotification('你取消了选择'+ emoticon.awk)        

    def showPic(self,file_path):
        pixmap = QPixmap(file_path)
        # 获取 label_display 控件的大小
        label_width = self.label_display_window.width()
        label_height = self.label_display_window.height()
        # 调整图像大小以适应 label_display 控件的大小，并保持纵横比
        scaled_pixmap = pixmap.scaled(label_width, label_height, aspectRatioMode=Qt.KeepAspectRatio)
        self.label_display_window.setAlignment(Qt.AlignCenter)  # 图像居中显示
        self.label_display_window.setPixmap(scaled_pixmap)
        self.label_display_path.setText(file_path)
        self.showNotification('处理结果显示成功'+ emoticon.ok)

    def changeSavePath(self):
        predict.img_saveFileName = self.lineEdit_pic_out.text() 
        predict.video_saveFileName = self.lineEdit_video_out.text()
        predict.heatmap_save_path = self.lineEdit_heatmap_out.text()
        predict.dir_save_path  = self.lineEdit_file_out.text()
        self.showNotification('存储路径已更改'+ emoticon.ok)

    def readSavePath(self):
        self.label_h5file.setText('best_epoch_weights')
        self.lineEdit_pic_out.setText(predict.img_save_path)
        self.lineEdit_video_out.setText(predict.video_save_path)
        self.lineEdit_heatmap_out.setText(predict.heatmap_save_path)
        self.lineEdit_file_out.setText(predict.dir_save_path)
        self.showNotification('读取存储路径完成'+ emoticon.ok)   

    def displayModeAndPath(self, path):
        self.label_mode.setText(predict.getCurrentModeName())
        self.label_currentPath.setText(path)
        
    def selectFolder(self):
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("选择文件夹")
        file_dialog.setFileMode(QFileDialog.Directory)
        file_dialog.setOption(QFileDialog.ShowDirsOnly)
        folder_path = file_dialog.getExistingDirectory(self, "选择文件夹", "/")
        # 如果用户选择了文件夹，则打印路径
        if folder_path:
            return folder_path, False
        else: return "你取消了选择", True

    def selectSaveFilePath(self):
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("选择图片/视频")
        # 获取用户选择的文件名及路径
        selected_file, _ = file_dialog.getSaveFileName(self.lineEdit_file_out, "保存文件", "", 
                                                    "图片 (*.png *.jpg *.jpeg)",
                                                    "视频 (*.mp4 *.avi *.mkv)")
        if selected_file:
            return selected_file, False
        else: return "你取消了选择", True   
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    predict = Predict(instance = None)
    emoticon = Emoticon()
    aboutWindow = AboutWindow() 
    mainWindow = MyWindow()
    predict.mainWindow = mainWindow
    mainWindow.show()
    sys.exit(app.exec_())