import math
import numpy as np

from bresenham_line import get_line

class Measurement:
    NONE = -1

    def __init__(self, position, orientation, dist, max_range):
        self.position = position
        self.orientation = orientation
        self.dist = dist
        self.max_range = max_range

    def _project(self, d):
        return [self.position[0] + d*math.cos(self.orientation), 
                self.position[1] + d*math.sin(self.orientation)]

    def estimation(self, min_valid_range):
        estimate = None
        if self.dist != self.NONE and self.dist >= min_valid_range:
            estimate = self._project(self.dist)
        return estimate

    def ray(self):
        return self._project(self.max_range)

class Laser:
    def __init__(self, laser_half_width, max_range, orientation):
        self.laser_half_width = laser_half_width
        self.orientation = orientation
        self.max_range = max_range

        self.ray = [max_range*math.cos(orientation), max_range*math.sin(orientation)]
        self.hash_lines = {}

    def endpoint(self, start):
        return [start[0]+self.ray[0], start[1]+self.ray[1]]

    def bresenham_line_hash_lookup(self, origin, spatial_hash):
        # Use bresenham line drawing algorithm to identify relevant bucket indices
        origin_hash = spatial_hash._hash(origin)

        line_bucket_inds = self.hash_lines.setdefault(spatial_hash.cell_size, {'start': (0,0), 'line': []})
        if not line_bucket_inds['line']:
            # Lazy initialization of the hash line for each hash cell size
            endpt_hash = spatial_hash._hash([origin[0]+self.ray[0], origin[1]+self.ray[1]])
            line_bucket_inds = {'start': origin_hash, 'line': get_line(origin_hash, endpt_hash)}

            self.hash_lines[spatial_hash.cell_size] = line_bucket_inds
        line_ind_offset = (origin_hash[0]-line_bucket_inds['start'][0], origin_hash[1]-line_bucket_inds['start'][1])

        # iterate over the line buckets
        close_by_sprites: set[SpriteType] = set()
        for b in line_bucket_inds['line']:
                new_items = spatial_hash.contents.setdefault((b[0]+line_ind_offset[0], b[1]+line_ind_offset[1]), [])
                close_by_sprites.update(new_items)
        return close_by_sprites

def line_pt_distance(l1, l2, p):
    l1 = np.array(l1)
    l2 = np.array(l2)
    p = np.array(p)
    return float(np.linalg.norm(np.cross(l2-l1, l1-p))/np.linalg.norm(l2-l1))

def point_in_box(pt, box):
    return pt[0] >= box[0] and pt[0] <= box[1] and pt[1] >= box[2] and pt[1] <= box[3]

def line_intersection(p1, p2, p3, p4):
    # Based on https://en.wikipedia.org/wiki/Line-line_intersection section "Given two points on each line segment"
    # using the formula for t = n/d then testing 0 <= t <= 1 becomes 
    # n <= d if d and n are positive or 
    # n >= d if d and n are negative
    # Also neither n or d can be 0
    n = (p1[0]-p3[0])*(p3[1]-p4[1])-(p1[1]-p3[1])*(p3[0]-p4[0])
    d = (p1[0]-p2[0])*(p3[1]-p4[1])-(p1[1]-p2[1])*(p3[0]-p4[0])
    if d == 0 or n == 0:
        return False
    if (d < 0 and n < 0 and n >= d) or (d > 0 and n > 0 and n <= d):
        return True
    return False

def line_box_intersection(start_pt, end_pt, box_center, box_w, box_h):
    left = box_center[0] - box_w/2.
    right = box_center[0] + box_w/2.
    bottom = box_center[1] - box_h/2.
    top = box_center[1] + box_h/2.
    if point_in_box(start_pt, [left, right, bottom, top]):
        return True
    if point_in_box(end_pt, [left, right, bottom, top]):
        return True
    if line_intersection(start_pt, end_pt, [left, top], [right, top]):
        return True
    if line_intersection(start_pt, end_pt, [left, bottom], [right, bottom]):
        return True
    if line_intersection(start_pt, end_pt, [left, top], [left, bottom]):
        return True
    if line_intersection(start_pt, end_pt, [right, top], [right, bottom]):
        return True
    return False

def pt_distance(p1, p2):
    p1 = np.array(p1)
    p2 = np.array(p2)
    return float(np.linalg.norm(p1-p2))

class LaserRangeFinder:
    def __init__(self, bot, laser_half_width, max_range, orientation):
        self.bot = bot
        self.laser = Laser(laser_half_width, max_range, orientation)

    def measure(self, obstructions):
        # obstructions must be a list of sprite lists with spatial hashing

        detection_candidates = []
        for subset in obstructions:
            detection_candidates.extend(self.laser.bresenham_line_hash_lookup(self.bot.position, subset.spatial_hash))

        laser_endpt = self.laser.endpoint(self.bot.position)
        invalid_d = self.laser.max_range+1
        min_d = invalid_d
        collision_distance = self.bot.grid_size / 2
        for candidate in detection_candidates:
            if line_pt_distance(self.bot.position, laser_endpt, candidate.position) > self.laser.laser_half_width:
                continue
            if line_box_intersection(self.bot.position, laser_endpt, candidate.position, candidate.width, candidate.height):
                d = pt_distance(candidate.position, self.bot.position)
                if d > collision_distance and d < min_d:
                    min_d = d

        result = Measurement(self.bot.position, self.laser.orientation, Measurement.NONE, self.laser.max_range)
        if min_d < invalid_d:
            result = Measurement(self.bot.position, self.laser.orientation, min_d, self.laser.max_range)
        
        return result
