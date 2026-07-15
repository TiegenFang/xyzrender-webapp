"""分子视角与四元数运算。"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def normalize_quaternion(q: Iterable[float]) -> tuple[float, float, float, float]:
    values = np.asarray(tuple(q), dtype=float)
    if values.shape != (4,):
        raise ValueError("quaternion must contain four values")
    norm = float(np.linalg.norm(values))
    if norm < 1e-12:
        return (1.0, 0.0, 0.0, 0.0)
    values /= norm
    return tuple(float(v) for v in values)


def multiply_quaternions(a, b) -> tuple[float, float, float, float]:
    aw, ax, ay, az = normalize_quaternion(a)
    bw, bx, by, bz = normalize_quaternion(b)
    return normalize_quaternion((
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ))


def axis_angle_quaternion(axis: tuple[float, float, float], angle: float):
    x, y, z = axis
    norm = math.sqrt(x * x + y * y + z * z)
    if norm < 1e-12:
        return (1.0, 0.0, 0.0, 0.0)
    s = math.sin(angle / 2.0) / norm
    return normalize_quaternion((math.cos(angle / 2.0), x * s, y * s, z * s))


def quaternion_matrix(q) -> np.ndarray:
    w, x, y, z = normalize_quaternion(q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], dtype=float)


def rotate_points(points: np.ndarray, quaternion, center: np.ndarray | None = None) -> np.ndarray:
    points = np.asarray(points, dtype=float)
    if not len(points):
        return points.copy()
    center = np.asarray(center, dtype=float) if center is not None else points.mean(axis=0)
    return (points - center) @ quaternion_matrix(quaternion).T + center


def rotate_molecule_copy(molecule, quaternion):
    """Rotate xyzrender graph, cube grid basis and crystal cell as one object."""
    mol = molecule.copy()
    node_ids = list(mol.graph.nodes)
    if not node_ids:
        return mol
    points = np.asarray([mol.graph.nodes[n]["position"] for n in node_ids], dtype=float)
    center = points.mean(axis=0)
    matrix = quaternion_matrix(quaternion)
    rotated = (points - center) @ matrix.T + center
    for node_id, position in zip(node_ids, rotated):
        mol.graph.nodes[node_id]["position"] = tuple(float(v) for v in position)

    cube = getattr(mol, "cube_data", None)
    if cube is not None:
        cube.origin = (np.asarray(cube.origin) - center) @ matrix.T + center
        cube.steps = np.asarray(cube.steps) @ matrix.T
        cube.atoms = [
            (symbol, tuple((np.asarray(position) - center) @ matrix.T + center))
            for symbol, position in cube.atoms
        ]
    cell = getattr(mol, "cell_data", None)
    if cell is not None:
        cell.lattice = np.asarray(cell.lattice) @ matrix.T
        cell.cell_origin = (np.asarray(cell.cell_origin) - center) @ matrix.T + center
    mol.oriented = True
    return mol
