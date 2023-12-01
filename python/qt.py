import sys
import time

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QWheelEvent
import types

"""
python安装目录的Scripts文件夹找到pyside6-designer.exe,pyside6-uic.exe,后者可以将ui文件转为py文件(pyside6-uic x.ui -o x.py)
designer中窗口->预览(ctrl+r)可以预览当前窗口,filter可以根据关键字过滤控件属性,tab widget布局时要先选中父tab而不是子tab,再布局

QWidget 获取父子控件
.setParent()       指定本控件的父控件
.parentWidget()    获取父控件
.children()        获取所有子控件，返回一个列表
.childAt()         获取在指定坐标的子控件,若该坐标无子控件则返回None
.childrenRect()    所有子控件(被隐藏的除外)构成的矩形
.childrenRegion()  所有子控件(被隐藏的除外)构成的范围

QWidget 可见度与可用度
窗口上的控件被设置为不可见后被隐藏,但不会被释放,仍占据原先的位置
.setVisible()   设置可见/不可见
.isVisible()    获取可见状态
对于编辑器、按钮、下拉框等控件可以设置不可用,用户不再能与之交互
.setEnabled()   设置可用/不可用
.isEnabled()    获取可用状态

QWidget 层级关系(z轴)
默认情况下,后绘制的控件会遮盖先绘制的控件,可通过API调整层级关系
.lower()                降低层级
.raise_()               提高层级(注意为避免和关键字冲突,末尾有下划线)
.stackUnder(QWidget q)  将自身置于q之下

QWidget 键盘输入焦点控制
只有当前获得焦点的控件才能与用户交互,键盘Tab键可以在控件间移动焦点,也可以用代码指定子控件获取焦点的先后顺序
每个控件都可以设置自己的焦点策略,即通过何种方式可以获取焦点
对于QPushButton、QTextEdit等控件的默认策略为StrongFocus,即通过键盘Tab键和鼠标点击两种方式获得焦点
对于QLabel等不需要与用户进行键盘输入交互的控件,焦点策略为NoFocus,不加入焦点链
焦点策略: https://doc.qt.io/qt-6/qwidget.html#setFocusProxy
.setFocusPolicy(policy: Qt.FocusPolicy)      设置焦点策略,详见下方Qt.FocusPolicy
.focusPolicy() -> Qt.FocusPolicy             返回该控件的焦点策略    
.setTabOrder(fist: QWidget, second: QWidget) 将第二个控件从焦点链中移除,并放置到第一个控件之后,默认为子控件创建顺序 
对本控件的焦点的控制: https://doc.qt.io/qt-6/qwidget.html#setFocus
.hasFocus() -> bool                          返回此控件(或其焦点代理)是否具有键盘输入焦点
.setFocus()                                  槽函数,若其父控件为活动窗口,则为此控件(或其焦点代理)设置焦点
.setFocus(reason: Qt.FocusReason)            Qt.FocusReason详见下文
.clearFocus()                                移除控件的焦点
对子控件的焦点的控制: https://doc.qt.io/qt-6/qwidget.html#focusNextPrevChild
.focusNextChild() -> bool
.focusPreviousChild() -> bool
.focusNextPrevChild(next: bool) -> bool      上两种方法的结合,当next为True时向前搜索,否则向后搜索
.focusWidget() -> QWidget
Qt.FocusReason 具体分为如下数种: https://doc.qt.io/qt-6/qt.html#FocusReason-enum
 - Qt.MouseFocusReason           鼠标活动导致
 - Qt.TabFocusReason             按下了Tab键
 - Qt.BacktabFocusReason         Backtab导致,例如按下Shift+Tab键
 - Qt.ActiveWindowFocusReason    窗口系统使该窗口处于活动或非活动状态
 - Qt.PopupFocusReason           应用程序打开/关闭一个弹出窗口,该弹出窗口抓取/释放键盘焦点
 - Qt.ShortcutFocusReason        用户输入了一个标签的伙伴快捷键(参阅QLabel.buddy)
 - Qt.MenuBarFocusReason         菜单栏获得了焦点
 - Qt.OtherFocusReason           其他原因
 Qt.FocusPolicy具体分为如下数种: https://doc.qt.io/qt-6/qt.html#FocusPolicy-enum
 - Qt.TabFocus         通过键盘Tab键获取焦点
 - Qt.ClickFocus       通过鼠标点击获取焦点
 - Qt.StrongFocus      通过键盘Tab或鼠标点击获取焦点
 - Qt.WheelFocus       在StrongFocus基础上,还支持鼠标滚轮滚动获取焦点,若只有一个控件设置为此策略,则需要当前焦点在该控件的上/下一个焦点时才有效
 - Qt.NoFocus          该控件不接受焦点,QLabel等不需要用户键盘操作的控件的默认值

QWidget 光标: https://doc.qt.io/qt-6/qcursor.html
可以自定义光标形状、获取光标位置等
控件默认使用箭头形状光标,Qt还内置提供了许多光标形状(参下方Qt.CursorShape),也可以使用位图自定义光标形状
子控件默认使用与父控件相同的光标形状,也可以单独设置
QWidget.setCursor(QCursor)   设置光标形状
QWidget.unsetCursor()        取消设置光标形状
QWidget.cursor() -> QCursor  获取光标形状
QCursor 类的常用方法:
QCursor.__init__(shape: Qt.CursorShape)      使用Qt内置的光标形状创建
QCursor.pos() -> QPoint                      返回该光标当前所在位置坐标(相对于整个屏幕)
QCursor.setPos(QPoint)                       设置光标位置坐标(相对于屏幕)
QCursor.__init__(pixmap: Union[QPixmap, QImage, str], hotX: int = -1, hotY: int = -1)  使用QPixmap位图创建
Qt.CursorShape具体分为二十余种,以下列举几种: https://doc.qt.io/qt-6/qt.html#CursorShape-enum
Qt.ArrowCursor       标准的箭头光标
Qt.WaitCursor        沙漏或手表光标,通常在阻止用户与应用程序交互的操作期间显示
Qt.IBeamCursor       插入符号或工字形光标,表示控件可以接受并显示文本输入
Qt.SizeFDiagCursor   用于对角调整顶级窗口左上角和右下角大小的元素的光标
Qt.ForbiddenCursor   一种斜线圆圈光标,通常在拖放操作期间使用,以指示拖放的内容不能放在特定控件上或放在特定区域内
Qt.BusyCursor        沙漏或手表光标,通常在操作期间显示,这些操作允许用户在后台执行时与应用程序进行交互

QScrollArea 主要功能在于将另一个控件滚动显示,被显示的控件暂且称为「视图控件」
拖拽ScrollArea控件时会自动带上scrollAreaWidgetContents,可理解为幕布,ScrollArea区域的内容只有在幕布范围上才可见
只要幕布控件scorllAreaWidgetContents的大小超过了QScrollArea的大小,就会出现滚动条(要把ScrollArea的setWidgetResizable改为False)
调用如下方法以将控件设置为滚动区域的视图控件,或获取、移除滚动区域的视图控件
.setWidget(widget: QWidget)          将widget设置为滚动区域的视图控件
.widget() -> QWidget                 返回滚动区域的视图控件
.takeWidget() -> QWidget             移除滚动区域的视图控件,并将该控件的所有权传递给函数调用者
当视图控件尺寸小于滚动区域尺寸时,可以控制视图控件在整个滚动区域中的对齐方式，默认值为对齐至左上
.setAlignment(Qt.Alignment)          设置视图控件在滚动区域中的对齐方式，默认为左上
.alignment() -> Qt.Alignment         返回视图控件在滚动区域中的对齐方式
默认情况下视图控件不可调整大小(False),滚动区域遵循其尺寸,可以通过widget.resize()调整视图控件尺寸,滚动区域将自动调整到新的尺寸
若此属性设置为True,则滚动区域将自动调整视图控件的尺寸,以尽可能避免出现滚动条,或利用额外的空间
.setWidgetResizable(resizable: bool) 设置视图控件可以改变尺寸,默认为False
.widgetResizable() -> bool           获取视图控件尺寸可变状态
调用方法滚动内容,确保滚动区域中的某点或某子控件出现在滚动区域的可见视口内
通过xmargin和ymargin参数控制边距,单位为像素,如果无法达到指定点/子控件,则将内容滚动到最近的有效位置
.ensureVisible(x: int, y: int, xmargin: int = 50, ymargin: int = 50)               确保视图控件内某点可见
.ensureWidgetVisible(child_widget: QWidget, xmargin: int = 50, ymargin: int = 50)  确保视图控件的某个子控件可见
"""


