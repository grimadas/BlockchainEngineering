import unittest

import yaml

from p2psimpy.config import PeerNameGenerator, ConnectionConfig, PeerConfig, load_from_config


class ConfigTests(unittest.TestCase):

    def setUp(self):
        # Load config dict from yaml file
        with open("../input/config.yml") as s:
            self.config = yaml.safe_load(s)

    def test_load_const_config(self):
        conn_config = self.config["basic"]["ConnectionConfig"]

        c = load_from_config(ConnectionConfig, conn_config)
        self.assertEqual(c.max_peers, conn_config['max_peers'])
        self.assertEqual(c.max_silence, conn_config['max_silence'])
        self.assertEqual(c.min_keep_time, conn_config['min_keep_time'])
        self.assertEqual(c.min_peers, conn_config['min_peers'])
        self.assertEqual(c.ping_interval, conn_config['ping_interval'])

    def test_load_peer_config(self):
        peer_config = self.config["basic"]["PeerConfig"]
        name_gen = PeerNameGenerator()

        c = PeerConfig.from_config(name_gen, 'basic', peer_config)
        self.assertEqual(c.name, "basic_1")