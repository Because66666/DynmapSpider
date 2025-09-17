"""
SIMMC爬虫核心类
负责从SIMMC服务器获取数据并进行处理存储
"""

import requests
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from report import report_information
from database import DatabaseManager, PlayerModel, CityModel, CountryModel
from parser import DataParser, ValidationHelper


class SIMMCSpider:
    """SIMMC服务器数据爬虫类"""
    
    def __init__(self, db_path: str = "simmc_data.db"):
        """
        初始化爬虫
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_manager = DatabaseManager(db_path)
        self.player_model = PlayerModel(self.db_manager)
        self.city_model = CityModel(self.db_manager)
        self.country_model = CountryModel(self.db_manager)
        self.parser = DataParser()
        
        # 记录首次运行时间戳（如果还没有记录的话）
        self._record_first_run_timestamp()
        
        # API端点
        self.player_api_url = "https://map.simmc.cn/standalone/dynmap_world.json"
        self.city_api_url = "https://map.simmc.cn/tiles/_markers_/marker_world.json"
        
        # 请求配置
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 30
        self.retry_count = 3
        self.retry_delay = 5
    
    def _record_first_run_timestamp(self):
        """
        记录首次运行时间戳
        如果系统配置中还没有首次运行时间戳，则记录当前时间
        """
        first_run_time = self.db_manager.get_system_config('first_run_timestamp')
        if first_run_time is None:
            current_time = int(time.time())
            success = self.db_manager.set_system_config('first_run_timestamp', str(current_time))
            if success:
                print(f"记录首次运行时间戳: {current_time} ({datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')})")
            else:
                print("记录首次运行时间戳失败")
        else:
            timestamp = int(first_run_time)
            print(f"系统首次运行时间: {datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
    
    def fetch_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        从指定URL获取JSON数据
        
        Args:
            url: API端点URL
            
        Returns:
            解析后的JSON数据，失败时返回None
        """
        for attempt in range(self.retry_count):
            try:
                print(f"正在获取数据: {url} (尝试 {attempt + 1}/{self.retry_count})")
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # 检查响应内容类型
                content_type = response.headers.get('content-type', '')
                if 'application/json' not in content_type and 'text/json' not in content_type:
                    print(f"警告: 响应内容类型不是JSON: {content_type}")
                
                data = response.json()
                print(f"成功获取数据，大小: {len(response.content)} 字节")
                return data
                
            except requests.exceptions.RequestException as e:
                print(f"请求失败 (尝试 {attempt + 1}/{self.retry_count}): {e}")
                if attempt < self.retry_count - 1:
                    print(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                break
            except Exception as e:
                print(f"未知错误: {e}")
                break
        
        print(f"获取数据失败: {url}")
        return None
    
    def fetch_player_data(self) -> List[Dict[str, Any]]:
        """
        获取在线玩家数据
        
        Returns:
            玩家数据列表
        """
        print("开始获取玩家数据...")
        
        data = self.fetch_data(self.player_api_url)
        if not data:
            print("获取玩家数据失败")
            return []
        
        players = self.parser.parse_player_data(data)
        print(f"成功解析 {len(players)} 个玩家数据")
        
        # 验证数据
        valid_players = []
        for player in players:
            if ValidationHelper.validate_player_data(player):
                valid_players.append(player)
            else:
                print(f"无效的玩家数据: {player}")
        
        print(f"有效玩家数据: {len(valid_players)} 个")
        return valid_players
    
    def fetch_city_data(self) -> List[Dict[str, Any]]:
        """
        获取城市数据
        
        Returns:
            城市数据列表
        """
        print("开始获取城市数据...")
        
        data = self.fetch_data(self.city_api_url)
        if not data:
            print("获取城市数据失败")
            return []
        
        cities = self.parser.parse_city_data(data)
        print(f"成功解析 {len(cities)} 个城市数据")
        
        # 验证数据
        valid_cities = []
        for city in cities:
            if ValidationHelper.validate_city_data(city):
                valid_cities.append(city)
            else:
                print(f"无效的城市数据: {city.get('city_name', 'Unknown')}")
        
        print(f"有效城市数据: {len(valid_cities)} 个")
        return valid_cities
    
    def process_and_store_data(self) -> bool:
        """
        获取、处理并存储所有数据
        
        Returns:
            操作是否成功
        """
        try:
            current_time = int(time.time())
            print(f"开始数据处理，当前时间戳: {current_time}")
            
            # 获取玩家数据
            players = self.fetch_player_data()
            if not players:
                print("没有获取到玩家数据")
                return False
            
            # 获取城市数据
            cities = self.fetch_city_data()
            if not cities:
                print("没有获取到城市数据")
                return False
            
            # 提取国家数据
            countries = self.parser.extract_country_data(cities)
            print(f"提取到 {len(countries)} 个国家数据")
            
            # 存储玩家数据
            print("正在存储玩家数据...")
            player_success_count = 0
            for player in players:
                if self.player_model.insert_or_update_player(player, current_time):
                    player_success_count += 1
            print(f"成功存储 {player_success_count}/{len(players)} 个玩家数据")
            
            # 存储城市数据
            print("正在存储城市数据...")
            city_success_count = 0
            for city in cities:
                if self.city_model.insert_or_update_city(city, current_time):
                    city_success_count += 1
            print(f"成功存储 {city_success_count}/{len(cities)} 个城市数据")
            
            # 存储国家数据
            print("正在存储国家数据...")
            country_success_count = 0
            for country in countries:
                if self.country_model.insert_or_update_country(country, current_time):
                    country_success_count += 1
            print(f"成功存储 {country_success_count}/{len(countries)} 个国家数据")
            
            # 更新国家统计信息
            print("正在更新国家统计信息...")
            self.country_model.update_country_statistics()
            
            # 检查非活跃玩家
            self.check_inactive_players(current_time)
            
            print("数据处理完成")
            return True
            
        except Exception as e:
            print(f"数据处理过程中出错: {e}")
            return False
    
    def check_inactive_players(self, current_time: int):
        """
        检查并报告非活跃玩家
        
        Args:
            current_time: 当前时间戳
        """
        print("正在检查非活跃玩家...")
        
        try:
            # 检查41-42天未活跃的玩家
            inactive_players_41 = self.player_model.get_inactive_players(current_time, 41)
            inactive_players_42 = self.player_model.get_inactive_players(current_time, 42)
            
            # 找出在41-42天范围内的玩家
            players_41_42_days = []
            for player in inactive_players_41:
                days_inactive = (current_time - player['update_time']) / (24 * 60 * 60)
                if 41 <= days_inactive < 42:
                    players_41_42_days.append(player)
            
            # 找出超过42天的玩家
            players_over_42_days = []
            for player in inactive_players_42:
                days_inactive = (current_time - player['update_time']) / (24 * 60 * 60)
                if days_inactive >= 42:
                    players_over_42_days.append(player)
            
            # 报告结果
            if players_41_42_days:
                print(f"\n发现 {len(players_41_42_days)} 个玩家离线41-42天:")
                report_information(f"\n发现 {len(players_41_42_days)} 个玩家离线41-42天:")
                for player in players_41_42_days:
                    self._print_player_info(player, current_time)
            
            if players_over_42_days:
                print(f"\n发现 {len(players_over_42_days)} 个玩家离线超过42天:")
                report_information(f"\n发现 {len(players_over_42_days)} 个玩家离线超过42天:")
                for player in players_over_42_days:
                    self._print_player_info(player, current_time)
            
            if not players_41_42_days and not players_over_42_days:
                print("没有发现长期非活跃玩家")
                
        except Exception as e:
            print(f"检查非活跃玩家时出错: {e}")
    
    def _print_player_info(self, player, current_time: int):
        """
        打印玩家详细信息
        
        Args:
            player: 玩家数据
            current_time: 当前时间戳
        """
        try:
            days_inactive = (current_time - player['update_time']) / (24 * 60 * 60)
            last_seen = datetime.fromtimestamp(player['update_time']).strftime('%Y-%m-%d %H:%M:%S')
            
            # 构建基本玩家信息
            player_info = f"""
玩家信息:
  账户: {player['account']}
  名称: {player['name']}
  世界: {player['world']}
  坐标: ({player['x']}, {player['y']}, {player['z']})
  生命值: {player['health']}
  护甲: {player['armor']}
  最后在线: {last_seen}
  离线天数: {days_inactive:.1f} 天"""
            
            # 查找玩家所在的城市
            cities = self.db_manager.execute_query(
                "SELECT * FROM cities WHERE city_players LIKE ?",
                (f'%{player["account"]}%',)
            )
            
            city_info = ""
            if cities:
                for city in cities:
                    import json
                    try:
                        city_players = json.loads(city['city_players'])
                        if player['account'] in city_players:
                            city_info = f"""
  所在城市: {city['city_name']}
    城市等级: {city['city_level']}
    城市所有者: {city['city_owner']}
    城市区块: {city['city_block']}"""
                            
                            # 查找城市所属国家
                            if city['city_country']:
                                country = self.country_model.get_country_by_name(city['city_country'])
                                if country:
                                    city_info += f"""
    所属国家: {country['country_name']}
    国家等级: {country['country_level']}
    国家首都: {country['country_capital']}
    国家领土数: {country['territory_count']}"""
                            break
                    except json.JSONDecodeError:
                        continue
            
            if not city_info:
                city_info = "\n  所在城市: 无"
            
            # 一次性打印完整信息
            print(player_info + city_info)
            report_information(player_info + city_info)

        except Exception as e:
            print(f"打印玩家信息时出错: {e}")
            report_information(f"打印玩家信息时出错: {e}")
    
    def run_continuous(self, interval_minutes: int = 30):
        """
        持续运行爬虫，定期获取数据
        
        Args:
            interval_minutes: 获取数据的间隔时间（分钟）
        """
        print(f"开始持续运行爬虫，间隔时间: {interval_minutes} 分钟")
        
        while True:
            try:
                print(f"\n{'='*50}")
                print(f"开始新一轮数据获取 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*50}")
                
                success = self.process_and_store_data()
                
                if success:
                    print("本轮数据获取成功")
                else:
                    print("本轮数据获取失败")
                
                print(f"等待 {interval_minutes} 分钟后进行下一轮获取...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n收到中断信号，停止爬虫")
                break
            except Exception as e:
                print(f"运行过程中出错: {e}")
                print(f"等待 {interval_minutes} 分钟后重试...")
                time.sleep(interval_minutes * 60)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 获取玩家统计
            player_count = self.db_manager.execute_query("SELECT COUNT(*) as count FROM players")[0]['count']
            
            # 获取城市统计
            city_count = self.db_manager.execute_query("SELECT COUNT(*) as count FROM cities")[0]['count']
            
            # 获取国家统计
            country_count = self.db_manager.execute_query("SELECT COUNT(*) as count FROM countries")[0]['count']
            
            # 获取最新更新时间
            latest_update = self.db_manager.execute_query(
                "SELECT MAX(update_time) as latest FROM players"
            )[0]['latest']
            
            latest_update_str = "无数据"
            if latest_update:
                latest_update_str = datetime.fromtimestamp(latest_update).strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'player_count': player_count,
                'city_count': city_count,
                'country_count': country_count,
                'latest_update': latest_update_str,
                'database_path': self.db_manager.db_path
            }
            
        except Exception as e:
            print(f"获取统计信息时出错: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        清理旧数据
        
        Args:
            days_to_keep: 保留数据的天数
        """
        try:
            cutoff_time = int(time.time()) - (days_to_keep * 24 * 60 * 60)
            
            # 删除旧的玩家数据
            deleted_players = self.db_manager.execute_update(
                "DELETE FROM players WHERE update_time < ?",
                (cutoff_time,)
            )
            
            print(f"清理了 {deleted_players} 条超过 {days_to_keep} 天的玩家数据")
            
        except Exception as e:
            print(f"清理旧数据时出错: {e}")


class SpiderConfig:
    """爬虫配置类"""
    
    def __init__(self):
        self.db_path = "simmc_data.db"
        self.timeout = 30
        self.retry_count = 3
        self.retry_delay = 5
        self.interval_minutes = 30
        
        # API端点
        self.player_api_url = "https://map.simmc.cn/standalone/dynmap_world.json"
        self.city_api_url = "https://map.simmc.cn/tiles/_markers_/marker_world.json"
    
    def load_from_file(self, config_file: str):
        """从配置文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            for key, value in config_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    
    def save_to_file(self, config_file: str):
        """保存配置到文件"""
        try:
            config_data = {
                'db_path': self.db_path,
                'timeout': self.timeout,
                'retry_count': self.retry_count,
                'retry_delay': self.retry_delay,
                'interval_minutes': self.interval_minutes,
                'player_api_url': self.player_api_url,
                'city_api_url': self.city_api_url
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存配置文件失败: {e}")