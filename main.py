import sys 
from enum import Enum
from collections import namedtuple
from math import sqrt, acos, degrees, floor

# from util import Vector3
# Utils below 

# A type for our 3D points.
# In this scenario, units are in km.
Vector3 = namedtuple('Vector3', ['x', 'y', 'z'])

# Center of the earth.
origin = Vector3(0,0,0)

# Speed of light, km/s
speed_of_light_km_s = 299792.0

# Beams per satellite.
beams_per_satellite = 32

# List of valid beam IDs.
valid_beam_ids = [str(i) for i in range(1, beams_per_satellite + 1)]

# Colors per satellite.
colors_per_satellite = 4

# List of valid color IDs.
valid_color_ids = [chr(ord('A') + i) for i in range(0, colors_per_satellite)]

# Self-interference angle, degrees
self_interference_max = 10.0

# Non-Starlink interference angle, degrees
non_starlink_interference_max = 20.0

# Max user to Starlink beam angle, degrees from vertical.
max_user_visible_angle = 45.0


def calculate_angle_degrees(vertex: Vector3, point_a: Vector3, point_b: Vector3) -> float:
    """
    Returns: the angle formed between point_a, the vertex, and point_b in degrees.
    """

    # Calculate vectors va and vb
    va = Vector3(point_a.x - vertex.x, point_a.y - vertex.y, point_a.z - vertex.z)
    vb = Vector3(point_b.x - vertex.x, point_b.y - vertex.y, point_b.z - vertex.z)

    # Calculate each vector's magnitude.
    va_mag = sqrt( (va.x ** 2) + (va.y ** 2) + (va.z ** 2) )
    vb_mag = sqrt( (vb.x ** 2) + (vb.y ** 2) + (vb.z ** 2) )

    # Normalize each vector.
    va_norm = Vector3(va.x / va_mag, va.y / va_mag, va.z / va_mag)
    vb_norm = Vector3(vb.x / vb_mag, vb.y / vb_mag, vb.z / vb_mag)

    # Calculate the dot product.
    dot_product = (va_norm.x * vb_norm.x) + (va_norm.y * vb_norm.y) + (va_norm.z * vb_norm.z)

    # Error can add up here. Bound the dot_product to something we can take the acos of. Scream if it's a big delta.
    dot_product_bound = min(1.0, max(-1.0, dot_product))
    if abs(dot_product_bound - dot_product) > 0.000001:
        print(f"dot_product: {dot_product} bounded to {dot_product_bound}")

    # Return the angle.
    return degrees(acos(dot_product_bound))


def calculate_distance(point_a: Vector3, point_b: Vector3) -> float:
    """
    Returns: the distance between two 3D points.
    """

    # The square root of the difference squared between each compontent.
    x_diff_squared = (point_b.x - point_a.x) ** 2
    y_diff_squared = (point_b.y - point_a.y) ** 2
    z_diff_squared = (point_b.z - point_a.z) ** 2
    return sqrt(x_diff_squared + y_diff_squared + z_diff_squared)

def read_object(object_type:str, line:str, dest:dict) -> bool:
    """
    Given line, of format 'type id float float float', grabs a Vector3 from the last
    three tokens and puts it into dest[id].

    Returns: Success or failure.
    """
    parts = line.split()
    if parts[0] != object_type or len(parts) != 5:
        print("Invalid line! " + line)
        return False
    else:
        ident = parts[1]
        try:
            x = float(parts[2])
            y = float(parts[3])
            z = float(parts[4])
        except:
            print("Can't parse location! " + line)
            return False

        dest[ident] = Vector3(x, y, z)
        return True


def read_scenario(filename:str, scenario:dict) -> bool:
    """
    Given a filename of a scenario file, and a dictionary to populate, populates
    the dictionary with the contents of the file, doing some validation along
    the way.

    Returns: Success or failure.
    """
    scenariofile_lines = open(filename).readlines()
    scenario['sats'] = {}
    scenario['users'] = {}
    scenario['interferers'] = {}
    for line in scenariofile_lines:
        if "#" in line:
            # Comment.
            continue

        elif line.strip() == "":
            # Whitespace or empty line.
            continue

        elif "interferer" in line:
            # Read a non-starlink-sat object.
            if not read_object('interferer', line, scenario['interferers']):
                return False

        elif "sat" in line:
            # Read a sat object.
            if not read_object('sat', line, scenario['sats']):
                return False

        elif "user" in line:
            # Read a user object.
            if not read_object('user', line, scenario['users']):
                return False

        else:
            print("Invalid line! " + line)
            return False

    return True

class BeamState(Enum):
    AVAILIBLE = 0 
    IN_USE = 1
    UNAVAILIBLE = -1

def set_user_beam(v: [[BeamState]], user_i, color_i, sat_id, state):
    """
    Updates the visibility matrix entry for user, color, sat to be the state specified
    """

    v[user_i][(sat_id - 1) * colors_per_satellite + color_i] = state 

