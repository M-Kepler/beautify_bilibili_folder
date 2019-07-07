#!/bin/python
# -*- coding:utf-8 -*-

"""
把从手机app上下载的bilibili视频从文件夹移出并按照视频标题命名

下载下来的目录结构如下:
1 # 视频分集
    lua.flv360.bilibili2api.16 # 下载的分辨率不同文件夹稍有差异
        0.blv # 视频文件
        0.blv.4m.sum
        index.json
    danmaku.xml
    entry.json # 保存了视频属性信息的json文件
"""
import os
import json


class BilibiliVideoHelper(object):
    def __init__(self):
        self.curr_path = os.path.abspath('.')
        # 视频文件夹列表
        self.dir_list = [x for x in os.listdir('.') if os.path.isdir(x)]
        # 视频文件
        self._def_video_name = '0.blv'
        # 视频文件扩展名
        self._ext = os.path.splitext(self._def_video_name)[1]

    def mv_video_out(self):
        """
        把视频从默认文件夹重命名为实际名称后移动到当前目录
        """
        for item in self.dir_list:
            item_path = os.path.join(self.curr_path, item)
            video_folder = [x for x in os.listdir(item_path) if x[:3] == 'lua']
            # 视频所在目录
            src_folder = os.path.join(item_path, video_folder[0])
            src_file = os.path.join(src_folder, self._def_video_name)
            title = self.parse_title(item_path)
            new_file = title + self._ext
            if os.path.exists(src_file):
                os.rename(src_file, new_file)
            else:
                pass

    def parse_title(self, item_path):
        """
        从entry.json文件中获取视频标题
        """
        json_path = os.path.join(item_path, 'entry.json')
        with open(json_path, 'r') as f:
            load_dict = json.load(f)
        title = load_dict['page_data']['part']
        return title


if __name__ == "__main__":
    api = BilibiliVideoHelper()
    api.mv_video_out()
