from PyQt6 import QtCore, QtGui, QtWidgets
from .page._dashboard_view import Ui_DashboardView

class MainWindow(QtWidgets.QMainWindow):
	"""docstring for MainWindow"""
	def __init__(self, arg=None):
		super(MainWindow, self).__init__()
		self.arg = arg

		self.ui = Ui_DashboardView();
		self.ui.setupUi(self);




if __name__ == '__main__':
	import sys
	App = QtWidgets.QApplication(sys.argv);
	Win = MainWindow()
	Win.show()
	sys.exit(App.exec());


