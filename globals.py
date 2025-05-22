# globals.py
#
# MARKS SYSTEM PATHS
CALC=calc='/usr/bin/galculator'  #MATH
FF=ff='/usr/bin/firefox' #BROWSE
ED=ed='/usr/bin/geany' #EDIT
HOME=home='/home/me' #HOME
paths=CALC,FF,ED,HOME

#TEXT MODS
RET=ret='\n'   #RETURN
FS=fs='/' #FILE SEPARATOR
BS=bs='\\' #WINDOWS
TAB=tab='\t' #TAB
DOT=dot='.' #DOT
BS=bs='\\' #BSLASH
DASH=dash='-' #DASH
HASH=hash='#' #HASH
SLASH=slash='/' #SLASH
#VARS=vars=dot,bs,dash,hash,slash,tab,ret,ed,ff,home
mods=RET,FS,BS,TAB,DOT,BS,DASH,HASH,SLASH

#MATH
PLUS=plus="+"   #+
MINUS=minus="-"	#-
MULT=mult="*"	#*
DIV=div="/"		#/
EQUAL=equal="="	#=
MOD="%"	        #remainder
math=PLUS,MINUS,MULT,DIV,EQUAL,MOD#MATH
PLUS=plus="+"   #+
MINUS=minus="-"	#-
MULT=mult="*"	#*
DIV=div="/"		#/
EQUAL=equal="="	#=
MOD="%"	        #remainder
math=PLUS,MINUS,MULT,DIV,EQUAL,MOD

#TRIG
SIN=sin="sin"	    #sine
COS=cos="cos"	    #cosine
TAN=tan="tan"	    #tangent
ASIN=asin="asin"	    #inverse sine
ACOS=acos="acos"	    #inverse cosine
ATAN=atan="atan"	    #inverse tangent
SINH=sinh="sinh"	    #hyperbolic sine
COSH=cosh="cosh"	    #hyperbolic cosine
TANH=tanh="tanh"	    #hyperbolic tangent
ASINH=asinh="asinh"	#inverse hyperbolic sine
ACOSH=acosh="acosh"	#inverse hyperbolic cosine
ATANH=atanh="atanh"	#inverse hyperbolic tangent
trig=SIN,COS,TAN,ASIN,ACOS,ATAN,SINH,COSH,TANH,ASINH,ACOSH,ATANH

#TRINITY
ADJ="4"	#TRINITY
OPP="3"	#TRINITY
HYP="5"	#TRINITY
trinity=ADJ,OPP,HYP

#HYP
SOH="sin=opp/hyp"	#
CAH="cos=adj/hyp"	#
TOA="tan=opp/adj"	#
CHK="soh + cah + toa = 180"	#sanity check
hyp=SOH,CAH,TOA,CHK

#TRIG
SIN=sin="sin"	    #sine
COS=cos="cos"	    #cosine
TAN=tan="tan"	    #tangent
ASIN=asin="asin"	    #inverse sine
ACOS=acos="acos"	    #inverse cosine
ATAN=atan="atan"	    #inverse tangent
SINH=sinh="sinh"	    #hyperbolic sine
COSH=cosh="cosh"	    #hyperbolic cosine
TANH=tanh="tanh"	    #hyperbolic tangent
ASINH=asinh="asinh"	#inverse hyperbolic sine
ACOSH=acosh="acosh"	#inverse hyperbolic cosine
ATANH=atanh="atanh"	#inverse hyperbolic tangent
trig=SIN,COS,TAN,ASIN,ACOS,ATAN,SINH,COSH,TANH,ASINH,ACOSH,ATANH

#TRINITY
ADJ="3"	#TRINITY
OPP="4"	#TRINITY
HYP="5"	#TRINITY
trinity=ADJ,OPP,HYP

#TRIANGLES
SOH="sin=opp/hyp"	#
CAH="cos=adj/hyp"	#
TOA="tan=opp/adj"	#
CHK="soh + cah + toa = 180"	#sanity check
triangles=SOH,CAH,TOA,CHK

#DATES
YYYY=yyyy="YYYY"	#YEAR
MM=mm="MM"	#MONTH
DD=dd="DD"	#DAY
HH=hh="HH"	#HOUR
MM=mm="MM"	#MINUTE
SS=ss="SS"	#SECOND
dates=YYYY,MM,DD,HH,MM,SS

#TURN_DIFFS
D1=-1   #DIFFICULTY
D2=-2   #DIFFICULTY
D3=-4   #DIFFICULTY
turn_diffs=D1,D2,D3

#TURN_ANGLES
T15=1   #15
T30=2   #30
T45=3   #45
turn_angles=T15,T30,T45

#DIFFICULTIES
EASY=+1 #
MID=0   #
HARD=-1 #
difficulties=T15,T30,T45

#MANEUVERS
DRIFT=0
SWERVE=-1
#BOOTLEGGER
#CAR WARS 
maneuvers=DRIFT,SWERVE

#VECTORS
F="Forward"     #yps,mph
B="Backward"    #yps,mph
L="Left"        #15degree increments
R="Right"       #15degree increments
U="Up"          #yps,mph
D="Down"        #yps,mph
vectors=F,B,L,R,U,D

#VEHICLES
MAN="Man"           #1x1   Man
BIKE="Bike"         #1x2   Bike
TRIKE="Trike"       #2x2   Trike
CAR="Car"           #2x4   Car
TRUCK="Truck"       #2x6   Truck
VAN="Van"           #2x4   Van
BUS="Bus"           #2x8   Bus
MINE="Mine"         #2x2   Mine
VEHICLE="Vehicle"   #?x?   Vehicle
vehicles=MAN,BIKE,TRIKE,CAR,TRUCK,VAN,BUS,MINE,VEHICLE

vars=paths,mods,math,trig,trinity,triangles,dates,turn_diffs,turn_angles,
difficulties,maneuvers,vectors,vehicles


class showVars():
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
    # This is executed when run as a script
    print("globals.py")
    print("This is executed when run as a script")
    showVars()

# Constants for image processing
IMAGE_DIMENSIONS = (3146, 2382)
DEFAULT_GRID_COLOR = 'lightgrey'
DEFAULT_LINE_COLOR = 'red'
DEFAULT_GRID_SIZE = (42, 32)

# File paths
INPUT_DIR = "/home/me/BACKUP/PROJECTS/CardCutter/gimp"
OUTPUT_DIR = "output"

# File lists
IMAGE_FILES = [
    "_cars1.png",
    "_cars1+.png",
    "_cars2.png",
    "_cars3.png",
    "_cars57+.png",
    "_cars78+.png",
    "_cars114+.png"
]

# Configuration tuples
GRID_SIZES = [
    (42,32),
    (28,16),
    (40,32),
    (44,34),
    (14,22),
    (32,16),
    (28,16)
]
