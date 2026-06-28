import asyncio
import json
import csv
from upbit_websocket_client import UpbitWebSocketClient, get_field
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataRecorder:
    """데이터 녹화 클래스"""
    
    def __init__(self, output_dir: str = "data"):
        """
        초기화
        
        Args:
            output_dir: 데이터 저장 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.files = {}
        self.writers = {}
    
    def get_filename(self, data_type: str, code: str) -> str:
        """파일명 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{code}_{data_type}_{timestamp}.csv"
    
    async def save_ticker_data(self, data: dict):
        """Ticker 데이터 저장"""
        code = data.get("code", "UNKNOWN")
        filename = f"ticker_{code}.csv"
        filepath = self.output_dir / filename
        
        # 첫 저장 시 파일 및 Writer 생성
        if filename not in self.writers:
            self.files[filename] = open(filepath, 'w', newline='', encoding='utf-8')
            self.writers[filename] = csv.DictWriter(
                self.files[filename],
                fieldnames=['timestamp', 'code', 'price', 'previous_close', 'change', 'change_rate', 'volume', 'acc_volume']
            )
            self.writers[filename].writeheader()
            logger.info(f"📝 Ticker 파일 생성: {filename}")
        
        # 데이터 저장
        row = {
            'timestamp': datetime.now().isoformat(),
            'code': code,
            'price': get_field(data, 'tp', 'trade_price'),
            'previous_close': get_field(data, 'pcp', 'prev_closing_price'),
            'change': get_field(data, 'scp', 'signed_change_price'),
            'change_rate': get_field(data, 'cr', 'signed_change_rate'),
            'volume': get_field(data, 'tv', 'trade_volume'),
            'acc_volume': get_field(data, 'atv', 'acc_trade_volume')
        }
        self.writers[filename].writerow(row)
        self.files[filename].flush()
    
    async def save_trade_data(self, data: dict):
        """Trade 데이터 저장"""
        code = data.get("code", "UNKNOWN")
        filename = f"trade_{code}.csv"
        filepath = self.output_dir / filename
        
        if filename not in self.writers:
            self.files[filename] = open(filepath, 'w', newline='', encoding='utf-8')
            self.writers[filename] = csv.DictWriter(
                self.files[filename],
                fieldnames=['timestamp', 'code', 'price', 'volume', 'ask_bid', 'best_ask_price', 'best_bid_price']
            )
            self.writers[filename].writeheader()
            logger.info(f"📝 Trade 파일 생성: {filename}")
        
        row = {
            'timestamp': datetime.now().isoformat(),
            'code': code,
            'price': get_field(data, 'tp', 'trade_price'),
            'volume': get_field(data, 'tv', 'trade_volume'),
            'ask_bid': get_field(data, 'ab', 'ask_bid', default=''),
            'best_ask_price': get_field(data, 'bap', 'best_ask_price'),
            'best_bid_price': get_field(data, 'bbp', 'best_bid_price')
        }
        self.writers[filename].writerow(row)
        self.files[filename].flush()
    
    async def save_orderbook_data(self, data: dict):
        """Orderbook 데이터 저장"""
        code = data.get("code", "UNKNOWN")
        filename = f"orderbook_{code}.csv"
        filepath = self.output_dir / filename
        
        if filename not in self.writers:
            self.files[filename] = open(filepath, 'w', newline='', encoding='utf-8')
            self.writers[filename] = csv.DictWriter(
                self.files[filename],
                fieldnames=['timestamp', 'code', 'total_ask_size', 'total_bid_size', 'units_count']
            )
            self.writers[filename].writeheader()
            logger.info(f"📝 Orderbook 파일 생성: {filename}")
        
        units = get_field(data, 'obu', 'orderbook_units', default=[])
        row = {
            'timestamp': datetime.now().isoformat(),
            'code': code,
            'total_ask_size': get_field(data, 'tas', 'total_ask_size'),
            'total_bid_size': get_field(data, 'tbs', 'total_bid_size'),
            'units_count': len(units)
        }
        self.writers[filename].writerow(row)
        self.files[filename].flush()
    
    async def save_candle_data(self, data: dict):
        """Candle 데이터 저장"""
        code = data.get("code", "UNKNOWN")
        candle_type = data.get("type", "unknown")
        filename = f"candle_{code}_{candle_type}.csv"
        filepath = self.output_dir / filename
        
        if filename not in self.writers:
            self.files[filename] = open(filepath, 'w', newline='', encoding='utf-8')
            self.writers[filename] = csv.DictWriter(
                self.files[filename],
                fieldnames=['timestamp', 'code', 'open', 'high', 'low', 'close', 'volume', 'trade_value']
            )
            self.writers[filename].writeheader()
            logger.info(f"📝 Candle 파일 생성: {filename}")
        
        row = {
            'timestamp': get_field(data, 'cdttmk', 'candle_date_time_kst', default=''),
            'code': code,
            'open': get_field(data, 'op', 'opening_price'),
            'high': get_field(data, 'hp', 'high_price'),
            'low': get_field(data, 'lp', 'low_price'),
            'close': get_field(data, 'tp', 'trade_price'),
            'volume': get_field(data, 'catv', 'candle_acc_trade_volume'),
            'trade_value': get_field(data, 'catp', 'candle_acc_trade_price')
        }
        self.writers[filename].writerow(row)
        self.files[filename].flush()
    
    async def handle_message(self, data: dict):
        """메시지 처리"""
        msg_type = data.get('type', '')
        
        if msg_type == 'ticker':
            await self.save_ticker_data(data)
        elif msg_type == 'trade':
            await self.save_trade_data(data)
        elif msg_type == 'orderbook':
            await self.save_orderbook_data(data)
        elif msg_type.startswith('candle'):
            await self.save_candle_data(data)
    
    def close_all(self):
        """모든 파일 닫기"""
        for f in self.files.values():
            f.close()
        logger.info("📦 모든 파일이 닫혔습니다")


