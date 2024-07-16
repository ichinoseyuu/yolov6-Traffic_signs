import time
import cv2
import numpy as np
import threading
from PIL import Image
from yolo import YOLO
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel,QProgressBar
from PyQt5.QtCore import Qt
from my_tool import Emoticon
from pathlib import Path

class Mode():
    #   mode用于指定测试的模式：
    #   'pic'           表示单张图片预测
    #   'video'         表示视频检测
    #   'realTime'      表示实时检测，可调用摄像头
    #   'fps'           表示测试fps
    #   'folder'        表示遍历文件夹进行检测并保存
    #   'heatmap'       表示进行预测结果的热力图可视化
    pic = 1
    video = 2
    realTime = 3
    fps = 4
    folder = 5
    heatmap = 6

    @staticmethod
    def is_Mode(mode):
        return mode in [Mode.pic, Mode.video, Mode.folder, Mode.heatmap, Mode.realTime, Mode.fps]

class Predict():
    predict_file_path = "_img/test.jpg"   
    img_save_path = "_img_out/output.jpg"
    video_save_path = "_video_out/video_out.mp4"
    dir_save_path   = "_img_out/"
    heatmap_save_path = "_img_out/heatmap_vision.png"
    video_fps       = 25.0
    mode = Mode.pic
    mode_names = {
        Mode.pic: "单图模式",
        Mode.video: "视频模式",
        Mode.folder: "多图模式",
        Mode.heatmap: "热力图模式",
        Mode.realTime: "实时检测模式",
        Mode.fps: "测试帧率"
    }
    
    #----------------------------------------------------------------------------------------------------------#
    #   test_interval       用于指定测量fps的时候，图片检测的次数。理论上test_interval越大，fps越准确。
    #   fps_image_path      用于指定测试的fps图片  
    #   test_interval和fps_image_path仅在mode='fps'有效
    #----------------------------------------------------------------------------------------------------------#
    test_interval   = 100
    #-------------------------------------------------------------------------#
    #   crop                指定了是否在单张图片预测后对目标进行截取
    #   count               指定了是否进行目标的计数
    #   crop、count仅在单图模式有效
    #-------------------------------------------------------------------------#
    crop            = False
    count           = False
    
    def __init__(self, instance):
        super().__init__()
        self.yolo = YOLO()  # 实例化 YOLO 类
        self.emoticon = Emoticon()
        self.mainWindow = instance # 用来存储主窗口的引用
        self.thread_instance = None#设置一个线程来进行处理视频，避免主程序卡顿
        self.stop_flag = False
    

    def start_thread(self,target_fun,*target_args):
        if self.thread_instance is None or not self.thread_instance.is_alive():
            self.stop_flag = False
            self.thread_instance = threading.Thread(target=target_fun, args=target_args)
            self.thread_instance.start()
        else: self.mainWindow.showNotification("有任务正在进行哦" + self.emoticon.awk)      
            
    def stop_thread(self):
        if self.thread_instance is not None:
            self.stop_flag = True
            self.thread_instance.join()  # 等待线程结束
            self.thread_instance = None
        else:
            self.mainWindow.showNotification("当前没有在进行处理哦" + self.emoticon.awk)
    
    #根据参数获取模式名
    def getModeNmae(self,mode):
        if Mode.is_Mode(mode):
            return self.mode_names.get(mode, "未知模式")
        else:
            print("error")
    
    #获取当前模式
    def getCurrentMode(self):
        return self.mode
    
    #获取当前模式的名字
    def getCurrentModeName(self):
        return self.getModeNmae(self.mode)
    
    #设置模式
    def setMode(self, mode):
        if Mode.is_Mode(mode):
            self.mode = mode
        else:
            print("参数错误")

    #根据模式处理
    def predictFile(self,display,progress):
         # 检查对象是否为有效的对象
        if not isinstance(display, QLabel):
            self.mainWindow.showNotification("请检查显示对象是否正确" + self.emoticon.sad)
            return 
        if not isinstance(progress, QProgressBar):
            self.mainWindow.showNotification("请检查进度条对象是否正确" + self.emoticon.sad)
            return
        mode_handlers = {
            Mode.pic: lambda: self.start_thread(self.predictPic,(display, progress)),
            Mode.folder: lambda: self.start_thread(self.predictFolder, (progress,)),
            Mode.fps: self.predictFps,
            Mode.realTime: lambda: self.start_thread(self.predictRealTime, (display,)),
            Mode.video: lambda: self.start_thread(self.predictVideo, (display, progress)),
            Mode.heatmap: lambda: self.start_thread(self.predictHeatmap,(display, progress)),
            }
        handler = mode_handlers.get(self.mode) #查找字典，判断以什么模式处理
        if handler:
            handler()
        else: self.mainWindow.showNotification("未知模式" + self.emoticon.sad)

    def showVideo(self, path, window, progressBar):
        target = (path,window,progressBar,)
        self.start_thread(self.readVideo,target)
        self.mainWindow.showNotification('打开视频成功'+ self.emoticon.ok)

    def predictPic(self, display):
        import os
        if not os.path.isfile(self.predict_file_path):
            self.mainWindow.showNotification("指定的路径不是文件哦"+self.emoticon.awk)
            return
        try:
            image = Image.open(self.predict_file_path)
        except IOError:
            self.mainWindow.showNotification("无法打开图片，请检查文件格式是否正确"+self.emoticon.awk)
            return
        bar = display[1]
        bar.setValue(0) # 初始化进度条
        r_image = self.yolo.detect_image(image, crop = self.crop, count = self.count)
        # 保存到指定目录
        directory_path = os.path.dirname(self.img_save_path)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        r_image.save(self.img_save_path)
        label_display= display[0]
        label_width = label_display.width() # 获取窗口控件的宽度
        label_height = label_display.height() # 获取窗口控件的长度
        label_display.setAlignment(Qt.AlignCenter)#图像居中
        # 显示图片
        pixmap = QPixmap(self.img_save_path) # 创建 QPixmap 对象
        # 调整图像大小以适应 label_display 控件的大小，并保持纵横比
        scaled_pixmap = pixmap.scaled(label_width, label_height, aspectRatioMode=Qt.KeepAspectRatio)
        #更新显示
        bar.setValue(100)
        label_display.setPixmap(scaled_pixmap)
        self.mainWindow.label_display_path.setText(self.img_save_path)
        self.mainWindow.showNotification("图片处理已完成"+self.emoticon.ok)

    def predictFps(self):
        import os
        if not os.path.isfile(self.predict_file_path):
            self.mainWindow.showNotification("指定的路径不是文件哦"+self.emoticon.awk)
            return
        try:
            img = Image.open(self.predict_file_path)
        except IOError:
            self.mainWindow.showNotification("无法打开图片，请检查文件格式是否正确"+self.emoticon.awk)
            return 
        tact_time = self.yolo.get_FPS(img, self.test_interval)
        message = "帧率测试成功,帧率为:"+str(tact_time) + "s," + str(1/tact_time) + "FPS, @batch_size 1"+self.emoticon.ok
        self.mainWindow.showNotification(message)

    def predictFolder(self,bar):
        import os
        if not os.path.isdir(self.predict_file_path):
            self.mainWindow.showNotification("指定的路径不是文件夹哦"+self.emoticon.awk)
            return
        files = os.listdir(self.predict_file_path)#获取文件路径下所有文件
        files_count = len(files)#获取文件路径下所有文件数
        imgs = []#用于存储待处理图片引用
        progress_index = 0 
        progress_percent = 0
        progress_bar = bar[0]
        progress_bar.setValue(0)
        for file in files: #筛选图片
            if self.stop_flag: #线程结束flag，用于按钮控制结束
                self.mainWindow.showNotification("你停止了批量处理"+self.emoticon.ok)
                return
            if file.lower().endswith((
                        '.bmp', '.dib', '.png', '.jpg', '.jpeg', '.pbm', 
                        '.pgm', '.ppm', '.tif', '.tiff')):
                imgs.append(file)
            else:#不是图片的文件直接更新进度条
                progress_index += 1
                progress_percent = int(100 * progress_index / files_count)
                progress_bar.setValue(progress_percent)
        for img in imgs:#依次处理图片
                if self.stop_flag: #线程结束flag，用于按钮控制结束
                    self.mainWindow.showNotification("你停止了批量处理"+self.emoticon.ok)
                    return
                image_path  = os.path.join(self.predict_file_path, img)
                image = Image.open(image_path)
                r_image = self.yolo.detect_image(image)
                if not os.path.exists(self.dir_save_path):
                    os.makedirs(self.dir_save_path)#保存图片
                r_image.save(os.path.join(self.dir_save_path, img.replace(".jpg", ".png")), quality=95, subsampling=0)
                #更新进度条
                progress_index += 1
                progress_percent = int(100 * progress_index / files_count)
                progress_bar.setValue(progress_percent)
        self.mainWindow.showNotification("所有文件处理已完成，该模式不支持显示所有结果"+self.emoticon.sad)


    def predictHeatmap(self, display):
        import os
        if not os.path.isfile(self.predict_file_path):
            self.mainWindow.showNotification("指定的路径不是文件哦"+self.emoticon.awk)
            return
        try:
            image = Image.open(self.predict_file_path)
        except IOError:
            self.mainWindow.showNotification("无法打开图片，请检查文件格式是否正确"+self.emoticon.awk)
            return
        bar = display[1]
        bar.setValue(0) # 初始化进度条
        self.yolo.detect_heatmap(image, self.heatmap_save_path)
        # 显示图片
        label_display = display[0]
        label_width = label_display.width() # 获取窗口控件的宽度
        label_height = label_display.height() # 获取窗口控件的长度
        label_display.setAlignment(Qt.AlignCenter)#图像居中
        pixmap = QPixmap(self.heatmap_save_path) # 创建 QPixmap 对象
        # 调整图像大小以适应 label_display 控件的大小，并保持纵横比
        scaled_pixmap = pixmap.scaled(label_width, label_height, aspectRatioMode=Qt.KeepAspectRatio)
        #更新显示
        bar.setValue(100)
        label_display.setPixmap(scaled_pixmap)
        self.mainWindow.label_display_path.setText(self.heatmap_save_path)
        self.mainWindow.showNotification("图片处理已完成，处理结果已显示"+self.emoticon.ok)
    

    def predictRealTime(self,display):
        capture = cv2.VideoCapture(0)#设置摄像头模式
        #尝试读取一帧
        ref, frame = capture.read()
        if not ref:
            self.mainWindow.showNotification("未能正确读取摄像头，请确认摄像头是否正确安装"+self.emoticon.awk)
            return 
        label_display = display[0] # 获取显示窗口控件
        label_width = label_display.width() # 获取窗口控件的宽度
        label_height = label_display.height() # 获取窗口控件的长度
        label_display.setAlignment(Qt.AlignCenter)#图像居中
        fps = 0.0 #用于计算视频处理后的帧率
        #循环读取
        while True:
            self.mainWindow.showNotification("正在实时检测中"+self.emoticon.happy)
            if self.stop_flag: #线程结束flag，用于按钮控制结束
                capture.release() #释放视频捕获对象，关闭摄像头。
                self.mainWindow.showNotification("停止实时检测"+self.emoticon.ok)
                return
             #读取一帧
            ref, frame = capture.read()
            t1 = time.time() #存储当前帧的时间
            #开始处理
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 将图像从 BGR 格式转换为 RGB 格式
            image = Image.fromarray(np.uint8(frame))  # 将 numpy 数组转换为 PIL Image
            image = np.array(self.yolo.detect_image(image))  # 使用 YOLO 对图像进行检测
            frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # 将检测后的图像从 RGB 格式转换为 BGR 格式
            fps = (fps + (1. / (time.time() - t1))) / 2  # 计算帧率
            # 在图像上显示帧率
            frame = cv2.putText(frame, "fps= %.2f" % (fps), (0, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 将图像从 BGR 格式转换为 RGB 格式
            # 将图像数据转换为 QImage 格式
            qImage = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            # 创建 QPixmap 对象
            pixmap = QPixmap.fromImage(qImage)
            # 调整图像大小以适应窗口控件的大小，并保持纵横比
            scaled_pixmap = pixmap.scaled(label_width, label_height, aspectRatioMode=Qt.KeepAspectRatio)
            #更新显示
            label_display.setPixmap(scaled_pixmap) 

    def predictVideo(self,display):
        import os
        if not os.path.isfile(self.predict_file_path):
            self.mainWindow.showNotification("指定路径不是文件哦"+self.emoticon.awk)
            return
        if not Path(self.predict_file_path).suffix.lower() in (".mp4", ".avi", ".mkv"):
            self.mainWindow.showNotification("文件格式不正确哦"+self.emoticon.awk)
            return
        capture = cv2.VideoCapture(self.predict_file_path)#设置文件模式
        #尝试读取一帧
        ref, frame = capture.read()
        if not ref:
            self.mainWindow.showNotification("未能正确读取视频，请检查文件格式是否正确"+self.emoticon.sad)
            return
        # 如果指定了视频保存路径，则创建 VideoWriter 对象
        if self.video_save_path != "":
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            size = (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            out = cv2.VideoWriter(self.video_save_path, fourcc, self.video_fps, size)
        label_display = display[0] # 获取显示窗口控件
        progress_bar = display[1]  # 获取进度条控件
        label_width = label_display.width() # 获取窗口控件的宽度
        label_height = label_display.height() # 获取窗口控件的长度
        label_display.setAlignment(Qt.AlignCenter)#图像居中
        progress_bar.setValue(0) # 初始化进度条
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))  # 获取视频总帧数，用于计算处理进度
        frame_index = 0  # 初始化当前帧数，用于计算处理进度
        fps = 0.0 #用于计算视频处理后的帧率
        #循环读取视频帧
        while True:
            self.mainWindow.showNotification("正在处理中"+self.emoticon.ok)
            if self.stop_flag: #线程结束flag，用于按钮控制结束
                capture.release() #释放视频捕获对象，关闭视频文件或摄像头。
                #如果指定了视频保存路径，则释放视频写入对象，关闭视频文件。
                if self.video_save_path != "":
                    out.release()
                self.mainWindow.showNotification("停止处理"+self.emoticon.ok)
                return 
            t1 = time.time() #存储当前帧的时间
            #检查视频是否已完成处理
            ref, frame = capture.read()
            if not ref:
                #有时候会有进度条走不满的情况，但实际已经处理完成
                #手动设置为100%
                progress_bar.setValue(100)
                #释放视频捕获对象，关闭视频文件或摄像头。
                capture.release()
                #如果指定了视频保存路径，则释放视频写入对象，关闭视频文件。
                if self.video_save_path != "":
                    out.release()
                self.mainWindow.showNotification("处理已完成"+self.emoticon.ok)
                return
            #开始处理
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 将图像从 BGR 格式转换为 RGB 格式
            image = Image.fromarray(np.uint8(frame))  # 将 numpy 数组转换为 PIL Image
            image = np.array(self.yolo.detect_image(image))  # 使用 YOLO 对图像进行检测
            frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # 将检测后的图像从 RGB 格式转换为 BGR 格式
            fps = (fps + (1. / (time.time() - t1))) / 2  # 计算帧率
            # 在图像上显示帧率
            frame = cv2.putText(frame, "fps= %.2f" % (fps), (0, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 将图像从 BGR 格式转换为 RGB 格式
            # 将图像数据转换为 QImage 格式
            qImage = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            # 创建 QPixmap 对象
            pixmap = QPixmap.fromImage(qImage)
            # 调整图像大小以适应窗口控件的大小，并保持纵横比
            scaled_pixmap = pixmap.scaled(label_width, label_height, aspectRatioMode=Qt.KeepAspectRatio)
            #计算进度条
            frame_index += 1
            progress_percent = int(100 * frame_index / frame_count)
            #更新显示
            progress_bar.setValue(progress_percent)
            label_display.setPixmap(scaled_pixmap)
            # 如果指定了视频保存路径，则将帧写入视频文件
            if self.video_save_path != "":
                out.write(frame)
                
    def readVideo(self,display):
         #指定类型
        capture = cv2.VideoCapture(display[0])
        #尝试读取
        ref, frame = capture.read()
        if not ref:
            self.mainWindow.showNotification("无法打开视频，请检查文件格式是否正确"+self.emoticon.awk)
            return
        # 获取 label_display 控件的大小
        label_display = display[1]
        progress_bar = display[2]
        label_width = label_display.width()
        label_height = label_display.height()
        label_display.setAlignment(Qt.AlignCenter) # 图像居中
        fps = capture.get(cv2.CAP_PROP_FPS)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))  # 获取视频总帧数
        frame_interval = 1.0 / fps if fps > 0 else 0.0  # 计算帧间隔
        frame_index = 0  # 初始化当前帧数
        progress_bar.setValue(0)
        while True:
            self.mainWindow.showNotification("播放中"+self.emoticon.ok)
            if self.stop_flag:
                #释放视频捕获对象，关闭视频文件或摄像头。
                capture.release()
                self.mainWindow.showNotification("停止播放"+self.emoticon.ok)
                break 
            #检查视频是否已完成处理
            ref, frame = capture.read()
            if not ref:
                progress_bar.setValue(100)
                #释放视频捕获对象，关闭视频文件或摄像头。
                capture.release()
                self.mainWindow.showNotification("播放已完成"+self.emoticon.ok)
                break 
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 将图像从 BGR 格式转换为 RGB 格式
            # 将图像数据转换为 QImage 格式
            qImage = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            # 创建 QPixmap 对象
            pixmap = QPixmap.fromImage(qImage)
            # 调整图像大小以适应窗口控件的大小，并保持纵横比
            scaled_pixmap = pixmap.scaled(label_width, label_height, aspectRatioMode=Qt.KeepAspectRatio) 
             # 计算进度条
            frame_index += 1
            progress_percent = int(100 * frame_index / frame_count)
             # 更新显示
            progress_bar.setValue(progress_percent)
            label_display.setPixmap(scaled_pixmap)
            time.sleep(frame_interval)
        
            
