# !/usr/bin/env python
# -*-coding: utf-8 -*-
import math


# 文件大小单位换算
def convert_size(byte):
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = 1024
    for i in range(len(units)):
        if (byte / size) < 1:
            return "%.2f %s" % (byte, units[i])  # 返回值保留小数点后两位
        byte = byte / size


# 计算时间差
def getDateDiff(startTs, endTs):
    diffTs = float(endTs) - float(startTs)

    # S = 1
    M = 60
    H = 60 * 60
    D = 60 * 60 * 24

    day = math.floor(diffTs / D)
    hour = math.floor(diffTs % D / H)
    minute = math.floor(diffTs % H / M)
    # second = math.floor(diffTs % M / S)

    dateDiffStr = f"{day}天{hour}小时{minute}分钟"

    return dateDiffStr


# 延迟颜色映射
def delay_color(ms):
    if ms < 90:
        return "green"
    elif ms < 200:
        return "orange"
    else:
        return "red"
