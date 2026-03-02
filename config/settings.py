# Data settings
TICKER = "SPY"
LOOKBACK_PERIOD = "1y"
INTERVAL = "1d"
RISK_FREE_RATE = 0.02
INITIAL_CAPITAL = 100000

# Data loader settings
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
REQUEST_TIMEOUT_SECONDS = 30
MIN_REQUIRED_ROWS = 100

# Optimization settings
# Balanced search bounds: short 5-50 step 2, long 20-200 step 5
SHORT_WINDOW_MIN = 5
SHORT_WINDOW_MAX = 50
SHORT_WINDOW_STEP = 2
LONG_WINDOW_MIN = 20
LONG_WINDOW_MAX = 200
LONG_WINDOW_STEP = 5

# Retune cadence settings
# Hybrid: scheduled weekly + performance-triggered
RETUNE_INTERVAL_DAYS = 7
PERFORMANCE_TRIGGER_SHARPE_THRESHOLD = -0.5  # Retune if Sharpe falls below this

# Objective function weights
# J = Sharpe - lambda * |MaxDrawdown|
DRAWDOWN_PENALTY_LAMBDA = 0.5

# Minimum bars required for optimization
MIN_BARS_FOR_OPTIMIZATION = 200  # Supports 1y daily data after holidays/missing sessions

# State schema version
STATE_SCHEMA_VERSION = 2