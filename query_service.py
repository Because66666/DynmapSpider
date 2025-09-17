"""
SIMMC数据查询服务类
提供各种数据查询和统计功能
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from database import DatabaseManager


class QueryService:
    """数据查询服务类"""
    
    def __init__(self, db_path: str = "simmc_data.db"):
        """
        初始化查询服务
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_manager = DatabaseManager(db_path)
    
    def get_player_info(self, account: str) -> Optional[Dict[str, Any]]:
        """
        查询特定玩家的详细信息
        
        Args:
            account: 玩家账户名
            
        Returns:
            玩家信息字典，包含玩家基本信息、所在城市和国家信息
        """
        try:
            # 查询玩家基本信息
            players = self.db_manager.execute_query(
                "SELECT * FROM players WHERE account = ? ORDER BY update_time DESC LIMIT 1",
                (account,)
            )
            
            if not players:
                return None
            
            player = players[0]
            
            # 格式化玩家信息
            player_info = {
                'account': player['account'],
                'name': player['name'],
                'world': player['world'],
                'coordinates': {
                    'x': player['x'],
                    'y': player['y'],
                    'z': player['z']
                },
                'health': player['health'],
                'armor': player['armor'],
                'last_seen': datetime.fromtimestamp(player['update_time']).strftime('%Y-%m-%d %H:%M:%S'),
                'city_info': None,
                'country_info': None
            }
            
            # 查找玩家所在的城市
            cities = self.db_manager.execute_query(
                "SELECT * FROM cities WHERE city_players LIKE ?",
                (f'%{account}%',)
            )
            
            for city in cities:
                try:
                    city_players = json.loads(city['city_players'])
                    if account in city_players:
                        player_info['city_info'] = {
                            'city_name': city['city_name'],
                            'city_level': city['city_level'],
                            'city_owner': city['city_owner'],
                            'city_balance': city['city_balance'],
                            'city_block': city['city_block'],
                            'coordinates': {
                                'x': city['x'],
                                'y': city['y'],
                                'z': city['z']
                            }
                        }
                        
                        # 查找城市所属国家
                        if city['city_country']:
                            country = self.get_country_info(city['city_country'])
                            if country:
                                player_info['country_info'] = country
                        break
                except json.JSONDecodeError:
                    continue
            
            return player_info
            
        except Exception as e:
            print(f"查询玩家信息时出错: {e}")
            return None
    
    def get_city_info(self, city_name: str) -> Optional[Dict[str, Any]]:
        """
        查询特定城市的详细信息
        
        Args:
            city_name: 城市名称
            
        Returns:
            城市信息字典
        """
        try:
            cities = self.db_manager.execute_query(
                "SELECT * FROM cities WHERE city_name = ? ORDER BY update_time DESC LIMIT 1",
                (city_name,)
            )
            
            if not cities:
                return None
            
            city = cities[0]
            
            # 解析玩家列表
            city_players = []
            try:
                city_players = json.loads(city['city_players'])
            except json.JSONDecodeError:
                pass
            
            city_info = {
                'city_name': city['city_name'],
                'city_level': city['city_level'],
                'city_owner': city['city_owner'],
                'city_balance': city['city_balance'],
                'city_block': city['city_block'],
                'coordinates': {
                    'x': city['x'],
                    'y': city['y'],
                    'z': city['z']
                },
                'players': city_players,
                'player_count': len(city_players),
                'last_updated': datetime.fromtimestamp(city['update_time']).strftime('%Y-%m-%d %H:%M:%S'),
                'country_info': None
            }
            
            # 查找城市所属国家
            if city['city_country']:
                country = self.get_country_info(city['city_country'])
                if country:
                    city_info['country_info'] = country
            
            return city_info
            
        except Exception as e:
            print(f"查询城市信息时出错: {e}")
            return None
    
    def get_country_info(self, country_name: str) -> Optional[Dict[str, Any]]:
        """
        查询特定国家的详细信息
        
        Args:
            country_name: 国家名称
            
        Returns:
            国家信息字典
        """
        try:
            countries = self.db_manager.execute_query(
                "SELECT * FROM countries WHERE country_name = ? ORDER BY update_time DESC LIMIT 1",
                (country_name,)
            )
            
            if not countries:
                return None
            
            country = countries[0]
            
            # 解析领土列表
            territories = []
            try:
                territories = json.loads(country['territories'])
            except json.JSONDecodeError:
                pass
            
            country_info = {
                'country_name': country['country_name'],
                'country_level': country['country_level'],
                'country_capital': country['country_capital'],
                'territories': territories,
                'territory_count': country['territory_count'],
                'player_count': country['player_count'],
                'total_blocks': country['total_blocks'],
                'last_updated': datetime.fromtimestamp(country['update_time']).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return country_info
            
        except Exception as e:
            print(f"查询国家信息时出错: {e}")
            return None
    
    def get_city_area_ranking(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取城市区块面积排行榜
        
        Args:
            limit: 返回的城市数量
            
        Returns:
            城市排行榜列表
        """
        try:
            cities = self.db_manager.execute_query(
                """
                SELECT city_name, city_level, city_owner, city_block, city_country,
                       x, y, z, update_time
                FROM cities 
                WHERE city_block > 0
                ORDER BY city_block DESC 
                LIMIT ?
                """,
                (limit,)
            )
            
            ranking = []
            for i, city in enumerate(cities, 1):
                ranking.append({
                    'rank': i,
                    'city_name': city['city_name'],
                    'city_level': city['city_level'],
                    'city_owner': city['city_owner'],
                    'city_block': city['city_block'],
                    'city_country': city['city_country'],
                    'coordinates': {
                        'x': city['x'],
                        'y': city['y'],
                        'z': city['z']
                    },
                    'last_updated': datetime.fromtimestamp(city['update_time']).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return ranking
            
        except Exception as e:
            print(f"查询城市排行榜时出错: {e}")
            return []
    
    def get_country_territory_ranking(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取国家领土面积排行榜
        
        Args:
            limit: 返回的国家数量
            
        Returns:
            国家排行榜列表
        """
        try:
            countries = self.db_manager.execute_query(
                """
                SELECT country_name, country_level, country_capital, 
                       territory_count, player_count, total_blocks, update_time
                FROM countries 
                WHERE total_blocks > 0
                ORDER BY total_blocks DESC 
                LIMIT ?
                """,
                (limit,)
            )
            
            ranking = []
            for i, country in enumerate(countries, 1):
                ranking.append({
                    'rank': i,
                    'country_name': country['country_name'],
                    'country_level': country['country_level'],
                    'country_capital': country['country_capital'],
                    'territory_count': country['territory_count'],
                    'player_count': country['player_count'],
                    'total_blocks': country['total_blocks'],
                    'last_updated': datetime.fromtimestamp(country['update_time']).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return ranking
            
        except Exception as e:
            print(f"查询国家排行榜时出错: {e}")
            return []
    
    def search_players(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索玩家
        
        Args:
            keyword: 搜索关键词
            limit: 返回的结果数量
            
        Returns:
            匹配的玩家列表
        """
        try:
            players = self.db_manager.execute_query(
                """
                SELECT DISTINCT account, name, world, x, y, z, health, armor, update_time
                FROM players 
                WHERE account LIKE ? OR name LIKE ?
                ORDER BY update_time DESC 
                LIMIT ?
                """,
                (f'%{keyword}%', f'%{keyword}%', limit)
            )
            
            result = []
            for player in players:
                result.append({
                    'account': player['account'],
                    'name': player['name'],
                    'world': player['world'],
                    'coordinates': {
                        'x': player['x'],
                        'y': player['y'],
                        'z': player['z']
                    },
                    'health': player['health'],
                    'armor': player['armor'],
                    'last_seen': datetime.fromtimestamp(player['update_time']).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return result
            
        except Exception as e:
            print(f"搜索玩家时出错: {e}")
            return []
    
    def search_cities(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索城市
        
        Args:
            keyword: 搜索关键词
            limit: 返回的结果数量
            
        Returns:
            匹配的城市列表
        """
        try:
            cities = self.db_manager.execute_query(
                """
                SELECT city_name, city_level, city_owner, city_block, city_country,
                       x, y, z, update_time
                FROM cities 
                WHERE city_name LIKE ? OR city_owner LIKE ?
                ORDER BY city_block DESC 
                LIMIT ?
                """,
                (f'%{keyword}%', f'%{keyword}%', limit)
            )
            
            result = []
            for city in cities:
                result.append({
                    'city_name': city['city_name'],
                    'city_level': city['city_level'],
                    'city_owner': city['city_owner'],
                    'city_block': city['city_block'],
                    'city_country': city['city_country'],
                    'coordinates': {
                        'x': city['x'],
                        'y': city['y'],
                        'z': city['z']
                    },
                    'last_updated': datetime.fromtimestamp(city['update_time']).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return result
            
        except Exception as e:
            print(f"搜索城市时出错: {e}")
            return []
    
    def search_countries(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索国家
        
        Args:
            keyword: 搜索关键词
            limit: 返回的结果数量
            
        Returns:
            匹配的国家列表
        """
        try:
            countries = self.db_manager.execute_query(
                """
                SELECT country_name, country_level, country_capital, 
                       territory_count, player_count, total_blocks, update_time
                FROM countries 
                WHERE country_name LIKE ? OR country_capital LIKE ?
                ORDER BY total_blocks DESC 
                LIMIT ?
                """,
                (f'%{keyword}%', f'%{keyword}%', limit)
            )
            
            result = []
            for country in countries:
                result.append({
                    'country_name': country['country_name'],
                    'country_level': country['country_level'],
                    'country_capital': country['country_capital'],
                    'territory_count': country['territory_count'],
                    'player_count': country['player_count'],
                    'total_blocks': country['total_blocks'],
                    'last_updated': datetime.fromtimestamp(country['update_time']).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return result
            
        except Exception as e:
            print(f"搜索国家时出错: {e}")
            return []
    
    def get_online_players(self, hours: int = 1) -> List[Dict[str, Any]]:
        """
        获取最近在线的玩家
        
        Args:
            hours: 最近多少小时内在线
            
        Returns:
            最近在线的玩家列表
        """
        try:
            import time
            cutoff_time = int(time.time()) - (hours * 60 * 60)
            
            players = self.db_manager.execute_query(
                """
                SELECT DISTINCT account, name, world, x, y, z, health, armor, update_time
                FROM players 
                WHERE update_time >= ?
                ORDER BY update_time DESC
                """,
                (cutoff_time,)
            )
            
            result = []
            for player in players:
                result.append({
                    'account': player['account'],
                    'name': player['name'],
                    'world': player['world'],
                    'coordinates': {
                        'x': player['x'],
                        'y': player['y'],
                        'z': player['z']
                    },
                    'health': player['health'],
                    'armor': player['armor'],
                    'last_seen': datetime.fromtimestamp(player['update_time']).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return result
            
        except Exception as e:
            print(f"查询在线玩家时出错: {e}")
            return []
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        获取数据库统计摘要
        
        Returns:
            统计信息字典
        """
        try:
            # 玩家统计
            player_stats = self.db_manager.execute_query(
                """
                SELECT 
                    COUNT(DISTINCT account) as total_players,
                    COUNT(*) as total_records,
                    MAX(update_time) as latest_update
                FROM players
                """
            )[0]
            
            # 城市统计
            city_stats = self.db_manager.execute_query(
                """
                SELECT 
                    COUNT(*) as total_cities,
                    SUM(city_block) as total_blocks,
                    AVG(city_block) as avg_blocks_per_city,
                    MAX(city_block) as max_blocks
                FROM cities
                WHERE city_block > 0
                """
            )[0]
            
            # 国家统计
            country_stats = self.db_manager.execute_query(
                """
                SELECT 
                    COUNT(*) as total_countries,
                    SUM(territory_count) as total_territories,
                    SUM(player_count) as total_country_players,
                    AVG(territory_count) as avg_territories_per_country
                FROM countries
                """
            )[0]
            
            # 最活跃的城市
            top_city = self.db_manager.execute_query(
                "SELECT city_name, city_block FROM cities ORDER BY city_block DESC LIMIT 1"
            )
            
            # 最大的国家
            top_country = self.db_manager.execute_query(
                "SELECT country_name, total_blocks FROM countries ORDER BY total_blocks DESC LIMIT 1"
            )
            
            return {
                'players': {
                    'total_unique_players': player_stats['total_players'],
                    'total_records': player_stats['total_records'],
                    'latest_update': datetime.fromtimestamp(player_stats['latest_update']).strftime('%Y-%m-%d %H:%M:%S') if player_stats['latest_update'] else '无数据'
                },
                'cities': {
                    'total_cities': city_stats['total_cities'],
                    'total_blocks': city_stats['total_blocks'] or 0,
                    'average_blocks_per_city': round(city_stats['avg_blocks_per_city'] or 0, 2),
                    'largest_city': {
                        'name': top_city[0]['city_name'] if top_city else '无',
                        'blocks': top_city[0]['city_block'] if top_city else 0
                    }
                },
                'countries': {
                    'total_countries': country_stats['total_countries'],
                    'total_territories': country_stats['total_territories'] or 0,
                    'total_players_in_countries': country_stats['total_country_players'] or 0,
                    'average_territories_per_country': round(country_stats['avg_territories_per_country'] or 0, 2),
                    'largest_country': {
                        'name': top_country[0]['country_name'] if top_country else '无',
                        'blocks': top_country[0]['total_blocks'] if top_country else 0
                    }
                }
            }
            
        except Exception as e:
            print(f"获取统计摘要时出错: {e}")
            return {}
    
    def export_data(self, data_type: str, output_file: str) -> bool:
        """
        导出数据到JSON文件
        
        Args:
            data_type: 数据类型 ('players', 'cities', 'countries', 'all')
            output_file: 输出文件路径
            
        Returns:
            导出是否成功
        """
        try:
            export_data = {}
            
            if data_type in ['players', 'all']:
                players = self.db_manager.execute_query("SELECT * FROM players ORDER BY update_time DESC")
                export_data['players'] = players
            
            if data_type in ['cities', 'all']:
                cities = self.db_manager.execute_query("SELECT * FROM cities ORDER BY city_block DESC")
                export_data['cities'] = cities
            
            if data_type in ['countries', 'all']:
                countries = self.db_manager.execute_query("SELECT * FROM countries ORDER BY total_blocks DESC")
                export_data['countries'] = countries
            
            # 添加导出时间戳
            export_data['export_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            export_data['export_type'] = data_type
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"数据已导出到: {output_file}")
            return True
            
        except Exception as e:
            print(f"导出数据时出错: {e}")
            return False


class QueryHelper:
    """查询辅助类，提供便捷的查询方法"""
    
    def __init__(self, query_service: QueryService):
        self.query_service = query_service
    
    def quick_search(self, keyword: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        快速搜索，同时搜索玩家、城市和国家
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            包含所有搜索结果的字典
        """
        return {
            'players': self.query_service.search_players(keyword, 5),
            'cities': self.query_service.search_cities(keyword, 5),
            'countries': self.query_service.search_countries(keyword, 5)
        }
    
    def get_player_full_info(self, account: str) -> Optional[Dict[str, Any]]:
        """
        获取玩家完整信息，包括历史记录
        
        Args:
            account: 玩家账户名
            
        Returns:
            玩家完整信息
        """
        player_info = self.query_service.get_player_info(account)
        if not player_info:
            return None
        
        # 获取玩家历史位置记录
        history = self.query_service.db_manager.execute_query(
            """
            SELECT x, y, z, world, update_time 
            FROM players 
            WHERE account = ? 
            ORDER BY update_time DESC 
            LIMIT 10
            """,
            (account,)
        )
        
        player_info['location_history'] = [
            {
                'coordinates': {'x': h['x'], 'y': h['y'], 'z': h['z']},
                'world': h['world'],
                'time': datetime.fromtimestamp(h['update_time']).strftime('%Y-%m-%d %H:%M:%S')
            }
            for h in history
        ]
        
        return player_info
    
    def compare_cities(self, city1: str, city2: str) -> Optional[Dict[str, Any]]:
        """
        比较两个城市
        
        Args:
            city1: 第一个城市名称
            city2: 第二个城市名称
            
        Returns:
            城市比较结果
        """
        info1 = self.query_service.get_city_info(city1)
        info2 = self.query_service.get_city_info(city2)
        
        if not info1 or not info2:
            return None
        
        return {
            'city1': info1,
            'city2': info2,
            'comparison': {
                'block_difference': info1['city_block'] - info2['city_block'],
                'player_difference': info1['player_count'] - info2['player_count'],
                'larger_city': city1 if info1['city_block'] > info2['city_block'] else city2
            }
        }
    
    def get_country_cities(self, country_name: str) -> List[Dict[str, Any]]:
        """
        获取国家下的所有城市
        
        Args:
            country_name: 国家名称
            
        Returns:
            城市列表
        """
        try:
            cities = self.query_service.db_manager.execute_query(
                """
                SELECT city_name, city_level, city_owner, city_block, x, y, z
                FROM cities 
                WHERE city_country = ?
                ORDER BY city_block DESC
                """,
                (country_name,)
            )
            
            return [
                {
                    'city_name': city['city_name'],
                    'city_level': city['city_level'],
                    'city_owner': city['city_owner'],
                    'city_block': city['city_block'],
                    'coordinates': {
                        'x': city['x'],
                        'y': city['y'],
                        'z': city['z']
                    }
                }
                for city in cities
            ]
            
        except Exception as e:
            print(f"获取国家城市时出错: {e}")
            return []