class Worker(QThread):
    task_signal = Signal(int)  # 参数int就代表这个信号可以传一个整数

    def run(self):  # 线程将在run函数返回后退出
        for i in range(2):
            time.sleep(1)
            print("in Worker.run", i)
            self.task_signal.emit(i)  # 发送信号


def wheel_event(self, event: QWheelEvent):
    scroll_bar = self.verticalScrollBar()  # scroll_bar.height() 滚动条长度
    scroll_bar_pos = scroll_bar.value()  # 滚动条头部当前位置
    delta = event.angleDelta().y()  # 滑轮滚动的角度(向前滑是正,向后滑是负)
    new_pos = scroll_bar_pos - 40 * delta // 120
    print("in wheel_event: ", delta)
    scroll_bar.setValue(new_pos)  # 越界会自动忽略


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()  # 调用父类的初始化方法
        self.process = None
        self.main_layout = QtWidgets.QHBoxLayout(self)

        self.set_main_window()
        self.set_menu()
        self.set_label()
        self.set_tab()
        self.set_text()
        self.set_scroll()

        self.setLayout(self.main_layout)

    @QtCore.Slot()
    def magic(self):
        print("click button")
        print(self.cursor().pos())

    def set_main_window(self):
        # 坐标系以「左上角」为原点，向右为x轴正方向，向下为y轴正方向
        # 当QWidget为窗口时,设置/获取其相对桌面的位置; 当QWidget为子控件时,设置/获取其相对父控件的位置
        self.setWindowTitle("测试")
        self.resize(1600, 900)  # 设置窗口大小，单位为像素
        self.setMaximumSize(1500, 1000)  # 限制用户拖拽窗口能达到的最大尺寸
        # self.setFixedSize(500, 500)  # 设置为固定尺寸，用户不再可拖拽改变窗口尺寸
        self.move(100, 50)  # 距离屏幕左上角向右向下平移
        # pixmap = QtGui.QPixmap("../../Resources/Icons/snowflake_128px.ico").scaled(52, 52)
        # my_cursor = QtGui.QCursor(pixmap, 26, 26)  # 以图片像素点位置26,26为热点(光标实际所在位置坐标)
        # self.setCursor(my_cursor)
        self.setCursor(Qt.OpenHandCursor)

        self.process = Worker()  # 创建子线程,如果不保存到实例变量,会在start后立马被销毁,导致线程执行失败
        self.process.task_signal.connect(lambda i: print(f"task_signal:{i}"))
        self.process.finished.connect(lambda: print("finished"))  # 还自带started信号,按钮的clicked也是信号
        self.process.start()

        print(self.x())
        print(self.y())
        print(self.pos())
        print(self.size())  # 返回窗口大小
        print(self.geometry())  # 位置、大小
        print(self.children())  # 以列表形式返回所有子控件,顺序同添加顺序

    def set_menu(self):
        test_menu = QtWidgets.QMenu(self)  # 创建一个菜单
        new_action = QtGui.QAction("新建", test_menu)  # 创建 action
        new_action.triggered.connect(lambda: print("新建文件"))
        exit_action = QtGui.QAction("关闭", test_menu)
        exit_action.triggered.connect(lambda: exit())

        open_url_menu = QtWidgets.QMenu("打开网页")  # 创建子菜单
        url_action_1 = QtGui.QAction("百度", open_url_menu)
        url_action_1.triggered.connect(lambda: QtGui.QDesktopServices.openUrl("https://www.baidu.com/"))
        url_action_2 = QtGui.QAction("QQ", open_url_menu)
        url_action_2.triggered.connect(lambda: QtGui.QDesktopServices.openUrl("https://mail.qq.com/"))

        open_url_menu.addAction(url_action_1)
        open_url_menu.addAction(url_action_2)
        test_menu.addAction(new_action)  # 将actions、子菜单、分割线添加到菜单
        test_menu.addMenu(open_url_menu)  # 将一个菜单添加到另一个菜单中，即成为子菜单
        test_menu.addSeparator()  # 添加分割线
        test_menu.addAction(exit_action)

        button = QtWidgets.QPushButton("菜单按钮", self)
        button.setMenu(test_menu)  # 为按钮设置菜单
        self.main_layout.addWidget(button)

    def set_label(self):
        label = QtWidgets.QLabel("标签控件默认焦点策略为NoFocus", self)  # 父控件为self,故不成为单独窗口,创建一个标签子控件
        # label.move(500, 100)  # 相对父控件(窗口)移动位置
        label.setStyleSheet("background-color: green; font-size: 12px;")  # 设置背景颜色,便于观察控件实际大小
        label.setContentsMargins(5, 0, 0, 0)  # 设置内容边距
        label.setCursor(Qt.ForbiddenCursor)  # 设置label中的光标为Qt内置的其他光标
        self.main_layout.addWidget(label)
        print("label pos: ", label.pos())  # 显示label相对父控件的位置
        print("label's parent: ", label.parentWidget())

    def set_tab(self):
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.resize(600, 500)
        # size_policy = QtWidgets.QSizePolicy()
        # size_policy.setHorizontalStretch(8)  # 设置水平伸展策略
        # scroll_area.setSizePolicy(size_policy)
        scroll_area.setWidgetResizable(True)  # 滚动区域将放大其视图控件尺寸，以充分利用空间

        tab_widget = QtWidgets.QTabWidget(scroll_area)
        tab_one = QtWidgets.QWidget()
        tab_widget.addTab(tab_one, "人")
        tab_two = QtWidgets.QWidget()
        tab_widget.addTab(tab_two, "动物")
        scroll_area.setWidget(tab_widget)  # 将图像标签设置为滚动区域的视图控件
        self.main_layout.addWidget(scroll_area)

        tab_widget.wheelEvent = types.MethodType(wheel_event, scroll_area)

    def set_text(self):
        line_edit = QtWidgets.QLineEdit(self)  # 单行文本编辑器,当获得焦点时可以输入内容
        text_edit = QtWidgets.QTextEdit(self)
        text_edit.setPlaceholderText("这是一个富文本编辑器")
        text_edit.setTabChangesFocus(True)  # 将富文本编辑器中按下Tab键功能设置为切换焦点
        # text_edit.setFocusPolicy(Qt.TabFocus)  # 只能通过键盘Tab键获取焦点
        # text_edit.setFocusPolicy(Qt.ClickFocus)  # 只能通过鼠标点击获取焦点
        text_edit.setFocusPolicy(Qt.StrongFocus)  # 可以通过以上两种方式获取焦点,对于QTextEdit默认策略为Qt.StrongFocus
        # text_edit.setFocusPolicy(Qt.WheelFocus)  # 还可以通过鼠标滚轮滚动获取焦点
        # text_edit.setFocusPolicy(Qt.NoFocus)  # 无法获得焦点,用户无法使用键盘对该控件操作
        self.setTabOrder(text_edit, line_edit)
        self.main_layout.addWidget(line_edit)
        self.main_layout.addWidget(text_edit)

    def set_scroll(self):
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.resize(300, 500)  # 手动指定滚动区域尺寸,而不是由视图控件自动设置
        image_label = QtWidgets.QLabel(scroll_area)
        image_label.setPixmap(QtGui.QPixmap("src/qt.jpg"))
        scroll_area.setWidget(image_label)  # 将图像标签设置为滚动区域的视图控件
        scroll_area.widget().resize(1000, 1000)  # 设置视图控件尺寸
        scroll_area.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)  # 设置为水平居中、垂直靠底部对齐
        # print(scroll_area.takeWidget())  # 将视图控件从滚动区域中移除
        self.main_layout.addWidget(scroll_area)

    def set_common(self):  # 为啥没生效
        common_layout = QtWidgets.QHBoxLayout()
        button = QtWidgets.QPushButton("点击我")  # 创建一个按钮控件,其上文字为"点击我"
        button.clicked.connect(self.magic)  # 将button.clicked这个信号与self.magic槽函数连接
        button.setShortcut(QtGui.QKeySequence(Qt.CTRL | Qt.Key_A))  # 添加 Ctrl+A 的键盘快捷键

        combo_box = QtWidgets.QComboBox()  # 下拉菜单,当获得焦点时可以用键盘方向键上下切换当前所选
        combo_box.addItem("选项1")
        combo_box.addItem("选项2")

        common_layout.addWidget(button)
        common_layout.addWidget(combo_box)
        self.main_layout.addLayout(common_layout)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = MyWidget()  # 实例化一个MyWidget类对象
    widget.show()  # 显示窗口
    app.exec()
