import asyncio
import json
import websockets
from typing import List, Optional, Callable
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_field(data: dict, *keys, default=0):
    """DEFAULT/SIMPLE 응답 필드명을 모두 지원해서 값을 가져옵니다."""
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return default


class UpbitWebSocketClient:
    """업비트 WebSocket 클라이언트"""
    
    # WebSocket 주소
    WEBSOCKET_URL = "wss://api.upbit.com/websocket/v1"
    
    def __init__(self):
        self.websocket = None
        self.is_connected = False
        self.ticker_id = None
        
    async def connect(self):
        """WebSocket 연결"""
        try:
            self.websocket = await websockets.connect(self.WEBSOCKET_URL)
            self.is_connected = True
            logger.info("✅ WebSocket 연결 성공")
            return True
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {e}")
            return False
    
    async def disconnect(self):
        """WebSocket 연결 해제"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("📴 WebSocket 연결 해제")
    
    async def subscribe_ticker(self, codes: List[str], format: str = "DEFAULT"):
        """
        Ticker(현재가) 구독
        
        Args:
            codes: 구독할 마켓 코드 리스트 (예: ["KRW-BTC", "KRW-ETH"])
            format: 응답 형식 ("DEFAULT" 또는 "SIMPLE_LIST")
        """
        if not self.is_connected:
            logger.error("❌ WebSocket이 연결되지 않았습니다")
            return False
        
        subscription_message = [
            {
                "ticket": "ticker_subscription"
            },
            {
                "type": "ticker",
                "codes": codes,
                "is_only_realtime": False
            },
            {
                "format": format
            }
        ]
        
        try:
            await self.websocket.send(json.dumps(subscription_message))
            logger.info(f"📍 Ticker 구독: {codes}")
            return True
        except Exception as e:
            logger.error(f"❌ Ticker 구독 실패: {e}")
            return False
    
    async def subscribe_trade(self, codes: List[str], format: str = "DEFAULT"):
        """
        Trade(체결) 구독
        
        Args:
            codes: 구독할 마켓 코드 리스트
            format: 응답 형식 ("DEFAULT" 또는 "JSON_LIST")
        """
        if not self.is_connected:
            logger.error("❌ WebSocket이 연결되지 않았습니다")
            return False
        
        subscription_message = [
            {
                "ticket": "trade_subscription"
            },
            {
                "type": "trade",
                "codes": codes,
                "is_only_realtime": False
            },
            {
                "format": format
            }
        ]
        
        try:
            await self.websocket.send(json.dumps(subscription_message))
            logger.info(f"🔄 Trade 구독: {codes}")
            return True
        except Exception as e:
            logger.error(f"❌ Trade 구독 실패: {e}")
            return False
    
    async def subscribe_orderbook(self, codes: List[str], level: Optional[int] = None):
        """
        Orderbook(호가) 구독
        
        Args:
            codes: 구독할 마켓 코드 리스트
            level: 호가 모아보기 단위 (원화 마켓만 지원)
        """
        if not self.is_connected:
            logger.error("❌ WebSocket이 연결되지 않았습니다")
            return False
        
        subscription_message = [
            {
                "ticket": "orderbook_subscription"
            },
            {
                "type": "orderbook",
                "codes": codes,
                **({"level": level} if level else {})
            },
            {
                "format": "DEFAULT"
            }
        ]
        
        try:
            await self.websocket.send(json.dumps(subscription_message))
            logger.info(f"📊 Orderbook 구독: {codes}")
            return True
        except Exception as e:
            logger.error(f"❌ Orderbook 구독 실패: {e}")
            return False
    
    async def subscribe_candle(self, codes: List[str], candle_type: str = "1m"):
        """
        Candle(캔들) 구독
        
        Args:
            codes: 구독할 마켓 코드 리스트
            candle_type: 캔들 유형 (1s, 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m)
        """
        if not self.is_connected:
            logger.error("❌ WebSocket이 연결되지 않았습니다")
            return False
        
        valid_types = ["1s", "1m", "3m", "5m", "10m", "15m", "30m", "60m", "240m"]
        if candle_type not in valid_types:
            logger.error(f"❌ 유효하지 않은 캔들 타입: {candle_type}")
            return False
        
        subscription_message = [
            {
                "ticket": "candle_subscription"
            },
            {
                "type": f"candle.{candle_type}",
                "codes": codes,
                "is_only_realtime": False
            },
            {
                "format": "DEFAULT"
            }
        ]
        
        try:
            await self.websocket.send(json.dumps(subscription_message))
            logger.info(f"🕯️ Candle 구독: {codes} ({candle_type}봉)")
            return True
        except Exception as e:
            logger.error(f"❌ Candle 구독 실패: {e}")
            return False
    
    async def receive_messages(self, callback: Optional[Callable] = None) -> None:
        """
        메시지 수신 및 처리
        
        Args:
            callback: 수신한 메시지를 처리할 콜백 함수
        """
        if not self.is_connected:
            logger.error("❌ WebSocket이 연결되지 않았습니다")
            return
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                
                # 콜백 함수 실행
                if callback:
                    await callback(data) if asyncio.iscoroutinefunction(callback) else callback(data)
                else:
                    self._print_message(data)
                    
        except asyncio.CancelledError:
            logger.info("📱 메시지 수신 중단됨")
        except Exception as e:
            logger.error(f"❌ 메시지 수신 오류: {e}")
        finally:
            await self.disconnect()
    
    def _print_message(self, data: dict) -> None:
        """메시지 출력 (기본 콜백)"""
        msg_type = data.get("type", "unknown")
        code = data.get("code", "")
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if msg_type == "ticker":
            price = get_field(data, "tp", "trade_price")
            change = get_field(data, "cr", "signed_change_rate")
            change_str = get_field(data, "c", "change", default="")
            print(f"[{timestamp}] {code} | {msg_type}: {price:,.0f}원 ({change_str} {change*100:+.2f}%)")
        
        elif msg_type == "trade":
            price = get_field(data, "tp", "trade_price")
            volume = get_field(data, "tv", "trade_volume")
            ask_bid = get_field(data, "ab", "ask_bid", default="")
            print(f"[{timestamp}] {code} | {msg_type}: {price:,.0f}원 x {volume:.8f} ({ask_bid})")
        
        elif msg_type == "orderbook":
            total_ask = get_field(data, "tas", "total_ask_size")
            total_bid = get_field(data, "tbs", "total_bid_size")
            print(f"[{timestamp}] {code} | {msg_type}: 매도 총잔량 {total_ask:.4f} / 매수 총잔량 {total_bid:.4f}")
        
        elif msg_type.startswith("candle"):
            price = get_field(data, "tp", "trade_price")
            volume = get_field(data, "catv", "candle_acc_trade_volume")
            print(f"[{timestamp}] {code} | {msg_type}: {price:,.0f}원 (거래량: {volume:.8f})")
        
        else:
            print(f"[{timestamp}] {data}")


async def main():
    """메인 함수 - 예시"""
    client = UpbitWebSocketClient()
    
    # 1. WebSocket 연결
    if not await client.connect():
        return
    
    # 2. 데이터 구독 (여러 종류 선택 가능)
    
    # Ticker(현재가) 구독 예시
    await client.subscribe_ticker(["KRW-BTC", "KRW-ETH", "KRW-XRP"])
    
    # Trade(체결) 구독 예시
    # await client.subscribe_trade(["KRW-BTC", "KRW-ETH"])
    
    # Orderbook(호가) 구독 예시
    # await client.subscribe_orderbook(["KRW-BTC", "KRW-ETH"])
    
    # Candle(캔들) 구독 예시
    # await client.subscribe_candle(["KRW-BTC", "KRW-ETH"], "1m")
    
    # 3. 메시지 수신
    try:
        await asyncio.wait_for(
            client.receive_messages(),
            timeout=60  # 60초 후 종료
        )
    except asyncio.TimeoutError:
        logger.info("⏱️ 타임아웃 (60초)")
        await client.disconnect()


if __name__ == "__main__":
    # 실행
    asyncio.run(main())
