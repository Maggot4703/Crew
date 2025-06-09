"""
Global variables and constants for the Crew Management application.

This module serves as a centralized place to define and manage
global state or configuration that needs to be accessible across
different parts of the application. Use with caution to avoid
tightly coupling modules.
"""

# Example Global Variables (replace with actual globals used in your project)

# --- Application Settings ---
APP_VERSION = "1.0.0"
APP_NAME = "Crew Management System"
DEBUG_MODE = False

# --- Paths ---
# Assuming a standard project structure
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DATA_DIR = os.path.join(BASE_DIR, 'data')
# LOG_FILE = os.path.join(BASE_DIR, 'app.log')

# --- UI Constants (if applicable) ---
DEFAULT_THEME = "light"
MAX_TABLE_ROWS = 100

# --- Database Configuration (example, better in a config file) ---
# DB_HOST = "localhost"
# DB_PORT = 5432
# DB_NAME = "crew_db"

# --- API Keys (example, should be stored securely, not hardcoded) ---
# THIRD_PARTY_API_KEY = "your_api_key_here"

# --- Logging Levels ---
# LOG_LEVEL_CONSOLE = "INFO"
# LOG_LEVEL_FILE = "DEBUG"

# --- Status Flags ---
# INITIALIZATION_COMPLETE = False

# --- Pre-commit Hook Related (if any globals are used by it) ---
# For example, if pre-commit needs to know about specific file patterns
# PRE_COMMIT_TARGET_EXTENSIONS = [".py", ".md", ".txt"]


# It's generally better to minimize the use of global variables.
# Consider using configuration files, dependency injection, or passing
# necessary data as parameters instead.

# If this file is intended to be populated by other modules at runtime,
# clearly document how and when these variables are set.

# Example of a global that might be set by the main application script:
# current_user = None

# Placeholder for any actual global variables used in the project.
# If there are no true global variables needed, this file might be
# for constants only, or it might be vestigial.

# The B018 error (useless expression) that was previously here suggests
# there might have been standalone expressions that weren't assigned
# or used. Ensure all code here has a purpose (assignment, function call, etc.)

# If you have specific global variables from your project, list them here.
# For instance:
# MAX_RETRIES = 3
# TIMEOUT_SECONDS = 30

print("globals.py loaded")  # Example: to confirm the module is imported

# globals.py

CALC = calc = "/usr/bin/galculator"
FF = ff = "/usr/bin/firefox"
ED = ed = "/usr/bin/geany"
HOME = home = "/home/me"
paths = CALC, FF, ED, HOME

RET = ret = "\n"
FS = fs = "/"  # FILE SEPARATOR
BS = bs = "\\"  # WINDOWS
TAB = tab = "\t"  # TAB
DOT = dot = "."  # DOT
BS = bs = "\\"  # BSLASH
DASH = dash = "-"  # DASH
HASH = hash = "#"  # HASH
SLASH = slash = "/"  # SLASH
mods = RET, FS, BS, TAB, DOT, BS, DASH, HASH, SLASH

PLUS = plus = "+"  # +
MINUS = minus = "-"  # -
MULT = mult = "*"  # *
DIV = div = "/"  # /
EQUAL = equal = "="  # =
MOD = "%"  # remainder
math = PLUS, MINUS, MULT, DIV, EQUAL, MOD

SIN = sin = "sin"  # sine
COS = cos = "cos"  # cosine
TAN = tan = "tan"  # tangent
ASIN = asin = "asin"  # inverse sine
ACOS = acos = "acos"  # inverse cosine
ATAN = atan = "atan"  # inverse tangent
SINH = sinh = "sinh"  # hyperbolic sine
COSH = cosh = "cosh"  # hyperbolic cosine
TANH = tanh = "tanh"  # hyperbolic tangent
ASINH = asinh = "asinh"  # inverse hyperbolic sine
ACOSH = acosh = "acosh"  # inverse hyperbolic cosine
ATANH = atanh = "atanh"  # inverse hyperbolic tangent
trig = SIN, COS, TAN, ASIN, ACOS, ATAN, SINH, COSH, TANH, ASINH, ACOSH, ATANH

