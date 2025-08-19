# Minimal 3D math helpers to avoid external deps
import math


def clamp(v, a, b):
    return max(a, min(b, v))


def add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def mul(a, s):
    return [a[0] * s, a[1] * s, a[2] * s]


def length(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def norm(v):
    l = length(v)
    if l == 0:
        return [0, 0, 0]
    return [v[0] / l, v[1] / l, v[2] / l]


def lerp(a, b, t):
    return [a[i] + (b[i] - a[i]) * t for i in range(3)]
