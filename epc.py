#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  4 13:50:45 2021

@author: mlnunes
"""

from PyQt5 import QtWidgets, uic, QtCore
import sys
from os import getenv
from shutil import copyfile
import utm
import geopandas as gpd
from shapely.geometry import Polygon
import elevation
import rasterio
import numpy as np
from scipy.io import savemat
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import json    


def do_export_file(dist, elev, s, t, f):
    if t =='.mat':
        mdic = {'distance': dist, 'elevation': elev,\
                "label": ("elevaton profile sampled at "+ str(s) + "m")}
        savemat((f + t), mdic)
    else:
        np.savez_compressed( f , distance = dist, elevation = elev, label = ("elevaton profile sampled at "+ str(s) + "m"))
    
    msgBox = QtWidgets.QMessageBox()
    msgBox.setIcon(QtWidgets.QMessageBox.Information)
    msgBox.setText("Your profile was saved!")
    msgBox.setWindowTitle("EPC")
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msgBox.exec()


def deltas (pt1, pt2, step):
        alpha = ((pt2[1] - pt1[1]) / (pt2[0] - pt1[0]))    
        beta = pt2[1] - (alpha * pt2[0])
        m = beta  - pt1[1]
        a = (1 + alpha ** 2 )
        b = (2 * alpha * m - 2 * pt1[0])
        c = m ** 2 - step ** 2 + pt1[0] ** 2
        x1 = (-b + (( b ** 2 - 4 * a * c) ** 0.5)) / (2 * a)
        x2 = (-b - (( b ** 2 - 4 * a * c) ** 0.5)) / (2 * a)    
        y1 = alpha * x1 + beta
        y2 = alpha * x2 + beta
        dx1 = x1 - pt1[0]
        dy1 = y1 - pt1[1]
        dx2 = x2 - pt1[0]
        dy2 = y2 - pt1[1]
        if pt1[0] > pt2[0]:
            if dx1 < dx2:
                dx = dx1
            else:
                dx = dx2
        else:
            if dx1 > dx2:
                dx = dx1
            else:
                dx = dx2
        if pt1[1] > pt2[1]:
            if dy1 < dy2:
                dy = dy1
            else:
                dy = dy2
        else:
            if dy1 > dy2:
                dy = dy1
            else:
                dy = dy2
        return ((dx, dy))

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('epc_main.ui', self) # Load the .ui file
        self.pushButton.setText('GET')
        self.pushButton_2.setText('Quit')
        self.comboBox.addItem('N')
        self.comboBox.addItem('S')
        self.comboBox_2.addItem('E')
        self.comboBox_2.addItem('W')
        self.comboBox_3.addItem('N')
        self.comboBox_3.addItem('S')
        self.comboBox_4.addItem('E')
        self.comboBox_4.addItem('W')
        self.read_param()
        self.pushButton.clicked.connect(self.get_profile)
        self.pushButton_2.clicked.connect(self.close)
        self.show() # Show the GUI
        
        
    def read_param(self):
        with open('conf_par.json') as json_conf : 
            conf = json.load(json_conf)
        self.spinBox.setValue(conf['station1']['lat']['g'])
        self.spinBox_2.setValue(conf['station1']['lat']['m'])
        self.doubleSpinBox.setValue(conf['station1']['lat']['s'])
        self.comboBox.setCurrentIndex((conf['station1']['lat']['i']))
        self.spinBox_3.setValue(conf['station1']['lon']['g'])
        self.spinBox_4.setValue(conf['station1']['lon']['m'])
        self.doubleSpinBox_2.setValue(conf['station1']['lon']['s'])
        self.comboBox_2.setCurrentIndex((conf['station2']['lon']['i']))
        self.spinBox_5.setValue(conf['station2']['lat']['g'])
        self.spinBox_6.setValue(conf['station2']['lat']['m'])
        self.doubleSpinBox_3.setValue(conf['station2']['lat']['s'])
        self.comboBox_3.setCurrentIndex((conf['station2']['lat']['i']))
        self.spinBox_7.setValue(conf['station2']['lon']['g'])
        self.spinBox_8.setValue(conf['station2']['lon']['m'])
        self.doubleSpinBox_4.setValue(conf['station2']['lon']['s'])
        self.comboBox_4.setCurrentIndex((conf['station2']['lon']['i']))
        
        
    def save_param(self):
        with open('conf_par.json') as json_conf : 
            conf = json.load(json_conf)
        
        conf['station1']['lat']['g'] = self.spinBox.value()
        conf['station1']['lat']['m'] = self.spinBox_2.value()
        conf['station1']['lat']['s'] = self.doubleSpinBox.value()
        conf['station1']['lat']['i'] = self.comboBox.currentIndex()
        conf['station1']['lon']['g'] = self.spinBox_3.value()
        conf['station1']['lon']['m'] = self.spinBox_4.value()
        conf['station1']['lon']['s'] = self.doubleSpinBox_2.value()
        conf['station2']['lon']['i'] = self.comboBox_2.currentIndex()
        conf['station2']['lat']['g'] = self.spinBox_5.value()
        conf['station2']['lat']['m'] = self.spinBox_6.value()
        conf['station2']['lat']['s'] = self.doubleSpinBox_3.value()
        conf['station2']['lat']['i'] = self.comboBox_3.currentIndex()
        conf['station2']['lon']['g'] = self.spinBox_7.value()
        conf['station2']['lon']['m'] = self.spinBox_8.value()
        conf['station2']['lon']['s'] = self.doubleSpinBox_4.value()
        conf['station2']['lon']['i'] = self.comboBox_4.currentIndex()
        conf_file = open("conf_par.json", "w")
        json.dump(conf, conf_file)
        conf_file.close()

    def back_main(self):
        uic.loadUi('epc_main.ui', self)
        self.pushButton.setText('GET')
        self.pushButton_2.setText('Quit')
        self.comboBox.addItem('N')
        self.comboBox.addItem('S')
        self.comboBox_2.addItem('E')
        self.comboBox_2.addItem('W')
        self.comboBox_3.addItem('N')
        self.comboBox_3.addItem('S')
        self.comboBox_4.addItem('E')
        self.comboBox_4.addItem('W')
        self.pushButton.clicked.connect(self.get_profile)
        self.pushButton_2.clicked.connect(self.close)
        widget = QtWidgets.QWidget()
        widget.setLayout(self.Layout_main)
        self.setCentralWidget(widget)
        self.read_param()
        QtWidgets.QApplication.restoreOverrideCursor()
        self.show()
        
      
    def get_profile(self):
        self.save_param()
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        tx_lat = self.spinBox.value() + self.spinBox_2.value() / 60 + \
            self.doubleSpinBox.value()/3600
        tx_lat = -tx_lat if self.comboBox.currentText() == 'S' else tx_lat
        tx_lon = self.spinBox_3.value() + self.spinBox_4.value() / 60 + \
            self.doubleSpinBox_2.value()/3600
        tx_lon = -tx_lon if self.comboBox_2.currentText() == 'W' else tx_lon
        rx_lat = self.spinBox_5.value() + self.spinBox_6.value() / 60 + \
            self.doubleSpinBox_3.value()/3600
        rx_lat = -rx_lat if self.comboBox_3.currentText() == 'S' else rx_lat
        rx_lon = self.spinBox_7.value() + self.spinBox_8.value() / 60 + \
            self.doubleSpinBox_4.value()/3600
        rx_lon = -rx_lon if self.comboBox_4.currentText() == 'W' else rx_lon
        
        tx = (tx_lon, tx_lat)
        rx = (rx_lon, rx_lat)
        print (rx)
        print (tx)
        home_dir = getenv('HOME')
        projecao = utm.from_latlon(tx[1], tx[0])
        txU = (projecao[0], projecao[1])
        zone_number = projecao[2]
        zone_letter = projecao[3]
        ummin = 1/60
        projecao = utm.from_latlon(rx[1], rx[0])
        rxU = (projecao[0], projecao[1])
        box_lon_min = (rx[0] if rx[0] < tx[0] else tx[0])-ummin
        box_lon_max = (rx[0] if rx[0] > tx[0] else tx[0])+ummin
        box_lat_min = (rx[1] if rx[1] < tx[1] else tx[1])-ummin
        box_lat_max = (rx[1] if rx[1] > tx[1] else tx[1])+ummin
        box = gpd.GeoSeries(Polygon([(box_lon_min, box_lat_min), (box_lon_max, box_lat_min), (box_lon_max, box_lat_max), (box_lon_min, box_lat_max)]))
        df1 = gpd.GeoDataFrame({'geometry': box, 'df1':[1]})
        bounds = df1.unary_union.bounds
        elevation.clip(bounds = bounds,output='terreno.tif',product='SRTM1')
        arquivo = copyfile(home_dir+'/.cache/elevation/SRTM1/terreno.tif', 'terreno.tif')
        raster = rasterio.open(arquivo)
        band1 = raster.read(1)
        distancia = ((txU[0]-rxU[0])**2+(txU[1]-rxU[1])**2)**0.5
        row , col = raster.index(rx[0], rx[1])
        perfil_elevacao=[]
        perfil_distancia = np.arange(0, distancia, 1)
        perfil_distancia = np.append(perfil_distancia, distancia)
        
        qxs = []
        qys = []
        delta_lat, delta_lon = deltas(txU, rxU, 1)
        print(txU, rxU, delta_lat, delta_lon, len(perfil_distancia))
        print(zone_number, zone_letter)
        for n in range(1, len(perfil_distancia) + 1):
            qx = txU[0] + delta_lat * n 
            qy = txU[1] + delta_lon * n
            projecao = utm.to_latlon(qx, qy,  zone_number, zone_letter)
            qx = projecao[1]
            qy = projecao[0]
            qxs.append(qx)
            qys.append(qy)
            row , col = raster.index(qx, qy)
            perfil_elevacao=np.append(perfil_elevacao, band1[row, col])
        
        
        range_elevacao = perfil_elevacao.max() - perfil_elevacao.min()
        sc = MplCanvas(self, width=5, height=4, dpi=100)
        sc.axes.fill_between(perfil_distancia, perfil_elevacao, (perfil_elevacao.min() - 0.1 * range_elevacao), color='brown')
        sc.axes.fill_between(perfil_distancia, perfil_elevacao, (perfil_elevacao.max() + 0.1 * range_elevacao), color='skyblue')
        toolbar = NavigationToolbar(sc, self)
        exportButton = QtWidgets.QPushButton("Export")
        backButton = QtWidgets.QPushButton("Back")
        export_sample = QtWidgets.QSpinBox()
        export_sample.setMaximum(1000)
        export_sample.setValue(1)
        export_sample_label = QtWidgets.QLabel('Output sample (m):')
        export_file = QtWidgets.QComboBox()
        export_file.addItem('.mat')
        export_file.addItem('.npz')
        export_file_label = QtWidgets.QLabel('File type:')
        export_file_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        export_filename_label = QtWidgets.QLabel('File name:')
        export_filename = QtWidgets.QLineEdit('output_file')
        
        exportButton.clicked.connect(lambda: do_export_file(perfil_distancia, \
                                    perfil_elevacao, export_sample.value(), export_file.currentText(), \
                                    export_filename.text()))
        
        backButton.clicked.connect(self.back_main)    
            
        layout_2 = QtWidgets.QHBoxLayout()
        layout_2.addWidget(export_sample_label)
        layout_2.addWidget(export_sample)
        layout_2.addWidget(export_file_label)
        layout_2.addWidget(export_file)
        layout_3 = QtWidgets.QHBoxLayout()
        layout_3.addWidget(export_filename_label)
        layout_3.addWidget(export_filename)
        layout_4 = QtWidgets.QHBoxLayout()
        layout_4.addWidget(exportButton)
        layout_4.addWidget(backButton)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(sc)
        layout.addLayout(layout_2)
        layout.addLayout(layout_3)
        layout.addLayout(layout_4)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        QtWidgets.QApplication.restoreOverrideCursor()
        self.show()

app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()