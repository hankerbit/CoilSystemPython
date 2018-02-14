﻿from PyQt5 import uic
from PyQt5.QtCore import QFile, QRegExp, QTimer, Qt, pyqtSlot
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMenu, QMessageBox
from fieldManager import FieldManager
from vision import Vision
from s826 import S826
from subThread import SubThread
import syntax
#=========================================================
# UI Config
#=========================================================
qtCreatorFile = "mainwindow.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
#=========================================================
# Creating instances of fieldManager and Camera
#=========================================================
field = FieldManager(S826())
vision = Vision()
#=========================================================
# a class that handles the signal and callbacks of the GUI
#=========================================================
class GUI(QMainWindow,Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self,None,Qt.WindowStaysOnTopHint)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.setupTimer()
        self.setupSubThread(field,vision)
        self.setupFileMenu()
        self.connectSignals()
        self.linkWidgets()

        self.currentFilePath = '' # directory to store the vision editor

    #=====================================================
    # [override] terminate the subThread and clear currents when closing the window
    #=====================================================
    def closeEvent(self,event):
        self.thrd.stop()
        self.clearField()
        event.accept()

    #=====================================================
    # QTimer handles updates of the GUI, run at 60Hz
    #=====================================================
    def setupTimer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(5) # msec

    def update(self):
        vision.updateFrame()

    #=====================================================
    # Connect buttons etc. of the GUI to callback functions
    #=====================================================
    def connectSignals(self):
        # General Control Tab
        self.dsb_x.valueChanged.connect(self.setFieldXYZ)
        self.dsb_y.valueChanged.connect(self.setFieldXYZ)
        self.dsb_z.valueChanged.connect(self.setFieldXYZ)
        self.btn_clearCurrent.clicked.connect(self.clearField)
        # Vision Tab
        self.highlighter = syntax.Highlighter(self.editor_vision.document())
        self.chb_bypassFilters.toggled.connect(self.on_chb_bypassFilters)
        self.chb_startPauseCapture.toggled.connect(self.on_chb_startPauseCapture)
        self.btn_refreshFilterRouting.clicked.connect(self.on_btn_refreshFilterRouting)
        self.chb_objectDetection.toggled.connect(self.on_chb_objectDetection)

        # Subthread Tab
        self.chb_startStopSubthread.toggled.connect(self.on_chb_startStopSubthread)
        self.dsb_freq.valueChanged.connect(self.thrd.setFreq)

    #=====================================================
    # Link GUI elements
    #=====================================================
    def linkWidgets(self):
        # link slider to doubleSpinBox
        self.dsb_x.valueChanged.connect(lambda value: self.hsld_x.setValue(int(value*100)))
        self.dsb_y.valueChanged.connect(lambda value: self.hsld_y.setValue(int(value*100)))
        self.dsb_z.valueChanged.connect(lambda value: self.hsld_z.setValue(int(value*100)))
        self.hsld_x.valueChanged.connect(lambda value: self.dsb_x.setValue(float(value/100)))
        self.hsld_y.valueChanged.connect(lambda value: self.dsb_y.setValue(float(value/100)))
        self.hsld_z.valueChanged.connect(lambda value: self.dsb_z.setValue(float(value/100)))

    #=====================================================
    # Thread Example
    #=====================================================
    def setupSubThread(self,field,vision):
        self.thrd = SubThread(field,vision)
        self.thrd.statusSignal.connect(self.updateSubThreadStatus)
        self.thrd.finished.connect(self.finishSubThreadProcess)

    # updating GUI according to the status of the subthread
    @pyqtSlot(str)
    def updateSubThreadStatus(self, receivedStr):
        print('Received message from subthread: ',receivedStr)
        # show something on GUI

    # run when the subthread is termianted
    @pyqtSlot()
    def finishSubThreadProcess(self):
        print('Subthread is terminated.')
        self.clearField()
        # disable some buttons etc.

    #=====================================================
    # File Menu
    #=====================================================
    def setupFileMenu(self):
        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)
        fileMenu.addAction("&New Editor", self.newFile, "Ctrl+N")
        fileMenu.addAction("&Open Editor...", self.openFile, "Ctrl+O")
        fileMenu.addAction("&Save Editor", self.saveFile, "Ctrl+S")
        fileMenu.addAction("E&xit", QApplication.instance().quit, "Ctrl+Q")

    def newFile(self):
        self.editor_vision.clear()
        self.currentFilePath = ''

    def openFile(self, path=None):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", '',
                "txt Files (*.txt)")

    def saveFile(self):
        if self.currentFilePath == '':
            self.currentFilePath, _ = QFileDialog.getSaveFileName(self, "Save file", '',
                    "txt Files (*.txt)")
        path = self.currentFilePath
        saveFile = open(path, "w")
        text = str(self.editor_vision.toPlainText())
        saveFile.write(text)
        saveFile.close()
    #=====================================================
    # Callback Functions
    #=====================================================
    # General control tab
    def setFieldXYZ(self):
        field.setX(self.dsb_x.value())
        field.setY(self.dsb_y.value())
        field.setZ(self.dsb_z.value())

    def clearField(self):
        self.dsb_x.setValue(0)
        self.dsb_y.setValue(0)
        self.dsb_z.setValue(0)
        field.setXYZ(0,0,0)

    # vision tab
    def on_chb_bypassFilters(self,state):
        vision.setStateFiltersBypass(state)

    def on_chb_startPauseCapture(self,state):
        vision.setStateUpdate(state)

    def on_btn_refreshFilterRouting(self):
        vision.createFilterRouting(self.editor_vision.toPlainText().splitlines())

    def on_chb_objectDetection(self,state):
        vision.setStateObjectDetection(state)

    # subthread
    def on_chb_startStopSubthread(self,state):
        if state:
            self.thrd.setup()
            self.thrd.start()
            print('Subthread starts.')
        else:
            self.thrd.stop()
