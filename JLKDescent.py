import pygame
import math
import sys
import random
import os
import json

# DISPLAY
WIDTH, HEIGHT  = 1000, 800
HALF_W, HALF_H = WIDTH // 2, HEIGHT // 2
FPS            = 60

# RAYCASTER / PHYSICS
FOV          = math.pi / 3
HALF_FOV     = FOV / 2
MAX_DEPTH    = 20.0
MOVE_SPEED   = 0.05
ROT_SPEED    = 0.03
PLAYER_RADIUS = 0.25
PITCH_STEP   = 0.02
PITCH_MAX    = 0.45

# ENEMY TUNING
ENEMY_HIT_RADIUS    = 0.4
ENEMY_ATTACK_RANGE  = 12.0
ENEMY_BASE_DAMAGE   = 5
ENEMY_ATTACK_RATE   = 1.5
ENEMY_DEATH_DISPLAY = 0.8
BULLET_SPEED        = 0.18
ENEMY_BULLET_SPEED  = 0.22
ENEMY_BULLET_RADIUS = 0.25
ENEMY_MOVE_SPEED    = 0.018
ENEMY_CHASE_RANGE   = 14.0
ENEMY_STOP_RANGE    = 3.0
ENEMY_PATH_INTERVAL = 0.45

# MINIMAP
MINIMAP_RADIUS = 8
MINIMAP_SCALE  = 4
MINIMAP_MARGIN = 10

# SCORING
KILL_SCORE  = 100
LEVEL_SCORE = 1000

# MUSIC EVENT
MUSIC_END = pygame.USEREVENT + 1

# GLOBAL STATE
WORLD_MAP     = []
MAP_W         = 0
MAP_H         = 0
ROOM_CENTERS  = []
enemies       = []
bullets       = []
enemy_bullets = []
note_objects  = []   # list of NoteObject in the world
cure_objects  = []   # list of CureObject in the world
exit_object   = None   # the level exit door
secret_door   = None   # the secret code door for cures
secret_code_input = ""   # tracks player's code entry

# Settings (can be changed in menu)
settings = {
    "mouse_sens": 0.002,
    "master_vol": 0.8,
    "music_vol":  0.5,
    "sfx_vol":    1.0,
    "fov_mult":   1.0,   # multiplier on FOV (1.0 = 60 deg)
}

# LEVEL THEME DATA
# Each level defines wall/ceiling/floor colours, enemy count, enemy aggression
# multiplier, ambient description, and which notes + cure pieces appear here.
LEVEL_THEMES = {
    1:  {"name": "JLK Utility Basement",
            "wall": (80, 80, 90),    "ceil": (15, 15, 20),  "floor": (10, 10, 12),
            "enemies": 6,  "aggro": 0.4, "duck_enemies": 2,
            "notes": ["note_01", "note_02"], "cure": None},

    2:  {"name": "The Archive",
            "wall": (70, 60, 50),    "ceil": (12, 10, 8),   "floor": (8, 6, 5),
            "enemies": 10, "aggro": 0.55, "duck_enemies": 3,
            "notes": ["note_03", "note_04"], "cure": None},

    3:  {"name": "First Laboratory",
            "wall": (60, 90, 90),    "ceil": (8, 14, 14),   "floor": (5, 10, 10),
            "enemies": 14, "aggro": 0.65, "duck_enemies": 4,
            "notes": ["note_05", "note_06"], "cure": "cure_01"},

    4:  {"name": "The Observation Deck",
            "wall": (40, 40, 70),    "ceil": (5, 5, 18),    "floor": (3, 3, 12),
            "enemies": 18, "aggro": 0.72, "duck_enemies": 5,
            "notes": ["note_07", "note_08"], "cure": None},

    5:  {"name": "The Old Lab",
            "wall": (90, 70, 40),    "ceil": (20, 14, 6),   "floor": (12, 8, 3),
            "enemies": 20, "aggro": 0.78, "duck_enemies": 6,
            "notes": ["note_09", "note_10"], "cure": None},

    6:  {"name": "The Colony",
            "wall": (100, 50, 50),   "ceil": (22, 8, 8),    "floor": (14, 4, 4),
            "enemies": 24, "aggro": 0.82, "duck_enemies": 7,
            "notes": ["note_11", "note_12"], "cure": None},

    7:  {"name": "The Loop",
            "wall": (60, 60, 60),    "ceil": (10, 10, 10),  "floor": (6, 6, 6),
            "enemies": 26, "aggro": 0.85, "duck_enemies": 8,
            "notes": ["note_13", "note_14"], "cure": None},

    8:  {"name": "The Specimen Wing",
            "wall": (110, 40, 80),   "ceil": (24, 6, 16),   "floor": (16, 3, 10),
            "enemies": 30, "aggro": 0.88, "duck_enemies": 9,
            "notes": ["note_15", "note_16"], "cure": "cure_02"},

    9:  {"name": "The Church",
            "wall": (60, 50, 80),    "ceil": (10, 8, 18),   "floor": (6, 4, 12),
            "enemies": 32, "aggro": 0.90, "duck_enemies": 10,
            "notes": ["note_17", "note_18"], "cure": None},

    10: {"name": "The Signal Room",
            "wall": (30, 80, 50),    "ceil": (5, 18, 10),   "floor": (3, 12, 6),
            "enemies": 34, "aggro": 0.92, "duck_enemies": 11,
            "notes": ["note_19", "note_20"], "cure": None},

    11: {"name": "The Flood",
            "wall": (30, 50, 110),   "ceil": (4, 8, 24),    "floor": (2, 4, 16),
            "enemies": 36, "aggro": 0.93, "duck_enemies": 12,
            "notes": ["note_21", "note_22"], "cure": None},

    12: {"name": "The Garden",
            "wall": (40, 110, 60),   "ceil": (6, 24, 10),   "floor": (3, 16, 6),
            "enemies": 38, "aggro": 0.94, "duck_enemies": 13,
            "notes": ["note_23", "note_24"], "cure": None},

    13: {"name": "The Threshold",
            "wall": (110, 80, 30),   "ceil": (24, 16, 4),   "floor": (16, 10, 2),
            "enemies": 40, "aggro": 0.95, "duck_enemies": 14,
            "notes": ["note_25", "note_26"], "cure": "cure_03"},

    14: {"name": "The Source — Layer I",
            "wall": (120, 30, 30),   "ceil": (28, 4, 4),    "floor": (20, 2, 2),
            "enemies": 44, "aggro": 0.96, "duck_enemies": 15,
            "notes": ["note_27"], "cure": None},

    15: {"name": "The Source — Layer II",
            "wall": (120, 30, 80),   "ceil": (28, 4, 18),   "floor": (20, 2, 12),
            "enemies": 46, "aggro": 0.97, "duck_enemies": 16,
            "notes": ["note_28"], "cure": None},

    16: {"name": "The Source — Layer III",
            "wall": (80, 30, 120),   "ceil": (18, 4, 28),   "floor": (12, 2, 20),
            "enemies": 48, "aggro": 0.97, "duck_enemies": 17,
            "notes": ["note_29"], "cure": None},

    17: {"name": "The Source — Layer IV",
            "wall": (30, 80, 120),   "ceil": (4, 18, 28),   "floor": (2, 12, 20),
            "enemies": 50, "aggro": 0.98, "duck_enemies": 18,
            "notes": ["note_30"], "cure": None},

    18: {"name": "The Source — Layer V",
            "wall": (120, 120, 30),  "ceil": (28, 28, 4),   "floor": (20, 20, 2),
            "enemies": 52, "aggro": 0.98, "duck_enemies": 19,
            "notes": ["note_31"], "cure": None},

    19: {"name": "The Anteroom",
            "wall": (150, 50, 50),   "ceil": (35, 8, 8),    "floor": (25, 4, 4),
            "enemies": 55, "aggro": 0.99, "duck_enemies": 20,
            "notes": ["note_32"], "cure": None},

    20: {"name": "The Core — Dr. Stephany",
            "wall": (180, 20, 20),   "ceil": (40, 3, 3),    "floor": (28, 2, 2),
            "enemies": 20, "aggro": 1.0,  "duck_enemies": 5,
            "notes": ["note_33"], "cure": None},
}

