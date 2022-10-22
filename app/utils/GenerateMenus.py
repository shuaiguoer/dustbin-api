# !/usr/bin/env python3
# -*-coding: utf-8 -*-
"""
# @File    : GenerateMenus.py
# @Time    : 2022/7/10 16:47
# @Author  : Shuai
# @Email   : ls12345666@qq.com
"""

""" 写的很垃圾, 需要优化! """


# 生成树形菜单
def generateMenuTree(baseMenuList, pid, subField="id"):
    menuTree = []
    for menu in baseMenuList:
        if menu.get("pid") == pid:
            children = generateMenuTree(baseMenuList, menu.get(subField), subField)
            if children:
                menu['children'] = children
            menuTree.append(menu)

    return menuTree


# 过滤掉角色权限的pid
def filterRoleTree(menuTree):
    for menu in menuTree:
        del menu["pid"]
        if menu.get("children"):
            filterRoleTree(menu.get("children"))
    return menuTree


# 过滤菜单树
def filterMenuTree(MenuTree):
    # 菜单排序
    MenuTree.sort(key=lambda x: x['sort'])

    for menu in MenuTree:
        # 向meta中添加所需数据
        menu["meta"] = {}
        if menu["title"]:
            menu["meta"]["title"] = menu["title"]
        if menu["icon"]:
            menu["meta"]["icon"] = menu["icon"]
        if menu["hidden"]:
            menu["meta"]["hidden"] = True
        if menu["sort"]:
            menu["meta"]["sort"] = menu["sort"]

        # 删除多余数据
        delItems = ["title", "id", "hidden", "icon", "type", "pid", "menu_id", "sort"]
        for i in delItems:
            if menu.get(i):
                del menu[i]

        # 删除空数据
        for m in list(menu.keys()):
            if not menu.get(m):
                del menu[m]

        if menu.get("children"):
            # 递归过滤
            filterMenuTree(menu["children"])

    return MenuTree
