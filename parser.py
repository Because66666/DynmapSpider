"""
数据解析器类
用于解析从SIMMC服务器获取的JSON数据和HTML描述信息
"""

import re
import json
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup


class DataParser:
    """数据解析器类，负责解析各种格式的数据"""
    
    @staticmethod
    def parse_player_data(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析玩家数据
        
        Args:
            json_data: 从API获取的JSON数据
            
        Returns:
            解析后的玩家数据列表
        """
        players = []
        
        if 'players' in json_data:
            for player in json_data['players']:
                # 确保所有必需字段都存在
                if all(key in player for key in ['account', 'name', 'world', 'x', 'y', 'z']):
                    players.append({
                        'account': player['account'],
                        'name': player['name'],
                        'world': player['world'],
                        'x': float(player['x']),
                        'y': float(player['y']),
                        'z': float(player['z']),
                        'health': float(player.get('health', 0)),
                        'armor': int(player.get('armor', 0)),
                        'sort': int(player.get('sort', 0)),
                        'type': player.get('type', 'player')
                    })
        
        return players
    
    @staticmethod
    def parse_city_data(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析城市数据
        
        Args:
            json_data: 从API获取的JSON数据
            
        Returns:
            解析后的城市数据列表
        """
        cities = []
        
        try:
            # 从sets中获取me.angeschossen.lands数据
            lands_data = json_data.get('sets', {}).get('me.angeschossen.lands', {})
            
            # 解析areas中的城市数据
            areas = lands_data.get('areas', {})
            markers = lands_data.get('markers', {})
            
            # 合并areas和markers数据
            all_city_data = {}
            all_city_data.update(areas)
            all_city_data.update(markers)
            
            for city_id, city_info in all_city_data.items():
                # 检查是否包含必要的字段
                if 'label' in city_info and 'desc' in city_info:
                    # 解析坐标
                    x = DataParser._get_coordinate(city_info.get('x', [0]))
                    y = city_info.get('y', city_info.get('ytop', 64))
                    z = DataParser._get_coordinate(city_info.get('z', [0]))
                    
                    # 解析描述信息
                    parsed_desc = DataParser.parse_city_description(city_info['desc'])
                    
                    # 跳过出生点
                    if parsed_desc.get('city_name') == '出生点':
                        continue
                    
                    city_data = {
                        'label': city_info['label'],
                        'x': x,
                        'y': y,
                        'z': z,
                        **parsed_desc
                    }
                    
                    cities.append(city_data)
                    
        except Exception as e:
            print(f"解析城市数据时出错: {e}")
        
        return cities
    
    @staticmethod
    def _get_coordinate(coord_data) -> float:
        """
        获取坐标值（如果是列表则取第一个值）
        
        Args:
            coord_data: 坐标数据（可能是数字或列表）
            
        Returns:
            坐标值
        """
        if isinstance(coord_data, list) and len(coord_data) > 0:
            return float(coord_data[0])
        elif isinstance(coord_data, (int, float)):
            return float(coord_data)
        else:
            return 0.0
    
    @staticmethod
    def parse_city_description(desc_html: str) -> Dict[str, Any]:
        """
        解析城市描述HTML
        
        Args:
            desc_html: HTML描述字符串
            
        Returns:
            解析后的城市信息字典
        """
        result = {
            'city_name': '',
            'city_level': '',
            'city_owner': '',
            'city_balance': '',
            'city_block': 0,
            'city_players': [],
            'city_country': '',
            'city_country_level': '',
            'city_country_capital': '',
            'city_country_territory': []
        }
        
        try:
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(desc_html, 'lxml')
            
            # 解析城市名称（从span标签中获取）
            city_name_span = soup.find('span', style=lambda x: x and 'font-size:200%' in x)
            if city_name_span:
                city_name_text = city_name_span.get_text(strip=True)
                result['city_name'] = city_name_text.replace('\n', '').replace('\r', '')
            
            # 解析城市基本信息
            li_elements = soup.find_all('li')
            for li in li_elements:
                text = li.get_text(strip=True)
                
                # 解析等级
                if text.startswith('等级:'):
                    result['city_level'] = text.replace('等级:', '').strip()
                
                # 解析余额
                elif text.startswith('余额:'):
                    result['city_balance'] = text.replace('余额:', '').strip()
                
                # 解析区块数
                elif text.startswith('区块:'):
                    try:
                        block_text = text.replace('区块:', '').strip()
                        result['city_block'] = int(block_text)
                    except ValueError:
                        result['city_block'] = 0
                
                # 解析玩家列表
                elif '玩家(' in text and '):' in text:
                    # 提取玩家列表
                    players_part = text.split('):')[1].strip()
                    if players_part:
                        players = [p.strip() for p in players_part.split(',')]
                        result['city_players'] = players
            if result['city_players'] == []:
                # 认为是出生点，之后有处理。
                pass
            # 解析所有者信息（从第一个div中获取）
            first_div = soup.find('div')
            if first_div:
                div_text = first_div.get_text()
                # 查找"所有者:"模式
                owner_match = re.search(r'所有者:\s*([^.]+)', div_text)
                if owner_match:
                    result['city_owner'] = owner_match.group(1).strip()
            # 如果没有所有者信息，则认为居住的第一个玩家为所有者
            if result['city_owner'] == '':
                result['city_owner'] = result['city_players'][0] if result['city_players'] else ''

            # 解析国家信息
            strong_elements = soup.find_all('strong')
            for strong in strong_elements:
                if '这片领土属于国家' in strong.get_text():
                    country_text = strong.get_text()
                    # 提取国家名称
                    country_match = re.search(r'这片领土属于国家([^:]+):', country_text)
                    if country_match:
                        result['city_country'] = country_match.group(1).strip()
                    
                    # 查找国家信息的ul元素
                    country_ul = strong.find_parent().find_next_sibling('ul')
                    if country_ul:
                        country_li_elements = country_ul.find_all('li')
                        for li in country_li_elements:
                            text = li.get_text(strip=True)
                            
                            # 解析国家等级
                            if text.startswith('等级:'):
                                result['city_country_level'] = text.replace('等级:', '').strip()
                            
                            # 解析首都
                            elif text.startswith('首都:'):
                                result['city_country_capital'] = text.replace('首都:', '').strip()
                            
                            # 解析领土列表
                            elif '领土(' in text and '):' in text:
                                territory_part = text.split('):')[1].strip()
                                if territory_part:
                                    territories = [t.strip() for t in territory_part.split(',')]
                                    result['city_country_territory'] = territories
                    break
                    
        except Exception as e:
            print(f"解析城市描述时出错: {e}")
        # if result['city_owner'] == '' and result['city_players'] == []:
        #     import os
        #     if os.path.exists('cache.txt'):
        #         mode = 'a'
        #     else:
        #         mode = 'w'
        #     with open('cache.txt',mode,encoding='utf-8') as f:
        #         f.write(desc_html)
        #         f.write(r'/n/n')
        return result
    
    @staticmethod
    def extract_country_data(cities_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从城市数据中提取国家数据
        
        Args:
            cities_data: 城市数据列表
            
        Returns:
            国家数据列表
        """
        countries = {}
        
        for city in cities_data:
            country_name = city.get('city_country')
            if country_name and country_name.strip():
                if country_name not in countries:
                    countries[country_name] = {
                        'country_name': country_name,
                        'country_level': city.get('city_country_level', ''),
                        'country_capital': city.get('city_country_capital', ''),
                        'country_territory': city.get('city_country_territory', []),
                        'territory_count': 0,
                        'player_count': 0,
                        'total_blocks': 0
                    }
                
                # 更新统计信息
                country_data = countries[country_name]
                if city.get('city_block'):
                    country_data['total_blocks'] += city['city_block']
                
                # 合并玩家列表（去重）
                city_players = city.get('city_players', [])
                if city_players:
                    existing_players = set()
                    for territory_city in cities_data:
                        if territory_city.get('city_country') == country_name:
                            existing_players.update(territory_city.get('city_players', []))
                    country_data['player_count'] = len(existing_players)
        
        return list(countries.values())


class HTMLCleaner:
    """HTML清理工具类"""
    
    @staticmethod
    def clean_html_text(html_text: str) -> str:
        """
        清理HTML文本，移除标签并格式化
        
        Args:
            html_text: 原始HTML文本
            
        Returns:
            清理后的文本
        """
        if not html_text:
            return ""
        
        # 使用BeautifulSoup移除HTML标签
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text()
        
        # 清理多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_text_between_tags(html_text: str, start_tag: str, end_tag: str) -> str:
        """
        提取指定标签之间的文本
        
        Args:
            html_text: HTML文本
            start_tag: 开始标签
            end_tag: 结束标签
            
        Returns:
            提取的文本
        """
        try:
            start_index = html_text.find(start_tag)
            if start_index == -1:
                return ""
            
            start_index += len(start_tag)
            end_index = html_text.find(end_tag, start_index)
            if end_index == -1:
                return ""
            
            return html_text[start_index:end_index].strip()
        except Exception:
            return ""


class ValidationHelper:
    """数据验证辅助类"""
    
    @staticmethod
    def validate_player_data(player_data: Dict[str, Any]) -> bool:
        """
        验证玩家数据的完整性
        
        Args:
            player_data: 玩家数据字典
            
        Returns:
            数据是否有效
        """
        required_fields = ['account', 'name', 'world', 'x', 'y', 'z']
        return all(field in player_data and player_data[field] is not None for field in required_fields)
    
    @staticmethod
    def validate_city_data(city_data: Dict[str, Any]) -> bool:
        """
        验证城市数据的完整性
        
        Args:
            city_data: 城市数据字典
            
        Returns:
            数据是否有效
        """
        required_fields = ['city_name', 'label', 'x', 'y', 'z']
        return all(field in city_data and city_data[field] is not None for field in required_fields)
    
    @staticmethod
    def validate_country_data(country_data: Dict[str, Any]) -> bool:
        """
        验证国家数据的完整性
        
        Args:
            country_data: 国家数据字典
            
        Returns:
            数据是否有效
        """
        return 'country_name' in country_data and country_data['country_name'] is not None