import sys
from PyQt5 import QtWidgets, QtCore, Qt
from PyQt5.QtWidgets import qApp, QMessageBox, QDialog, QListWidget, QListWidgetItem
from yapgrep_gui import Ui_MainWindow
from yapgrep_common_gui import Ui_Common
import os
import glob
import regex
from timeit import default_timer as timer
from icecream import ic
from datetime import datetime
import argparse
import html
import json


types = {}  # type dict from json file


def unixTimestamp():
    return '%s |> ' % datetime.now()

ic.configureOutput(prefix=unixTimestamp)


class YapgrepGuiProgram(Ui_MainWindow):
    def __init__(self, MainWindow):
        super().__init__()

        self.version = 0.5

        self.setupUi(MainWindow)

        self.Common = QDialog()
        self.ui2 = Ui_Common()
        self.ui2.setupUi(self.Common)

        self.recursive = True
        self.ignorecase = False
        self.linenumber = False
        self.column = False
        self.ui2.checkBox.setChecked(self.recursive)
        self.ui2.checkBox_2.setChecked(self.ignorecase)
        self.ui2.checkBox_3.setChecked(self.linenumber)
        self.ui2.checkBox_4.setChecked(self.column)

        self.statusbar.showMessage('ready')

        self.typeList = []   # list of file exts

        f = self.textEdit.font()
        f.setFamily("Courier New")
        f.setPointSize(18)
        self.textEdit.setFont(f)

        self.textEdit.append('yapgrep {}'.format(self.version))

        self.actionQuit.triggered.connect(self.exitCall)
        self.actionGo.triggered.connect(self.search)
        self.pushButton.clicked.connect(self.search)
        self.actionCommon.triggered.connect(self.common_settings)
        self.actionAbout.triggered.connect(self.about)

    def common_settings(self):
        self.Common.exec_()
        self.recursive = self.ui2.checkBox.isChecked()
        self.ignorecase = self.ui2.checkBox_2.isChecked()
        self.linenumber = self.ui2.checkBox_3.isChecked()
        self.column = self.ui2.checkBox_4.isChecked()

    def about(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Yapygrep " + str(self.version))
#        msg.setInformativeText("This is additional information")
        msg.setWindowTitle("About")
#        msg.setDetailedText("The details are as follows:")

        msg.exec_()

    def search(self):
        self.files = 0
        self.matches = 0
        self.statusbar.showMessage('Searching . . .')
        self.textEdit.clear()
        directory = self.lineEdit.text()
        pattern = self.lineEdit_2.text()
        pattern = '(' + pattern + ')'
        if self.ignorecase:
            reg = regex.compile(pattern, flags=regex.IGNORECASE)
        else:
            reg = regex.compile(pattern)

        for d in directory.split(':'):
            self.start = timer()
            ic('Directory from user: {}'.format(d))

            try:
                self.walkDirs(d, reg)
            except:
                ic("Some error occurred!".join(sys.exc_info()))
            self.end = timer()
            self.textEdit.append('Time: {:.2f}'.format(self.end - self.start))

        self.statusbar.showMessage('Searching completed.')

    def checkExtInTypeList(self, ext):
        if self.typeList == []:
            return True

        if ext[1:] in self.typeList:
            return True

        return False


    def walkDirs(self, fileSpec, pattern):
        fs = os.path.expanduser(fileSpec)
        ic(fs)

        fs = os.path.expandvars(fs)
        ic(fs)

        base = os.path.basename(fs)
        ic(base)

        path = os.path.dirname(fs)
        ic(path)

        if os.path.isdir(fs):
            fs += '/**'
        elif os.path.isdir(path):
            fs = path + '/**/' + base

        global types
        self.typeList = []
        for i in range(ui.ui2.listWidget.count()):
            if ui.ui2.listWidget.item(i).checkState() == QtCore.Qt.Checked:
                self.typeList += types[str(ui.ui2.listWidget.item(i).text())]
                ic(types[str(ui.ui2.listWidget.item(i).text())])

        ic(fs)
        ic(self.recursive)
        ic(self.ignorecase)

        for p in glob.iglob(fs, recursive=self.recursive):
            (root, ext) = os.path.splitext(p)
            if os.path.isfile(p) and self.checkExtInTypeList(ext):
                buf = self.grepFile(p, pattern)
                if buf:
                    self.textEdit.append('file: {}'.format(p))
                    self.textEdit.append("".join(buf))

        ic(fs)
        self.textEdit.append('Files searched: {}, Matches found: {}'.format(self.files, self.matches))
        ic('Files searched: {}, Matches found: {}'.format(self.files, self.matches))
        self.files,self.matches = 0,0

    def grepFile(self, fileName, pattern):
        global app
        self.statusbar.showMessage(fileName)
        app.processEvents()
        buf = []
        with open(fileName, 'r') as f:
            try:
                self.files += 1
                for i, line in enumerate(f):
                    if pattern.search(line):
                        self.matches += 1
                        # escape HTML in line
                        line = html.escape(line)
                        newLine = regex.sub(pattern, r'<font color="red"><b>\1</b></font>', line)
                        if self.linenumber:
                            if self.column:
                                for m in regex.finditer(pattern, line):
                                    c = m.start()
                                    break
                                buf.append('&nbsp;&nbsp;&nbsp;&nbsp;{}:{}<br>'.format('<font color="blue">'+str(i)+":"+str(c)+'</font>', newLine))
                            else:
                                buf.append('&nbsp;&nbsp;&nbsp;&nbsp;{}:{}<br>'.format('<font color="blue">'+str(i)+'</font>', newLine))
                        else:
                            buf.append('&nbsp;&nbsp;&nbsp;&nbsp;{}<br>'.format(newLine))
            except UnicodeDecodeError:
                pass
        return buf

    def exitCall(self):
        self.statusbar.showMessage('Exit app')
        qApp.quit()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-r", "-R", "--recurse", help="recurse down the directory tree", action="store_true", default=True)
    argparser.add_argument("-n", "--no-recurse", help="don't recurse down the directory tree", action="store_false", dest="recurse")
    argparser.add_argument("-g", "--go", help="implicitly push the search button", action="store_true")
    argparser.add_argument("-t", "--type", help="specify filetypes for search", action="append", dest="ftype")
    argparser.add_argument("-i", "--ignorecase", help="ignore case of search term", action="store_true")
    argparser.add_argument("-l", "--line-number", help="print line number of each line that contains a match", action="store_true", dest="linenumber")
    argparser.add_argument("-c", "--column", help="print column number of each line that contains a match", action="store_true")
    argparser.add_argument("--help-types", "--list-file-types", help="print file types and exit", action="store_true", dest="helptypes")

    argparser.add_argument("pattern", nargs="?", default="")
    argparser.add_argument("filedirs", nargs="*", default=[os.getcwd()])
    args = argparser.parse_args()

    if args.helptypes:
        with open('types.json', 'r') as f:
            types = json.load(f)

            for t in types:
                print(t, ':', types[t])

        sys.exit(1)

    ic(args.filedirs)

    MainWindow = QtWidgets.QMainWindow()

    ui = YapgrepGuiProgram(MainWindow)

    ic(args)
    ic(args.recurse)
    ui.recursive = args.recurse
    ui.ignorecase = args.ignorecase
    ui.linenumber = args.linenumber
    ui.column = args.column

    ui.ui2.checkBox.setChecked(ui.recursive)
    ui.ui2.checkBox_2.setChecked(ui.ignorecase)
    ui.ui2.checkBox_3.setChecked(ui.linenumber)
    ui.ui2.checkBox_4.setChecked(ui.column)
    ui.lineEdit.setText(QtCore.QCoreApplication.translate("MainWindow", ':'.join(args.filedirs)))
    ui.lineEdit_2.setText(QtCore.QCoreApplication.translate("MainWindow", args.pattern))

    MainWindow.show()

    # Read in valid types
    with open('types.json', 'r') as f:
        types = json.load(f)

        for t in types:
            wi = QListWidgetItem(t)
            wi.setCheckState(QtCore.Qt.Unchecked)
            ui.ui2.listWidget.addItem(wi)

    # Find user selected type
    if args.ftype is not None:
        for t in args.ftype:
            if t in types:
                ui.typeList += types[t]
                ic(ui.typeList)
                item = ui.ui2.listWidget.findItems(t, QtCore.Qt.MatchExactly)

                if item:
                    item[0].setCheckState(QtCore.Qt.Checked)
            else:
                msg = 'User specified type not found: {}'.format(t)
                ic(msg)
                ui.textEdit.append('<font color="red">{}</font>'.format(msg))

    if args.go:
        if len(args.pattern) > 0:
            ui.search()
        else:
            ui.textEdit.append('<font color="red">No pattern specified</font>')

    sys.exit(app.exec_())
