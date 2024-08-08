"""
Utility functions and classes for the project
"""

import arcade
from copy import deepcopy
import math
import numpy as np
from typing import Optional, Union


# Geometry tools
# TODO: If any exist in arcade then consider replacing this version with that one

type ListPt = list[float]
type fTuplePt2 = tuple[float, float]
type iTuplePt2 = tuple[int, int]
type PtType = Union[ListPt, fTuplePt2, np.array]
type BoxType = Union[list[float], tuple[float, float, float, float]]

def manhattan_dist(p1: PtType, p2: PtType) -> float:
    return (abs(p1[0]-p2[0])+abs(p1[1]-p2[1]))

def pt_distance(p1: PtType, p2: PtType) -> float:
    p1 = np.array(p1)
    p2 = np.array(p2)
    return float(np.linalg.norm(p1-p2))

def line_pt_distance(l1: PtType, l2: PtType, p: PtType) -> float:
    """ Perpendicular distance between a point and a line """
    if l1[0] == l2[0] and l1[1] == l2[1]:
        raise ValueError(f"Point line distance called with two points: {l1} {l2} {p}")
    if pt_distance(l1, l2) < 1:
        print(f"{l1} {l2} {p}")
    l1 = np.array(l1)
    l2 = np.array(l2)
    p = np.array(p)
    return float(np.linalg.norm(np.cross(l2-l1, l1-p))/np.linalg.norm(l2-l1))

def ray(start_pt: PtType, end_pt: PtType) -> PtType:
    return [end_pt[0]-start_pt[0], end_pt[1]-start_pt[1]]

def cartesian_to_polar(start_pt: PtType, end_pt: PtType) -> PtType:
    r = pt_distance(start_pt, end_pt)
    pt_ray = ray(start_pt, end_pt)
    theta = float(np.arctan2(pt_ray[1], pt_ray[0]))
    return r, theta

def polar_to_cartesian(length: float, orientation: float) -> fTuplePt2:
   return (length*math.cos(orientation), length*math.sin(orientation))

def is_point_in_box(pt: PtType, box: BoxType) -> bool:
    return pt[0] >= box[0] and pt[0] <= box[1] and pt[1] >= box[2] and pt[1] <= box[3]

def line_intersection(p1: PtType, p2: PtType, p3: PtType, p4: PtType) -> bool:
    """ Based on https://en.wikipedia.org/wiki/Line-line_intersection section "Given two points on each line segment" """
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

def line_box_intersection(start_pt: PtType, end_pt: PtType, box_center: PtType, box_w: float, box_h: float) -> bool:
    """ Checks for a line-line intersection with each side of a box """
    left = box_center[0] - box_w/2.
    right = box_center[0] + box_w/2.
    bottom = box_center[1] - box_h/2.
    top = box_center[1] + box_h/2.
    if is_point_in_box(start_pt, [left, right, bottom, top]):
        return True
    if is_point_in_box(end_pt, [left, right, bottom, top]):
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