# ============================================================================
# 실시간 데이터 수집 및 저장
# ============================================================================
async def record_ticker_data(codes: list, duration: int = 300):
    """
    Ticker 데이터 수집 및 저장
    
    Args:
        codes: 수집할 마켓 코드
        duration: 수집 시간 (초)
    """
    recorder = DataRecorder()
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    await client.subscribe_ticker(codes)
    
    print(f"\n📊 Ticker 데이터 수집 시작 ({duration}초)")
    print(f"수집 대상: {', '.join(codes)}\n")
    
    try:
        await asyncio.wait_for(
            client.receive_messages(callback=recorder.handle_message),
            timeout=duration
        )
    except asyncio.TimeoutError:
        print(f"\n✅ 수집 완료 - {duration}초 경과")
    finally:
        recorder.close_all()
        await client.disconnect()


async def record_trade_data(codes: list, duration: int = 300):
    """
    Trade 데이터 수집 및 저장
    
    Args:
        codes: 수집할 마켓 코드
        duration: 수집 시간 (초)
    """
    recorder = DataRecorder()
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    await client.subscribe_trade(codes)
    
    print(f"\n📊 Trade 데이터 수집 시작 ({duration}초)")
    print(f"수집 대상: {', '.join(codes)}\n")
    
    try:
        await asyncio.wait_for(
            client.receive_messages(callback=recorder.handle_message),
            timeout=duration
        )
    except asyncio.TimeoutError:
        print(f"\n✅ 수집 완료 - {duration}초 경과")
    finally:
        recorder.close_all()
        await client.disconnect()


async def record_orderbook_data(codes: list, duration: int = 300):
    """
    Orderbook 데이터 수집 및 저장
    
    Args:
        codes: 수집할 마켓 코드
        duration: 수집 시간 (초)
    """
    recorder = DataRecorder()
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    await client.subscribe_orderbook(codes)
    
    print(f"\n📊 Orderbook 데이터 수집 시작 ({duration}초)")
    print(f"수집 대상: {', '.join(codes)}\n")
    
    try:
        await asyncio.wait_for(
            client.receive_messages(callback=recorder.handle_message),
            timeout=duration
        )
    except asyncio.TimeoutError:
        print(f"\n✅ 수집 완료 - {duration}초 경과")
    finally:
        recorder.close_all()
        await client.disconnect()


async def record_candle_data(codes: list, candle_type: str = "1m", duration: int = 300):
    """
    Candle 데이터 수집 및 저장
    
    Args:
        codes: 수집할 마켓 코드
        candle_type: 캔들 타입
        duration: 수집 시간 (초)
    """
    recorder = DataRecorder()
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    await client.subscribe_candle(codes, candle_type)
    
    print(f"\n📊 Candle({candle_type}) 데이터 수집 시작 ({duration}초)")
    print(f"수집 대상: {', '.join(codes)}\n")
    
    try:
        await asyncio.wait_for(
            client.receive_messages(callback=recorder.handle_message),
            timeout=duration
        )
    except asyncio.TimeoutError:
        print(f"\n✅ 수집 완료 - {duration}초 경과")
    finally:
        recorder.close_all()
        await client.disconnect()


if __name__ == "__main__":
    print("=" * 70)
    print("업비트 WebSocket 데이터 수집 및 저장")
    print("=" * 70)
    
    examples = {
        "1": ("Ticker 수집", lambda: record_ticker_data(["KRW-BTC", "KRW-ETH"], 60)),
        "2": ("Trade 수집", lambda: record_trade_data(["KRW-BTC", "KRW-ETH"], 60)),
        "3": ("Orderbook 수집", lambda: record_orderbook_data(["KRW-BTC", "KRW-ETH"], 60)),
        "4": ("Candle 수집", lambda: record_candle_data(["KRW-BTC", "KRW-ETH"], "1m", 60)),
    }
    
    print("\n선택 가능한 수집 옵션:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    choice = input("\n실행할 옵션을 선택하세요 (1-4): ").strip()
    
    if choice in examples:
        name, func = examples[choice]
        print(f"\n➡️  {name}을(를) 시작합니다...")
        asyncio.run(func())
    else:
        print("❌ 유효하지 않은 선택입니다")
