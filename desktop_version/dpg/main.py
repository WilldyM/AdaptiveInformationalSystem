# -*- coding: utf-8 -*-
import os
from pathlib import Path

import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

import config
from model_srv.mongodb.auth.AuthService import MongoAuthService


class MainWindow:
    mongo_conn = None
    user = None
    auth_tag_window = 'AuthWindow'
    main_tag_window = 'AdaptiveIS'
    view_port = None

    login_line = None
    password_line = None

    def set_cyrillic(self):
        big_let_start = 0x00C0  # Capital "A" in cyrillic alphabet
        big_let_end = 0x00DF  # Capital "Я" in cyrillic alphabet
        small_let_end = 0x00FF  # small "я" in cyrillic alphabet
        remap_big_let = 0x0410  # Starting number for remapped cyrillic alphabet
        alph_len = big_let_end - big_let_start + 1  # adds the shift from big letters to small
        alph_shift = remap_big_let - big_let_start  # adds the shift from remapped to non-remapped

        with dpg.font_registry():
            with dpg.font(config.ARIALN, 17, default_font=True, id='Default_font'):
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
                biglet = remap_big_let  # Starting number for remapped cyrillic alphabet
                for i1 in range(big_let_start, big_let_end + 1):  # Cycle through big letters in cyrillic alphabet
                    dpg.add_char_remap(i1, biglet)  # Remap the big cyrillic letter
                    dpg.add_char_remap(i1 + alph_len, biglet + alph_len)  # Remap the small cyrillic letter
                    biglet += 1  # choose next letter
        dpg.bind_font('Default_font')

    def auth_window(self):
        dpg.create_context()
        dpg.create_viewport(title='AdaptiveIS.Login', width=600, height=300)

        self.set_cyrillic()
        with dpg.window(tag=self.auth_tag_window, autosize=True):
            auth_width = 210
            pos_x = dpg.get_viewport_width() - auth_width
            pos_y = dpg.get_viewport_height() - 200
            with dpg.group(horizontal=False) as auth_group:
                dpg.add_text('Авторизация')
                with dpg.group(horizontal=False, width=210):
                    self.login_line = dpg.add_input_text(hint='Логин')
                    self.password_line = dpg.add_input_text(hint='Пароль', password=True)
                with dpg.group(horizontal=True, width=100, horizontal_spacing=10):
                    dpg.add_button(label='Авторизация', tag='auth_button', callback=self.check_auth_data)
                    dpg.add_button(label='Регистрация', tag='register_button', callback=self.check_auth_data)

        main_width = dpg.get_viewport_width()
        main_height = dpg.get_viewport_height()


        # demo.show_demo()
        # dpg.show_style_editor()
        # dpg.show_item_registry()

        dpg.toggle_viewport_fullscreen()
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.auth_tag_window, True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def main_app(self):
        with dpg.window(tag=self.main_tag_window):
            dpg.add_text('Hello, world')
        dpg.set_primary_window(self.auth_tag_window, False)
        dpg.configure_item(self.auth_tag_window, show=False)
        dpg.set_viewport_title('AdaptiveIS')
        dpg.set_viewport_height(600)
        dpg.set_viewport_width(1200)
        dpg.set_primary_window(self.main_tag_window, True)

    @staticmethod
    def show_info(title, message, selection_callback=None):
        if selection_callback is None:
            selection_callback = lambda: dpg.configure_item(modal_id, show=False)

        # guarantee these commands happen in the same frame
        with dpg.mutex():
            viewport_width = dpg.get_viewport_client_width()
            viewport_height = dpg.get_viewport_client_height()

            with dpg.window(label=title, modal=True, no_close=True) as modal_id:
                dpg.add_text(message)
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Ok", width=75, user_data=(modal_id, True), callback=selection_callback)
                    dpg.add_button(label="Cancel", width=75, user_data=(modal_id, False), callback=selection_callback)

        # guarantee these commands happen in another frame
        dpg.split_frame()
        width = dpg.get_item_width(modal_id)
        height = dpg.get_item_height(modal_id)
        dpg.set_item_pos(modal_id, [viewport_width // 2 - width // 2, viewport_height // 2 - height // 2])

    @staticmethod
    def set_item_to_center(item_id):
        pass

    def check_auth_data(self, sender):
        self.mongo_conn = MongoAuthService()
        login = dpg.get_value(self.login_line)
        password = dpg.get_value(self.password_line)
        if sender == 'auth_button':
            print('auth')
            try:
                self.user = self.mongo_conn.auth(login, password)
            except ValueError as err:
                text_error = err.args[0]
                print(text_error)
                self.show_info('Ошибка при авторизации', text_error)

        elif sender == 'register_button':
            print('register')
            try:
                self.user = self.mongo_conn.register(login, password)
            except ValueError as err:
                text_error = err.args[0]
                self.show_info('Ошибка при регистрации', text_error)

        self.mongo_conn.close_connection()
        if self.user is not None:
            self.main_app()


if __name__ == '__main__':
    mw = MainWindow()
    mw.auth_window()
