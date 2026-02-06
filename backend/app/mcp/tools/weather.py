"""
MCP 工具集合 - 天气查询
"""
from typing import Dict, Any, List
import httpx
from datetime import datetime

from app.mcp.base import MCPTool, MCPToolParameter


class WeatherTool(MCPTool):
    """天气查询工具"""
    
    @property
    def name(self) -> str:
        return "get_weather"
    
    @property
    def description(self) -> str:
        return "查询指定城市的实时天气信息，包括温度、湿度、风速等"
    
    @property
    def parameters(self) -> List[MCPToolParameter]:
        return [
            MCPToolParameter(
                name="city",
                type="string",
                description="城市名称，例如：北京、上海、深圳",
                required=True
            ),
            MCPToolParameter(
                name="unit",
                type="string",
                description="温度单位，celsius(摄氏度)或fahrenheit(华氏度)",
                required=False,
                default="celsius"
            )
        ]
    
    async def execute(self, city: str, unit: str = "celsius") -> Dict[str, Any]:
        """
        执行天气查询
        
        注意：这是一个示例实现，使用模拟数据
        实际部署时应接入真实的天气API（如高德地图、和风天气等）
        """
        # 模拟天气数据
        mock_weather_data = {
            "北京": {"temp": 15, "humidity": 45, "wind_speed": 12, "condition": "晴"},
            "上海": {"temp": 20, "humidity": 65, "wind_speed": 8, "condition": "多云"},
            "深圳": {"temp": 28, "humidity": 75, "wind_speed": 6, "condition": "阴"},
            "广州": {"temp": 26, "humidity": 70, "wind_speed": 5, "condition": "小雨"},
            "杭州": {"temp": 18, "humidity": 55, "wind_speed": 10, "condition": "晴"}
        }
        
        # 查找城市数据
        weather = mock_weather_data.get(city)
        
        if weather is None:
            # 如果没有数据，返回默认值
            weather = {
                "temp": 20,
                "humidity": 60,
                "wind_speed": 8,
                "condition": "未知"
            }
        
        # 温度单位转换
        temp = weather["temp"]
        if unit == "fahrenheit":
            temp = temp * 9 / 5 + 32
            temp_unit = "°F"
        else:
            temp_unit = "°C"
        
        return {
            "city": city,
            "temperature": f"{temp:.1f}{temp_unit}",
            "humidity": f"{weather['humidity']}%",
            "wind_speed": f"{weather['wind_speed']} km/h",
            "condition": weather["condition"],
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "模拟数据"
        }


# 实际生产环境中接入真实API的示例
class RealWeatherTool(MCPTool):
    """真实天气查询工具（接入高德地图API示例）"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
    
    @property
    def name(self) -> str:
        return "get_real_weather"
    
    @property
    def description(self) -> str:
        return "查询真实天气信息（高德地图API）"
    
    @property
    def parameters(self) -> List[MCPToolParameter]:
        return [
            MCPToolParameter(
                name="city",
                type="string",
                description="城市名称或城市编码",
                required=True
            )
        ]
    
    async def execute(self, city: str) -> Dict[str, Any]:
        """执行真实天气查询"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.base_url,
                    params={
                        "city": city,
                        "key": self.api_key,
                        "extensions": "base"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "1" and data.get("lives"):
                    live = data["lives"][0]
                    return {
                        "city": live.get("city"),
                        "temperature": f"{live.get('temperature')}°C",
                        "humidity": f"{live.get('humidity')}%",
                        "wind_direction": live.get("winddirection"),
                        "wind_power": live.get("windpower"),
                        "condition": live.get("weather"),
                        "update_time": live.get("reporttime"),
                        "source": "高德地图"
                    }
                else:
                    raise Exception(f"天气查询失败: {data.get('info', '未知错误')}")
                    
            except httpx.RequestError as e:
                raise Exception(f"网络请求失败: {str(e)}")
