import threading
# emoticons.add_emoticon("love", "(｡♥‿♥｡)") # 添加新表情
# emoticons.del_emoticon("love")# 删除特定表情
class Emoticon:
    def __init__(self):
        self.happy = "    (⑅˃◡˂⑅)"
        self.sad = "    °(৹˃﹏˂৹)°"
        self.ok = "    (•̤̀ᵕ•̤́๑)ᵒᵏ"
        self.awk = "    =͟͟͞͞(꒪⌓꒪*)"

    # 添加新表情
    def add_emoticon(self, emoticon_name, emoticon):
        setattr(self, emoticon_name, emoticon)

    # 删除特定表情
    def del_emoticon(self, emoticon_name):
        if hasattr(self, emoticon_name):
            delattr(self, emoticon_name)
        else:
            return(f"表情{emoticon_name}不存在！")


class MyThread:
    def __init__(self, target_method = None, *args):
        self.thread_instance = None
        self.stop_flag = False
        self.target_method = target_method
        self.args = args

    def start_thread(self):
        try:
            self.stop_flag = False
            self.thread_instance = threading.Thread(target=self.target_method, args=self.args)
            self.thread_instance.start()
            return "Thread started"
        except Exception as e:
            # 创建一个新的异常，并包含原始异常的信息
            new_exception = Exception("An error occurred: {}".format(e))
            # 将新的异常抛出，让调用者处理
            raise new_exception

    def start_thread_custom(self, target_method, *args):
        self.stop_flag = False
        self.thread_instance = threading.Thread(target=target_method, args=args)
        self.thread_instance.start()

    def stop_thread(self):
        if self.thread_instance:
            self.stop_flag = True
            self.thread_instance.join()  # 等待线程结束
            self.thread_instance = None


