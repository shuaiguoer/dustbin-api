# !/usr/bin/env python
# -*-coding: utf-8 -*-
import platform
import time

import psutil
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required

from app.utils.ConnectionRedis import redisConnection
from app.utils.ResponseWrap import successResponseWrap
from app.utils.utils import convert_size, delay_color, getDateDiff

monitor = Blueprint('monitor', __name__)


# 获取在线用户列表
@monitor.get("/monitor/online/list")
@jwt_required()
def getOnlineUserList():
    ipaddr = request.args.get("ipaddr", default="")
    username = request.args.get("username", default="")
    page = request.args.get("page", type=int)
    pageSize = request.args.get("pageSize", type=int)

    # 连接Redis
    rdb_online_users = redisConnection(0)

    # 获取数据
    online_users_jti = rdb_online_users.keys("*")

    userList = []

    for u in online_users_jti:
        userInfo = rdb_online_users.hgetall(u)
        userInfo["id"] = u

        if ipaddr in userInfo.get("ipaddr") and username in userInfo.get("username"):
            userList.append(userInfo)

    itemCount = rdb_online_users.dbsize()
    pageCount = int((itemCount + pageSize - 1) / pageSize)

    Data = {
        "list": userList[(page * pageSize - pageSize):(page * pageSize)],
        "page": page,
        "pageSize": pageSize,
        "pageCount": pageCount,
        "itemCount": itemCount,
    }

    return successResponseWrap(data=Data)


# 获取系统信息
@monitor.get("/monitor/system")
def getSystemInfo():
    G = 1024 * 1024 * 1024
    cpu_times_percent = psutil.cpu_times_percent(interval=1)
    mem = psutil.virtual_memory()
    devs = psutil.disk_partitions()
    ip = current_app.config.get("REDIS_HOST")
    ts = int(round(time.time()))
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    users = psutil.users()
    boot_ts = psutil.boot_time()

    systemInfoData = {
        "sys": {
            "node": platform.node(),
            "system": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "ip": ip,
            "now": now,
            "users": [u.name for u in users],
            "dateDiff": getDateDiff(boot_ts, ts)
        },
        "cpu": {
            "cpu_count": psutil.cpu_count(logical=False),
            "user_used": cpu_times_percent.user,
            "sys_used": cpu_times_percent.system,
            "free": cpu_times_percent.idle
        },
        "mem": {
            "total": round(mem.total / G, 2),
            "available": round(mem.available / G, 2),
            "used": round(mem.used / G, 2),
            "free": round(mem.free / G, 2),
            "percent": mem.percent,
        },
        "disk": [],
    }

    # 获取所有磁盘的信息
    for dev in devs:
        disk_usage = psutil.disk_usage(dev.mountpoint)

        systemInfoData["disk"].append({
            "device": dev.device,
            "mountpoint": dev.mountpoint,
            "fstype": dev.fstype,
            "total": round(disk_usage.total / G, 2),
            "used": round(disk_usage.used / G, 2),
            "free": round(disk_usage.free / G, 2),
            "percent": disk_usage.percent,
        })

    return successResponseWrap(data=systemInfoData)


# 获取网络和磁盘IO
@monitor.get("/monitor/net-disk-io")
def getNetDiskIO():
    KB = 1024
    MB = 1024 * 1024
    t = int(round(time.time()))
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))

    # 网络
    netsr = psutil.net_io_counters()
    # 上传字节
    bytes_sent_1 = netsr.bytes_sent
    # 下载字节
    bytes_recv_1 = netsr.bytes_recv

    # 磁盘
    diskrw = psutil.disk_io_counters()
    # 读写字节
    read_bytes_1 = diskrw.read_bytes
    write_bytes_1 = diskrw.write_bytes
    # 读写次数
    read_count_1 = diskrw.read_count
    write_count_1 = diskrw.write_count
    # 读写时间
    write_time_1 = diskrw.write_time

    time.sleep(1)

    # 网络
    netsr = psutil.net_io_counters()
    # 上传字节
    bytes_sent_2 = netsr.bytes_sent
    # 下载字节
    bytes_recv_2 = netsr.bytes_recv

    # 磁盘
    diskrw = psutil.disk_io_counters()
    # 读写字节
    read_bytes_2 = diskrw.read_bytes
    write_bytes_2 = diskrw.write_bytes
    # 读写次数
    read_count_2 = diskrw.read_count
    write_count_2 = diskrw.write_count
    # 读写时间
    write_time_2 = diskrw.write_time

    # 网络每秒 上传/下载 字节
    bytes_sent = bytes_sent_2 - bytes_sent_1
    bytes_recv = bytes_recv_2 - bytes_recv_1

    # 磁盘每秒 读/写 字节
    read_bytes = read_bytes_2 - read_bytes_1
    write_bytes = write_bytes_2 - write_bytes_1

    # 磁盘每秒读写次数
    write_read_count = (read_count_2 - read_count_1) + (write_count_2 - write_count_1)
    write_time = write_time_2 - write_time_1

    netDiskIOData = {
        "net": {
            "bytes_sent": [now, float(format((bytes_sent / KB), '.2f'))],
            "bytes_recv": [now, float(format((bytes_recv / KB), '.2f'))],
            "statistics": [
                {
                    "value": convert_size(bytes_sent),
                    "text": "上传",
                    "color": "#37A2DA"
                },
                {
                    "value": convert_size(bytes_recv),
                    "text": "下载",
                    "color": "#FFD85C"
                },
                {
                    "value": convert_size(bytes_sent_2),
                    "text": "总上传",
                },
                {
                    "value": convert_size(bytes_recv_2),
                    "text": "总下载",
                }
            ],
        },
        "disk": {
            "read_bytes": [now, float(format((read_bytes / MB), '.2f'))],
            "write_bytes": [now, float(format((write_bytes / MB), '.2f'))],
            "statistics": [
                {
                    "value": convert_size(read_bytes),
                    "text": "读取",
                    "color": "#37A2DA"
                },
                {
                    "value": convert_size(write_bytes),
                    "text": "写入",
                    "color": "#FFD85C"
                },
                {
                    "value": str(write_read_count) + " 次",
                    "text": "每秒读写",
                },
                {
                    "value": str(write_time) + " ms",
                    "text": "读写延迟",
                    "textColor": delay_color(write_time)
                }
            ]
        }
    }

    return successResponseWrap(data=netDiskIOData)