def update_visibility(v, scenario, target_user_i, sat_id, color_i, beam_i):
    """
    Updates v to activate the beam described by sat_id and color_id for user user_id, 
    following the contraints below

    Constraints: 
    - no beams same color from same satellite < 10deg 
    - 32 beam cap 
    """

    set_user_beam(v, target_user_i, color_i, sat_id, BeamState.IN_USE)

    target_user_pos = scenario['users'][str(target_user_i + 1)]

    mark_sat_full = False
    if beam_i == beams_per_satellite - 1: 
        mark_sat_full = True 
    
    sat_i = (sat_id - 1) * colors_per_satellite
    sat_i_color_i = sat_i + color_i 

    num_users = len(v)
    num_sat_beam = len(v[0])
    for user_i in range(num_users): 
        user = v[user_i]

        if mark_sat_full: 
            for i in range(sat_i, sat_i + colors_per_satellite):
                if v[user_i][i] == BeamState.AVAILIBLE:
                    v[user_i][i] = BeamState.UNAVAILIBLE
            # don't have to worry about below constraint bc all AVAILIBLE
            # beams will be set to unavail
            continue

        if user[sat_i_color_i] != BeamState.AVAILIBLE: 
            # only need to update beams that are current availible 
            continue

        user_pos = scenario['users'][str(user_i + 1)]
        sat_pos = scenario['sats'][str(sat_id)]
        angle = calculate_angle_degrees(sat_pos, target_user_pos, user_pos)

        if angle < self_interference_max: 
            v[user_i][sat_i_color_i] = BeamState.UNAVAILIBLE


def main() -> int:
    """
    Entry point.

    Returns: exit code.
    """

    # Make sure args are valid.
    if len(sys.argv) != 2 and len(sys.argv) != 1:
        print("Usage: python3.7 evaluate.py /path/to/scenario.txt")
        print("   If the optional /path/to/scenario.txt is not provided, stdin will be read.")
        return -1

    # Read and store inputs. Some validation is done here.

    scenario = {}
    # Scenario structure:
    # scenario['sats'][sat_id] = position as a Vector3
    # scenario['users'][user_id] = position as a Vector3
    # scenario['interferers'][interferer_id] = position as a Vector3

    if not read_scenario(sys.argv[1], scenario):
        return -1

    # print(scenario)
    solution = {}
    # Solution structure:
    # solution[satellite_id][beam_id] = user_id

    v = generate_visibility_matrix(scenario)
    
    # keeps track of current beam id for sat
    sat_beams = {}

    # greedy solver 
    num_users = len(v)
    num_sat_beam = len(v[0])
    for user_i in range(num_users): 
        user = v[user_i]
        for sat_beam_i in range(num_sat_beam): 
            sat_beam_status = v[user_i][sat_beam_i]

            if sat_beam_status == BeamState.AVAILIBLE: 
                sat_id = floor(sat_beam_i / colors_per_satellite) + 1
                color_i = sat_beam_i % colors_per_satellite
                
                if sat_id not in solution: 
                    solution[sat_id] = []
                
                new_beam = [user_i + 1, color_i]

                solution[sat_id].append(new_beam)
                current_beam_i = len(solution[sat_id]) - 1
                update_visibility(v, scenario, user_i, sat_id, color_i, current_beam_i)
                break
    format_solution(solution)
    return 0

def format_solution(solution:dict, outfile:str=None):
    result = ""
    for sat_id in solution: 
        sat = solution[sat_id]
        num_beams = len(sat)
        for beam_i in range(num_beams):
            beam = str(beam_i + 1)
            user = str(sat[beam_i][0])
            color = valid_color_ids[sat[beam_i][1]] 
            # TODO use string formatting for this 
            new_line = " ".join(["sat", str(sat_id), "beam", beam, "user", user, "color", color]) 
            new_line += "\n"
            result += new_line 
    print(result)

def matrix_printer(m):
    """
    Prints the matrix in a readable format
    """
    num_rows = len(m)
    num_cols = len(m[0])
    for row in range(num_rows):
        for col in range(num_cols):
            print(str(m[row][col]), end=", ")
        print()

def generate_visibility_matrix(scenario:dict) -> [[BeamState]]:
    """
    Generates a visibility matrix given the scenario. 

    Visibility matrix: (# users) x (# sats * colors/sat)
    ; each row is a user's availibility to each satelleites color beam

    entries are in [UNAVAILIBLE, AVAILIBLE, IN_USE] given constraints
    """
    users = scenario['users']
    sats = scenario['sats']
    interferers = scenario['interferers']

    # max beams of a certain color that a satellite could have (1 per self_interference_max deg) * visible_angle
    sat_dim = len(sats) * colors_per_satellite # * beams_per_color 
    user_dim = len(users)
    v = [[BeamState.UNAVAILIBLE for _ in range(sat_dim)] for _ in range(user_dim)] # users x (sat * colors * num_beams)

    for user_id in users: 
        for sat_id in sats: 
            user_pos = users[user_id]
            sat_pos = sats[sat_id]
            angle = calculate_angle_degrees(user_pos, origin, sat_pos)

            # User terminals are unable to form beams too far off of from vertical.
            if angle <= (180.0-max_user_visible_angle):
                # sat is outside of range of user 
                continue

            interferer_violation = False
            for interferer_id in interferers:
                interferer_pos = interferers[interferer_id]
                interferer_angle = calculate_angle_degrees(user_pos, interferer_pos, sat_pos)
                if interferer_angle < non_starlink_interference_max:
                    interferer_violation = True
                    break
            if interferer_violation:
                continue
                
            for i in range(colors_per_satellite):
                sat_i = (int(sat_id) -1) * colors_per_satellite + i
                user_i = int(user_id) - 1
                v[user_i][sat_i] = BeamState.AVAILIBLE 

    return v

if __name__ == "__main__":
    exit(main())