def get_line(start: PtType, end: PtType) -> list[iTuplePt2]:
    """Bresenham's Line Algorithm

    Downloaded from https://github.com/Azrood/python-bresenham

    This code was unlicensed at the time of copying (Aug 2, 2024)

    Produces a list of tuples from start and end

    >>> points1 = get_line((0, 0), (3, 4))
    >>> points2 = get_line((3, 4), (0, 0))
    >>> assert(set(points1) == set(points2))
    >>> print points1
    [(0, 0), (1, 1), (1, 2), (2, 3), (3, 4)]
    >>> print points2
    [(3, 4), (2, 3), (1, 2), (1, 1), (0, 0)]
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)

    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    # Swap start and end points if necessary and store swap state
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True

    # Recalculate differentials
    dx = x2 - x1
    dy = y2 - y1

    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1

    # Iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx

    # Reverse the list if the coordinates were swapped
    if swapped:
        points.reverse()
    return points


class LineSegmentCollisionDetector:
    """ Simulate the laser by looking for a line collision with the spatial hash table """

    def __init__(self):
        self.hash_lines = {}

    def setup_polar(self, start_pt: PtType, length: float, orientation: float):
        self.start_pt = start_pt
        self.orientation = orientation
        self.length = length
        self.ray = polar_to_cartesian(self.length, self.orientation)

    def setup_pts(self, start_pt: PtType, end_pt: PtType):
        self.start_pt = start_pt
        self.length, self.orientation = cartesian_to_polar(start_pt, end_pt)
        self.ray = ray(start_pt, end_pt)

    def endpoint(self, start: Optional[PtType]) -> fTuplePt2:
        """ Furthest point the laser can reach and be reflected """
        if start is None:
            start = self.start_pt
        return (start[0]+self.ray[0], start[1]+self.ray[1])

    def _bresenham_line_hash_lookup(self, spatial_hash, origin: Optional[PtType]=None) -> set[arcade.Sprite]:
        """ Use bresenham line drawing algorithm to identify relevant bucket indices """
        if origin is None:
            origin = self.start_pt
        origin_hash = spatial_hash._hash(origin)

        # get indices of the line segment
        line_bucket_inds = self.hash_lines.setdefault(spatial_hash.cell_size, {'start': (0,0), 'line': []})
        if not line_bucket_inds['line']:
            # Lazy initialization of the hash line for each hash cell size
            endpt_hash = spatial_hash._hash([origin[0]+self.ray[0], origin[1]+self.ray[1]])
            line_bucket_inds = {'start': origin_hash, 'line': get_line(origin_hash, endpt_hash)}

            self.hash_lines[spatial_hash.cell_size] = line_bucket_inds
        # calculate the offset to move the line from it's first calculation to the current sensor position
        line_ind_offset = (origin_hash[0]-line_bucket_inds['start'][0], origin_hash[1]-line_bucket_inds['start'][1])

        # iterate over the line buckets
        close_by_sprites: set[arcade.Sprite] = set()
        for b in line_bucket_inds['line']:
            new_items = spatial_hash.contents.setdefault((b[0]+line_ind_offset[0], b[1]+line_ind_offset[1]), [])
            close_by_sprites.update(new_items)
        return close_by_sprites

    def detect_collisions(self, line_width: float, obstructions: list[arcade.SpriteList], origin: Optional[PtType]=None) -> tuple[bool, Optional[arcade.Sprite], float]:
        """ Find nearest collision along a line segment """
        if origin is None:
            origin = self.start_pt

        # Find any obstacles near the laser path
        detection_candidates = []
        for subset in obstructions:
            detection_candidates.extend(self._bresenham_line_hash_lookup(subset.spatial_hash, origin))

        # Find the nearest valid candidate
        laser_endpt = self.endpoint(origin)
        invalid_d = self.length+1
        colliding_sprite = None
        min_d = invalid_d
        collision_distance = line_width / 2.
        for candidate in detection_candidates:
            if line_pt_distance(origin, laser_endpt, candidate.position) > collision_distance:
                # ignore candidates that are outside the beam width
                continue
            if line_box_intersection(origin, laser_endpt, candidate.position, candidate.width, candidate.height):
                # find the nearest obstruction along the line segment
                d = pt_distance(candidate.position, origin)
                if d > collision_distance and d < min_d:
                    colliding_sprite = candidate
                    min_d = d

        if min_d < invalid_d:
            return True, colliding_sprite, min_d
        return False, None, -1


# Dictionary tools

def copy_override_dict(main_dict: dict, override_dict: dict) -> dict:
    """ Recursive copying of override values from one dict to another """
    if override_dict is None:
        return
    invalid_overrides = {} # For keys in the override dict that don't exist in the main dict
    for key, value in override_dict.items():
        if key in main_dict:
            if isinstance(value, dict):
                sub_invalid_overrides = copy_override_dict(main_dict[key], override_dict[key])
                if sub_invalid_overrides != {}:
                    invalid_overrides[key] = sub_invalid_overrides
            else:
                main_dict[key] = override_dict[key]
        else:
            invalid_overrides[key] = deepcopy(override_dict[key])
    return invalid_overrides

def is_valid_key_chain(config: dict, key_chain: list[str]) -> bool:
    """ Check a sequence of keys exist in a nested dictionary """
    if config is None:
        return False
    subconfig = deepcopy(config)
    for key in key_chain:
        if key in subconfig:
            subconfig = subconfig[key]
        else:
            return False
    return True