# ALL NOTES  (lore, real ONU history woven in)
NOTES = {
"note_01": (
    "MAINTENANCE LOG — JLK BUILDING, Sub-Level 1\n"
    "Date: October 3, 1987\n\n"
    "Discovered anomalous concrete settling in SE corridor.\n"
    "Void space detected beneath slab — estimated 4ft depth.\n"
    "Referred to Physical Plant. No further action recommended.\n\n"
    "   — R. Holloway, Facilities"
),
"note_02": (
    "INTERNAL MEMO — Ohio Northern University\n"
    "Dept. of Engineering  |  Ada, Ohio  |  Nov 12, 1987\n\n"
    "The void beneath JLK is NOT a karst formation.\n"
    "Sonar depth: indeterminate. Repeat — indeterminate.\n"
    "Do not file with county. Do not contact ODNR.\n"
    "Forward all findings to Dean Harwick's office only.\n\n"
    "   — Prof. G. Aldenmoor, Civil Engineering"
),
"note_03": (
    "GEOLOGY SURVEY — CONFIDENTIAL\n"
    "Ohio Northern University  |  Ada, Ohio  |  1991\n\n"
    "Survey commissioned by the Structural Studies Initiative.\n"
    "Findings: cavity extends minimum 200ft below foundation.\n"
    "Walls show no natural erosion. Geometry is... regular.\n"
    "Recommend immediate controlled exploration.\n\n"
    "ONU was founded in 1871. Ada sits on Devonian limestone.\n"
    "Standard karst does not produce regular geometry.\n"
    "This is not standard karst."
),
"note_04": (
    "JOURNAL — H. Wetch, Professor of Engineering\n"
    "March 4, 1994\n\n"
    "They let me go down today. The cavity is real.\n"
    "The walls are smooth. Not carved — grown.\n"
    "I found what looked like script near the base.\n"
    "Not any language I recognise. Not any language\n"
    "anyone recognises, it turns out.\n\n"
    "The SSI has been down here since '91.\n"
    "They have been very quiet about that."
),
"note_05": (
    "SSI INTERNAL DOCUMENT — LEVEL 3 FINDINGS\n"
    "Classified — Structural Studies Initiative\n"
    "Date: February 2001\n\n"
    "The organism responds to acoustic stimulation.\n"
    "Frequency range: 18-22Hz (infrasound).\n"
    "Response: bioluminescent pulse. Duration 3-7 seconds.\n"
    "We have been calling it 'the signal' informally.\n\n"
    "Dr. Wetch has retired. His replacement, Dr. S., has\n"
    "expressed interest in expanding the protocol.\n"
    "Budget request submitted to Provost office."
),
"note_06": (
    "HANDWRITTEN NOTE — torn from a spiral notebook\n\n"
    "If you find this — GET OUT.\n"
    "The elevator goes down further than the button says.\n"
    "There is a sub-level 4. The SSI doesn't put it\n"
    "on the map they give the grad students.\n\n"
    "I went down to sub-4. I saw what they're keeping there.\n"
    "I am leaving this here and I am not coming back.\n\n"
    "   — M.T., Grad Student, Mech. Engineering, 2003"
),
"note_07": (
    "SSI ORIENTATION DOCUMENT — FOR FELLOWS ONLY\n"
    "Ohio Northern University  |  2008\n\n"
    "Welcome to the Structural Studies Initiative.\n"
    "You have been selected for your academic excellence\n"
    "and your discretion.\n\n"
    "The JLK sub-levels are a RESTRICTED RESEARCH AREA.\n"
    "You are not to discuss your work with other students,\n"
    "faculty, or family. Your fellowship agreement\n"
    "includes a non-disclosure clause.\n\n"
    "Dr. Stephany leads all active research.\n"
    "Her authority in the sub-levels is absolute."
),
"note_08": (
    "EMAIL PRINTOUT — Sender: H.Wetch@onu.edu\n"
    "To: UniversityPresident@onu.edu\n"
    "Date: March 17, 2009\n\n"
    "President McCall,\n\n"
    "I am writing to formally request that the SSI\n"
    "program be suspended immediately.\n"
    "What began as geological study has become something\n"
    "I cannot in good conscience allow to continue.\n\n"
    "Dr. Stephany's Phase 2 protocol involves direct\n"
    "biological contact with the organism.\n"
    "I do not believe the IRB approved this.\n"
    "I do not believe the IRB was told.\n\n"
    "   — Harold Wetch, Professor Emeritus"
    "\n\n[No reply on record.]"
),
"note_09": (
    "ADA TOWNSHIP HISTORICAL RECORD — 1853\n"
    "Hardin County Survey, State of Ohio\n\n"
    "Surveyor J. Pembroke notes in his field journal:\n"
    "'Found unusual depression near centre of proposed\n"
    " township. Local Shawnee guides refused to approach.\n"
    " They call it Mshi-Waabooz — the place that breathes.\n"
    " I dropped a stone. Did not hear it land.'\n\n"
    "ONU was founded on this land 18 years later.\n"
    "The JLK building was constructed directly above\n"
    "the Pembroke depression in 1962."
),
"note_10": (
    "SSI RESEARCH LOG — Dr. Stephany, Lead Researcher\n"
    "Entry 47  |  Date: November 2011\n\n"
    "Phase 2 complete. Results exceed projections.\n"
    "The organism does not merely respond to stimuli.\n"
    "It learns. It adapts. It has been adapting\n"
    "for a very long time, I suspect.\n\n"
    "The subjects from the 2010 cohort are stable.\n"
    "Their morphology has changed but cognition\n"
    "remains partially intact in 3 of 7 cases.\n\n"
    "Beginning Phase 3 planning. This is the work\n"
    "we were always meant to do."
),
"note_11": (
    "PERSONAL JOURNAL — unknown author\n"
    "Found wedged behind a filing cabinet\n\n"
    "Day 12 underground.\n"
    "They said it would be a week.\n"
    "The elevator doesn't work anymore.\n\n"
    "There are six of us. We have food for maybe 4 days.\n"
    "Marcus found another staircase going down.\n"
    "We voted not to take it.\n\n"
    "Dr. Stephany came by today. She seemed... fine.\n"
    "More than fine. She said we were not trapped,\n"
    "we were 'transitioning.' I don't know what that means.\n"
    "I'm not sure I want to."
),
"note_12": (
    "SSI DOCUMENT — PHASE 3 OVERVIEW\n"
    "EYES ONLY  |  Dr. Stephany  |  2015\n\n"
    "Containment is no longer the objective.\n"
    "We have spent 24 years trying to understand\n"
    "the organism by keeping it at arm's length.\n\n"
    "Phase 3 is integration.\n"
    "The organism has already begun this process\n"
    "in several of our long-term personnel.\n"
    "We will now do so deliberately, with controls.\n\n"
    "The university board has been briefed.\n"
    "They have approved funding through 2025.\n"
    "The ONU seal contains the organism's primary\n"
    "symbol. It has been there since 1871.\n"
    "The founders knew."
),
"note_13": (
    "GRAD STUDENT BLOG — printed copy\n"
    "Posted: September 3, 2019\n\n"
    "'I got the SSI fellowship!!! Best research\n"
    " opportunity of my PhD, they said. Full stipend,\n"
    " housing, the works. Only rule is no phones\n"
    " in the sub-levels. Totally understandable\n"
    " for a sensitive research environment right?'\n\n"
    "[Three more posts follow, increasingly short.]\n"
    "[Final post, October 1, 2019:]\n"
    "'I need someone to come to JLK. Sub-level 1.\n"
    " Tell them Jake sent you. Please hurry.'\n\n"
    "[Account inactive since October 2019.]"
),
"note_14": (
    "NOTE SCRATCHED INTO THE WALL\n"
    "Sub-Level 3 corridor, east passage\n\n"
    "THE HALLWAY LOOPS\n"
    "COUNT THE CEILING TILES\n"
    "THE SHORT HALLWAY HAS 14\n"
    "THE REAL EXIT HAS 13\n\n"
    "IF ONE EXISTS BEHIND\n"
    "THE SEALED DOOR...\n"
    "REMEMBER: THE COUNT.\n"
    "ENTER CODE TO UNLOCK"
),
"note_15": (
    "SSI SPECIMEN LOG — Classified\n"
    "Dr. Stephany  |  2017\n\n"
    "Specimen designations:\n"
    "  Class A — Standard organism fauna. Docile.\n"
    "  Class B — Organism-influenced personnel.\n"
    "             Partial cognition retained.\n"
    "  Class C — Full integration subjects.\n"
    "             Do not approach without protocol gear.\n\n"
    "Class C specimens have demonstrated coordinated\n"
    "behaviour not observed in Class A fauna.\n"
    "They appear to protect the deeper levels.\n"
    "Dr. Stephany believes they are 'guardians.'\n"
    "I believe they are people. Were people.\n\n"
    "   — Asst. Researcher K. Lorne (resigned 2018)"
),
"note_16": (
    "HANDWRITTEN — URGENT\n\n"
    "The vial is real. I made three.\n"
    "The organism's integration is not permanent\n"
    "if caught early enough.\n\n"
    "I hid the pieces in three places.\n"
    "You will know them when you find them.\n"
    "Each piece alone does nothing.\n"
    "Together, the compound reverses integration\n"
    "in Class B and early Class C subjects.\n\n"
    "I don't know if it works on someone as far\n"
    "along as Dr. Stephany. But it might.\n"
    "It has to be worth trying.\n\n"
    "   — K. Lorne, 2018"
),
"note_17": (
    "STONE INSCRIPTION — translated by SSI linguist\n"
    "Location: Sub-level 9, cathedral chamber\n"
    "Date of translation: 2012\n\n"
    "'This place is a mouth.\n"
    " What descends is changed.\n"
    " What the mouth keeps is kept forever.\n"
    " Those who fed the mouth willingly\n"
    " became the walls.\n"
    " Those who fed it unwillingly\n"
    " became the doors.\n"
    " You who read this — you are neither yet.'\n\n"
    "[Linguist's note: No known ancient culture\n"
    " in Ohio produced inscriptions. This predates\n"
    " any known human habitation of the region.]"
),
"note_18": (
    "ONU OFFICIAL SEAL — Historical Note\n"
    "Sourced from University Archives, 1998\n\n"
    "The symbol at the base of the ONU seal,\n"
    "described officially as 'a stylised torch',\n"
    "does not match any historical torch design.\n\n"
    "Cross-referenced with SSI specimen room\n"
    "wall markings: identical.\n\n"
    "The seal was designed by Henry Solomon Lehr,\n"
    "ONU's founder, in 1871.\n"
    "Lehr spent six months in Ada prior to founding\n"
    "the university. No records exist of his\n"
    "activities during that period."
),
"note_19": (
    "SSI SIGNAL ROOM LOG\n"
    "Date: January 14, 2023\n"
    "Operator: Dr. Stephany\n\n"
    "Broadcast frequency adjusted to 19.2Hz.\n"
    "Response amplitude: maximum recorded.\n\n"
    "The organism is aware of the broadcast.\n"
    "I believe it has always been aware.\n"
    "I believe it has been waiting for us\n"
    "to find the right frequency.\n\n"
    "Phase 3 is no longer an experiment.\n"
    "Phase 3 is an invitation.\n"
    "I have accepted on behalf of the university.\n"
    "On behalf of everyone."
),
"note_20": (
    "TEXT MESSAGE THREAD — recovered from phone\n"
    "Found: Sub-level 10 signal room\n\n"
    "Unknown > Campus Security:\n"
    "'Something is wrong in JLK. I can hear\n"
    " something through the floor of my office.'\n\n"
    "Security > Unknown:\n"
    "'Noted. Maintenance will check sub-level 1.'\n\n"
    "Unknown > Campus Security:\n"
    "'It's not sub-level 1. It's deeper. It sounds\n"
    " like... singing? Please just come look.'\n\n"
    "[No further messages. Phone battery dead.\n"
    " Date of messages: March 3, 2023.]"
),
"note_21": (
    "EMERGENCY INCIDENT REPORT — DRAFT\n"
    "Never filed\n\n"
    "On the night of April 7, 2023, sub-levels 6-8\n"
    "experienced rapid fluid ingress from the organism.\n"
    "Eleven SSI personnel were present.\n"
    "Four evacuated successfully to sub-level 5.\n"
    "Seven did not evacuate.\n\n"
    "Dr. Stephany was in sub-level 11 at the time.\n"
    "She was not among those who attempted to evacuate.\n"
    "She was not among those who failed to evacuate.\n"
    "Her current location is unknown.\n\n"
    "[Report abandoned mid-sentence]"
),
"note_22": (
    "SOGGY NOTE — barely legible\n"
    "Found floating in sub-level 11\n\n"
    "the water came fast\n"
    "we ran up but the door was sealed\n"
    "i dont know who sealed it\n"
    "i dont think it was a person\n\n"
    "if you find this you found a way through\n"
    "that means there is a way through\n"
    "keep going\n"
    "im sorry i cant\n"
),
"note_23": (
    "SSI BOTANICAL LOG — anomalous\n"
    "Date: 2020\n\n"
    "Sub-level 12 flora defies classification.\n"
    "Bioluminescent. No chlorophyll. No root system.\n"
    "Growth medium appears to be the organism itself.\n\n"
    "The fauna here are passive. They watch us.\n"
    "One researcher sat among them for an hour.\n"
    "She said it felt like being forgiven.\n"
    "She requested transfer to permanent sub-12 duty.\n"
    "We approved it. She is still there.\n"
    "She seems happy. That worries me more\n"
    "than anything else I have seen down here.\n\n"
    "   — SSI Researcher, name redacted"
),
"note_24": (
    "DR. STEPHANY — Personal Note\n"
    "Date unknown\n\n"
    "The organism is not hostile.\n"
    "We were.\n\n"
    "Everything that happened — the subjects,\n"
    "the specimens, the ones who didn't come back —\n"
    "that was us. Our fear. Our urgency.\n\n"
    "The organism would have shared itself freely.\n"
    "We took instead.\n\n"
    "I understand that now. I am trying to\n"
    "correct it. The integration, for me, is\n"
    "not a loss. It is an apology.\n\n"
    "But I am afraid of what I am becoming.\n"
    "If someone reads this — I left a way out.\n"
    "For both of us."
),
"note_25": (
    "LORNE'S FINAL LAB NOTES\n"
    "K. Lorne, 2018\n\n"
    "Compound synthesis complete.\n"
    "Three components, separated for safety.\n"
    "Combined formula reverses organism integration\n"
    "by disrupting the bioluminescent binding mechanism.\n\n"
    "Component 1: Sub-level 3, east lab, specimen cabinet 4.\n"
    "Component 2: Sub-level 8, false wall behind mirror.\n"
    "Component 3: Sub-level 13, collapsed east passage.\n\n"
    "If Dr. Stephany is still... herself enough\n"
    "to accept it — give her all three.\n"
    "If not — you may need to make a harder choice.\n\n"
    "Good luck. I'm sorry I won't be there."
),
"note_26": (
    "SCRATCHED ON THE THRESHOLD DOOR\n\n"
    "WHAT IS BEYOND THIS DOOR\n"
    "IS WHAT WAS ALWAYS HERE\n"
    "BEFORE THE BUILDING\n"
    "BEFORE THE TOWN\n"
    "BEFORE THE PEOPLE\n\n"
    "IT IS NOT EVIL\n"
    "IT IS NOT GOOD\n"
    "IT IS VERY OLD\n"
    "AND IT IS VERY HUNGRY\n"
    "AND IT HAS BEEN WAITING\n\n"
    "THE WOMAN WITH THE RESEARCH\n"
    "SHE IS STILL IN THERE\n"
    "SOMEWHERE"
),
"note_27": (
    "SSI INTERNAL LOG — Fauna Classification Review\n"
    "Date: March 2006  |  Researcher: Dr. Aldenmoor\n\n"
    "Anomalous development in Class A fauna.\n"
    "The organism's surface-level creatures have begun\n"
    "adopting new morphology in sectors where human\n"
    "presence has been consistent for 6+ months.\n\n"
    "Specifically: small, rounded, bipedal forms.\n"
    "Yellow colouration. Vocalisation approximating\n"
    "a soft repeated tone.\n\n"
    "Working hypothesis: the organism reads emotional\n"
    "states from nearby humans and adapts its fauna\n"
    "to minimise perceived threat.\n"
    "It is, in its way, trying to seem safe.\n\n"
    "Several researchers have started calling them\n"
    "'the ducks.' Dr. Stephany finds this funny.\n"
    "I find it one of the most unsettling things\n"
    "I have ever seen.\n\n"
    "   — G. Aldenmoor, retiring end of term"
),
"note_28": ("SOURCE LAYER II\nDr. Stephany's voice on the old intercom:\n"
            "'I can hear you. I have been waiting.\nPlease — be careful. I am not\n"
            "entirely in control of what protects this place.'"),
"note_29": ("SOURCE LAYER III\nA photograph pinned to the wall:\n"
            "ONU faculty, 2018. Dr. Stephany front row, centre.\n"
            "Smiling. Normal. Human.\nSomeone has written below it:\n"
            "'She went first. She went willingly.\nShe went for us.'\n"
            "Someone else has added:\n'She went too far.'"),
"note_30": (
    "SCRATCHED INTO THE WALL — Source Layer IV\n"
    "Author unknown\n\n"
    "I know what the ducks are.\n\n"
    "The organism doesn't understand death.\n"
    "When it takes someone — really takes them,\n"
    "Class C integration, the full process —\n"
    "it tries to give something back.\n\n"
    "It thinks the ducks make us happy.\n"
    "It learned that from us. From the researchers\n"
    "who laughed the first time they saw one.\n\n"
    "So when it absorbed the 2010 cohort —\n"
    "eight grad students, two researchers —\n"
    "it kept them close, the way it knows how.\n\n"
    "The ducks are not fauna.\n"
    "The ducks are what the organism made\n"
    "from the people it loved most.\n"
    "It thought it was being kind.\n\n"
    "Do not shoot the ducks.\n"
    "I'm begging you.\n"
    "I know one of them.\n"
    "Knew.\n"
),
"note_31": ("SOURCE LAYER V\nYou can hear it now.\n"
            "The frequency Dr. Stephany found — 19.2Hz.\nYou feel it in your teeth.\n"
            "The organism knows you are here.\nIt has known since Level 1.\n"
            "It let you come this far.\nAsk yourself why."),
"note_32": ("THE ANTEROOM\nOne door ahead.\nBehind it — Dr. Stephany.\n"
            "Professor of Biological Engineering, ONU.\n2019 Faculty Excellence Award.\n"
            "Author of 34 peer-reviewed papers.\n"
            "Last seen: April 7, 2023.\n\n"
            "She is in there.\nSo is something else.\nGood luck."),
"note_33": ("DR. STEPHANY'S LAST COHERENT NOTE\n"
            "Date: unknown  |  Sub-level 20\n\n"
            "If you have the compound — use it.\nI will fight you. I can't help it.\n"
            "The organism fights through me now.\n"
            "But somewhere in here I am still Stephany.\n\n"
            "If you don't have it — I understand.\nDo what you must.\n"
            "Tell the university what happened here.\n"
            "Tell them what the seal means.\n"
            "Tell them to close the building.\n\n"
            "Tell them I tried."),
}

