import requests
from urllib.parse import urlparse, urlunparse

FORMATTED_URL_BOOLEAN = 'bool' #格式化是否成功
FORMATTED_URL_DOMAIN = 'domain' #是否是跨域url 跨域True
FORMATTED_URL_ABSOLUTE = 'absolute' #绝对地址url
FORMATTED_URL_RELATIVE = 'relative' #相对地址url

def format(url_absolute, url):
    """
    此方法用于格式化url路径
    :param url_absolute:绝对路径
    :param url:需要格式化的路径
    :return : dict
    list = {url_format_bool:是否格式化成功,url_format_absolute:url格式化成绝对路径，url_format_relative:url格式化成最简相对路径}
    """
    # 格式化结果标记
    # print('url_absolute=%s,url=%s' % (url_absolute,url))
    format_bool = True
    url_abs_parse = urlparse(url_absolute)
    if not url_abs_parse.netloc:
        return {FORMATTED_URL_BOOLEAN: False, FORMATTED_URL_DOMAIN: False,
                FORMATTED_URL_ABSOLUTE: url_absolute, FORMATTED_URL_RELATIVE: url}
    url_parse = urlparse(url)
    url_abs_levels = url_abs_parse.path.split('/')
    url_levels = url_parse.path.split('/')
    url_abs_copy = url_abs_levels.copy()
    url_levels_copy1 = url_levels.copy()
    url_levels_copy2 = url_levels.copy()
    # url 为绝对路径
    if url_parse.netloc:
        # 域名不同，格式化失败
        if url_parse.netloc != url_abs_parse.netloc:
            return {FORMATTED_URL_BOOLEAN: True, FORMATTED_URL_DOMAIN: True,
                    FORMATTED_URL_ABSOLUTE: url, FORMATTED_URL_RELATIVE: url}
        # 从左至右判断是否存在相同级别名称，如有则删除
        for i, url_abs in enumerate(url_abs_levels):
            if len(url_levels) > i:
                url_rel = url_levels[i]
                if url_abs == url_rel:
                    url_abs_copy.remove(url_abs)
                    url_levels_copy2.remove(url_rel)
                else:
                    break
            else:
                break
        # 根据绝对路径剩余的层级数，添加相应的相对符号
        for i in enumerate(url_abs_copy):
            if i == 0:
                url_levels_copy2.insert(0, '.')
            elif i == 1:
                url_levels_copy2[0] = '..'
            else:
                url_levels_copy2.insert(0, '..')
        return format(url_absolute, '/'.join(url_levels_copy2))
    else:
        for i, url_level in enumerate(url_levels):
            # url相对根目录
            if url_level == '':
                if len(url_levels) == 1:
                    url_levels_copy1.clear()
                    url_levels_copy1.clear()
                else:
                    if url_level != url_levels[-1]:
                        url_abs_copy.clear()
                        url_levels_copy1 = url_levels[1:]
                        url_levels_copy2 = url_levels[1:]
                # 根据绝对路径剩余的层级数，添加相应的相对符号
                url_abs_copy2 = [i for i in url_abs_copy if i not in ['', '.', '..']]
                for i in range(len(url_abs_copy2)):
                    if i == 0:
                        url_levels_copy2.insert(0, '.')
                    elif i == 1:
                        url_levels_copy2[0] = '..'
                    else:
                        url_levels_copy2.insert(0, '..')
                break
            # url同级
            elif url_level == '.':
                if url_abs_copy:
                    url_abs_copy.pop()
                url_levels_copy1.remove(url_level)
            # url往上一级
            elif url_level == '..':
                if url_abs_copy:
                    url_abs_copy.pop()
                url_levels_copy1.remove(url_level)
                if i == 0:
                    if url_abs_copy:
                        url_abs_copy.pop()
            else:
                # url无层级符号，也就是同级
                if url_levels[0] not in ['', '.', '..']:
                    if url_abs_copy:
                        url_abs_copy.pop()
                # url和url_absolute存在层级重复
                elif url_level in url_abs_copy and url_level != url_levels[-1]:
                    url_abs_copy.remove(url_level)
                    url_levels_copy2.remove(url_level)
                else:
                    pass

        formatted_absolute = urlunparse([url_abs_parse.scheme, url_abs_parse.netloc,
                                         '/'.join(url_abs_copy + url_levels_copy1), '', '', ''])
        formatted_relative = urlunparse(['', '', '/'.join(url_levels_copy2), '', '', ''])
    formatted = {FORMATTED_URL_BOOLEAN: format_bool,
                 FORMATTED_URL_DOMAIN: False,
                 FORMATTED_URL_ABSOLUTE: formatted_absolute,
                 FORMATTED_URL_RELATIVE: formatted_relative}
    return formatted


def download(url, file_path):
    html = requests.get(url)
    with open(file_path, 'wb') as f:
        f.write(html.content)