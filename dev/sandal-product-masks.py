#!/usr/bin/env python3
"""Camera-local material boundaries for the retained open-toe product painting.

These paths describe surfaces, never source RGB. In particular, the cream
footbed, tan strap backs, piping and champagne hardware cannot become cloth
merely because a source pixel happens to be neutral. Coordinates are in the
immutable 1024 x 640 product camera. This is a development candidate only.
"""
import numpy as np
from PIL import Image, ImageDraw


def path_mask(size, commands, scale=4):
    """Rasterize closed cubic paths with source-pixel antialiasing."""
    points = []
    cursor = (0, 0)
    for command in commands:
        op, *v = command
        if op in ('M', 'L'):
            cursor = tuple(v)
            points.append(cursor)
        elif op == 'C':
            start = np.array(cursor, dtype=float)
            a, b, end = np.array(v, dtype=float).reshape(3, 2)
            for t in np.linspace(0, 1, 33)[1:]:
                points.append(tuple((1-t)**3*start + 3*(1-t)**2*t*a + 3*(1-t)*t*t*b + t**3*end))
            cursor = tuple(end)
        else:
            raise ValueError(op)
    im = Image.new('L', (size[0]*scale, size[1]*scale))
    ImageDraw.Draw(im).polygon([(round(x*scale), round(y*scale)) for x, y in points], fill=255)
    return np.array(im.resize(size, Image.Resampling.LANCZOS), dtype=float)


SURFACES = {
    'forefoot': [
        ('M',208,458), ('C',209,432,225,406,249,402),
        ('C',288,397,326,453,343,492), ('L',352,528), ('L',507,529),
        ('C',489,477,451,419,407,386), ('C',377,363,353,353,337,352),
        ('C',310,360,262,389,237,402), ('C',218,414,210,436,208,458)],
    'outer_footbed_wall': [
        ('M',510,526), ('C',558,524,596,512,622,488),
        ('C',654,458,676,418,710,386), ('C',745,352,790,321,837,298),
        ('L',850,279), ('C',791,308,747,334,707,370),
        ('C',671,403,645,445,615,473), ('C',588,498,553,509,505,508)],
    'near_diagonal': [
        ('M',500,246), ('C',541,279,579,317,609,353),
        ('C',634,383,650,413,655,443), ('L',674,419),
        ('C',673,393,653,360,628,333), ('C',595,295,553,257,515,233)],
    'far_diagonal_front': [
        ('M',476,271), ('C',490,238,520,211,557,190),
        ('C',621,154,714,125,815,93), ('L',811,104),
        ('C',718,136,628,168,564,204), ('C',527,226,501,248,489,278)],
    'ankle_front': [
        ('M',600,77), ('C',659,81,727,69,801,54),
        ('L',804,78), ('C',724,96,656,106,603,98)],
    'rear_counter_and_heel': [
        ('M',870,61), ('C',877,88,904,122,916,157),
        ('C',930,195,930,231,916,249), ('C',898,281,879,306,870,333),
        ('C',860,370,855,418,855,463), ('L',831,463),
        ('C',829,416,830,364,828,344), ('C',827,324,815,312,802,309),
        ('L',817,300), ('C',839,251,848,200,852,154),
        ('C',857,118,861,88,861,72)],
    'ankle_outer_return': [
        ('M',855,34), ('C',862,29,868,29,873,34), ('L',875,57),
        ('L',862,72), ('L',856,66)],
    'buckle_fabric_inset': [
        ('M',818,56), ('L',839,50), ('L',842,68), ('L',820,74)],
}

# These explicit protected surfaces also provide meaningful acceptance ROIs.
PROTECTED = {
    'front_cream_footbed': [
        ('M',100,495), ('C',130,476,183,469,233,463),
        ('C',252,472,289,489,337,501), ('L',343,520),
        ('C',244,518,151,517,100,507)],
    'main_insole': [
        ('M',474,449), ('C',529,430,571,410,610,375),
        ('C',669,322,735,275,830,238), ('L',824,269),
        ('C',745,308,704,342,673,377), ('C',637,416,615,460,583,482),
        ('C',553,503,528,503,507,504)],
    'rear_lining': [
        ('M',755,246), ('C',777,189,801,137,835,100),
        ('L',852,88), ('C',848,137,841,194,829,225)],
}


def semantic_masks(rgba):
    size = (rgba.shape[1], rgba.shape[0])
    if size != (1024, 640):
        raise ValueError('Product semantic masks require the fixed 1024x640 camera')
    regions = {name: path_mask(size, path) for name, path in SURFACES.items()}
    protected = {name: path_mask(size, path) for name, path in PROTECTED.items()}
    cloth = np.maximum.reduce(list(regions.values()))
    # Bands sit in front of the insole. Their continuous painted foreground
    # must win at overlaps; an insole-shaped knockout would cut white patches
    # through the diagonal strap. Each material path already excludes the
    # visible neutral surfaces along its own boundary.
    upper = cloth * rgba[:, :, 3].astype(float)/255
    return rgba[:, :, 3].astype(float), upper, {
        'method': 'camera-local cubic semantic paths; no RGB classification',
        'surfaces': list(regions), 'protected': list(protected),
    }
