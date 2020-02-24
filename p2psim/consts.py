from enum import Enum

KBit = 1024 / 8
MBit = 1024 * KBit

NUM_PEERS = 50
SIM_DURATION = 30 # in seconds

VISUALIZATION = False


class SimModel(Enum):
    GAUSS = 1
    UNIFORM = 2
    PARETO = 3
    FROM_FILE = 4


# Latency of peers
PEER_LATENCY_MIN = 10 # ms
PEER_LATENCY_MAX = 300 # ms
PEER_LATENCY_MODEL = SimModel.PARETO

# Bandwidth of peers
PEER_BANDWIDTH_MODEL = SimModel.GAUSS
PEER_BANDWIDTH_MIN = 10 * MBit
PEER_BANDWIDTH_MAX = 300 * MBit

# Peer connections manager
CONNECTION_MAX_SILENCE = 2
CONNECTION_PING_INTERVAL = 1  # verify each interval that peer is online
CONNECTION_MAX_PEERS = 10
CONNECTION_MIN_PEERS = 5
CONNECTION_MIN_KEEP_TIME = 5  # time to allow unnecessary peers to stay connected

# Peer crash modeling
DOWNTIME_MEAN_INTERVAL = 2. * 60  # secs (mean time between failures)
DOWNTIME_AVAILABILITY = 0.9
DOWNTIME_CLOCK_INTERVAL = 1.

# Network slowdown
SLOWDOWN_MEAN_INTERVAL = 1. * 60  # secs (mean time between failures)
SLOWDOWN_AVAILABILITY = 0.6
SLOWDOWN_CLOCK_INTERVAL = 1.
SLOWDOWN_BANDWIDTH_REDUCTION = 0.2
