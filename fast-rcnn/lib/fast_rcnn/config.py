# --------------------------------------------------------
# Fast R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

"""Fast R-CNN config system.

This file specifies default config options for Fast R-CNN. You should not
change values in this file. Instead, you should write a config file (in yaml)
and use cfg_from_file(yaml_file) to load it and override the default options.

Most tools in $ROOT/tools take a --cfg option to specify an override file.
    - See tools/{train,test}_net.py for example code that uses cfg_from_file()
    - See experiments/cfgs/*.yml for example YAML config override files
"""

import os
import os.path as osp
import numpy as np
import math
# `pip install easydict` if you don't have it
from easydict import EasyDict as edict

__C = edict()
# Consumers can get config by:
#   from fast_rcnn_config import cfg
cfg = __C

#
# Training options
#

__C.TRAIN = edict()

# Scales to compute real features
__C.TRAIN.SCALES_BASE = (0.25, 0.5, 1.0, 2.0, 3.0)

# The number of scales per octave in the image pyramid 
# An octave is the set of scales up to half of the initial scale
__C.TRAIN.NUM_PER_OCTAVE = 4

# parameters for ROI generating
__C.TRAIN.SPATIAL_SCALE = 0.0625
__C.TRAIN.KERNEL_SIZE = 5

# Aspect ratio to use during training
__C.TRAIN.ASPECTS = (1, 0.75, 0.5, 0.25)

# Images to use per minibatch
__C.TRAIN.IMS_PER_BATCH = 2

# Minibatch size (number of regions of interest [ROIs])
__C.TRAIN.BATCH_SIZE = 128

# Fraction of minibatch that is labeled foreground (i.e. class > 0)
__C.TRAIN.FG_FRACTION = 0.25

# Overlap threshold for a ROI to be considered foreground (if >= FG_THRESH)
__C.TRAIN.FG_THRESH = 0.5

# Overlap threshold for a ROI to be considered background (class = 0 if
# overlap in [LO, HI))
__C.TRAIN.BG_THRESH_HI = 0.5
__C.TRAIN.BG_THRESH_LO = 0.1

# Use horizontally-flipped images during training?
__C.TRAIN.USE_FLIPPED = True

# Train bounding-box regressors
__C.TRAIN.BBOX_REG = True

# Overlap required between a ROI and ground-truth box in order for that ROI to
# be used as a bounding-box regression training example
__C.TRAIN.BBOX_THRESH = 0.5

# Iterations between snapshots
__C.TRAIN.SNAPSHOT_ITERS = 10000

# solver.prototxt specifies the snapshot path prefix, this adds an optional
# infix to yield the path: <prefix>[_<infix>]_iters_XYZ.caffemodel
__C.TRAIN.SNAPSHOT_INFIX = ''

# Use a prefetch thread in roi_data_layer.layer
# So far I haven't found this useful; likely more engineering work is required
__C.TRAIN.USE_PREFETCH = False

# Train using subclasses
__C.TRAIN.SUBCLS = True

#
# Testing options
#

__C.TEST = edict()

# Scales to compute real features
__C.TEST.SCALES_BASE = (0.25, 0.5, 1.0, 2.0, 3.0)

# The number of scales per octave in the image pyramid 
# An octave is the set of scales up to half of the initial scale
__C.TEST.NUM_PER_OCTAVE = 4

# Aspect ratio to use during testing
__C.TEST.ASPECTS = (1, 0.75, 0.5, 0.25)

# parameters for ROI generating
__C.TEST.SPATIAL_SCALE = 0.0625
__C.TEST.KERNEL_SIZE = 5

# Overlap threshold used for non-maximum suppression (suppress boxes with
# IoU >= this threshold)
__C.TEST.NMS = 0.5

# Experimental: treat the (K+1) units in the cls_score layer as linear
# predictors (trained, eg, with one-vs-rest SVMs).
__C.TEST.SVM = False

# Test using bounding-box regressors
__C.TEST.BBOX_REG = True

# Test using subclass
__C.TEST.SUBCLS = True

# Threshold of ROIs in testing
__C.TEST.ROI_THRESHOLD = 0.1

#
# MISC
#

# The mapping from image coordinates to feature map coordinates might cause
# some boxes that are distinct in image space to become identical in feature
# coordinates. If DEDUP_BOXES > 0, then DEDUP_BOXES is used as the scale factor
# for identifying duplicate boxes.
# 1/16 is correct for {Alex,Caffe}Net, VGG_CNN_M_1024, and VGG16
__C.DEDUP_BOXES = 1./16.

