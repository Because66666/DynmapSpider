"""
数据库模型类
用于定义和管理SQLite数据库中的玩家、城市、国家数据表
"""

import sqlite3
import time
from typing import List, Dict, Any, Optional


class DatabaseManager:
    """数据库管理器类，负责数据库连接和表的创建"""
    
    def __init__(self, db_path: str = "simmc_data.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        return conn
    
    def init_database(self):
        """初始化数据库，创建所有必要的表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建玩家数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    world TEXT NOT NULL,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    z REAL NOT NULL,
                    health REAL NOT NULL,
                    armor INTEGER NOT NULL,
                    sort INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    update_time INTEGER NOT NULL
                )
            ''')
            
            # 创建城市数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city_name TEXT UNIQUE NOT NULL,
                    label TEXT NOT NULL,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    z REAL NOT NULL,
                    city_level TEXT,
                    city_owner TEXT,
                    city_balance TEXT,
                    city_block INTEGER,
                    city_players TEXT,  -- JSON字符串存储玩家列表
                    city_country TEXT,
                    update_time INTEGER NOT NULL
                )
            ''')
            
            # 创建国家数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS countries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country_name TEXT UNIQUE NOT NULL,
                    country_level TEXT,
                    country_capital TEXT,
                    country_territory TEXT,  -- JSON字符串存储领土列表
                    territory_count INTEGER DEFAULT 0,
                    player_count INTEGER DEFAULT 0,
                    total_blocks INTEGER DEFAULT 0,
                    update_time INTEGER NOT NULL
                )
            ''')
            
            # 创建系统配置表，用于记录首次运行时间等系统信息
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT NOT NULL,
                    created_time INTEGER NOT NULL,
                    updated_time INTEGER NOT NULL
                )
            ''')
            
            conn.commit()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        执行更新语句
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            受影响的行数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def get_system_config(self, config_key: str) -> Optional[str]:
        """
        获取系统配置值
        
        Args:
            config_key: 配置键名
            
        Returns:
            配置值，如果不存在则返回None
        """
        result = self.execute_query(
            "SELECT config_value FROM system_config WHERE config_key = ?",
            (config_key,)
        )
        return result[0]['config_value'] if result else None
    
    def set_system_config(self, config_key: str, config_value: str) -> bool:
        """
        设置系统配置值
        
        Args:
            config_key: 配置键名
            config_value: 配置值
            
        Returns:
            操作是否成功
        """
        current_time = int(time.time())
        try:
            # 尝试更新现有配置
            rows_affected = self.execute_update(
                "UPDATE system_config SET config_value = ?, updated_time = ? WHERE config_key = ?",
                (config_value, current_time, config_key)
            )
            
            # 如果没有更新任何行，说明配置不存在，需要插入
            if rows_affected == 0:
                self.execute_update(
                    "INSERT INTO system_config (config_key, config_value, created_time, updated_time) VALUES (?, ?, ?, ?)",
                    (config_key, config_value, current_time, current_time)
                )
            
            return True
        except Exception as e:
            print(f"设置系统配置失败: {e}")
            return False


class PlayerModel:
    """玩家数据模型类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def insert_or_update_player(self, player_data: Dict[str, Any], update_time: int) -> bool:
        """
        插入或更新玩家数据
        
        Args:
            player_data: 玩家数据字典
            update_time: 更新时间戳
            
        Returns:
            操作是否成功
        """
        try:
            # 检查玩家是否已存在
            existing = self.db.execute_query(
                "SELECT id FROM players WHERE account = ?",
                (player_data['account'],)
            )
            
            if existing:
                # 更新现有玩家数据
                query = '''
                    UPDATE players SET 
                    name = ?, world = ?, x = ?, y = ?, z = ?, 
                    health = ?, armor = ?, sort = ?, type = ?, update_time = ?
                    WHERE account = ?
                '''
                params = (
                    player_data['name'], player_data['world'], player_data['x'],
                    player_data['y'], player_data['z'], player_data['health'],
                    player_data['armor'], player_data['sort'], player_data['type'],
                    update_time, player_data['account']
                )
            else:
                # 插入新玩家数据
                query = '''
                    INSERT INTO players 
                    (account, name, world, x, y, z, health, armor, sort, type, update_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                params = (
                    player_data['account'], player_data['name'], player_data['world'],
                    player_data['x'], player_data['y'], player_data['z'],
                    player_data['health'], player_data['armor'], player_data['sort'],
                    player_data['type'], update_time
                )
            
            self.db.execute_update(query, params)
            return True
        except Exception as e:
            print(f"插入或更新玩家数据失败: {e}")
            return False
    
    def get_player_by_account(self, account: str) -> Optional[sqlite3.Row]:
        """根据账户名获取玩家信息"""
        result = self.db.execute_query(
            "SELECT * FROM players WHERE account = ?",
            (account,)
        )
        return result[0] if result else None
    
    def get_inactive_players(self, current_time: int, days_threshold: int = 41) -> List[sqlite3.Row]:
        """
        获取非活跃玩家（超过指定天数未更新的玩家）
        新逻辑：根据城市表的city_owner查询玩家上一次数据更新时间，
        如果玩家不在表里，则采用spider首次运行时候的时间戳作为玩家上次数据更新时间
        
        Args:
            current_time: 当前时间戳
            days_threshold: 天数阈值
            
        Returns:
            非活跃玩家列表
        """
        time_threshold = current_time - (days_threshold * 24 * 60 * 60)
        
        # 获取首次运行时间戳，如果不存在则使用当前时间
        first_run_time_str = self.db.get_system_config('first_run_timestamp')
        first_run_time = int(first_run_time_str) if first_run_time_str else current_time
        
        # 查询所有在城市表中有记录的玩家及其最新更新时间
        # 对于不在城市表中的玩家，使用首次运行时间戳
        query = '''
        SELECT DISTINCT p.*, 
               COALESCE(MAX(c.update_time), ?) as last_activity_time
        FROM players p
        LEFT JOIN cities c ON p.account = c.city_owner
        GROUP BY p.account
        HAVING last_activity_time < ?
        '''
        
        return self.db.execute_query(query, (first_run_time, time_threshold))


class CityModel:
    """城市数据模型类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def insert_or_update_city(self, city_data: Dict[str, Any], update_time: int) -> bool:
        """
        插入或更新城市数据
        
        Args:
            city_data: 城市数据字典
            update_time: 更新时间戳
            
        Returns:
            操作是否成功
        """
        try:
            import json
            
            # 检查城市是否已存在
            existing = self.db.execute_query(
                "SELECT id FROM cities WHERE city_name = ?",
                (city_data['city_name'],)
            )
            
            # 将玩家列表转换为JSON字符串
            city_players_json = json.dumps(city_data.get('city_players', []), ensure_ascii=False)
            
            if existing:
                # 更新现有城市数据
                query = '''
                    UPDATE cities SET 
                    label = ?, x = ?, y = ?, z = ?, city_level = ?, city_owner = ?,
                    city_balance = ?, city_block = ?, city_players = ?, city_country = ?, update_time = ?
                    WHERE city_name = ?
                '''
                params = (
                    city_data['label'], city_data['x'], city_data['y'], city_data['z'],
                    city_data.get('city_level'), city_data.get('city_owner'),
                    city_data.get('city_balance'), city_data.get('city_block'),
                    city_players_json, city_data.get('city_country'), update_time,
                    city_data['city_name']
                )
            else:
                # 插入新城市数据
                query = '''
                    INSERT INTO cities 
                    (city_name, label, x, y, z, city_level, city_owner, city_balance, 
                     city_block, city_players, city_country, update_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                params = (
                    city_data['city_name'], city_data['label'], city_data['x'], city_data['y'],
                    city_data['z'], city_data.get('city_level'), city_data.get('city_owner'),
                    city_data.get('city_balance'), city_data.get('city_block'),
                    city_players_json, city_data.get('city_country'), update_time
                )
            
            self.db.execute_update(query, params)
            return True
        except Exception as e:
            print(f"插入或更新城市数据失败: {e}")
            return False
    
    def get_city_by_name(self, city_name: str) -> Optional[sqlite3.Row]:
        """根据城市名获取城市信息"""
        result = self.db.execute_query(
            "SELECT * FROM cities WHERE city_name = ?",
            (city_name,)
        )
        return result[0] if result else None
    
    def get_top_cities_by_blocks(self, limit: int = 5) -> List[sqlite3.Row]:
        """获取区块面积排行前N的城市"""
        return self.db.execute_query(
            "SELECT * FROM cities ORDER BY city_block DESC LIMIT ?",
            (limit,)
        )


class CountryModel:
    """国家数据模型类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def insert_or_update_country(self, country_data: Dict[str, Any], update_time: int) -> bool:
        """
        插入或更新国家数据
        
        Args:
            country_data: 国家数据字典
            update_time: 更新时间戳
            
        Returns:
            操作是否成功
        """
        try:
            import json
            
            # 检查国家是否已存在
            existing = self.db.execute_query(
                "SELECT id FROM countries WHERE country_name = ?",
                (country_data['country_name'],)
            )
            
            # 将领土列表转换为JSON字符串
            territory_json = json.dumps(country_data.get('country_territory', []), ensure_ascii=False)
            
            if existing:
                # 更新现有国家数据
                query = '''
                    UPDATE countries SET 
                    country_level = ?, country_capital = ?, country_territory = ?,
                    territory_count = ?, player_count = ?, total_blocks = ?, update_time = ?
                    WHERE country_name = ?
                '''
                params = (
                    country_data.get('country_level'), country_data.get('country_capital'),
                    territory_json, country_data.get('territory_count', 0),
                    country_data.get('player_count', 0), country_data.get('total_blocks', 0),
                    update_time, country_data['country_name']
                )
            else:
                # 插入新国家数据
                query = '''
                    INSERT INTO countries 
                    (country_name, country_level, country_capital, country_territory,
                     territory_count, player_count, total_blocks, update_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                '''
                params = (
                    country_data['country_name'], country_data.get('country_level'),
                    country_data.get('country_capital'), territory_json,
                    country_data.get('territory_count', 0), country_data.get('player_count', 0),
                    country_data.get('total_blocks', 0), update_time
                )
            
            self.db.execute_update(query, params)
            return True
        except Exception as e:
            print(f"插入或更新国家数据失败: {e}")
            return False
    
    def get_country_by_name(self, country_name: str) -> Optional[sqlite3.Row]:
        """根据国家名获取国家信息"""
        result = self.db.execute_query(
            "SELECT * FROM countries WHERE country_name = ?",
            (country_name,)
        )
        return result[0] if result else None
    
    def get_top_countries_by_territory(self, limit: int = 5) -> List[sqlite3.Row]:
        """获取领土面积排行前N的国家"""
        return self.db.execute_query(
            "SELECT * FROM countries ORDER BY total_blocks DESC LIMIT ?",
            (limit,)
        )
    
    def update_country_statistics(self):
        """更新所有国家的统计信息（领土数量、玩家数量、总区块数）"""
        try:
            import json
            
            # 获取所有国家
            countries = self.db.execute_query("SELECT * FROM countries")
            
            for country in countries:
                # 解析领土列表
                territory_list = json.loads(country['country_territory'])
                territory_count = len(territory_list)
                
                # 计算该国家的总区块数和玩家数
                total_blocks = 0
                total_players = set()
                
                for territory in territory_list:
                    city = self.db.execute_query(
                        "SELECT city_block, city_players FROM cities WHERE city_name = ?",
                        (territory,)
                    )
                    if city:
                        city_data = city[0]
                        if city_data['city_block']:
                            total_blocks += city_data['city_block']
                        
                        if city_data['city_players']:
                            city_players = json.loads(city_data['city_players'])
                            total_players.update(city_players)
                
                # 更新国家统计信息
                self.db.execute_update(
                    '''UPDATE countries SET 
                       territory_count = ?, player_count = ?, total_blocks = ?
                       WHERE country_name = ?''',
                    (territory_count, len(total_players), total_blocks, country['country_name'])
                )
                
        except Exception as e:
            print(f"更新国家统计信息失败: {e}")