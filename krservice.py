# -*- coding:utf-8 -*-
"""
百度推广 关键词规划师相关逻辑
"""
import json
import time

import requests

username = ''
password = ''
token = ''
ESTIMATED_URL = 'https://api.baidu.com/json/sms/service/KRService/getEstimatedData'
WORD_EXPAND_URL = 'https://api.baidu.com/json/sms/service/KRService/getKRByQuery'


class KRQueryTypeEnum(EnumBase):
    """
    规划师查询类型
    """
    ESTIMATED = 1  # 根据出价查询关键词预估结果
    WORD_EXPAND = 2 # 获取种子词条件下的推荐词


def _build_kr_request_header():
    return {
        'username': username,
        'password': password,
        'token': token
    }


def build_estimated_query_body(word_list):
    """
    构造查询关键词预估结果的消息体
    """
    request_body = [{'word': word} for word in word_list]
    request_body = {
        'header': _build_kr_request_header(),
        'body': {
            'words': request_body,
            "seedFilter": {"maxNum": 1000}
        },

    }
    return request_body


def build_word_expand_body(query):
    """
    构造获取推荐词查询的消息体
    """
    request_body = {
        'header': _build_kr_request_header(),
        'body': {
            'query': query,
            'queryType': 1,
        },

    }
    return request_body


def estimated_result_parser(response_data):
    """
    关键词预估请求结果分析
    """
    return {
        word: {
            'pv': str(round(response_data[0]['mobile'][index]['pv'], 2)),
            'ad_price': response_data[0]['mobile'][index]['bid'],
        }
        for index, word in enumerate(response_data[0]['words'])
    }


def word_expand_result_parser(response_data):
    """
    获取推荐词请求结果分析
    """
    return {
        item['word']: {
            'pv': str(round(item['mobilePV'], 2)),
            'ad_price': item['recBid']
        }
        for item in response_data
    }


KR_SERVICE_CONFIG_MAP = {
    KRQueryTypeEnum.ESTIMATED: {
        'url': ESTIMATED_URL,
        'body_builder': build_estimated_query_body,
        'result_parser': estimated_result_parser,
    },
    KRQueryTypeEnum.WORD_EXPAND: {
        'url': WORD_EXPAND_URL,
        'body_builder': build_word_expand_body,
        'result_parser': word_expand_result_parser,
    }
}


def get_keyword_service_info_base(query_method, query_obj):
    """
    基础查询封装，封装重复代码
    """
    query_config = KR_SERVICE_CONFIG_MAP[query_method]
    url = query_config['url']
    build_func = query_config['body_builder']
    request_body = build_func(query_obj)
    result_parser = query_config['result_parser']

    # 发起查询
    retry_count = 0
    response = None
    while retry_count < 3:
        try:
            response = requests.post(url, data=json.dumps(request_body))
            break
        except:
            print('network error with [%s]' % url)
            retry_count += 1
            time.sleep(0.2)
            continue

    if not response:
        print('get_keyword_service_info_base failed with retry')
        return {}

    if response.status_code != 200:
        print('get_keyword_service_info_base failed with response[%s]' % response.status_code)
        return {}
    try:
        response_data = json.loads(response.content)
    except:
        return {}
    if 'header' not in response_data or 'body' not in response_data:
        print('wrong format return [%s]' % response_data)
        return {}
    if response_data['header']['desc'] != 'success':
        print('baidu api return error [%s]' % response_data)
        return {}
    data = response_data['body']['data']
    return result_parser(data)


def get_estimated_data_by_bid(word_list):
    """
    根据出价获取关键词预估结果 主要是拿搜索量
    :param word_list:
    :return:
    """
    return get_keyword_service_info_base(KRQueryTypeEnum.ESTIMATED, word_list)


def get_expand_words_by_query(query):
    """
    根据传入的种子词从规划师拿推荐词
    """
    return get_keyword_service_info_base(KRQueryTypeEnum.WORD_EXPAND, query)
