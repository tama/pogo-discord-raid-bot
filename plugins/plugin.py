#!/usr/bin/env python3.5
#coding: utf8

from datetime import datetime

class Plugin(object):
        # Plugin name
        name = 'Interface'
        clients = []

        def __init__(self):
                self.clients = []

        def is_disabled(self):
                return False

        def get_modo_roles(self):
                return ['MODO']

        def get_instinct_role(self):
                return '[?]'

        def get_valor_role(self):
                return '[?]'

        def get_mystic_role(self):
                return '[?]'
        
        def get_instinct_emoji(self):
                return '[?]'

        def get_valor_emoji(self):
                return '[?]'

        def get_mystic_emoji(self):
                return '[?]'
        
        def get_welcome_message(self):
                return 'Bot summoned, this message will update with participants list.'
        
        def is_raid_channel(self, name):
                raise Exception('Subclass must implement is_raid_channel')

        def is_message_valid(self, message):
                raise Exception('Subclass must implement is_message_valid')

        def parse_message(self, message, message_content):
                raise Exception('Subclass must implement parse_message')

        def is_beta_server(self):
                return False
        
        def should_archive_on_delete(self):
                return True