# Pixel mean values (BGR order) as a (1, 1, 3) array
# These are the values originally used for training VGG16
__C.PIXEL_MEANS = np.array([[[102.9801, 115.9465, 122.7717]]])

# For reproducibility
__C.RNG_SEED = 3

# A small number that's used many times
__C.EPS = 1e-14

# Root directory of project
__C.ROOT_DIR = osp.abspath(osp.join(osp.dirname(__file__), '..', '..'))

# Place outputs under an experiments directory
__C.EXP_DIR = 'default'

def get_output_dir(imdb, net):
    """Return the directory where experimental artifacts are placed.

    A canonical path is built using the name from an imdb and a network
    (if not None).
    """
    path = osp.abspath(osp.join(__C.ROOT_DIR, 'output', __C.EXP_DIR, imdb.name))
    if net is None:
        return path
    else:
        return osp.join(path, net.name)

def _add_more_info(is_train):
    # compute all the scales
    if is_train:
        scales_base = __C.TRAIN.SCALES_BASE
        num_per_octave = __C.TRAIN.NUM_PER_OCTAVE
    else:
        scales_base = __C.TEST.SCALES_BASE
        num_per_octave = __C.TEST.NUM_PER_OCTAVE

    num_scale_base = len(scales_base)
    num = (num_scale_base - 1) * num_per_octave + 1
    scales = []
    for i in xrange(num):
        index_scale_base = i / num_per_octave
        sbase = scales_base[index_scale_base]
        j = i % num_per_octave
        if j == 0:
            scales.append(sbase)
        else:
            sbase_next = scales_base[index_scale_base+1]
            step = (sbase_next - sbase) / num_per_octave
            scales.append(sbase + j * step)

    if is_train:
        __C.TRAIN.SCALES = scales
    else:
        __C.TEST.SCALES = scales
    print scales


    # map the scales to scales for RoI pooling of classification
    if is_train:
        kernel_size = __C.TRAIN.KERNEL_SIZE / __C.TRAIN.SPATIAL_SCALE
    else:
        kernel_size = __C.TEST.KERNEL_SIZE / __C.TEST.SPATIAL_SCALE

    area = kernel_size * kernel_size
    scales = np.array(scales)
    areas = np.repeat(area, num) / (scales ** 2)
    scaled_areas = areas[:, np.newaxis] * (scales[np.newaxis, :] ** 2)
    diff_areas = np.abs(scaled_areas - 224 * 224)
    levels = diff_areas.argmin(axis=1)

    if is_train:
        __C.TRAIN.SCALE_MAPPING = levels
    else:
        __C.TEST.SCALE_MAPPING = levels

    # compute width and height of grid box
    if is_train:
        area = __C.TRAIN.KERNEL_SIZE * __C.TRAIN.KERNEL_SIZE
        aspect = __C.TRAIN.ASPECTS  # height / width
    else:
        area = __C.TEST.KERNEL_SIZE * __C.TEST.KERNEL_SIZE
        aspect = __C.TEST.ASPECTS  # height / width

    num_aspect = len(aspect)
    widths = np.zeros((num_aspect), dtype=np.float32)
    heights = np.zeros((num_aspect), dtype=np.float32)
    for i in xrange(num_aspect):
        widths[i] = math.sqrt(area / aspect[i])
        heights[i] = widths[i] * aspect[i]

    if is_train:
        __C.TRAIN.ASPECT_WIDTHS = widths
        __C.TRAIN.ASPECT_HEIGHTS = heights
    else:
        __C.TEST.ASPECT_WIDTHS = widths
        __C.TEST.ASPECT_HEIGHTS = heights

def _merge_a_into_b(a, b):
    """Merge config dictionary a into config dictionary b, clobbering the
    options in b whenever they are also specified in a.
    """
    if type(a) is not edict:
        return

    for k, v in a.iteritems():
        # a must specify keys that are in b
        if not b.has_key(k):
            raise KeyError('{} is not a valid config key'.format(k))

        # the types must match, too
        if type(b[k]) is not type(v):
            raise ValueError(('Type mismatch ({} vs. {}) '
                              'for config key: {}').format(type(b[k]),
                                                           type(v), k))

        # recursively merge dicts
        if type(v) is edict:
            try:
                _merge_a_into_b(a[k], b[k])
            except:
                print('Error under config key: {}'.format(k))
                raise
        else:
            b[k] = v

def cfg_from_file(filename):
    """Load a config file and merge it into the default options."""
    import yaml
    with open(filename, 'r') as f:
        yaml_cfg = edict(yaml.load(f))

    _merge_a_into_b(yaml_cfg, __C)
    _add_more_info(1)
    _add_more_info(0)