# MAP HELPERS
def tile_is_wall(mx, my):
    if my < 0 or my >= MAP_H or mx < 0 or mx >= MAP_W:
        return True
    return WORLD_MAP[my][mx] != 0

def tile_is_open(mx, my):
    return not tile_is_wall(mx, my)

# MAP GENERATION
def carve_maze(size):
    maze = [[1] * size for _ in range(size)]
    for y in range(1, size - 1, 2):
        for x in range(1, size - 1, 2):
            maze[y][x] = 0
    stack   = [(1, 1)]
    visited = {(1, 1)}
    while stack:
        x, y = stack[-1]
        neighbors = [(x+dx, y+dy)
                        for dx, dy in ((2,0),(-2,0),(0,2),(0,-2))
                        if 1 <= x+dx < size-1 and 1 <= y+dy < size-1
                        and (x+dx, y+dy) not in visited]
        if not neighbors:
            stack.pop()
            continue
        nx, ny = random.choice(neighbors)
        maze[(y+ny)//2][(x+nx)//2] = 0
        maze[ny][nx] = 0
        visited.add((nx, ny))
        stack.append((nx, ny))
    return maze

def carve_rect(rx, ry, rw, rh):
    for y in range(ry, ry+rh):
        for x in range(rx, rx+rw):
            WORLD_MAP[y][x] = 0

def carve_corridor(x1, y1, x2, y2):
    if random.random() < 0.5:
        for x in range(min(x1,x2), max(x1,x2)+1):
            WORLD_MAP[y1][x] = 0
            if y1+1 < MAP_H: WORLD_MAP[y1+1][x] = 0
        for y in range(min(y1,y2), max(y1,y2)+1):
            WORLD_MAP[y][x2] = 0
            if x2+1 < MAP_W: WORLD_MAP[y][x2+1] = 0
    else:
        for y in range(min(y1,y2), max(y1,y2)+1):
            WORLD_MAP[y][x1] = 0
            if x1+1 < MAP_W: WORLD_MAP[y][x1+1] = 0
        for x in range(min(x1,x2), max(x1,x2)+1):
            WORLD_MAP[y2][x] = 0
            if y2+1 < MAP_H: WORLD_MAP[y2+1][x] = 0

def bfs_connected(sx, sy, gx, gy):
    if (sx,sy) == (gx,gy): return True
    visited, stack = set(), [(sx,sy)]
    while stack:
        x, y = stack.pop()
        if (x,y) == (gx,gy): return True
        if (x,y) in visited: continue
        visited.add((x,y))
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if tile_is_open(nx, ny) and (nx,ny) not in visited:
                stack.append((nx, ny))
    return False

def generate_map():
    global WORLD_MAP, MAP_W, MAP_H, ROOM_CENTERS
    size = 50
    WORLD_MAP    = carve_maze(size)
    MAP_W        = size
    MAP_H        = size
    ROOM_CENTERS = []
    placed = []
    for _ in range(40):
        if len(placed) >= 10: break
        rw = random.randint(6, 10)
        rh = random.randint(6, 10)
        rx = random.randint(2, size - rw - 2)
        ry = random.randint(2, size - rh - 2)
        overlap = any(rx < ox+ow+2 and ox < rx+rw+2 and
                        ry < oy+oh+2 and oy < ry+rh+2
                        for ox,oy,ow,oh in placed)
        if not overlap:
            carve_rect(rx, ry, rw, rh)
            placed.append((rx, ry, rw, rh))
            ROOM_CENTERS.append((rx + rw//2, ry + rh//2))
    if len(ROOM_CENTERS) >= 2:
        connected = [ROOM_CENTERS[0]]
        remaining = ROOM_CENTERS[1:]
        while remaining:
            best_dist, best_a, best_b = float('inf'), None, None
            for a in connected:
                for b in remaining:
                    d = (a[0]-b[0])**2 + (a[1]-b[1])**2
                    if d < best_dist:
                        best_dist, best_a, best_b = d, a, b
            carve_corridor(best_a[0], best_a[1], best_b[0], best_b[1])
            connected.append(best_b)
            remaining.remove(best_b)
        for _ in range(min(3, len(ROOM_CENTERS)-1)):
            a, b = random.sample(ROOM_CENTERS, 2)
            carve_corridor(a[0], a[1], b[0], b[1])
    if len(ROOM_CENTERS) >= 2:
        src = ROOM_CENTERS[0]
        for dst in ROOM_CENTERS[1:]:
            if not bfs_connected(src[0], src[1], dst[0], dst[1]):
                carve_corridor(src[0], src[1], dst[0], dst[1])
    if not ROOM_CENTERS:
        carve_rect(2, 2, 8, 8)
        ROOM_CENTERS.append((6, 6))

# COLLISION
def position_free(px, py):
    if tile_is_wall(int(px), int(py)): return False
    for dx, dy in ((PLAYER_RADIUS,0),(-PLAYER_RADIUS,0),
                    (0,PLAYER_RADIUS),(0,-PLAYER_RADIUS)):
        if tile_is_wall(int(px+dx), int(py+dy)): return False
    return True

def slide_move(px, py, dx, dy):
    if position_free(px+dx, py+dy): return px+dx, py+dy
    if position_free(px+dx, py):    return px+dx, py
    if position_free(px, py+dy):    return px, py+dy
    return px, py

# PATHFINDING
def bfs_next_step(sx, sy, gx, gy):
    start, goal = (sx,sy), (gx,gy)
    if start == goal: return None
    parent = {start: None}
    queue  = [start]
    found  = False
    while queue:
        curr = queue.pop(0)
        if curr == goal: found = True; break
        cx, cy = curr
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nb = (cx+dx, cy+dy)
            if nb not in parent and tile_is_open(nb[0], nb[1]):
                parent[nb] = curr
                queue.append(nb)
    if not found: return None
    node = goal
    while parent[node] != start:
        node = parent[node]
        if node is None: return None
    return node

# SPAWN HELPERS
def find_open_tile():
    for _ in range(2000):
        x = random.randint(1, MAP_W-2)
        y = random.randint(1, MAP_H-2)
        if WORLD_MAP[y][x] != 0: continue
        open_nb = sum(1 for dx,dy in ((-1,0),(1,0),(0,-1),(0,1),
                                        (-1,-1),(1,-1),(-1,1),(1,1))
                        if tile_is_open(x+dx, y+dy))
        if open_nb >= 5: return x+0.5, y+0.5
    for y in range(1, MAP_H-1):
        for x in range(1, MAP_W-1):
            if WORLD_MAP[y][x] == 0: return x+0.5, y+0.5
    return 2.5, 2.5

def best_facing_angle(px, py, steps=16):
    best_angle, best_score = 0.0, -1.0
    for i in range(steps):
        angle = i * (2*math.pi / steps)
        total = 0.0
        for j in range(7):
            ray = angle + (j/6 - 0.5) * FOV
            cos_r, sin_r = math.cos(ray), math.sin(ray)
            for k in range(1, 150):
                tx = px + cos_r*(k*0.1)
                ty = py + sin_r*(k*0.1)
                if tile_is_wall(int(tx), int(ty)):
                    total += k*0.1; break
            else:
                total += MAX_DEPTH
        avg = total / 7
        if avg > best_score: best_score = avg; best_angle = angle
    return best_angle

def find_spawn(min_dist_from=None, min_dist=8.0):
    for _ in range(2000):
        x = random.randint(1, MAP_W-2)
        y = random.randint(1, MAP_H-2)
        if WORLD_MAP[y][x] != 0: continue
        px, py = x+0.5, y+0.5
        if min_dist_from and math.hypot(px-min_dist_from[0], py-min_dist_from[1]) < min_dist:
            continue
        if position_free(px, py): return px, py
    return find_open_tile()

# INTERACTABLE WORLD OBJECTS
class NoteObject:
    def __init__(self, x, y, note_key):
        self.x        = x
        self.y        = y
        self.note_key = note_key
        self.picked_up = False
        self.radius   = 0.5

class CureObject:
    def __init__(self, x, y, piece_id):
        self.x        = x
        self.y        = y
        self.piece_id = piece_id
        self.picked_up = False
        self.radius   = 0.5

class ExitObject:
    def __init__(self, x, y):
        self.x        = x
        self.y        = y
        self.active   = False   # lights up when score threshold reached
        self.radius   = 0.6

class SecretDoor:
    def __init__(self, x, y, code):
        self.x         = x
        self.y         = y
        self.code      = code   # e.g. "13"
        self.unlocked  = False
        self.radius    = 0.6

def place_world_objects(level, player_x, player_y):
    note_objects.clear()
    cure_objects.clear()
    theme = LEVEL_THEMES.get(level, LEVEL_THEMES[1])
    # Place exit door far from player
    global exit_object, secret_door, secret_code_input
    secret_code_input = ""   # reset code input for new level
    if level < 20:
        ex, ey = find_spawn(min_dist_from=(player_x, player_y), min_dist=15.0)
        exit_object = ExitObject(ex, ey)
    else:
        exit_object = None
    # Place secret code door on levels with cure items
    if theme["cure"] is not None:
        sx, sy = find_spawn(min_dist_from=(player_x, player_y), min_dist=12.0)
        secret_door = SecretDoor(sx, sy, "13")
    else:
        secret_door = None

    # Place notes in random open spots away from player
    for note_key in theme["notes"]:
        for _ in range(200):
            x, y = find_spawn(min_dist_from=(player_x, player_y), min_dist=5.0)
            note_objects.append(NoteObject(x, y, note_key))
            break

    # Place cure piece if this level has one
    if theme["cure"]:
        for _ in range(200):
            x, y = find_spawn(min_dist_from=(player_x, player_y), min_dist=10.0)
            cure_objects.append(CureObject(x, y, theme["cure"]))
            break

# ENEMY
class Enemy:
    def __init__(self, x, y, is_duck=False, is_boss=False):
        self.x            = x
        self.y            = y
        self.alive        = True
        self.dead         = False
        self.state        = 'idle'
        self.dmg_timer    = 0.0
        self.death_timer  = 0.0
        self.path_timer   = 0.0
        self.waypoint     = None
        self.is_duck      = is_duck   # duck-type enemy: hops around, drops duck on death
        self.is_boss      = is_boss
        self.boss_phase   = 1         # boss has 3 phases
        self.boss_health  = 300 if is_boss else 1
        self.flash_timer  = 0.0       # red flash when boss is hit
        self.spawn_grace  = 3.0       # seconds before enemy activates
        self.duck_timer   = 0.0       # counts up; transforms to duck at threshold
        self.was_human    = not is_duck and not is_boss  # eligible for transformation

def spawn_enemies(count, duck_count, avoid_x, avoid_y, level):
    theme  = LEVEL_THEMES.get(level, LEVEL_THEMES[1])
    aggro  = theme["aggro"]
    placed = 0
    duck_placed = 0
    for _ in range((count + duck_count) * 80):
        if placed >= count and duck_placed >= duck_count: break
        px, py = find_spawn(min_dist_from=(avoid_x, avoid_y), min_dist=8.0)
        if any(math.hypot(px-e.x, py-e.y) < 1.0 for e in enemies if not e.dead):
            continue
        if duck_placed < duck_count:
            enemies.append(Enemy(px, py, is_duck=True))
            duck_placed += 1
        elif placed < count:
            enemies.append(Enemy(px, py))
            placed += 1

def spawn_boss(avoid_x, avoid_y):
    for _ in range(500):
        px, py = find_spawn(min_dist_from=(avoid_x, avoid_y), min_dist=12.0)
        enemies.append(Enemy(px, py, is_boss=True))
        return

# BULLETS
class Bullet:
    def __init__(self, x, y, angle):
        self.x     = x
        self.y     = y
        self.dx    = math.cos(angle) * BULLET_SPEED
        self.dy    = math.sin(angle) * BULLET_SPEED
        self.alive = True

    def update(self, level):
        self.x += self.dx
        self.y += self.dy
        if tile_is_wall(int(self.x), int(self.y)):
            self.alive = False; return
        for enemy in enemies:
            if not enemy.alive: continue
            if math.hypot(enemy.x-self.x, enemy.y-self.y) < ENEMY_HIT_RADIUS:
                if enemy.is_boss:
                    enemy.boss_health -= 1
                    enemy.flash_timer  = 0.1
                    if enemy.boss_health <= 200: enemy.boss_phase = 2
                    if enemy.boss_health <= 100: enemy.boss_phase = 3
                    if enemy.boss_health <= 0:
                        enemy.alive = False; enemy.dead = True
                        enemy.state = 'dead'; enemy.death_timer = 1.5
                else:
                    enemy.alive = False; enemy.dead = True
                    enemy.state = 'dead'; enemy.death_timer = ENEMY_DEATH_DISPLAY
                self.alive = False; return

class EnemyBullet:
    def __init__(self, x, y, angle, is_boss=False):
        spd = ENEMY_BULLET_SPEED * (1.5 if is_boss else 1.0)
        self.x     = x
        self.y     = y
        self.dx    = math.cos(angle) * spd
        self.dy    = math.sin(angle) * spd
        self.alive = True
        self.dmg   = ENEMY_BASE_DAMAGE * (2 if is_boss else 1)

    def update(self, player):
        self.x += self.dx
        self.y += self.dy
        if tile_is_wall(int(self.x), int(self.y)):
            self.alive = False; return
        if math.hypot(self.x-player.x, self.y-player.y) < ENEMY_BULLET_RADIUS:
            player.take_hit(self.dmg)
            self.alive = False

# PLAYER
class Player:
    def __init__(self):
        self.x              = 2.5
        self.y              = 2.5
        self.angle          = 0.0
        self.pitch          = 0.0
        self.health         = 100
        self.score          = 0
        self.level          = 1
        self.target_score   = LEVEL_SCORE
        self.dmg_cooldown   = 0.0
        self.cure_pieces    = []   # list of piece IDs collected
        self.notes_this_level_total = 0   # how many notes exist on current level
        self.notes_this_level_found = 0   # how many picked up this level
        self.notes_read     = []   # list of note keys read
        self.boss_defeated  = False
        self.has_audio      = False
        pygame.mixer.init()
        self.snd_shoot    = None
        self.snd_door     = None
        self.snd_note     = None
        self.has_audio    = False
        try:
            self.snd_shoot = pygame.mixer.Sound('assets/sounds/dspistol.wav')
            self.snd_shoot.set_volume(settings["sfx_vol"])
            self.has_audio = True
        except Exception:
            pass
        try:
            self.snd_door = pygame.mixer.Sound('assets/sounds/door.wav')
            self.snd_door.set_volume(settings["sfx_vol"])
        except Exception:
            pass
        try:
            self.snd_note = pygame.mixer.Sound('sounds/note_pickup.mp3')
            self.snd_note.set_volume(settings["sfx_vol"])
        except Exception:
            pass

    def shoot(self):
        if self.has_audio:
            self.snd_shoot.set_volume(settings["sfx_vol"])
            self.snd_shoot.play()
        bullets.append(Bullet(self.x, self.y, self.angle))

    def play_door(self):
        if self.snd_door:
            self.snd_door.set_volume(settings["sfx_vol"] * settings["master_vol"])
            self.snd_door.play()

    def play_note_pickup(self):
        if self.snd_note:
            self.snd_note.set_volume(settings["sfx_vol"] * settings["master_vol"])
            self.snd_note.play()

    def move(self, keys, dt):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        spd   = MOVE_SPEED
        fwd   = spd  if keys[pygame.K_w] else (-spd if keys[pygame.K_s] else 0)
        side  = spd  if keys[pygame.K_d] else (-spd if keys[pygame.K_a] else 0)
        dx    = cos_a*fwd - sin_a*side
        dy    = sin_a*fwd + cos_a*side
        self.x, self.y = slide_move(self.x, self.y, dx, dy)
        if keys[pygame.K_LEFT]:  self.angle -= ROT_SPEED
        if keys[pygame.K_RIGHT]: self.angle += ROT_SPEED
        if keys[pygame.K_q] or keys[pygame.K_PAGEUP]:
            self.pitch = min(PITCH_MAX, self.pitch + PITCH_STEP)
        if keys[pygame.K_e] or keys[pygame.K_PAGEDOWN]:
            self.pitch = max(-PITCH_MAX, self.pitch - PITCH_STEP)
        self.angle %= (2 * math.pi)

    def apply_mouse(self, rel_x):
        self.angle += rel_x * settings["mouse_sens"]
        self.angle %= (2 * math.pi)

    def tick(self, dt):
        if self.dmg_cooldown > 0:
            self.dmg_cooldown = max(0.0, self.dmg_cooldown - dt)

    def take_hit(self, amount):
        if self.dmg_cooldown <= 0:
            self.health       = max(0, self.health - amount)
            self.dmg_cooldown = 0.8

    def check_interactions(self):
        for note in note_objects:
            if not note.picked_up:
                if math.hypot(self.x-note.x, self.y-note.y) < note.radius + 0.3:
                    return ("note", note)
        for cure in cure_objects:
            if not cure.picked_up:
                if math.hypot(self.x-cure.x, self.y-cure.y) < cure.radius + 0.3:
                    return ("cure", cure)
        if exit_object and exit_object.active:
            if math.hypot(self.x-exit_object.x, self.y-exit_object.y) < exit_object.radius + 0.3:
                return ("exit", exit_object)
        if secret_door and not secret_door.unlocked:
            if math.hypot(self.x-secret_door.x, self.y-secret_door.y) < secret_door.radius + 0.3:
                return ("secret_door", secret_door)
        return None

# RAYCASTER (DDA)
def cast_rays(screen, player, wall_color, ceil_color, floor_color):
    effective_fov  = FOV * settings["fov_mult"]
    effective_half = effective_fov / 2
    vertical_shift = int(player.pitch * HALF_H)
    pygame.draw.rect(screen, ceil_color,  (0, 0, WIDTH, HALF_H + vertical_shift))
    pygame.draw.rect(screen, floor_color, (0, HALF_H + vertical_shift, WIDTH, HEIGHT))
    z_buffer = [MAX_DEPTH] * WIDTH

    for col in range(WIDTH):
        camera_x  = 2.0 * col / WIDTH - 1.0
        plane_len = math.tan(effective_half)
        dir_x     = math.cos(player.angle)
        dir_y     = math.sin(player.angle)
        plane_x   = -dir_y * plane_len
        plane_y   =  dir_x * plane_len
        ray_dx    = dir_x + plane_x * camera_x
        ray_dy    = dir_y + plane_y * camera_x
        map_x     = int(player.x)
        map_y     = int(player.y)
        delta_x   = abs(1.0/ray_dx) if ray_dx != 0 else 1e30
        delta_y   = abs(1.0/ray_dy) if ray_dy != 0 else 1e30
        if ray_dx < 0: step_x=-1; side_dx=(player.x-map_x)*delta_x
        else:          step_x= 1; side_dx=(map_x+1.0-player.x)*delta_x
        if ray_dy < 0: step_y=-1; side_dy=(player.y-map_y)*delta_y
        else:          step_y= 1; side_dy=(map_y+1.0-player.y)*delta_y
        hit = False; side = 0
        for _ in range(int(MAX_DEPTH*3)):
            if side_dx < side_dy: side_dx+=delta_x; map_x+=step_x; side=0
            else:                 side_dy+=delta_y; map_y+=step_y; side=1
            if map_y<0 or map_y>=MAP_H or map_x<0 or map_x>=MAP_W: break
            if WORLD_MAP[map_y][map_x] != 0: hit=True; break
        if not hit: continue
        if side==0: perp_dist=(map_x-player.x+(1-step_x)/2)/ray_dx
        else:       perp_dist=(map_y-player.y+(1-step_y)/2)/ray_dy
        perp_dist     = max(perp_dist, 0.05)
        z_buffer[col] = perp_dist
        wall_h   = int(HEIGHT/perp_dist)
        draw_top = max(0, HALF_H - wall_h//2 + vertical_shift)
        draw_bot = min(HEIGHT-1, HALF_H + wall_h//2 + vertical_shift)
        shade    = 0.65 if side==1 else 1.0
        bright   = shade * max(0.0, 1.0 - perp_dist/MAX_DEPTH)
        color    = tuple(max(0,min(255,int(c*bright))) for c in wall_color)
        pygame.draw.line(screen, color, (col,draw_top), (col,draw_bot))
    return z_buffer

# syringe bullets
def draw_syringe(surface, cx, cy, size, y_spin_angle):
    # Y-axis spin: squish width with cos, flip direction past 90deg
    x_scale = abs(math.cos(y_spin_angle))
    flip    = math.cos(y_spin_angle) < 0
    s       = max(1, size)

    # Barrel (main body)
    barrel_w = max(3, int(s * 2.2 * x_scale))
    barrel_h = max(2, int(s * 0.45))
    barrel_x = cx - barrel_w if not flip else cx
    pygame.draw.rect(surface, (200, 220, 255),
                     (barrel_x, cy - barrel_h // 2, barrel_w, barrel_h))

    # Fluid fill inside barrel (green bioluminescent)
    if x_scale > 0.15:
        fluid_w = max(1, int(barrel_w * 0.7))
        fluid_x = (cx - fluid_w + int(barrel_w * 0.1)) if not flip else (cx + int(barrel_w * 0.1))
        pygame.draw.rect(surface, (80, 255, 140),
                         (fluid_x, cy - barrel_h // 2 + 1, fluid_w, barrel_h - 2))

    # Plunger cap (flat end)
    cap_w = max(2, int(s * 0.35 * x_scale))
    cap_h = max(3, int(s * 0.75))
    cap_x = (cx - barrel_w - cap_w) if not flip else (cx + barrel_w)
    pygame.draw.rect(surface, (180, 60, 60),
                     (cap_x, cy - cap_h // 2, cap_w, cap_h))

    # Plunger rod
    if x_scale > 0.1:
        rod_w = max(1, int(s * 0.12 * x_scale))
        rod_x = cap_x + (cap_w if not flip else 0) - rod_w // 2
        pygame.draw.rect(surface, (150, 150, 160),
                         (rod_x, cy - rod_w // 2, rod_w, rod_w))

    # Needle tip (tapers to point)
    if x_scale > 0.2:
        needle_w = max(2, int(s * 0.8 * x_scale))
        tip_x    = cx if not flip else (cx - needle_w)
        tip_dir  = 1 if not flip else -1
        tip_pts  = [
            (tip_x,                cy - max(1, int(s * 0.15))),
            (tip_x,                cy + max(1, int(s * 0.15))),
            (tip_x + tip_dir * needle_w, cy),
        ]
        pygame.draw.polygon(surface, (210, 220, 230), tip_pts)

    # Graduation marks on barrel
    if x_scale > 0.4 and barrel_w > 6:
        mark_col = (100, 130, 160)
        num_marks = 3
        for i in range(1, num_marks + 1):
            frac  = i / (num_marks + 1)
            mx    = (cx - int(barrel_w * frac)) if not flip else (cx + int(barrel_w * frac))
            pygame.draw.line(surface, mark_col,
                             (mx, cy - barrel_h // 2),
                             (mx, cy - barrel_h // 2 - max(2, int(s * 0.25))), 1)

# ENEMY SPRITE
def draw_enemy_sprite(screen, cx, cy, size, state, is_duck, is_boss, boss_phase, flash):
    if is_duck:
        # Duck enemy — draw a rubber duck shape directly (no draw_duck dependency)
        s = max(1, size // 2)
        body_w = max(4, int(s * 1.8)); body_h = max(3, int(s * 1.2))
        duck_surf = pygame.Surface((size * 3, size * 2), pygame.SRCALPHA)
        dcx = duck_surf.get_width() // 2
        dcy = duck_surf.get_height() // 2
        pygame.draw.ellipse(duck_surf, (255, 220, 0),
                            (dcx - body_w, dcy - body_h // 2, body_w * 2, body_h))
        head_r  = max(2, int(s * 0.7))
        head_cx = dcx + body_w // 2
        head_cy = dcy - body_h // 2
        pygame.draw.circle(duck_surf, (255, 220, 0), (head_cx, head_cy), head_r)
        bill_w = max(2, int(s * 0.7)); bill_h = max(1, int(s * 0.35))
        pygame.draw.rect(duck_surf, (255, 140, 0),
                         (head_cx + head_r - 1, head_cy - bill_h // 2, bill_w, bill_h))
        pygame.draw.circle(duck_surf, (0, 0, 0),
                           (head_cx + max(1, head_r // 2), head_cy - max(1, head_r // 3)),
                           max(1, int(s * 0.18)))
        rect = duck_surf.get_rect(center=(int(cx), int(cy)))
        screen.blit(duck_surf, rect)
        return

    if is_boss:
        col = (255, 50, 50) if flash else {1:(200,20,20),2:(220,10,80),3:(255,0,120)}.get(boss_phase,(200,20,20))
        # Larger, more imposing boss sprite
        bw = max(30, int(size*0.5)); bh = max(50, int(size*0.9))
        hr = max(14, int(size*0.22)); lh = max(14, int(size*0.25))
    elif state == 'dead':
        col = (50,0,0); bw=max(10,int(size*0.28)); bh=max(18,int(size*0.55))
        hr=max(6,int(size*0.12)); lh=max(5,int(size*0.14))
    elif state == 'attack':
        col = (240,50,50); bw=max(14,int(size*0.32)); bh=max(24,int(size*0.65))
        hr=max(8,int(size*0.15)); lh=max(8,int(size*0.18))
    elif state == 'chase':
        col = (200,80,20); bw=max(14,int(size*0.32)); bh=max(24,int(size*0.65))
        hr=max(8,int(size*0.15)); lh=max(8,int(size*0.18))
    else:
        col = (140,20,20); bw=max(14,int(size*0.32)); bh=max(24,int(size*0.65))
        hr=max(8,int(size*0.15)); lh=max(8,int(size*0.18))

    bx = int(cx-bw/2); by = int(cy+hr)
    pygame.draw.rect(screen, col, (bx, by, bw, bh))
    head_col = tuple(min(255,c+70) for c in col)
    pygame.draw.circle(screen, head_col, (int(cx),int(cy+hr)), hr)
    pygame.draw.circle(screen,(255,255,255),(int(cx),int(cy+hr)),max(2,hr//4))
    pygame.draw.line(screen,(30,0,0),(bx+4,by+bh),(bx+4,by+bh+lh),2)
    pygame.draw.line(screen,(30,0,0),(bx+bw-4,by+bh),(bx+bw-4,by+bh+lh),2)

    if is_boss:
        # Boss health bar above sprite
        bar_w = max(40, int(size*0.8))
        bar_x = int(cx - bar_w//2)
        bar_y = int(cy - size//2 - 14)
        pygame.draw.rect(screen,(60,0,0),(bar_x,bar_y,bar_w,8))
        # We don't have the boss object here but colour conveys phase
        phase_fills = {1:(200,20,20),2:(220,10,80),3:(255,0,120)}
        fill_w = bar_w if boss_phase==1 else (bar_w*2//3 if boss_phase==2 else bar_w//3)
        pygame.draw.rect(screen, phase_fills.get(boss_phase,(200,20,20)),
                            (bar_x,bar_y,fill_w,8))

# ENEMY AI + RENDERING
def update_and_draw_enemies(screen, player, z_buffer, dt, level):
    theme  = LEVEL_THEMES.get(level, LEVEL_THEMES[1])
    aggro  = theme["aggro"]
    eff_stop  = ENEMY_STOP_RANGE
    eff_chase = ENEMY_CHASE_RANGE
    eff_spd   = ENEMY_MOVE_SPEED * (1.0 + (level-1)*0.04)
    eff_rate  = ENEMY_ATTACK_RATE * (1.0 - aggro*0.3)

    for enemy in list(enemies):
        if enemy.dead:
            enemy.death_timer -= dt
            if enemy.death_timer <= 0:
                enemies.remove(enemy)
                continue
        else:
            if enemy.spawn_grace > 0:
                enemy.spawn_grace -= dt
                enemy.state = 'idle'
                continue

            dx   = enemy.x - player.x
            dy   = enemy.y - player.y
            dist = math.hypot(dx, dy)
            has_los = False
            if dist <= eff_chase:
                steps = max(1, int(dist/0.15))
                cd = dx/dist if dist>0 else 0
                sd = dy/dist if dist>0 else 0
                blocked = False
                for k in range(1, steps):
                    tx = player.x + cd*(k*0.15)
                    ty = player.y + sd*(k*0.15)
                    if tile_is_wall(int(tx),int(ty)): blocked=True; break
                has_los = not blocked

            boss_stop = eff_stop * (2.0 if enemy.is_boss else 1.0)

# Duck transformation — non-duck, non-boss enemies that stay in
            # player LOS for too long gradually transform into ducks
            if enemy.was_human and not enemy.is_duck and not enemy.is_boss:
                if dist < 6.0 and has_los:
                    enemy.duck_timer += dt
                else:
                    enemy.duck_timer = max(0.0, enemy.duck_timer - dt * 0.5)
                if enemy.duck_timer >= 4.0:
                    enemy.is_duck    = True
                    enemy.was_human  = False
                    enemy.duck_timer = 0.0
                    enemy.state      = 'idle'
                    enemy.waypoint   = None

            if dist > eff_chase:
                enemy.state='idle'; enemy.waypoint=None

            elif has_los and dist <= boss_stop:
                enemy.state='attack'; enemy.waypoint=None
                enemy.dmg_timer -= dt
                if enemy.dmg_timer <= 0:
                    if enemy.is_boss:
                        # Boss fires 3-way spread
                        base = math.atan2(player.y-enemy.y, player.x-enemy.x)
                        for spread in (-0.3, 0.0, 0.3):
                            enemy_bullets.append(EnemyBullet(enemy.x,enemy.y,base+spread,is_boss=True))
                    else:
                        ang = math.atan2(player.y-enemy.y, player.x-enemy.x)
                        spread = random.uniform(-0.05,0.05)
                        enemy_bullets.append(EnemyBullet(enemy.x,enemy.y,ang+spread))
                    enemy.dmg_timer = eff_rate

            else:
                enemy.state = 'chase'
                at_wp = (enemy.waypoint is None or
                            math.hypot(enemy.x-enemy.waypoint[0],
                                    enemy.y-enemy.waypoint[1]) < 0.5)
                enemy.path_timer -= dt
                if enemy.path_timer <= 0 or at_wp:
                    enemy.path_timer = ENEMY_PATH_INTERVAL
                    nt = bfs_next_step(int(enemy.x),int(enemy.y),
                                        int(player.x),int(player.y))
                    enemy.waypoint = (nt[0]+0.5,nt[1]+0.5) if nt else (player.x,player.y)

                if enemy.waypoint:
                    wx,wy  = enemy.waypoint
                    wdx,wdy = wx-enemy.x, wy-enemy.y
                    wdist  = math.hypot(wdx,wdy)
                    if wdist > 0.01:
                        spd = eff_spd*(1.5 if enemy.is_boss else 1.0)
                        nx,ny = slide_move(enemy.x,enemy.y,
                                            (wdx/wdist)*spd,(wdy/wdist)*spd)
                        enemy.x=nx; enemy.y=ny

                if has_los and dist <= eff_chase:
                    enemy.dmg_timer -= dt
                    if enemy.dmg_timer <= 0:
                        ang = math.atan2(player.y-enemy.y, player.x-enemy.x)
                        spread = random.uniform(-0.05,0.05)
                        enemy_bullets.append(EnemyBullet(enemy.x,enemy.y,ang+spread,
                                                            is_boss=enemy.is_boss))
                        enemy.dmg_timer = eff_rate

            if enemy.flash_timer > 0:
                enemy.flash_timer -= dt

        # Projection
        dx   = enemy.x - player.x
        dy   = enemy.y - player.y
        effective_fov  = FOV * settings["fov_mult"]
        effective_half = effective_fov / 2
        angle_to   = math.atan2(dy, dx)
        diff_angle = (angle_to-player.angle+math.pi)%(2*math.pi)-math.pi
        if abs(diff_angle) > effective_half+0.3: continue
        perp_dist = math.hypot(dx,dy)*math.cos(diff_angle)
        if perp_dist < 0.1: continue
        screen_x = int(HALF_W + math.tan(diff_angle)*(WIDTH/(2*math.tan(effective_half))))
        z_col = max(0,min(WIDTH-1,screen_x))
        if z_buffer[z_col] < perp_dist: continue
        sprite_h = max(1, int(HEIGHT/perp_dist))
        sprite_w = max(1, int(sprite_h*0.5))
        if screen_x+sprite_w//2 < 0 or screen_x-sprite_w//2 >= WIDTH: continue
        vertical_shift = int(player.pitch*HALF_H)
        sprite_y = HALF_H - sprite_h//2 + vertical_shift
        state = 'dead' if enemy.dead else enemy.state
        draw_enemy_sprite(screen, screen_x, sprite_y, sprite_h, state,
                            enemy.is_duck, enemy.is_boss, enemy.boss_phase,
                            enemy.flash_timer > 0)
        if enemy.dead and abs(enemy.death_timer-ENEMY_DEATH_DISPLAY) < dt+0.001:
            player.score += KILL_SCORE * (5 if enemy.is_boss else 1)

# WORLD OBJECT RENDERING  (notes, cure)
def draw_world_objects(screen, player, z_buffer):
    effective_fov  = FOV * settings["fov_mult"]
    effective_half = effective_fov / 2
    vertical_shift = int(player.pitch*HALF_H)

    def project_sprite(ox, oy, color, size_base):
        dx   = ox - player.x
        dy   = oy - player.y
        dist = math.hypot(dx, dy)
        if dist < 0.1: return
        ang  = math.atan2(dy, dx)
        diff = (ang-player.angle+math.pi)%(2*math.pi)-math.pi
        if abs(diff) > effective_half+0.2: return
        pd = dist*math.cos(diff)
        if pd < 0.1: return
        sx = int(HALF_W + math.tan(diff)*(WIDTH/(2*math.tan(effective_half))))
        if not (0 <= sx < WIDTH): return
        if z_buffer[sx] < pd: return
        sz = max(6, int(HEIGHT/pd*size_base))
        sy = HALF_H + vertical_shift
        pygame.draw.circle(screen, color, (sx,sy), sz)
        # Inner icon
        pygame.draw.circle(screen, (255,255,255), (sx,sy), max(2, sz//3))

    for note in note_objects:
        if not note.picked_up:
            project_sprite(note.x, note.y, (200,180,100), 0.2)

    for cure in cure_objects:
        if not cure.picked_up:
            project_sprite(cure.x, cure.y, (0,255,120), 0.25)

    # Render secret door
    if secret_door and not secret_door.unlocked:
        project_sprite(secret_door.x, secret_door.y, (200, 100, 200), 0.24)
    elif secret_door and secret_door.unlocked:
        project_sprite(secret_door.x, secret_door.y, (100, 255, 200), 0.24)

    if exit_object and not exit_object.active:
        # Draw dim/locked indicator
        project_sprite(exit_object.x, exit_object.y, (150, 80, 150), 0.22)
    elif exit_object and exit_object.active:
        # Draw bright active exit
        project_sprite(exit_object.x, exit_object.y, (255, 200, 0), 0.28)
        # Pulsing inner ring
        dx2 = exit_object.x - player.x
        dy2 = exit_object.y - player.y
        dist2 = math.hypot(dx2, dy2)
        if dist2 < 0.1: pass
        else:
            ang2  = math.atan2(dy2, dx2)
            diff2 = (ang2-player.angle+math.pi)%(2*math.pi)-math.pi
            if abs(diff2) < effective_half+0.2:
                pd2 = dist2*math.cos(diff2)
                if pd2 > 0.1:
                    sx2 = int(HALF_W + math.tan(diff2)*(WIDTH/(2*math.tan(effective_half))))
                    if 0 <= sx2 < WIDTH and z_buffer[sx2] >= pd2:
                        sz2 = max(6, int(HEIGHT/pd2*0.28))
                        pygame.draw.circle(screen, (255,255,255), (sx2, HALF_H+vertical_shift), max(2, sz2//4))

# BULLET RENDERING (spinning duck)
def draw_bullets(screen, player, z_buffer, duck_frame):
    effective_fov  = FOV * settings["fov_mult"]
    effective_half = effective_fov / 2
    vertical_shift = int(player.pitch*HALF_H)
    for b in bullets:
        dx   = b.x - player.x
        dy   = b.y - player.y
        dist = math.hypot(dx, dy)
        if dist < 0.1: continue
        ang  = math.atan2(dy, dx)
        diff = (ang-player.angle+math.pi)%(2*math.pi)-math.pi
        if abs(diff) > effective_half+0.1: continue
        pd   = dist*math.cos(diff)
        if pd < 0.1: continue
        sx   = int(HALF_W + math.tan(diff)*(WIDTH/(2*math.tan(effective_half))))
        if not (0 <= sx < WIDTH): continue
        if z_buffer[sx] < pd: continue
        size = max(4, int(HEIGHT / pd * 0.3))
        sy   = HALF_H + vertical_shift
        ds   = size * 2
        surf = pygame.Surface((ds * 4, ds * 2), pygame.SRCALPHA)
        y_spin_angle = (duck_frame / 20) * 2 * math.pi
        draw_syringe(surf, surf.get_width() // 2, surf.get_height() // 2,
                        size, y_spin_angle)
        screen.blit(surf, surf.get_rect(center=(sx, sy)))

def update_and_draw_enemy_bullets(screen, player, z_buffer):
    effective_fov  = FOV * settings["fov_mult"]
    effective_half = effective_fov / 2
    vertical_shift = int(player.pitch*HALF_H)
    for b in list(enemy_bullets): b.update(player)
    enemy_bullets[:] = [b for b in enemy_bullets if b.alive]
    for b in enemy_bullets:
        dx   = b.x-player.x; dy=b.y-player.y
        dist = math.hypot(dx,dy)
        if dist < 0.1: continue
        ang  = math.atan2(dy,dx)
        diff = (ang-player.angle+math.pi)%(2*math.pi)-math.pi
        if abs(diff) > effective_half+0.1: continue
        pd   = dist*math.cos(diff)
        if pd < 0.1: continue
        sx   = int(HALF_W+math.tan(diff)*(WIDTH/(2*math.tan(effective_half))))
        if not (0 <= sx < WIDTH): continue
        if z_buffer[sx] < pd: continue
        size = max(3, int(HEIGHT/pd*0.3))
        sy   = HALF_H+vertical_shift
        pygame.draw.circle(screen,(255,80,0),(sx,sy),size)

# MINIMAP
def draw_minimap(screen, player):
    r=MINIMAP_RADIUS; sc=MINIMAP_SCALE; mm=(r*2+1)*sc
    surf=pygame.Surface((mm,mm),pygame.SRCALPHA); surf.fill((0,0,0,160))
    cx,cy=int(player.x),int(player.y)
    for dy in range(-r,r+1):
        for dx in range(-r,r+1):
            tx,ty=cx+dx,cy+dy; px,py=(dx+r)*sc,(dy+r)*sc
            if 0<=ty<MAP_H and 0<=tx<MAP_W:
                color=(160,30,30,220) if WORLD_MAP[ty][tx]!=0 else (40,40,40,180)
            else: color=(10,10,10,220)
            surf.fill(color,(px,py,sc,sc))
    for note in note_objects:
        if not note.picked_up:
            nx=int((note.x-cx+r)*sc); ny=int((note.y-cy+r)*sc)
            if 0<=nx<mm and 0<=ny<mm:
                pygame.draw.rect(surf,(220,200,100,220),(nx-2,ny-2,5,5))
    for cure in cure_objects:
        if not cure.picked_up:
            nx=int((cure.x-cx+r)*sc); ny=int((cure.y-cy+r)*sc)
            if 0<=nx<mm and 0<=ny<mm:
                pygame.draw.rect(surf,(0,255,120,220),(nx-2,ny-2,6,6))
    for enemy in enemies:
        if not enemy.dead:
            ex=int((enemy.x-cx+r)*sc); ey=int((enemy.y-cy+r)*sc)
            if 0<=ex<mm and 0<=ey<mm:
                col=(255,0,200,220) if enemy.is_boss else (0,255,0,220)
                pygame.draw.rect(surf,col,(ex-2,ey-2,5,5))
    if exit_object:
        ex=int((exit_object.x-cx+r)*sc); ey=int((exit_object.y-cy+r)*sc)
        if 0<=ex<mm and 0<=ey<mm:
            col=(255,255,0,220) if exit_object.active else (150,150,150,220)
            pygame.draw.rect(surf,col,(ex-3,ey-3,7,7))
    ppx,ppy=r*sc,r*sc
    pygame.draw.circle(surf,(255,255,255,255),(ppx,ppy),3)
    lx=int(ppx+math.cos(player.angle)*5*sc); ly=int(ppy+math.sin(player.angle)*5*sc)
    pygame.draw.line(surf,(255,255,255,200),(ppx,ppy),(lx,ly),1)
    screen.blit(surf,(WIDTH-mm-MINIMAP_MARGIN,MINIMAP_MARGIN))

# HUD
def draw_hud(screen, player, font_sm, font_tiny, level):
    # Crosshair
    pygame.draw.line(screen,(255,255,255),(HALF_W-10,HALF_H),(HALF_W+10,HALF_H),2)
    pygame.draw.line(screen,(255,255,255),(HALF_W,HALF_H-10),(HALF_W,HALF_H+10),2)
    hp_col = (255,60,60) if player.health < 30 else (255,255,255)
    theme = LEVEL_THEMES.get(level, LEVEL_THEMES[1])

    alive_enemies = sum(1 for e in enemies if e.alive)
    screen.blit(font_sm.render(f"HEALTH: {player.health}", True,hp_col),(20,20))
    screen.blit(font_sm.render(f"LEVEL {level}: {theme['name']}", True,(0,200,255)),(20,56))
    screen.blit(font_tiny.render(f"Enemies remaining: {alive_enemies}", True,(200,200,200)),(20,94))
    note_col = (0,255,120) if player.notes_this_level_found >= player.notes_this_level_total else (200,180,100)
    screen.blit(font_tiny.render(
        f"Notes: {player.notes_this_level_found}/{player.notes_this_level_total}",
        True, note_col),(20,152))
    
    # Cure piece inventory
    cure_labels = {"cure_01":"Compound A","cure_02":"Compound B","cure_03":"Compound C"}
    cy_off = 160
    for pid, label in cure_labels.items():
        col = (0,255,120) if pid in player.cure_pieces else (60,60,60)
        screen.blit(font_tiny.render(f"[{label}]", True, col),(20,cy_off))
        cy_off += 22

    # Prompt if near something interactable
    inter = player.check_interactions()
    if inter:
        kind, obj = inter
        if kind == "note":
            msg = "Press F to read note"
        elif kind == "cure":
            msg = "Press F to collect compound"
        else:
            msg = "Press F to descend" if level < 20 else "Press F to confront Dr. Stephany"
        surf = font_sm.render(msg, True,(255,220,80))
        screen.blit(surf, surf.get_rect(center=(HALF_W, HEIGHT-60)))

    draw_minimap(screen, player)

# NOTE DISPLAY (full screen typewriter)
def show_note(screen, font_note, font_tiny, text, clock):
    displayed = ""
    idx       = 0
    char_timer = 0.0
    char_rate  = 0.025
    done       = False
    while True:
        dt = clock.tick(60)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_f):
                    if done: return
                    else: displayed = text; idx = len(text); done = True

        if not done:
            char_timer += dt
            while char_timer >= char_rate and idx < len(text):
                displayed += text[idx]; idx += 1; char_timer -= char_rate
            if idx >= len(text): done = True

        overlay = pygame.Surface((WIDTH,HEIGHT))
        overlay.fill((8,5,5))
        screen.blit(overlay,(0,0))
        pygame.draw.rect(screen,(40,25,20),(40,40,WIDTH-80,HEIGHT-80))
        pygame.draw.rect(screen,(120,80,40),(40,40,WIDTH-80,HEIGHT-80),2)

        lines = displayed.split('\n')
        y = 70
        for line in lines:
            if y > HEIGHT-80: break
            surf = font_note.render(line, True,(220,200,170))
            screen.blit(surf,(60,y)); y+=22

        if done:
            prompt = font_tiny.render("Press ENTER or F to close", True,(120,100,80))
            screen.blit(prompt, prompt.get_rect(center=(HALF_W,HEIGHT-50)))
        pygame.display.flip()

# OVERLAY MESSAGE
def show_message(screen, font, lines, delay_ms=2000):
    overlay = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
    overlay.fill((0,0,0,160))
    screen.blit(overlay,(0,0))
    for i,(text,colour) in enumerate(lines):
        surf = font.render(text,True,colour)
        rect = surf.get_rect(center=(HALF_W,HALF_H-40+i*50))
        screen.blit(surf,rect)
    pygame.display.flip()
    pygame.time.delay(delay_ms)

# ENDING SCREENS
def show_ending(screen, font_big, font_sm, font_tiny, clock, ending):
    if ending == "good":
        title   = "GOOD ENDING"
        t_col   = (0,255,120)
        lines   = [
            "You administer the compound.",
            "Dr. Stephany screams.",
            "Then she is quiet.",
            "Then she opens her eyes.",
            " ",
            "You both climb out of JLK at 4:17am.",
            "The building is locked behind you.",
            " ",
            "One year later, an email:",
            "'I think we have to go public.",
            " I think they need to know.",
            " - Stephany'",
            " ",
            "You never replied.",
            "Neither of you went back.",
            "The seal on the ONU crest",
            "still means what it always meant.",
        ]
    elif ending == "normal":
        title   = "NORMAL ENDING"
        t_col   = (200,200,100)
        lines   = [
            "You defeat Dr. Stephany.",
            "She does not get up.",
            "You find the elevator.",
            "Somehow, it works.",
            " ",
            "You walk out of JLK at 4:17am.",
            "No one sees you leave.",
            " ",
            "A headline, six weeks later:",
            "'ONU Professor Missing Since April —",
            " University Declines to Comment'",
            " ",
            "You say nothing.",
            "You tell yourself that was the right call.",
            "Some nights you almost believe it.",
        ]
    else:
        title   = "BAD ENDING"
        t_col   = (255,40,40)
        lines   = [
            "The organism takes you.",
            "Not violently. Gently.",
            "Like it was always waiting.",
            " ",
            "You are still in JLK.",
            "You will always be in JLK.",
            " ",
            "Somewhere, a student finds a note",
            "wedged behind a filing cabinet.",
            "It is in your handwriting.",
            "You don't remember writing it.",
            " ",
            "'If you find this — GET OUT.'",
            " ",
            "They don't.",
        ]

    running = True
    scroll  = 0
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running=False
                if event.key == pygame.K_DOWN: scroll = min(scroll+1, max(0,len(lines)-12))
                if event.key == pygame.K_UP:   scroll = max(0,scroll-1)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4: scroll=max(0,scroll-1)
                if event.button == 5: scroll=min(scroll+1,max(0,len(lines)-12))

        screen.fill((5,3,3))
        t_surf = font_big.render(title, True, t_col)
        screen.blit(t_surf, t_surf.get_rect(center=(HALF_W,60)))
        pygame.draw.line(screen,t_col,(60,90),(WIDTH-60,90),1)
        y = 110
        for line in lines[scroll:scroll+16]:
            surf = font_sm.render(line, True,(210,190,180))
            screen.blit(surf,(80,y)); y+=28
        hint = font_tiny.render("ESC — Main Menu   ↑↓ Scroll", True,(80,70,60))
        screen.blit(hint, hint.get_rect(center=(HALF_W,HEIGHT-30)))
        pygame.display.flip()

# FINAL CHOICE SCREEN
def show_final_choice(screen, font_big, font_sm, font_tiny, clock, has_all_cure):
    selected = 0
    if has_all_cure:
        options = ["Use the compound on Dr. Stephany", "Leave her. Just escape."]
    else:
        options = ["End this. (You have no compound.)", "...Try anyway."]
    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):    selected = max(0,selected-1)
                if event.key in (pygame.K_DOWN, pygame.K_s):  selected = min(len(options)-1,selected+1)
                if event.key == pygame.K_RETURN:
                    if has_all_cure and selected==0: return "good"
                    elif selected==0: return "bad"
                    else: return "normal"

        screen.fill((5,3,3))
        t = font_big.render("THE CHOICE", True,(200,50,50))
        screen.blit(t, t.get_rect(center=(HALF_W,80)))
        desc = font_sm.render("Dr. Stephany is defeated. She is still breathing.", True,(180,160,150))
        screen.blit(desc, desc.get_rect(center=(HALF_W,140)))
        for i, opt in enumerate(options):
            col = (255,220,80) if i==selected else (120,100,90)
            prefix = "> " if i==selected else "  "
            surf = font_sm.render(prefix+opt, True,col)
            screen.blit(surf, surf.get_rect(center=(HALF_W,220+i*60)))
        hint = font_tiny.render("↑↓ to choose   ENTER to confirm", True,(80,70,60))
        screen.blit(hint, hint.get_rect(center=(HALF_W,HEIGHT-40)))
        pygame.display.flip()

def notebook_menu(screen, font_big, font_sm, font_tiny, font_note, clock, player):
    #Browse all collected notes, organised by level.
    # Build index: level -> list of (note_key, short_title)
    level_notes = {}
    for lvl, theme in LEVEL_THEMES.items():
        level_notes[lvl] = theme["notes"]

    # Flat list of collected notes in level order
    collected = []
    for lvl in sorted(level_notes.keys()):
        for key in level_notes[lvl]:
            if key in player.notes_read:
                # First non-empty line = title
                raw = NOTES.get(key, "")
                title_line = next((l.strip() for l in raw.split('\n') if l.strip()), key)
                title_line = title_line[:55] + ("..." if len(title_line) > 55 else "")
                collected.append((lvl, key, title_line))

    if not collected:
        # Empty notebook screen
        running = True
        while running:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN: running = False
            screen.fill((8, 5, 5))
            t = font_big.render("NOTEBOOK", True, (200, 180, 100))
            screen.blit(t, t.get_rect(center=(HALF_W, 80)))
            msg = font_sm.render("No notes collected yet.", True, (120, 100, 80))
            screen.blit(msg, msg.get_rect(center=(HALF_W, HALF_H)))
            hint = font_tiny.render("Any key — Back", True, (70, 60, 50))
            screen.blit(hint, hint.get_rect(center=(HALF_W, HEIGHT - 30)))
            pygame.display.flip()
        return

    selected  = 0
    scroll    = 0
    viewing   = False     # True = reading full note text
    view_scroll = 0
    VISIBLE   = 14        # entries visible at once in list

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if viewing:
                    # Scrolling inside a note
                    if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_f):
                        viewing = False
                    if event.key == pygame.K_DOWN:  view_scroll += 1
                    if event.key == pygame.K_UP:    view_scroll = max(0, view_scroll - 1)
                else:
                    if event.key == pygame.K_ESCAPE: return
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = min(len(collected) - 1, selected + 1)
                        if selected >= scroll + VISIBLE: scroll += 1
                    if event.key in (pygame.K_UP, pygame.K_w):
                        selected = max(0, selected - 1)
                        if selected < scroll: scroll -= 1
                    if event.key in (pygame.K_RETURN, pygame.K_f):
                        viewing     = True
                        view_scroll = 0
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    if viewing: view_scroll = max(0, view_scroll - 1)
                    else:
                        selected = max(0, selected - 1)
                        if selected < scroll: scroll -= 1
                if event.button == 5:
                    if viewing:  view_scroll += 1
                    else:
                        selected = min(len(collected) - 1, selected + 1)
                        if selected >= scroll + VISIBLE: scroll += 1

        screen.fill((8, 5, 5))
        pygame.draw.rect(screen, (30, 20, 15), (30, 30, WIDTH - 60, HEIGHT - 60))
        pygame.draw.rect(screen, (100, 70, 40), (30, 30, WIDTH - 60, HEIGHT - 60), 2)

        if viewing:
            lvl, key, _ = collected[selected]
            full_text    = NOTES.get(key, "[Note missing]")
            lines        = full_text.split('\n')
            t = font_sm.render("NOTEBOOK  —  Reading", True, (200, 180, 100))
            screen.blit(t, (50, 42))
            pygame.draw.line(screen, (100, 70, 40), (50, 72), (WIDTH - 50, 72), 1)
            y = 82
            for line in lines[view_scroll:view_scroll + 22]:
                surf = font_note.render(line, True, (220, 200, 170))
                screen.blit(surf, (55, y))
                y += 21
            hint = font_tiny.render("↑↓ Scroll   ESC/F — Back to list", True, (100, 80, 60))
            screen.blit(hint, hint.get_rect(center=(HALF_W, HEIGHT - 42)))

        else:
            header = font_sm.render(
                f"NOTEBOOK  —  {len(collected)} note(s) collected", True, (200, 180, 100))
            screen.blit(header, (50, 42))
            pygame.draw.line(screen, (100, 70, 40), (50, 72), (WIDTH - 50, 72), 1)

            current_lvl = None
            y = 80
            entry_idx = 0
            for i, (lvl, key, title) in enumerate(collected):
                if i < scroll: entry_idx += 1; continue
                if i >= scroll + VISIBLE: break

                # Level group header
                if lvl != current_lvl:
                    current_lvl = lvl
                    lname = LEVEL_THEMES.get(lvl, {}).get("name", f"Level {lvl}")
                    lhdr  = font_tiny.render(f"— Level {lvl}: {lname} —", True, (100, 80, 60))
                    screen.blit(lhdr, (55, y))
                    y += 20

                col = (255, 220, 80) if i == selected else (180, 160, 140)
                prefix = "> " if i == selected else "  "
                surf = font_sm.render(prefix + title, True, col)
                screen.blit(surf, (65, y))
                y += 30
                entry_idx += 1

            # Scroll indicators
            if scroll > 0:
                screen.blit(font_tiny.render("▲ more above", True, (100,80,60)), (HALF_W - 40, 78))
            if scroll + VISIBLE < len(collected):
                screen.blit(font_tiny.render("▼ more below", True, (100,80,60)),
                            (HALF_W - 40, HEIGHT - 60))

            hint = font_tiny.render(
                "↑↓ Navigate   ENTER/F Read   ESC Back", True, (80, 65, 50))
            screen.blit(hint, hint.get_rect(center=(HALF_W, HEIGHT - 42)))

        pygame.display.flip()

# SETTINGS MENU
def settings_menu(screen, font_big, font_sm, font_tiny, clock):
    sliders = [
        ("Mouse Sensitivity", "mouse_sens",  0.0005, 0.006,  0.0005),
        ("Master Volume",     "master_vol",  0.0,    1.0,    0.05),
        ("Music Volume",      "music_vol",   0.0,    1.0,    0.05),
        ("SFX Volume",        "sfx_vol",     0.0,    1.0,    0.05),
        ("FOV Multiplier",    "fov_mult",    0.6,    1.4,    0.05),
    ]
    selected = 0
    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return
                if event.key in (pygame.K_UP,pygame.K_w):
                    selected = max(0,selected-1)
                if event.key in (pygame.K_DOWN,pygame.K_s):
                    selected = min(len(sliders)-1,selected+1)
                if event.key in (pygame.K_LEFT,pygame.K_a):
                    name,key,mn,mx,step = sliders[selected]
                    settings[key] = max(mn, round(settings[key]-step,4))
                    pygame.mixer.music.set_volume(settings["music_vol"]*settings["master_vol"])
                if event.key in (pygame.K_RIGHT,pygame.K_d):
                    name,key,mn,mx,step = sliders[selected]
                    settings[key] = min(mx, round(settings[key]+step,4))
                    pygame.mixer.music.set_volume(settings["music_vol"]*settings["master_vol"])

        screen.fill((8,5,5))
        t = font_big.render("SETTINGS", True,(0,180,255))
        screen.blit(t, t.get_rect(center=(HALF_W,50)))
        pygame.draw.line(screen,(0,100,140),(60,85),(WIDTH-60,85),1)

        for i,(name,key,mn,mx,step) in enumerate(sliders):
            y    = 120 + i*80
            col  = (255,220,80) if i==selected else (160,150,140)
            screen.blit(font_sm.render(name, True, col),(60,y))
            val  = settings[key]
            frac = (val-mn)/(mx-mn)
            bar_x, bar_y, bar_w, bar_h = 60, y+30, WIDTH-120, 16
            pygame.draw.rect(screen,(40,40,40),(bar_x,bar_y,bar_w,bar_h))
            pygame.draw.rect(screen,(0,180,255),(bar_x,bar_y,int(bar_w*frac),bar_h))
            pygame.draw.rect(screen,(120,120,120),(bar_x,bar_y,bar_w,bar_h),1)
            vstr = f"{val:.4f}" if key=="mouse_sens" else f"{val:.2f}"
            screen.blit(font_tiny.render(vstr, True,(200,200,200)),(bar_x+bar_w+8,bar_y))

        hint = font_tiny.render("↑↓ Select   ←→ Adjust   ESC Back", True,(80,70,60))
        screen.blit(hint, hint.get_rect(center=(HALF_W,HEIGHT-30)))
        pygame.display.flip()

# PAUSE MENU
def pause_menu(screen, font_big, font_sm, font_tiny, clock):
    options = ["Resume", "Settings", "Main Menu", "Quit"]
    selected = 0
    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return "resume"
                if event.key in (pygame.K_UP,pygame.K_w):
                    selected=max(0,selected-1)
                if event.key in (pygame.K_DOWN,pygame.K_s):
                    selected=min(len(options)-1,selected+1)
                if event.key == pygame.K_RETURN:
                    return options[selected].lower().replace(" ","_")
            if event.type == pygame.MOUSEMOTION:
                mx,my = event.pos
                for i in range(len(options)):
                    oy = 200+i*60
                    if HALF_W-120 < mx < HALF_W+120 and oy < my < oy+40:
                        selected=i
            if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                mx,my = event.pos
                for i,opt in enumerate(options):
                    oy = 200+i*60
                    if HALF_W-120 < mx < HALF_W+120 and oy < my < oy+40:
                        return opt.lower().replace(" ","_")

        overlay = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        screen.blit(overlay,(0,0))
        t = font_big.render("PAUSED", True,(0,180,255))
        screen.blit(t,t.get_rect(center=(HALF_W,120)))
        for i,opt in enumerate(options):
            col = (255,220,80) if i==selected else (180,170,160)
            surf = font_sm.render(opt, True,col)
            rect = surf.get_rect(center=(HALF_W,220+i*60))
            if i==selected:
                pygame.draw.rect(screen,(40,35,30),rect.inflate(20,10))
                pygame.draw.rect(screen,(80,70,50),rect.inflate(20,10),1)
            screen.blit(surf,rect)
        pygame.display.flip()

# MAIN MENU
def main_menu(screen, font_big, font_med, font_sm, font_tiny, clock):
    options = ["New Game", "Notebook", "Settings",  "Quit"]
    selected = 0
    tick = 0
    while True:
        dt = clock.tick(60)/1000.0
        tick += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP,pygame.K_w):
                    selected=max(0,selected-1)
                if event.key in (pygame.K_DOWN,pygame.K_s):
                    selected=min(len(options)-1,selected+1)
                if event.key == pygame.K_RETURN:
                    return options[selected].lower().replace(" ","_")
            if event.type == pygame.MOUSEMOTION:
                mx,my = event.pos
                for i in range(len(options)):
                    oy = 300+i*70
                    if HALF_W-120 < mx < HALF_W+120 and oy < my < oy+50:
                        selected=i
            if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                mx,my = event.pos
                for i,opt in enumerate(options):
                    oy = 300+i*70
                    if HALF_W-120 < mx < HALF_W+120 and oy < my < oy+50:
                        return opt.lower().replace(" ","_")

        screen.fill((5,3,3))
        # Animated scanline effect
        for row in range(0,HEIGHT,4):
            alpha = int(20+10*math.sin(row*0.05+tick*2))
            pygame.draw.line(screen,(0,0,0),(0,row),(WIDTH,row))

        # Title
        glow_col = (int(150+50*math.sin(tick*1.5)), 20, 20)
        t1 = font_big.render("JLK DESCENT", True, glow_col)
        t2 = font_med.render("Ohio Northern University", True,(100,80,70))
        t3 = font_tiny.render("'What descends is changed.'", True,(70,55,50))
        screen.blit(t1, t1.get_rect(center=(HALF_W,120)))
        screen.blit(t2, t2.get_rect(center=(HALF_W,185)))
        screen.blit(t3, t3.get_rect(center=(HALF_W,220)))
        pygame.draw.line(screen,(80,40,40),(80,255),(WIDTH-80,255),1)

        for i,opt in enumerate(options):
            col = (255,220,80) if i==selected else (160,150,140)
            surf = font_sm.render(opt, True, col)
            rect = surf.get_rect(center=(HALF_W,310+i*70))
            if i==selected:
                pygame.draw.rect(screen,(35,25,20),rect.inflate(30,14))
                pygame.draw.rect(screen,(100,70,40),rect.inflate(30,14),1)
            screen.blit(surf,rect)

        footer = font_tiny.render("ONU — Ada, Ohio — Est. 1871 — Sub-Level Access Restricted",
                                    True,(50,40,35))
        screen.blit(footer, footer.get_rect(center=(HALF_W,HEIGHT-25)))
        pygame.display.flip()

def _play_music_for_level(level):
    LEVEL_MUSIC = {
        1:  'assets/sounds/ambient.mp3',
        2:  'assets/sounds/ambient.mp3',
        3:  'assets/sounds/ambient2.mp3',
        4:  'assets/sounds/ambient2.mp3',
        5:  'assets/sounds/ambient3.mp3',
        6:  'assets/sounds/ambient3.mp3',
        7:  'assets/sounds/ambient2.mp3',
        8:  'assets/sounds/ambient4.mp3',
        9:  'assets/sounds/ambient4.mp3',
        10: 'assets/sounds/ambient3.mp3',
        11: 'assets/sounds/ambient5.mp3',
        12: 'assets/sounds/ambient4.mp3',
        13: 'assets/sounds/ambient5.mp3',
        14: 'assets/sounds/ambient5.mp3',
        15: 'assets/sounds/ambient4.mp3',
        16: 'assets/sounds/ambient5.mp3',
        17: 'assets/sounds/ambient3.mp3',
        18: 'assets/sounds/ambient5.mp3',
        19: 'assets/sounds/ambient5.mp3',
        20: 'assets/sounds/boss.mp3',
    }
    track = LEVEL_MUSIC.get(level, 'assets/sounds/ambient.mp3')
    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        pygame.mixer.music.load(track)
        pygame.mixer.music.set_volume(
            settings["music_vol"] * settings["master_vol"])
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"Music load failed for '{track}': {e}")

# LEVEL SETUP
def setup_level(player):
    global exit_object
    enemies.clear(); bullets.clear(); enemy_bullets.clear()
    exit_object = None
    generate_map()
    px, py = find_spawn()
    player.x     = px; player.y = py
    player.angle = best_facing_angle(px, py)
    player.pitch = 0.0
    if not position_free(player.x, player.y):
        player.x, player.y = find_open_tile()

    level = player.level
    theme = LEVEL_THEMES.get(level, LEVEL_THEMES[19])

    spawn_enemies(theme["enemies"], theme["duck_enemies"], player.x, player.y, level)
    if level == 20:
        spawn_boss(player.x, player.y)

    place_world_objects(level, player.x, player.y)
    # Target score is based on total enemy count for this level
    total_enemies = theme["enemies"] + theme["duck_enemies"]
    player.target_score = total_enemies * KILL_SCORE

    # Per-level note tracking
    player.notes_this_level_total = len(theme["notes"])
    player.notes_this_level_found = 0

    # Music — restart only if level changed
    _play_music_for_level(level)

def show_intro(screen, font_sm, font_tiny, clock):
    pages = [
        [
            "Ada, Ohio.",
            "2:48am.",
            " ",
            "You've been a graduate research assistant",
            "at Ohio Northern University for two years.",
            "You know the JLK building the way you know",
            "any place you've spent too many late nights —",
            "badly lit, always cold, always humming.",
            " ",
            "Tonight the hum is different.",
        ],
        [
            "You came back for your laptop.",
            "You left it in the first-level lab.",
            "The kind of thing you do without thinking.",
            " ",
            "The elevator is where it always is.",
            "You press 1.",
            "The elevator goes lower than the first floor.",
            "It keeps going.",
            " ",
            "You don't remember pressing anything else.",
        ],
        [
            "It stops.",
            " ",
            "The doors open onto a corridor",
            "that was not here last Tuesday.",
            "Concrete. Fluorescent lights.",
            "A smell like old water and something else —",
            "something mineral, something alive.",
            " ",
            "At the end of the corridor:",
            "a door.",
            "Abandoned. Rusted. Open.",
        ],
        [
            "There is a maintenance log nailed to the frame.",
            "It is dated 1987.",
            " ",
            "The elevator doors close behind you.",
            " ",
            "You hear it descend.",
            " ",
            " ",
            "You are going to have to find another way out.",
        ],
    ]

    for page in pages:
        displayed_lines = [""] * len(page)
        char_indices    = [0]   * len(page)
        line_idx        = 0
        char_timer      = 0.0
        char_rate       = 0.03
        done            = False

        while True:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE,):
                        return   # skip entire intro
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_f):
                        if done:
                            break   # advance to next page
                        else:
                            # Snap all text immediately
                            for i, ln in enumerate(page):
                                displayed_lines[i] = ln
                            done = True
                if event.type == pygame.KEYDOWN and done:
                    break
            else:
                # Typewriter tick
                if not done:
                    char_timer += dt
                    while char_timer >= char_rate and line_idx < len(page):
                        ln = page[line_idx]
                        if char_indices[line_idx] < len(ln):
                            displayed_lines[line_idx] += ln[char_indices[line_idx]]
                            char_indices[line_idx]    += 1
                            char_timer -= char_rate
                        else:
                            line_idx  += 1
                            char_timer = 0.0
                    if line_idx >= len(page):
                        done = True
                pygame.display.flip()

                screen.fill((5, 3, 3))
                pygame.draw.rect(screen, (25, 15, 12),
                                    (50, 50, WIDTH-100, HEIGHT-100))
                pygame.draw.rect(screen, (80, 50, 30),
                                    (50, 50, WIDTH-100, HEIGHT-100), 1)

                y = 80
                for line in displayed_lines:
                    surf = font_sm.render(line, True, (210, 190, 170))
                    screen.blit(surf, (75, y))
                    y += 34

                if done:
                    blink = int(pygame.time.get_ticks() / 500) % 2 == 0
                    if blink:
                        hint = font_tiny.render(
                            "SPACE / ENTER — Continue   ESC — Skip",
                            True, (100, 80, 60))
                        screen.blit(hint, hint.get_rect(
                            center=(HALF_W, HEIGHT-55)))
                continue

            break   # inner break hit — advance page

# MAIN
def main():
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption("JLK Descent — Ohio Northern University")
    clock = pygame.time.Clock()

    # Fonts — uses system fallback if custom font not found
    def load_font(size):
        for name in ["Courier New","Courier","monospace"]:
            try: return pygame.font.SysFont(name, size)
            except: pass
        return pygame.font.Font(None, size)

    font_big   = load_font(52)
    font_med   = load_font(30)
    font_sm    = load_font(28)
    font_tiny  = load_font(20)
    font_note  = load_font(18)

    bullet_timer = 0.0
    bullet_frame = 0

    # Main loop state machine
    game_state = "menu"   # menu | playing | paused | note | ending
    player = None
    active_note_text = ""
    ending_type = ""

    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)

    while True:
        dt = clock.tick(FPS)/1000.0
        dt = min(dt, 0.05)

        # MENU 
        if game_state == "menu":
            result = main_menu(screen, font_big, font_med, font_sm, font_tiny, clock)
            if result == "new_game":
                show_intro(screen, font_sm, font_tiny, clock)
                player = Player()
                player.level = 1
                setup_level(player)
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)
                game_state = "playing"
            elif result == "notebook":
                # Need a dummy player if none exists yet to avoid crash
                nb_player = player if player else Player.__new__(Player)
                if player is None:
                    nb_player.notes_read = []
                    nb_player.notes_this_level_total = 0
                    nb_player.notes_this_level_found = 0
                notebook_menu(screen, font_big, font_sm, font_tiny, font_note, clock, nb_player)
            elif result == "settings":
                settings_menu(screen, font_big, font_sm, font_tiny, clock)
            elif result == "quit":
                pygame.quit(); sys.exit()

        # PLAYING 
        elif game_state == "playing":
            bullet_timer += dt
            if bullet_timer >= 0.05:
                bullet_timer = 0.0
                bullet_frame = (bullet_frame+1)%20

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                        result = pause_menu(screen, font_big, font_sm, font_tiny, clock)
                        if result == "resume":
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                        elif result == "settings":
                            settings_menu(screen, font_big, font_sm, font_tiny, clock)
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                        elif result == "main_menu":
                            game_state = "menu"
                            pygame.mouse.set_visible(True)
                            pygame.event.set_grab(False)
                        elif result == "quit":
                            pygame.quit(); sys.exit()
                    if event.key in (pygame.K_SPACE,):
                        if player.health > 0: player.shoot()
                    if event.key == pygame.K_f:
                        inter = player.check_interactions()
                        if inter:
                            kind, obj = inter
                            if kind == "note":
                                obj.picked_up = True
                                player.play_note_pickup()
                                if obj.note_key not in player.notes_read:
                                    player.notes_read.append(obj.note_key)
                                    player.notes_this_level_found += 1
                                active_note_text = NOTES.get(obj.note_key, "[Note missing]")
                                pygame.mouse.set_visible(True)
                                pygame.event.set_grab(False)
                                game_state = "note"
                            elif kind == "cure":
                                obj.picked_up = True
                                player.play_door()
                                if obj.piece_id not in player.cure_pieces:
                                    player.cure_pieces.append(obj.piece_id)
                                show_message(screen, font_sm,
                                    [(f"COMPOUND COLLECTED: {obj.piece_id.upper()}", (0, 255, 120)),
                                        ("Keep searching for the other pieces.", (200, 200, 200))],
                                    delay_ms=2000)
                    if event.key >= pygame.K_0 and event.key <= pygame.K_9:
                        secret_code_input += chr(event.key)
                        if len(secret_code_input) > 4:
                            secret_code_input = secret_code_input[-4:]
                        # Check if code is correct
                        if secret_door and not secret_door.unlocked and secret_code_input == secret_door.code:
                            secret_door.unlocked = True
                            player.play_door()
                            show_message(screen, font_sm,
                                [("CODE ACCEPTED", (0, 255, 150)),
                                    ("The sealed door opens...", (150, 200, 255))],
                                delay_ms=2000)
                            secret_code_input = ""
                        elif len(secret_code_input) == 2 and secret_door and secret_code_input != secret_door.code[:len(secret_code_input)]:
                            show_message(screen, font_sm,
                                [("INCORRECT CODE", (255, 100, 100)),
                                    ("Try again", (150, 150, 150))],
                                delay_ms=800)
                            secret_code_input = ""
                    if event.key == pygame.K_BACKSPACE:
                        secret_code_input = secret_code_input[:-1]
                    if event.key == pygame.K_ESCAPE:
                        secret_code_input = ""
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button==1 and player.health>0: player.shoot()

            rel_x,_ = pygame.mouse.get_rel()
            player.apply_mouse(rel_x)
            keys = pygame.key.get_pressed()
            if player.health > 0: player.move(keys, dt)
            player.tick(dt)

            for b in bullets: b.update(player.level)
            bullets[:] = [b for b in bullets if b.alive]

            level  = player.level
            theme  = LEVEL_THEMES.get(level, LEVEL_THEMES[1])
            z_buf  = cast_rays(screen, player,
                                theme["wall"], theme["ceil"], theme["floor"])
            update_and_draw_enemies(screen, player, z_buf, dt, level)
            draw_world_objects(screen, player, z_buf)
            draw_bullets(screen, player, z_buf, bullet_frame)
            update_and_draw_enemy_bullets(screen, player, z_buf)
            draw_hud(screen, player, font_sm, font_tiny, level)

            # Check boss defeat on level 20
            boss_alive = any(e.is_boss and e.alive for e in enemies)
            boss_dead  = any(e.is_boss and e.dead  for e in enemies)
            if level == 20 and boss_dead and not boss_alive:
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)
                has_all = all(p in player.cure_pieces
                                for p in ["cure_01","cure_02","cure_03"])
                ending_type = show_final_choice(screen, font_big, font_sm,
                                                font_tiny, clock, has_all)
                game_state = "ending"

            # Level advance
            # Activate exit when all enemies are defeated
            if exit_object and not exit_object.active:
                if not any(e.alive for e in enemies):
                    exit_object.active = True
                    show_message(screen, font_sm,
                        [("EXIT UNLOCKED",(0,180,255)),
                            ("Find the blue door to descend.",(180,180,200))],
                        delay_ms=1800)

            # Level advance via exit door
            inter = player.check_interactions()
            if inter and inter[0] == "exit" and level < 20:
                player.play_door()
                show_message(screen,font_sm,
                    [(f"LEVEL {level} COMPLETE",(0,255,0)),
                        (f"Descending to: {LEVEL_THEMES.get(level+1,{}).get('name','???')}",(0,200,255)),
                        ("+50 HEALTH",(0,220,100))],
                    delay_ms=2500)
                player.level  += 1
                player.score   = 0
                player.health  = min(100,player.health+50)
                setup_level(player)

            # Death
            elif player.health <= 0:
                show_message(screen,font_sm,
                    [("YOU DIED",(220,40,40)),
                        ("The organism keeps what it takes.",(180,150,140))],
                    delay_ms=3000)
                show_ending(screen,font_big,font_sm,font_tiny,clock,"bad")
                game_state = "menu"
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)

            pygame.display.flip()

        #  NOTE READING
        elif game_state == "note":
            show_note(screen, font_note, font_tiny, active_note_text, clock)
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
            game_state = "playing"
            pygame.mouse.get_rel()  # flush accumulated mouse delta

        # ENDING 
        elif game_state == "ending":
            show_ending(screen, font_big, font_sm, font_tiny, clock, ending_type)
            game_state = "menu"
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)

if __name__ == "__main__":
    main()