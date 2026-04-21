DoomGame Setup and Run Instructions

1. Install Python 3.11
Download from: https://www.python.org/downloads/windows
Run the installer for 3.11.0(64 bit)

once back in vs code
preess ctrl+shift+p and search for python: select interpreter
select 3.11.0

2. Open project folder in terminal
cd path/to/doomgame

3. Create virtual environment
py -3.11 -m venv venv

4. Activate virtual environment

Windows:
venv\Scripts\activate

Mac/Linux:
source venv/bin/activate

5. Install dependencies (if applicable)
pip install pygame

6. Run the program
python JLKDescent.py