ADJ = "4"  # TRINITY
OPP = "3"  # TRINITY
HYP = "5"  # TRINITY
trinity = ADJ, OPP, HYP

SOH = "sin=opp/hyp"  #
CAH = "cos=adj/hyp"  #
TOA = "tan=opp/adj"  #
CHK = "soh + cah + toa = 180"  # sanity check
hyp = SOH, CAH, TOA, CHK

ADJ = "3"  # TRINITY
OPP = "4"  # TRINITY
HYP = "5"  # TRINITY
trinity = ADJ, OPP, HYP

SOH = "sin=opp/hyp"  #
CAH = "cos=adj/hyp"  #
TOA = "tan=opp/adj"  #
CHK = "soh + cah + toa = 180"  # sanity check
triangles = SOH, CAH, TOA, CHK

YYYY = yyyy = "YYYY"  # YEAR
MM = mm = "MM"  # MONTH
DD = dd = "DD"  # DAY
HH = hh = "HH"  # HOUR
MM = mm = "MM"  # MINUTE
SS = ss = "SS"  # SECOND
dates = YYYY, MM, DD, HH, MM, SS

D1 = -1  # DIFFICULTY
D2 = -2  # DIFFICULTY
D3 = -4  # DIFFICULTY
turn_diffs = D1, D2, D3

T15 = 1  # 15
T30 = 2  # 30
T45 = 3  # 45
turn_angles = T15, T30, T45

EASY = +1  #
MID = 0  #
HARD = -1  #
difficulties = T15, T30, T45

DRIFT = 0
SWERVE = -1
maneuvers = DRIFT, SWERVE

F = "Forward"  # yps,mph
B = "Backward"  # yps,mph
L = "Left"  # 15degree increments
R = "Right"  # 15degree increments
U = "Up"  # yps,mph
D = "Down"  # yps,mph
vectors = F, B, L, R, U, D

MAN = "Man"  # 1x1   Man
BIKE = "Bike"  # 1x2   Bike
TRIKE = "Trike"  # 2x2   Trike
CAR = "Car"  # 2x4   Car
TRUCK = "Truck"  # 2x6   Truck
VAN = "Van"  # 2x4   Van
BUS = "Bus"  # 2x8   Bus
MINE = "Mine"  # 2x2   Mine
VEHICLE = "Vehicle"  # ?x?   Vehicle
vehicles = MAN, BIKE, TRIKE, CAR, TRUCK, VAN, BUS, MINE, VEHICLE

vars = (
    paths,
    mods,
    math,
    trig,
    trinity,
    triangles,
    dates,
    turn_diffs,
    turn_angles,
    difficulties,
    maneuvers,
    vectors,
    vehicles,
)


class showVars:
    def __init__(self):
        self.count = 0
        self.vars = vars

    def showvars(self):
        for var in self.vars:
            self.count = 0
            for v in var:
                print(v)
                self.count += 1
            print(f"{self.count}\n")
        return self.count


if __name__ == "__main__":
    print("globals.py")
    print("This is executed when run as a script")
    showVars()

IMAGE_DIMENSIONS = (3146, 2382)
DEFAULT_GRID_COLOR = "lightgrey"
DEFAULT_LINE_COLOR = "red"
DEFAULT_GRID_SIZE = (42, 32)

INPUT_DIR = "/home/me/BACKUP/PROJECTS/CardCutter/gimp"
OUTPUT_DIR = "output"

IMAGE_FILES = [
    "_cars1.png",
    "_cars1+.png",
    "_cars2.png",
    "_cars3.png",
    "_cars57+.png",
    "_cars78+.png",
    "_cars114+.png",
]

GRID_SIZES = [(42, 32), (28, 16), (40, 32), (44, 34), (14, 22), (32, 16), (28, 16)]
