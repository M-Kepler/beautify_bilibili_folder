#!/bin/python
# -*- coding:utf-8 -*-

"""
把从手机app上下载的bilibili视频从文件夹移出并按照视频标题命名
依赖 ffmpeg 工具来完成视频拼接和音视频合并 https://ffmpeg.zeranoe.com/builds/
处理后的视频会输出到传入的路径下
"""

import getopt
import json
import multiprocessing
import os
import shutil
import subprocess
import sys


class Config(object):
    def __init__(self):
        self.entry_file = "entry.json"
        self.def_video_name = "video.m4s"
        self.def_audio_name = "audio.m4s"
        self.blv_postfix = ".blv"
        self.new_video_postfix = ".mp4"


class EntryConfig(Config):
    """
    bilibili 视频配置文件
    https://www.cnblogs.com/holittech/p/12210691.html
    """

    def __init__(self, cfg_path):
        # self._get_video_entry_info 用到了 entry_file 所以先继承
        super().__init__()
        self.entry_info = self._get_video_entry_info(cfg_path)

    def _get_video_entry_info(self, entry_info_path):
        """
        返回entry.json配置信息
        """
        entry_info_file = os.path.join(entry_info_path, self.entry_file)
        with open(entry_info_file, "r") as fd:
            entry_info = json.load(fd)
        return entry_info

    @property
    def media_type(self):
        """
        视频类型
        值为2: m4s项目是bilibili存储的一些清晰度较高或较大较长的视频文件
        值为1: mediablv其实就是bilibili更改的FLV文件，你可以使用ffmpeg转换，也可以直接该拓展名为flv
        """
        return self.entry_info['media_type']

    @property
    def need_transmission(self):
        """
        是否需要做视频转换
        """
        return self.media_type == 2

    @property
    def type_tag(self):
        """
        视频文件所在目录
        """
        return self.entry_info['type_tag']

    @property
    def video_collection_name(self):
        """
        获取本视频集合名称
        """
        return self.entry_info['title']

    @property
    def video_title(self):
        """
        获取视频标题
        """
        part_title = self.entry_info.get("page_data", {}).get('part')
        return part_title if part_title else self.video_collection_name


class BilibiliVideoHelper(object):
    """
    新版APP下载下来视频格式变了，新版目录结构为：
    883741576 # 每个合集一个文件夹
        1 # 每个视频分集放到一个文件夹
            80
                音频视频资料分开了，可以使用 ffmpeg 把他们合成一个文件
                audio.m4s   # 音频资料
                video.m4s   # 视频资料
                index.json
            danmuku.xml
            entry.json
    """

    def __init__(self, curr_path):
        self.config = Config()
        self.curr_path = curr_path
        self.pool = multiprocessing.Pool(processes=4)

    def _make_video(self, video_path, new_video_dir, new_video_name):
        """
        把视频资料和音频资料合并成一个文件

        :param video_path 视频当前所在目录
        :param new_video_dir 新生成视频所存放目录
        :param new_video_neme 新生成视频名称
        """
        subprocess.check_output([
            "ffmpeg",
            "-i",
            os.path.join(video_path, self.config.def_video_name),
            "-i",
            os.path.join(video_path, self.config.def_audio_name),
            "-codec",
            "copy",
            os.path.join(
                new_video_dir, new_video_name +
                self.config.new_video_postfix)
        ])

    def _merge_blv_video(self, video_path, video_title):
        """
        把多个 blv 视频拼接在一起
        https://blog.csdn.net/winniezhang/article/details/89260841
        """
        blv_videos = "|".join([
            os.path.join(video_path, x)
            for x in os.listdir(video_path)
            if x.endswith(self.config.blv_postfix)
        ])
        subprocess.check_output([
            "ffmpeg",
            "-i",
            "concat:" + blv_videos,
            "-c",
            "copy",
            os.path.join(
                self.curr_path,
                video_title + self.config.new_video_postfix)
        ])

    def _get_video_folders(self, root_path):
        """
        如果当前目录下所有包含 entry.json 文件的目录，即视频信息所在目录
        """
        video_folders = list()
        for root, dirs, files in os.walk(root_path):
            if self.config.entry_file in files:
                # 如果当前目录下存在 entry.json 文件
                video_folders.append(root)
        return video_folders

    def mv_video_out(self, clean):
        """
        把视频移动到本专辑根目录下

        :param 是否删除旧文件
        """
        for video_item in self._get_video_folders(self.curr_path):
            # 各集内容所在文件夹
            video_dir = os.path.join(
                self.curr_path, video_item
            )

            entry_cfg = EntryConfig(video_dir)
            # 视频存放目录
            video_path = os.path.join(
                video_dir,
                entry_cfg.type_tag
            )

            print("===== video_path: [%s] =====" % video_path)
            print("===== video_tile: [%s] =====" % entry_cfg.video_title)
            print("========================\n")

            # 把合成的视频放到专辑目录下
            if entry_cfg.need_transmission:
                self._make_video(video_path,
                                 self.curr_path,
                                 entry_cfg.video_title)
            else:
                self._merge_blv_video(video_path, entry_cfg.video_title)

            # 删除目录
            if clean:
                shutil.rmtree(video_dir)


def usage(msg=None):
    # 输出重定向
    print("""
usage:
    python beautify_bilibili_folder.py /path/to/your/folder
    script will auto find the video and handler it.

    -p or --path=  path to your bilibili download folder
    -c or --clean= if clean old files.
""")
    if msg:
        print("error:\n\t%s." % msg)
    sys.exit(1)


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:p:", [
                                   "clean=", "path=", "help"])
    except Exception as ex:
        usage(ex)

    # if not opts:
        # usage()

    path = "."
    clean = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        if opt in ('-c', '--clean'):
            clean = arg
            continue
        if opt in ('-p', '--path'):
            path = arg
            continue
        else:
            usage()
    api = BilibiliVideoHelper(path)
    api.mv_video_out(clean)
