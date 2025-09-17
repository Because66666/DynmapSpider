"""
SIMMC服务器数据爬虫主程序
整合所有功能模块，提供完整的爬虫和查询功能
"""

import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Any

# 导入自定义模块
from spider import SIMMCSpider, SpiderConfig
from query_service import QueryService, QueryHelper
from database import DatabaseManager


class SIMMCCrawler:
    """SIMMC爬虫主类，整合所有功能"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        初始化爬虫系统
        
        Args:
            config_file: 配置文件路径
        """
        # 加载配置
        self.config = SpiderConfig()
        try:
            self.config.load_from_file(config_file)
            print(f"已加载配置文件: {config_file}")
        except:
            print(f"配置文件 {config_file} 不存在，使用默认配置")
            self.config.save_to_file(config_file)
            print(f"已创建默认配置文件: {config_file}")
        
        # 初始化组件
        self.spider = SIMMCSpider(self.config.db_path)
        self.query_service = QueryService(self.config.db_path)
        self.query_helper = QueryHelper(self.query_service)
        
        print(f"SIMMC爬虫系统初始化完成")
        print(f"数据库路径: {self.config.db_path}")
    
    def run_once(self) -> bool:
        """
        执行一次完整的数据获取和处理
        
        Returns:
            操作是否成功
        """
        print(f"\n{'='*60}")
        print(f"开始执行数据获取 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            # 执行数据获取和处理
            success = self.spider.process_and_store_data()
            
            if success:
                print("\n数据获取和处理完成！")
                
                # 显示统计信息
                stats = self.spider.get_statistics()
                print(f"\n当前数据库统计:")
                print(f"  玩家数量: {stats.get('player_count', 0)}")
                print(f"  城市数量: {stats.get('city_count', 0)}")
                print(f"  国家数量: {stats.get('country_count', 0)}")
                print(f"  最后更新: {stats.get('latest_update', '无数据')}")
                
                return True
            else:
                print("\n数据获取失败！")
                return False
                
        except Exception as e:
            print(f"\n执行过程中出错: {e}")
            return False
    
    def run_continuous(self, interval_minutes: int = None):
        """
        持续运行爬虫
        
        Args:
            interval_minutes: 间隔时间（分钟），如果为None则使用配置文件中的值
        """
        if interval_minutes is None:
            interval_minutes = self.config.interval_minutes
        
        print(f"开始持续运行模式，间隔时间: {interval_minutes} 分钟")
        print("按 Ctrl+C 停止运行")
        
        self.spider.run_continuous(interval_minutes)
    
    def query_player(self, account: str):
        """查询玩家信息"""
        print(f"\n正在查询玩家: {account}")
        
        player_info = self.query_helper.get_player_full_info(account)
        if not player_info:
            print(f"未找到玩家: {account}")
            return
        
        print(f"\n玩家信息:")
        print(f"  账户: {player_info['account']}")
        print(f"  名称: {player_info['name']}")
        print(f"  世界: {player_info['world']}")
        print(f"  坐标: ({player_info['coordinates']['x']}, {player_info['coordinates']['y']}, {player_info['coordinates']['z']})")
        print(f"  生命值: {player_info['health']}")
        print(f"  护甲: {player_info['armor']}")
        print(f"  最后在线: {player_info['last_seen']}")
        
        if player_info['city_info']:
            city = player_info['city_info']
            print(f"\n所在城市:")
            print(f"  城市名称: {city['city_name']}")
            print(f"  城市等级: {city['city_level']}")
            print(f"  城市所有者: {city['city_owner']}")
            print(f"  城市余额: {city['city_balance']}")
            print(f"  城市区块: {city['city_block']}")
            print(f"  城市坐标: ({city['coordinates']['x']}, {city['coordinates']['y']}, {city['coordinates']['z']})")
        
        if player_info['country_info']:
            country = player_info['country_info']
            print(f"\n所属国家:")
            print(f"  国家名称: {country['country_name']}")
            print(f"  国家等级: {country['country_level']}")
            print(f"  国家首都: {country['country_capital']}")
            print(f"  领土数量: {country['territory_count']}")
            print(f"  玩家数量: {country['player_count']}")
            print(f"  总区块数: {country['total_blocks']}")
        
        if 'location_history' in player_info and player_info['location_history']:
            print(f"\n最近位置记录:")
            for i, location in enumerate(player_info['location_history'][:5], 1):
                coords = location['coordinates']
                print(f"  {i}. ({coords['x']}, {coords['y']}, {coords['z']}) - {location['time']}")
    
    def query_city(self, city_name: str):
        """查询城市信息"""
        print(f"\n正在查询城市: {city_name}")
        
        city_info = self.query_service.get_city_info(city_name)
        if not city_info:
            print(f"未找到城市: {city_name}")
            return
        
        print(f"\n城市信息:")
        print(f"  城市名称: {city_info['city_name']}")
        print(f"  城市等级: {city_info['city_level']}")
        print(f"  城市所有者: {city_info['city_owner']}")
        print(f"  城市余额: {city_info['city_balance']}")
        print(f"  城市区块: {city_info['city_block']}")
        print(f"  城市坐标: ({city_info['coordinates']['x']}, {city_info['coordinates']['y']}, {city_info['coordinates']['z']})")
        print(f"  玩家数量: {city_info['player_count']}")
        print(f"  最后更新: {city_info['last_updated']}")
        
        if city_info['players']:
            print(f"\n城市玩家:")
            for i, player in enumerate(city_info['players'], 1):
                print(f"  {i}. {player}")
        
        if city_info['country_info']:
            country = city_info['country_info']
            print(f"\n所属国家:")
            print(f"  国家名称: {country['country_name']}")
            print(f"  国家等级: {country['country_level']}")
            print(f"  国家首都: {country['country_capital']}")
    
    def query_country(self, country_name: str):
        """查询国家信息"""
        print(f"\n正在查询国家: {country_name}")
        
        country_info = self.query_service.get_country_info(country_name)
        if not country_info:
            print(f"未找到国家: {country_name}")
            return
        
        print(f"\n国家信息:")
        print(f"  国家名称: {country_info['country_name']}")
        print(f"  国家等级: {country_info['country_level']}")
        print(f"  国家首都: {country_info['country_capital']}")
        print(f"  领土数量: {country_info['territory_count']}")
        print(f"  玩家数量: {country_info['player_count']}")
        print(f"  总区块数: {country_info['total_blocks']}")
        print(f"  最后更新: {country_info['last_updated']}")
        
        if country_info['territories']:
            print(f"\n国家领土:")
            for i, territory in enumerate(country_info['territories'], 1):
                print(f"  {i}. {territory}")
        
        # 显示国家下的城市
        cities = self.query_helper.get_country_cities(country_name)
        if cities:
            print(f"\n国家城市 (按区块数排序):")
            for i, city in enumerate(cities, 1):
                coords = city['coordinates']
                print(f"  {i}. {city['city_name']} - {city['city_block']} 区块 - 所有者: {city['city_owner']} - 坐标: ({coords['x']}, {coords['y']}, {coords['z']})")
    
    def show_rankings(self):
        """显示排行榜"""
        print(f"\n{'='*60}")
        print("SIMMC服务器排行榜")
        print(f"{'='*60}")
        
        # 城市区块排行榜
        print(f"\n🏙️ 城市区块面积排行榜 (前5名):")
        city_ranking = self.query_service.get_city_area_ranking(5)
        if city_ranking:
            for city in city_ranking:
                coords = city['coordinates']
                print(f"  {city['rank']}. {city['city_name']} - {city['city_block']} 区块")
                print(f"      等级: {city['city_level']} | 所有者: {city['city_owner']} | 国家: {city['city_country']}")
                print(f"      坐标: ({coords['x']}, {coords['y']}, {coords['z']}) | 更新: {city['last_updated']}")
        else:
            print("  暂无数据")
        
        # 国家领土排行榜
        print(f"\n🌍 国家领土面积排行榜 (前5名):")
        country_ranking = self.query_service.get_country_territory_ranking(5)
        if country_ranking:
            for country in country_ranking:
                print(f"  {country['rank']}. {country['country_name']} - {country['total_blocks']} 总区块")
                print(f"      等级: {country['country_level']} | 首都: {country['country_capital']}")
                print(f"      领土: {country['territory_count']} | 玩家: {country['player_count']} | 更新: {country['last_updated']}")
        else:
            print("  暂无数据")
    
    def search(self, keyword: str):
        """搜索功能"""
        print(f"\n正在搜索: {keyword}")
        
        results = self.query_helper.quick_search(keyword)
        
        # 显示玩家搜索结果
        if results['players']:
            print(f"\n👤 找到 {len(results['players'])} 个相关玩家:")
            for i, player in enumerate(results['players'], 1):
                coords = player['coordinates']
                print(f"  {i}. {player['account']} ({player['name']}) - 最后在线: {player['last_seen']}")
                print(f"      坐标: ({coords['x']}, {coords['y']}, {coords['z']}) | 世界: {player['world']}")
        
        # 显示城市搜索结果
        if results['cities']:
            print(f"\n🏙️ 找到 {len(results['cities'])} 个相关城市:")
            for i, city in enumerate(results['cities'], 1):
                coords = city['coordinates']
                print(f"  {i}. {city['city_name']} - {city['city_block']} 区块")
                print(f"      等级: {city['city_level']} | 所有者: {city['city_owner']} | 国家: {city['city_country']}")
                print(f"      坐标: ({coords['x']}, {coords['y']}, {coords['z']})")
        
        # 显示国家搜索结果
        if results['countries']:
            print(f"\n🌍 找到 {len(results['countries'])} 个相关国家:")
            for i, country in enumerate(results['countries'], 1):
                print(f"  {i}. {country['country_name']} - {country['total_blocks']} 总区块")
                print(f"      等级: {country['country_level']} | 首都: {country['country_capital']}")
                print(f"      领土: {country['territory_count']} | 玩家: {country['player_count']}")
        
        if not any(results.values()):
            print("  未找到相关结果")
    
    def show_statistics(self):
        """显示统计信息"""
        print(f"\n{'='*60}")
        print("SIMMC服务器数据统计")
        print(f"{'='*60}")
        
        stats = self.query_service.get_statistics_summary()
        if not stats:
            print("无法获取统计信息")
            return
        
        # 玩家统计
        player_stats = stats['players']
        print(f"\n👤 玩家统计:")
        print(f"  独立玩家数量: {player_stats['total_unique_players']}")
        print(f"  总记录数量: {player_stats['total_records']}")
        print(f"  最后更新时间: {player_stats['latest_update']}")
        
        # 城市统计
        city_stats = stats['cities']
        print(f"\n🏙️ 城市统计:")
        print(f"  城市总数: {city_stats['total_cities']}")
        print(f"  总区块数: {city_stats['total_blocks']}")
        print(f"  平均区块数: {city_stats['average_blocks_per_city']}")
        print(f"  最大城市: {city_stats['largest_city']['name']} ({city_stats['largest_city']['blocks']} 区块)")
        
        # 国家统计
        country_stats = stats['countries']
        print(f"\n🌍 国家统计:")
        print(f"  国家总数: {country_stats['total_countries']}")
        print(f"  总领土数: {country_stats['total_territories']}")
        print(f"  国家总玩家数: {country_stats['total_players_in_countries']}")
        print(f"  平均领土数: {country_stats['average_territories_per_country']}")
        print(f"  最大国家: {country_stats['largest_country']['name']} ({country_stats['largest_country']['blocks']} 区块)")
    
    def show_online_players(self, hours: int = 1):
        """显示最近在线玩家"""
        print(f"\n最近 {hours} 小时内在线的玩家:")
        
        players = self.query_service.get_online_players(hours)
        if players:
            for i, player in enumerate(players, 1):
                coords = player['coordinates']
                print(f"  {i}. {player['account']} ({player['name']}) - {player['last_seen']}")
                print(f"      坐标: ({coords['x']}, {coords['y']}, {coords['z']}) | 世界: {player['world']}")
        else:
            print(f"  最近 {hours} 小时内没有玩家在线")
    
    def export_data(self, data_type: str = "all", output_file: str = None):
        """导出数据"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"simmc_data_{data_type}_{timestamp}.json"
        
        print(f"\n正在导出 {data_type} 数据到 {output_file}...")
        
        success = self.query_service.export_data(data_type, output_file)
        if success:
            print(f"数据导出成功: {output_file}")
        else:
            print("数据导出失败")
    
    def interactive_mode(self):
        """交互模式"""
        print(f"\n{'='*60}")
        print("SIMMC爬虫系统 - 交互模式")
        print(f"{'='*60}")
        print("可用命令:")
        print("  1. run - 执行一次数据获取")
        print("  2. continuous [间隔分钟] - 持续运行模式")
        print("  3. player <账户名> - 查询玩家信息")
        print("  4. city <城市名> - 查询城市信息")
        print("  5. country <国家名> - 查询国家信息")
        print("  6. search <关键词> - 搜索玩家/城市/国家")
        print("  7. rankings - 显示排行榜")
        print("  8. stats - 显示统计信息")
        print("  9. online [小时数] - 显示最近在线玩家")
        print("  10. export [类型] [文件名] - 导出数据")
        print("  11. help - 显示帮助")
        print("  12. quit - 退出程序")
        print()
        
        while True:
            try:
                command = input("请输入命令: ").strip().split()
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd == 'quit' or cmd == 'exit':
                    print("再见！")
                    break
                elif cmd == 'help':
                    print("\n可用命令:")
                    print("  run, continuous, player, city, country, search, rankings, stats, online, export, help, quit")
                elif cmd == 'run':
                    self.run_once()
                elif cmd == 'continuous':
                    interval = int(command[1]) if len(command) > 1 else None
                    self.run_continuous(interval)
                elif cmd == 'player':
                    if len(command) > 1:
                        self.query_player(command[1])
                    else:
                        print("请提供玩家账户名")
                elif cmd == 'city':
                    if len(command) > 1:
                        self.query_city(' '.join(command[1:]))
                    else:
                        print("请提供城市名称")
                elif cmd == 'country':
                    if len(command) > 1:
                        self.query_country(' '.join(command[1:]))
                    else:
                        print("请提供国家名称")
                elif cmd == 'search':
                    if len(command) > 1:
                        self.search(' '.join(command[1:]))
                    else:
                        print("请提供搜索关键词")
                elif cmd == 'rankings':
                    self.show_rankings()
                elif cmd == 'stats':
                    self.show_statistics()
                elif cmd == 'online':
                    hours = int(command[1]) if len(command) > 1 else 1
                    self.show_online_players(hours)
                elif cmd == 'export':
                    data_type = command[1] if len(command) > 1 else "all"
                    output_file = command[2] if len(command) > 2 else None
                    self.export_data(data_type, output_file)
                else:
                    print(f"未知命令: {cmd}，输入 'help' 查看可用命令")
                    
            except KeyboardInterrupt:
                print("\n\n收到中断信号，退出程序")
                break
            except Exception as e:
                print(f"执行命令时出错: {e}")


def main():
    """主函数"""
    print("SIMMC服务器数据爬虫系统")
    print("=" * 60)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        # 初始化爬虫系统
        crawler = SIMMCCrawler()
        
        if command == 'run':
            # 执行一次数据获取
            crawler.run_once()
        elif command == 'continuous':
            # 持续运行模式
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else None
            crawler.run_continuous(interval)
        elif command == 'interactive':
            # 交互模式
            crawler.interactive_mode()
        elif command == 'stats':
            # 显示统计信息
            crawler.show_statistics()
        elif command == 'rankings':
            # 显示排行榜
            crawler.show_rankings()
        elif command == 'player' and len(sys.argv) > 2:
            # 查询玩家
            crawler.query_player(sys.argv[2])
        elif command == 'city' and len(sys.argv) > 2:
            # 查询城市
            crawler.query_city(' '.join(sys.argv[2:]))
        elif command == 'country' and len(sys.argv) > 2:
            # 查询国家
            crawler.query_country(' '.join(sys.argv[2:]))
        elif command == 'search' and len(sys.argv) > 2:
            # 搜索
            crawler.search(' '.join(sys.argv[2:]))
        elif command == 'export':
            # 导出数据
            data_type = sys.argv[2] if len(sys.argv) > 2 else "all"
            output_file = sys.argv[3] if len(sys.argv) > 3 else None
            crawler.export_data(data_type, output_file)
        else:
            print("使用方法:")
            print("  python main.py run                    - 执行一次数据获取")
            print("  python main.py continuous [间隔分钟]   - 持续运行模式")
            print("  python main.py interactive            - 交互模式")
            print("  python main.py stats                  - 显示统计信息")
            print("  python main.py rankings               - 显示排行榜")
            print("  python main.py player <账户名>        - 查询玩家信息")
            print("  python main.py city <城市名>          - 查询城市信息")
            print("  python main.py country <国家名>       - 查询国家信息")
            print("  python main.py search <关键词>        - 搜索功能")
            print("  python main.py export [类型] [文件名] - 导出数据")
    else:
        # 默认进入交互模式
        crawler = SIMMCCrawler()
        crawler.interactive_mode()


if __name__ == "__main__":
    main()