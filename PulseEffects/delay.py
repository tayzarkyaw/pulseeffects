# -*- coding: utf-8 -*-

import logging
import os

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstInsertBin', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GObject, Gst, GstInsertBin, Gtk

Gst.init(None)


class Delay():

    def __init__(self, settings):
        self.settings = settings
        self.module_path = os.path.dirname(__file__)

        self.log = logging.getLogger('PulseEffects')

        if Gst.ElementFactory.make(
                'lsp-plug-in-plugins-lv2-comp-delay-x2-stereo'):
            self.is_installed = True
        else:
            self.is_installed = False

            self.log.warn('Delay plugin was not found. Disabling it!')

        self.build_bin()

    def on_filter_added(self, bin, element, success, user_data):
        pass

    def build_bin(self):
        self.delay = Gst.ElementFactory.make(
            'lsp-plug-in-plugins-lv2-comp-delay-x2-stereo', None)

        self.input_level = Gst.ElementFactory.make('level',
                                                   'delay_input_level')
        self.output_level = Gst.ElementFactory.make('level',
                                                    'delay_output_level')

        self.bin = GstInsertBin.InsertBin.new('delay_bin')

        if self.is_installed:
            # There is a bug in gstreaner. Booleans are inverted. For example
            # we have to turn on bypass in order to effects to be applied

            registry = Gst.Registry().get()
            use_workaround = not registry.check_feature_version('pulsesrc', 1,
                                                                12, 5)

            if use_workaround:
                self.delay.set_property('bypass', True)
            else:
                self.delay.set_property('bypass', False)

            self.delay.set_property('mode-l', 'Distance')
            self.delay.set_property('mode-r', 'Distance')
            self.delay.set_property('dry-l', 0)
            self.delay.set_property('wet-l', 1)
            self.delay.set_property('dry-r', 0)
            self.delay.set_property('wet-r', 1)

            self.bin.append(self.input_level, self.on_filter_added, None)
            self.bin.append(self.delay, self.on_filter_added, None)
            self.bin.append(self.output_level, self.on_filter_added, None)

    def post_messages(self, state):
        self.input_level.set_property('post-messages', state)
        self.output_level.set_property('post-messages', state)

    def init_ui(self):
        self.builder = Gtk.Builder.new_from_file(self.module_path +
                                                 '/ui/delay.glade')

        self.builder.connect_signals(self)

        self.ui_window = self.builder.get_object('window')
        self.ui_controls = self.builder.get_object('controls')
        self.ui_listbox_control = self.builder.get_object('listbox_control')

        self.ui_enable = self.builder.get_object('enable')
        self.ui_img_state = self.builder.get_object('img_state')

        # self.ui_amount = self.builder.get_object('amount')

        self.ui_input_level_left = self.builder.get_object('input_level_left')
        self.ui_input_level_right = self.builder.get_object(
            'input_level_right')
        self.ui_output_level_left = self.builder.get_object(
            'output_level_left')
        self.ui_output_level_right = self.builder.get_object(
            'output_level_right')

        self.ui_input_level_left_label = self.builder.get_object(
            'input_level_left_label')
        self.ui_input_level_right_label = self.builder.get_object(
            'input_level_right_label')
        self.ui_output_level_left_label = self.builder.get_object(
            'output_level_left_label')
        self.ui_output_level_right_label = self.builder.get_object(
            'output_level_right_label')

    def bind(self):
        # binding ui widgets to gsettings

        flag = Gio.SettingsBindFlags.DEFAULT

        self.settings.bind('delay-state', self.ui_enable, 'active',
                           flag)
        self.settings.bind('delay-state', self.ui_img_state, 'visible',
                           flag)
        self.settings.bind('delay-state', self.ui_controls, 'sensitive',
                           Gio.SettingsBindFlags.GET)
        # self.settings.bind('exciter-amount', self.ui_amount, 'value',
        #                    flag)

        # binding ui widgets to gstreamer plugins

        flag = GObject.BindingFlags.BIDIRECTIONAL | \
            GObject.BindingFlags.SYNC_CREATE

        # self.ui_amount.bind_property('value', self.delay, 'amount', flag)

    def ui_update_level(self, widgets, peak):
        left, right = peak[0], peak[1]

        widget_level_left = widgets[0]
        widget_level_right = widgets[1]
        widget_level_left_label = widgets[2]
        widget_level_right_label = widgets[3]

        if left >= -99:
            l_value = 10**(left / 10)
            widget_level_left.set_value(l_value)
            widget_level_left_label.set_text(str(round(left)))
        else:
            widget_level_left.set_value(0)
            widget_level_left_label.set_text('-99')

        if right >= -99:
            r_value = 10**(right / 10)
            widget_level_right.set_value(r_value)
            widget_level_right_label.set_text(str(round(right)))
        else:
            widget_level_right.set_value(0)
            widget_level_right_label.set_text('-99')

    def ui_update_input_level(self, peak):
        widgets = [self.ui_input_level_left, self.ui_input_level_right,
                   self.ui_input_level_left_label,
                   self.ui_input_level_right_label]

        self.ui_update_level(widgets, peak)

    def ui_update_output_level(self, peak):
        widgets = [self.ui_output_level_left, self.ui_output_level_right,
                   self.ui_output_level_left_label,
                   self.ui_output_level_right_label]

        self.ui_update_level(widgets, peak)

    def reset(self):
        self.settings.reset('delay-state')
        # self.settings.reset('exciter-blend')
