#!/usr/bin/env python

from __future__ import division
from sstv import byte_to_freq, FREQ_BLACK, FREQ_WHITE, FREQ_VIS_START
from grayscale import GrayscaleSSTV
from itertools import chain


RED, GREEN, BLUE = range(3)

class ColorSSTV(GrayscaleSSTV):
    def on_init(self):
        self.pixels = self.image.load()

    def encode_line(self, line):
        msec_pixel = self.SCAN / self.WIDTH
        image = self.pixels
        for index in self.COLOR_SEQ:
            for item in self.before_channel(index):
                yield item
            for col in xrange(self.WIDTH):
                pixel = image[col, line]
                freq_pixel = byte_to_freq(pixel[index])
                yield freq_pixel, msec_pixel
            for item in self.after_channel(index):
                yield item

    def before_channel(self, index):
        return []

    after_channel = before_channel


class MartinM1(ColorSSTV):
    COLOR_SEQ = (GREEN, BLUE, RED)
    VIS_CODE = 0x2c
    WIDTH = 320
    HEIGHT = 256
    SYNC = 4.862
    SCAN = 146.432
    INTER_CH_GAP = 0.572

    def before_channel(self, index):
        if index == GREEN:
            yield FREQ_BLACK, self.INTER_CH_GAP

    def after_channel(self, index):
        yield FREQ_BLACK, self.INTER_CH_GAP


class MartinM2(MartinM1):
    VIS_CODE = 0x28
    WIDTH = 160
    SCAN = 73.216


class ScottieS1(MartinM1):
    VIS_CODE = 0x3c
    SYNC = 9
    INTER_CH_GAP = 1.5
    SCAN = 138.24 - INTER_CH_GAP

    def horizontal_sync(self):
        return []

    def before_channel(self, index):
        if index == ColorSSTV.RED:
            for item in MartinM1.horizontal_sync(self):
                yield item
        yield FREQ_BLACK, self.INTER_CH_GAP


class ScottieS2(ScottieS1):
    VIS_CODE = 0x38
    SCAN = 88.064 - ScottieS1.INTER_CH_GAP
    WIDTH = 160


class Robot36(ColorSSTV):
    VIS_CODE = 0x08
    WIDTH = 320
    HEIGHT = 240
    SYNC = 9
    INTER_CH_GAP = 4.5
    Y_SCAN = 88
    C_SCAN = 44
    PORCH = 1.5
    SYNC_PORCH = 3
    INTER_CH_FREQS = [None, FREQ_BLACK, FREQ_WHITE]

    def on_init(self):
        self.yuv = self.image.convert('YCbCr').load()

    def encode_line(self, line):
        pixels = [self.yuv[col, line] for col in xrange(self.WIDTH)]
        channel = (line % 2) + 1
        y_pixel_time = self.Y_SCAN / self.WIDTH
        uv_pixel_time = self.C_SCAN / self.WIDTH
        return chain(
                [(FREQ_BLACK, self.SYNC_PORCH)],
                ((byte_to_freq(p[0]), y_pixel_time) for p in pixels),
                [(self.INTER_CH_FREQS[channel], self.INTER_CH_GAP),
                    (FREQ_VIS_START, self.PORCH)],
                ((byte_to_freq(p[channel]), uv_pixel_time) for p in pixels))


MODES = (MartinM1, MartinM2, ScottieS1, ScottieS2, Robot36)
