#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Silversat Packet Receiver
# Author: Tom Conrad
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
import math
from gnuradio import blocks
from gnuradio import blocks, gr
from gnuradio import digital
from gnuradio import filter
from gnuradio import eng_notation
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from math import pi
import datetime
import os
import passdata_playback_epy_block_0 as epy_block_0  # embedded python block
import passdata_playback_epy_block_1 as epy_block_1  # embedded python block
import passdata_playback_epy_block_2 as epy_block_2  # embedded python block
import passdata_playback_epy_block_4 as epy_block_4  # embedded python block
import pathlib
import sip
import threading



class passdata_playback(gr.top_block, Qt.QWidget):

    def __init__(self, access_threshold=3, capture_session_id=0, doppler_en=0, frequency_offset=0, output_path='received_files/', processing_run_id=0, source_file=os.path.join(os.getenv('SILVERSAT_ROOT'), "captures/20260112_233622.557094.wav"), store_packets=0):
        gr.top_block.__init__(self, "Silversat Packet Receiver", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Silversat Packet Receiver")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "passdata_playback")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Parameters
        ##################################################
        self.access_threshold = access_threshold
        self.capture_session_id = capture_session_id
        self.doppler_en = doppler_en
        self.frequency_offset = frequency_offset
        self.output_path = output_path
        self.processing_run_id = processing_run_id
        self.source_file = source_file
        self.store_packets = store_packets

        ##################################################
        # Variables
        ##################################################
        self.symbol_rate = symbol_rate = 9600
        self.samples_per_symbol = samples_per_symbol = 16
        self.project_root = project_root = os.getenv('SILVERSAT_ROOT')
        self.transition = transition = 1000
        self.tle_file = tle_file = os.path.join(project_root, 'default.tle')
        self.symbol_sample_rate = symbol_sample_rate = symbol_rate*samples_per_symbol
        self.squelch = squelch = -60
        self.samp_rate = samp_rate = symbol_rate*16
        self.oversample = oversample = 16*8
        self.fsk_deviation_hz = fsk_deviation_hz = symbol_rate/2*0.5
        self.freq = freq = 437175
        self.decimation = decimation = 1
        self.chan_bw = chan_bw = (1+0.5)*symbol_rate
        self.center_diff = center_diff = 0
        self.TED_bandwidth = TED_bandwidth = 0.1

        ##################################################
        # Blocks
        ##################################################

        self.tab0 = Qt.QTabWidget()
        self.tab0_widget_0 = Qt.QWidget()
        self.tab0_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tab0_widget_0)
        self.tab0_grid_layout_0 = Qt.QGridLayout()
        self.tab0_layout_0.addLayout(self.tab0_grid_layout_0)
        self.tab0.addTab(self.tab0_widget_0, '0')
        self.top_layout.addWidget(self.tab0)
        self._squelch_range = qtgui.Range(-100, -20, 1, -60, 100)
        self._squelch_win = qtgui.RangeWidget(self._squelch_range, self.set_squelch, "'squelch'", "counter", float, QtCore.Qt.Horizontal)
        self.tab0_grid_layout_0.addWidget(self._squelch_win, 0, 3, 2, 1)
        for r in range(0, 2):
            self.tab0_grid_layout_0.setRowStretch(r, 1)
        for c in range(3, 4):
            self.tab0_grid_layout_0.setColumnStretch(c, 1)
        self._center_diff_tool_bar = Qt.QToolBar(self)

        if None:
            self._center_diff_formatter = None
        else:
            self._center_diff_formatter = lambda x: eng_notation.num_to_str(x)

        self._center_diff_tool_bar.addWidget(Qt.QLabel("'center_diff'"))
        self._center_diff_label = Qt.QLabel(str(self._center_diff_formatter(self.center_diff)))
        self._center_diff_tool_bar.addWidget(self._center_diff_label)
        self.top_layout.addWidget(self._center_diff_tool_bar)
        self.qtgui_waterfall_sink_x_0 = qtgui.waterfall_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            (samp_rate/8), #bw
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0.set_update_time(0.10)
        self.qtgui_waterfall_sink_x_0.enable_grid(False)
        self.qtgui_waterfall_sink_x_0.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_0.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_0.set_line_alpha(i, alphas[i])

        self.qtgui_waterfall_sink_x_0.set_intensity_range(-140, 20)

        self._qtgui_waterfall_sink_x_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0.qwidget(), Qt.QWidget)

        self.tab0_grid_layout_0.addWidget(self._qtgui_waterfall_sink_x_0_win, 1, 1, 1, 1)
        for r in range(1, 2):
            self.tab0_grid_layout_0.setRowStretch(r, 1)
        for c in range(1, 2):
            self.tab0_grid_layout_0.setColumnStretch(c, 1)
        self.qtgui_time_sink_x_1_0_0_0 = qtgui.time_sink_f(
            512, #size
            symbol_rate, #samp_rate
            'symbols', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_1_0_0_0.set_update_time(0.10)
        self.qtgui_time_sink_x_1_0_0_0.set_y_axis(-1, 2)

        self.qtgui_time_sink_x_1_0_0_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_1_0_0_0.enable_tags(False)
        self.qtgui_time_sink_x_1_0_0_0.set_trigger_mode(qtgui.TRIG_MODE_TAG, qtgui.TRIG_SLOPE_POS, 0.5, 0, 0, 'squelch_sob')
        self.qtgui_time_sink_x_1_0_0_0.enable_autoscale(False)
        self.qtgui_time_sink_x_1_0_0_0.enable_grid(True)
        self.qtgui_time_sink_x_1_0_0_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_1_0_0_0.enable_control_panel(False)
        self.qtgui_time_sink_x_1_0_0_0.enable_stem_plot(False)

        self.qtgui_time_sink_x_1_0_0_0.disable_legend()

        labels = ['clock', 'symbol sync', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_1_0_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_1_0_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_1_0_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_1_0_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_1_0_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_1_0_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_1_0_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_1_0_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_1_0_0_0.qwidget(), Qt.QWidget)
        self.tab0_grid_layout_0.addWidget(self._qtgui_time_sink_x_1_0_0_0_win, 2, 1, 1, 1)
        for r in range(2, 3):
            self.tab0_grid_layout_0.setRowStretch(r, 1)
        for c in range(1, 2):
            self.tab0_grid_layout_0.setColumnStretch(c, 1)
        self.qtgui_time_sink_x_1_0_0 = qtgui.time_sink_f(
            512, #size
            symbol_rate, #samp_rate
            'symbol sync', #name
            2, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_1_0_0.set_update_time(0.10)
        self.qtgui_time_sink_x_1_0_0.set_y_axis(-4, 4)

        self.qtgui_time_sink_x_1_0_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_1_0_0.enable_tags(False)
        self.qtgui_time_sink_x_1_0_0.set_trigger_mode(qtgui.TRIG_MODE_TAG, qtgui.TRIG_SLOPE_POS, 0.5, 0, 0, 'squelch_sob')
        self.qtgui_time_sink_x_1_0_0.enable_autoscale(False)
        self.qtgui_time_sink_x_1_0_0.enable_grid(False)
        self.qtgui_time_sink_x_1_0_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_1_0_0.enable_control_panel(False)
        self.qtgui_time_sink_x_1_0_0.enable_stem_plot(False)

        self.qtgui_time_sink_x_1_0_0.disable_legend()

        labels = ['clock', 'symbol sync', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(2):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_1_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_1_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_1_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_1_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_1_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_1_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_1_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_1_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_1_0_0.qwidget(), Qt.QWidget)
        self.tab0_grid_layout_0.addWidget(self._qtgui_time_sink_x_1_0_0_win, 3, 0, 1, 1)
        for r in range(3, 4):
            self.tab0_grid_layout_0.setRowStretch(r, 1)
        for c in range(0, 1):
            self.tab0_grid_layout_0.setColumnStretch(c, 1)
        self.qtgui_time_sink_x_0_1 = qtgui.time_sink_f(
            10240, #size
            samp_rate/100, #samp_rate
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0_1.set_update_time(0.10)
        self.qtgui_time_sink_x_0_1.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_0_1.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0_1.enable_tags(True)
        self.qtgui_time_sink_x_0_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.01, 0, 0, 'squelch_sob')
        self.qtgui_time_sink_x_0_1.enable_autoscale(True)
        self.qtgui_time_sink_x_0_1.enable_grid(True)
        self.qtgui_time_sink_x_0_1.enable_axis_labels(True)
        self.qtgui_time_sink_x_0_1.enable_control_panel(False)
        self.qtgui_time_sink_x_0_1.enable_stem_plot(False)


        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0_1.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0_1.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0_1.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0_1.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0_1.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0_1.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_1_win = sip.wrapinstance(self.qtgui_time_sink_x_0_1.qwidget(), Qt.QWidget)
        self.tab0_grid_layout_0.addWidget(self._qtgui_time_sink_x_0_1_win, 2, 3, 1, 1)
        for r in range(2, 3):
            self.tab0_grid_layout_0.setRowStretch(r, 1)
        for c in range(3, 4):
            self.tab0_grid_layout_0.setColumnStretch(c, 1)
        self.qtgui_time_sink_x_0_0 = qtgui.time_sink_f(
            (256*8), #size
            symbol_sample_rate, #samp_rate
            'post gaussian filter', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0_0.set_y_axis(-2, 2)

        self.qtgui_time_sink_x_0_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0_0.enable_tags(True)
        self.qtgui_time_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_TAG, qtgui.TRIG_SLOPE_POS, 0.5, 0, 0, 'squelch_sob')
        self.qtgui_time_sink_x_0_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0_0.enable_grid(True)
        self.qtgui_time_sink_x_0_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0_0.enable_stem_plot(False)

        self.qtgui_time_sink_x_0_0.disable_legend()

        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0_0.qwidget(), Qt.QWidget)
        self.tab0_grid_layout_0.addWidget(self._qtgui_time_sink_x_0_0_win, 4, 1, 1, 1)
        for r in range(4, 5):
            self.tab0_grid_layout_0.setRowStretch(r, 1)
        for c in range(1, 2):
            self.tab0_grid_layout_0.setColumnStretch(c, 1)
        self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
            (256*8*6), #size
            symbol_sample_rate, #samp_rate
            'demod out', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-2, 2)

        self.qtgui_time_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0.enable_tags(True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_TAG, qtgui.TRIG_SLOPE_POS, 0.5, 0, 0, 'squelch_sob')
        self.qtgui_time_sink_x_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0.enable_grid(True)
        self.qtgui_time_sink_x_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0.enable_stem_plot(False)

        self.qtgui_time_sink_x_0.disable_legend()

        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.qwidget(), Qt.QWidget)
        self.tab0_grid_layout_0.addWidget(self._qtgui_time_sink_x_0_win, 2, 0, 1, 1)
        for r in range(2, 3):
            self.tab0_grid_layout_0.setRowStretch(r, 1)
        for c in range(0, 1):
            self.tab0_grid_layout_0.setColumnStretch(c, 1)
        self.qtgui_freq_sink_x_0_0 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            freq, #fc
            (samp_rate/20), #bw
            'Baseband', #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0_0.enable_grid(True)
        self.qtgui_freq_sink_x_0_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0_0.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0_0.qwidget(), Qt.QWidget)
        self.tab0_grid_layout_0.addWidget(self._qtgui_freq_sink_x_0_0_win, 1, 0, 1, 1)
        for r in range(1, 2):
            self.tab0_grid_layout_0.setRowStretch(r, 1)
        for c in range(0, 1):
            self.tab0_grid_layout_0.setColumnStretch(c, 1)
        self.qtgui_eye_sink_x_0 = qtgui.eye_sink_f(
            128, #size
            symbol_sample_rate, #samp_rate
            1, #number of inputs
            None
        )
        self.qtgui_eye_sink_x_0.set_update_time(0.10)
        self.qtgui_eye_sink_x_0.set_samp_per_symbol(8)
        self.qtgui_eye_sink_x_0.set_y_axis(-2, 2)

        self.qtgui_eye_sink_x_0.set_y_label('Amplitude', "Eye")

        self.qtgui_eye_sink_x_0.enable_tags(True)
        self.qtgui_eye_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_TAG, qtgui.TRIG_SLOPE_POS, 0.5, 0, 0, 'squelch_sob')
        self.qtgui_eye_sink_x_0.enable_autoscale(False)
        self.qtgui_eye_sink_x_0.enable_grid(True)
        self.qtgui_eye_sink_x_0.enable_axis_labels(True)
        self.qtgui_eye_sink_x_0.enable_control_panel(False)

        self.qtgui_eye_sink_x_0.disable_legend()

        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'blue', 'blue', 'blue', 'blue',
            'blue', 'blue', 'blue', 'blue', 'blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_eye_sink_x_0.set_line_label(i, "Eye[Data {0}]".format(i))
            else:
                self.qtgui_eye_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_eye_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_eye_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_eye_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_eye_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_eye_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_eye_sink_x_0_win = sip.wrapinstance(self.qtgui_eye_sink_x_0.qwidget(), Qt.QWidget)
        self.tab0_grid_layout_0.addWidget(self._qtgui_eye_sink_x_0_win, 3, 1, 1, 1)
        for r in range(3, 4):
            self.tab0_grid_layout_0.setRowStretch(r, 1)
        for c in range(1, 2):
            self.tab0_grid_layout_0.setColumnStretch(c, 1)
        self.freq_xlating_fir_filter_xxx_0_0 = filter.freq_xlating_fir_filter_ccc(1, firdes.low_pass(1.0, samp_rate, chan_bw/2, transition, window.WIN_HAMMING), 0, samp_rate)
        self.freq_xlating_fir_filter_xxx_0 = filter.freq_xlating_fir_filter_ccc(1, firdes.low_pass(1.0, samp_rate, chan_bw/2, transition, window.WIN_HAMMING), center_diff, samp_rate)
        self.fir_filter_xxx_1 = filter.fir_filter_fff(1, firdes.gaussian(1.0, samp_rate/symbol_rate, 0.5, 4*samples_per_symbol))
        self.fir_filter_xxx_1.declare_sample_delay(0)
        self.fir_filter_xxx_0 = filter.fir_filter_fff(100, firdes.low_pass(1.0, samp_rate, samp_rate/4, transition, window.WIN_HAMMING))
        self.fir_filter_xxx_0.declare_sample_delay(0)
        self.epy_block_4 = epy_block_4.il2p_decoder(lfsr_seed=0x1F0, output_dir="", processing_run_id=processing_run_id, store_packets=store_packets)
        self.epy_block_1 = epy_block_1.blk(sync_tag="sync", code_len_bits=32)
        self.epy_block_0 = epy_block_0.blk(wav_file=source_file, tle_file=tle_file, catalog_number='66909U', sat_freq_hz=freq, center_freq_hz=freq, lat=38.9830, lon=-76.4830, elev=2, capture_session_id=capture_session_id, timezone='America/NewYork', debug=True)
        self.digital_symbol_sync_xx_1 = digital.symbol_sync_ff(
            digital.TED_EARLY_LATE,
            16,
            TED_bandwidth,
            1.0,
            0.3,
            1.5,
            1,
            digital.constellation_bpsk().base(),
            digital.IR_MMSE_8TAP,
            128,
            [])
        self.digital_correlate_access_code_tag_xx_0_0 = digital.correlate_access_code_tag_bb('00110011010101010011001101010101', access_threshold, 'sync')
        self.digital_binary_slicer_fb_0 = digital.binary_slicer_fb()
        self.blocks_wavfile_source_0 = blocks.wavfile_source(source_file, False)
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_selector_0_0 = blocks.selector(gr.sizeof_gr_complex*1,doppler_en,0)
        self.blocks_selector_0_0.set_enabled(True)
        self.blocks_selector_0 = blocks.selector(gr.sizeof_gr_complex*1,doppler_en,0)
        self.blocks_selector_0.set_enabled(True)
        self.blocks_msgpair_to_var_0 = blocks.msg_pair_to_var(self.set_center_diff)
        self.blocks_message_debug_0_0_0 = blocks.message_debug(True, gr.log_levels.trace)
        self.blocks_freqshift_cc_0 = blocks.rotator_cc(2.0*math.pi*frequency_offset/samp_rate)
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(1)
        self.blocks_char_to_float_0 = blocks.char_to_float(1, 1)
        self.analog_quadrature_demod_cf_0 = analog.quadrature_demod_cf((samp_rate/decimation/(2*pi*fsk_deviation_hz)))
        self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_cc(squelch, (1e-4), 0, True)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.epy_block_0, 'freq'), (self.blocks_msgpair_to_var_0, 'inpair'))
        self.msg_connect((self.epy_block_0, 'freq'), (self.freq_xlating_fir_filter_xxx_0, 'freq'))
        self.msg_connect((self.epy_block_1, 'pdus'), (self.epy_block_4, 'pdus'))
        self.msg_connect((self.epy_block_4, 'out'), (self.blocks_message_debug_0_0_0, 'log'))
        self.connect((self.analog_pwr_squelch_xx_0, 0), (self.analog_quadrature_demod_cf_0, 0))
        self.connect((self.analog_quadrature_demod_cf_0, 0), (self.fir_filter_xxx_1, 0))
        self.connect((self.analog_quadrature_demod_cf_0, 0), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.blocks_char_to_float_0, 0), (self.qtgui_time_sink_x_1_0_0_0, 0))
        self.connect((self.blocks_complex_to_mag_0, 0), (self.fir_filter_xxx_0, 0))
        self.connect((self.blocks_float_to_complex_0, 0), (self.blocks_selector_0_0, 0))
        self.connect((self.blocks_freqshift_cc_0, 0), (self.freq_xlating_fir_filter_xxx_0, 0))
        self.connect((self.blocks_freqshift_cc_0, 0), (self.freq_xlating_fir_filter_xxx_0_0, 0))
        self.connect((self.blocks_selector_0, 0), (self.analog_pwr_squelch_xx_0, 0))
        self.connect((self.blocks_selector_0, 0), (self.blocks_complex_to_mag_0, 0))
        self.connect((self.blocks_selector_0, 0), (self.qtgui_freq_sink_x_0_0, 0))
        self.connect((self.blocks_selector_0, 0), (self.qtgui_waterfall_sink_x_0, 0))
        self.connect((self.blocks_selector_0_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_freqshift_cc_0, 0))
        self.connect((self.blocks_wavfile_source_0, 1), (self.blocks_float_to_complex_0, 1))
        self.connect((self.blocks_wavfile_source_0, 0), (self.blocks_float_to_complex_0, 0))
        self.connect((self.digital_binary_slicer_fb_0, 0), (self.blocks_char_to_float_0, 0))
        self.connect((self.digital_binary_slicer_fb_0, 0), (self.digital_correlate_access_code_tag_xx_0_0, 0))
        self.connect((self.digital_correlate_access_code_tag_xx_0_0, 0), (self.epy_block_1, 0))
        self.connect((self.digital_symbol_sync_xx_1, 0), (self.digital_binary_slicer_fb_0, 0))
        self.connect((self.digital_symbol_sync_xx_1, 0), (self.qtgui_eye_sink_x_0, 0))
        self.connect((self.digital_symbol_sync_xx_1, 1), (self.qtgui_time_sink_x_1_0_0, 1))
        self.connect((self.digital_symbol_sync_xx_1, 0), (self.qtgui_time_sink_x_1_0_0, 0))
        self.connect((self.epy_block_0, 0), (self.blocks_selector_0_0, 1))
        self.connect((self.fir_filter_xxx_0, 0), (self.qtgui_time_sink_x_0_1, 0))
        self.connect((self.fir_filter_xxx_1, 0), (self.digital_symbol_sync_xx_1, 0))
        self.connect((self.fir_filter_xxx_1, 0), (self.qtgui_time_sink_x_0_0, 0))
        self.connect((self.freq_xlating_fir_filter_xxx_0, 0), (self.blocks_selector_0, 1))
        self.connect((self.freq_xlating_fir_filter_xxx_0_0, 0), (self.blocks_selector_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "passdata_playback")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_access_threshold(self):
        return self.access_threshold

    def set_access_threshold(self, access_threshold):
        self.access_threshold = access_threshold
        self.digital_correlate_access_code_tag_xx_0_0.set_threshold(self.access_threshold)

    def get_capture_session_id(self):
        return self.capture_session_id

    def set_capture_session_id(self, capture_session_id):
        self.capture_session_id = capture_session_id
        self.epy_block_0.capture_session_id = self.capture_session_id

    def get_doppler_en(self):
        return self.doppler_en

    def set_doppler_en(self, doppler_en):
        self.doppler_en = doppler_en
        self.blocks_selector_0.set_input_index(self.doppler_en)
        self.blocks_selector_0_0.set_input_index(self.doppler_en)

    def get_frequency_offset(self):
        return self.frequency_offset

    def set_frequency_offset(self, frequency_offset):
        self.frequency_offset = frequency_offset
        self.blocks_freqshift_cc_0.set_phase_inc(2.0*math.pi*self.frequency_offset/self.samp_rate)

    def get_output_path(self):
        return self.output_path

    def set_output_path(self, output_path):
        self.output_path = output_path

    def get_processing_run_id(self):
        return self.processing_run_id

    def set_processing_run_id(self, processing_run_id):
        self.processing_run_id = processing_run_id
        self.epy_block_4.processing_run_id = self.processing_run_id

    def get_source_file(self):
        return self.source_file

    def set_source_file(self, source_file):
        self.source_file = source_file
        self.epy_block_0.wav_file = self.source_file

    def get_store_packets(self):
        return self.store_packets

    def set_store_packets(self, store_packets):
        self.store_packets = store_packets
        self.epy_block_4.store_packets = self.store_packets

    def get_symbol_rate(self):
        return self.symbol_rate

    def set_symbol_rate(self, symbol_rate):
        self.symbol_rate = symbol_rate
        self.set_chan_bw((1+0.5)*self.symbol_rate)
        self.set_fsk_deviation_hz(self.symbol_rate/2*0.5)
        self.set_samp_rate(self.symbol_rate*16)
        self.set_symbol_sample_rate(self.symbol_rate*self.samples_per_symbol)
        self.fir_filter_xxx_1.set_taps(firdes.gaussian(1.0, self.samp_rate/self.symbol_rate, 0.5, 4*self.samples_per_symbol))
        self.qtgui_time_sink_x_1_0_0.set_samp_rate(self.symbol_rate)
        self.qtgui_time_sink_x_1_0_0_0.set_samp_rate(self.symbol_rate)

    def get_samples_per_symbol(self):
        return self.samples_per_symbol

    def set_samples_per_symbol(self, samples_per_symbol):
        self.samples_per_symbol = samples_per_symbol
        self.set_symbol_sample_rate(self.symbol_rate*self.samples_per_symbol)
        self.fir_filter_xxx_1.set_taps(firdes.gaussian(1.0, self.samp_rate/self.symbol_rate, 0.5, 4*self.samples_per_symbol))

    def get_project_root(self):
        return self.project_root

    def set_project_root(self, project_root):
        self.project_root = project_root
        self.set_tle_file(os.path.join(self.project_root, 'default.tle'))

    def get_transition(self):
        return self.transition

    def set_transition(self, transition):
        self.transition = transition
        self.fir_filter_xxx_0.set_taps(firdes.low_pass(1.0, self.samp_rate, self.samp_rate/4, self.transition, window.WIN_HAMMING))
        self.freq_xlating_fir_filter_xxx_0.set_taps(firdes.low_pass(1.0, self.samp_rate, self.chan_bw/2, self.transition, window.WIN_HAMMING))
        self.freq_xlating_fir_filter_xxx_0_0.set_taps(firdes.low_pass(1.0, self.samp_rate, self.chan_bw/2, self.transition, window.WIN_HAMMING))

    def get_tle_file(self):
        return self.tle_file

    def set_tle_file(self, tle_file):
        self.tle_file = tle_file
        self.epy_block_0.tle_file = self.tle_file

    def get_symbol_sample_rate(self):
        return self.symbol_sample_rate

    def set_symbol_sample_rate(self, symbol_sample_rate):
        self.symbol_sample_rate = symbol_sample_rate
        self.qtgui_eye_sink_x_0.set_samp_rate(self.symbol_sample_rate)
        self.qtgui_time_sink_x_0.set_samp_rate(self.symbol_sample_rate)
        self.qtgui_time_sink_x_0_0.set_samp_rate(self.symbol_sample_rate)

    def get_squelch(self):
        return self.squelch

    def set_squelch(self, squelch):
        self.squelch = squelch
        self.analog_pwr_squelch_xx_0.set_threshold(self.squelch)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_quadrature_demod_cf_0.set_gain((self.samp_rate/self.decimation/(2*pi*self.fsk_deviation_hz)))
        self.blocks_freqshift_cc_0.set_phase_inc(2.0*math.pi*self.frequency_offset/self.samp_rate)
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)
        self.fir_filter_xxx_0.set_taps(firdes.low_pass(1.0, self.samp_rate, self.samp_rate/4, self.transition, window.WIN_HAMMING))
        self.fir_filter_xxx_1.set_taps(firdes.gaussian(1.0, self.samp_rate/self.symbol_rate, 0.5, 4*self.samples_per_symbol))
        self.freq_xlating_fir_filter_xxx_0.set_taps(firdes.low_pass(1.0, self.samp_rate, self.chan_bw/2, self.transition, window.WIN_HAMMING))
        self.freq_xlating_fir_filter_xxx_0_0.set_taps(firdes.low_pass(1.0, self.samp_rate, self.chan_bw/2, self.transition, window.WIN_HAMMING))
        self.qtgui_freq_sink_x_0_0.set_frequency_range(self.freq, (self.samp_rate/20))
        self.qtgui_time_sink_x_0_1.set_samp_rate(self.samp_rate/100)
        self.qtgui_waterfall_sink_x_0.set_frequency_range(0, (self.samp_rate/8))

    def get_oversample(self):
        return self.oversample

    def set_oversample(self, oversample):
        self.oversample = oversample

    def get_fsk_deviation_hz(self):
        return self.fsk_deviation_hz

    def set_fsk_deviation_hz(self, fsk_deviation_hz):
        self.fsk_deviation_hz = fsk_deviation_hz
        self.analog_quadrature_demod_cf_0.set_gain((self.samp_rate/self.decimation/(2*pi*self.fsk_deviation_hz)))

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.epy_block_0.center_freq_hz = self.freq
        self.epy_block_0.sat_freq_hz = self.freq
        self.qtgui_freq_sink_x_0_0.set_frequency_range(self.freq, (self.samp_rate/20))

    def get_decimation(self):
        return self.decimation

    def set_decimation(self, decimation):
        self.decimation = decimation
        self.analog_quadrature_demod_cf_0.set_gain((self.samp_rate/self.decimation/(2*pi*self.fsk_deviation_hz)))

    def get_chan_bw(self):
        return self.chan_bw

    def set_chan_bw(self, chan_bw):
        self.chan_bw = chan_bw
        self.freq_xlating_fir_filter_xxx_0.set_taps(firdes.low_pass(1.0, self.samp_rate, self.chan_bw/2, self.transition, window.WIN_HAMMING))
        self.freq_xlating_fir_filter_xxx_0_0.set_taps(firdes.low_pass(1.0, self.samp_rate, self.chan_bw/2, self.transition, window.WIN_HAMMING))

    def get_center_diff(self):
        return self.center_diff

    def set_center_diff(self, center_diff):
        self.center_diff = center_diff
        Qt.QMetaObject.invokeMethod(self._center_diff_label, "setText", Qt.Q_ARG("QString", str(self._center_diff_formatter(self.center_diff))))
        self.freq_xlating_fir_filter_xxx_0.set_center_freq(self.center_diff)

    def get_TED_bandwidth(self):
        return self.TED_bandwidth

    def set_TED_bandwidth(self, TED_bandwidth):
        self.TED_bandwidth = TED_bandwidth
        self.digital_symbol_sync_xx_1.set_loop_bandwidth(self.TED_bandwidth)



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--access-threshold", dest="access_threshold", type=intx, default=3,
        help="Set access_threshold [default=%(default)r]")
    parser.add_argument(
        "--capture-session-id", dest="capture_session_id", type=intx, default=0,
        help="Set capture_session_id [default=%(default)r]")
    parser.add_argument(
        "--doppler-en", dest="doppler_en", type=intx, default=0,
        help="Set doppler_en [default=%(default)r]")
    parser.add_argument(
        "--frequency-offset", dest="frequency_offset", type=eng_float, default=eng_notation.num_to_str(float(0)),
        help="Set frequency_offset [default=%(default)r]")
    parser.add_argument(
        "--output-path", dest="output_path", type=str, default='received_files/',
        help="Set output_path [default=%(default)r]")
    parser.add_argument(
        "--processing-run-id", dest="processing_run_id", type=intx, default=0,
        help="Set processing_run_id [default=%(default)r]")
    parser.add_argument(
        "--source-file", dest="source_file", type=str, default=os.path.join(os.getenv('SILVERSAT_ROOT'), "captures/20260112_233622.557094.wav"),
        help="Set source_file [default=%(default)r]")
    parser.add_argument(
        "--store-packets", dest="store_packets", type=intx, default=0,
        help="Set store_packets [default=%(default)r]")
    return parser


def main(top_block_cls=passdata_playback, options=None):
    if options is None:
        options = argument_parser().parse_args()

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(access_threshold=options.access_threshold, capture_session_id=options.capture_session_id, doppler_en=options.doppler_en, frequency_offset=options.frequency_offset, output_path=options.output_path, processing_run_id=options.processing_run_id, source_file=options.source_file, store_packets=options.store_packets)

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
