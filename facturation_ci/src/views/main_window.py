from PyQt6 import QtCore, QtGui, QtWidgets
from .page._main_window import Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow):
	"""docstring for MainWindow"""
	def __init__(self, arg=None):
		super(MainWindow, self).__init__()
		self.arg = arg

		self.ui = Ui_MainWindow();
		self.ui.setupUi(self);




if __name__ == '__main__':
	import sys
	App = QtWidgets.QApplication(sys.argv);
	Win = MainWindow()
	Win.show()
	sys.exit(App.exec());


