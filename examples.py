import asyncio
import json
from upbit_websocket_client import UpbitWebSocketClient, get_field
from datetime import datetime


# ============================================================================
# 예시 1: Ticker(현재가) 실시간 수신
# ============================================================================
async def example_ticker():
    """실시간 현재가 데이터 수신"""
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    # BTC, ETH, XRP의 현재가 구독
    await client.subscribe_ticker(["KRW-BTC", "KRW-ETH", "KRW-XRP"])
    
    print("\n=== Ticker(현재가) 예시 ===")
    print("30초간 실시간 현재가를 수신합니다...\n")
    
    try:
        await asyncio.wait_for(
            client.receive_messages(),
            timeout=30
        )
    except asyncio.TimeoutError:
        print("\n✅ 수신 완료")
        await client.disconnect()


# ============================================================================
# 예시 2: Trade(체결) 데이터 수신
# ============================================================================
async def example_trade():
    """체결 데이터 수신"""
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    await client.subscribe_trade(["KRW-BTC", "KRW-ETH"])
    
    print("\n=== Trade(체결) 예시 ===")
    print("30초간 체결 데이터를 수신합니다...\n")
    
    try:
        await asyncio.wait_for(
            client.receive_messages(),
            timeout=30
        )
    except asyncio.TimeoutError:
        print("\n✅ 수신 완료")
        await client.disconnect()


# ============================================================================
# 예시 3: Orderbook(호가) 데이터 수신
# ============================================================================
async def example_orderbook():
    """호가 데이터 수신"""
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    # level=100000으로 설정하면 10만원 단위로 호가 모아보기
    await client.subscribe_orderbook(["KRW-BTC", "KRW-ETH"], level=None)
    
    print("\n=== Orderbook(호가) 예시 ===")
    print("30초간 호가 데이터를 수신합니다...\n")
    
    try:
        await asyncio.wait_for(
            client.receive_messages(),
            timeout=30
        )
    except asyncio.TimeoutError:
        print("\n✅ 수신 완료")
        await client.disconnect()


# ============================================================================
# 예시 4: Candle(캔들) 데이터 수신
# ============================================================================
async def example_candle():
    """캔들 데이터 수신"""
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    # 1분봉 캔들 구독
    await client.subscribe_candle(["KRW-BTC", "KRW-ETH"], "1m")
    
    print("\n=== Candle(캔들) 예시 - 1분봉 ===")
    print("30초간 1분봉 캔들 데이터를 수신합니다...\n")
    
    try:
        await asyncio.wait_for(
            client.receive_messages(),
            timeout=30
        )
    except asyncio.TimeoutError:
        print("\n✅ 수신 완료")
        await client.disconnect()


# ============================================================================
# 예시 5: 커스텀 콜백 함수를 사용한 데이터 처리
# ============================================================================
ticker_data = []

async def custom_callback(data):
    """커스텀 콜백 함수"""
    msg_type = data.get("type", "")
    
    if msg_type == "ticker":
        code = data.get("code", "")
        price = get_field(data, "tp", "trade_price")
        volume = get_field(data, "atv", "acc_trade_volume")
        change_rate = get_field(data, "cr", "signed_change_rate")
        
        # 데이터 저장
        ticker_data.append({
            "time": datetime.now().isoformat(),
            "code": code,
            "price": price,
            "volume": volume,
            "change_rate": change_rate
        })
        
        # 콘솔에 출력
        print(f"{code}: {price:>12,}원 | 변동률: {change_rate*100:>+6.2f}% | 거래량: {volume:>10.2f}")


async def example_custom_callback():
    """커스텀 콜백 함수를 사용한 예시"""
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    await client.subscribe_ticker(["KRW-BTC", "KRW-ETH", "KRW-XRP"])
    
    print("\n=== 커스텀 콜백 함수 예시 ===")
    print("현재가 데이터를 처리하고 저장합니다...\n")
    print("코드         | 가격          | 변동률     | 거래량")
    print("-" * 60)
    
    try:
        await asyncio.wait_for(
            client.receive_messages(callback=custom_callback),
            timeout=30
        )
    except asyncio.TimeoutError:
        pass
    
    print(f"\n✅ 수신 완료 - 총 {len(ticker_data)}개 데이터 수집됨")
    print("\n최근 데이터 샘플:")
    for data in ticker_data[-3:]:
        print(f"  {data}")


# ============================================================================
# 예시 6: 여러 마켓 동시 구독
# ============================================================================
async def example_multiple_streams():
    """여러 데이터 스트림을 동시에 구독"""
    client = UpbitWebSocketClient()
    
    if not await client.connect():
        return
    
    # 여러 종류의 데이터를 동시에 구독할 수 없으므로 하나만 선택
    await client.subscribe_ticker(
        ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-AVAX"]
    )
    
    print("\n=== 다중 마켓 구독 예시 ===")
    print("5개 마켓의 현재가를 동시에 수신합니다...\n")
    
    try:
        await asyncio.wait_for(
            client.receive_messages(),
            timeout=30
        )
    except asyncio.TimeoutError:
        print("\n✅ 수신 완료")
        await client.disconnect()


if __name__ == "__main__":
    print("=" * 70)
    print("업비트 WebSocket 예시")
    print("=" * 70)
    
    # 실행할 예시 선택 (1 ~ 6)
    examples = {
        "1": ("Ticker(현재가)", example_ticker),
        "2": ("Trade(체결)", example_trade),
        "3": ("Orderbook(호가)", example_orderbook),
        "4": ("Candle(캔들)", example_candle),
        "5": ("커스텀 콜백 함수", example_custom_callback),
        "6": ("다중 마켓 구독", example_multiple_streams),
    }
    
    print("\n선택 가능한 예시:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    choice = input("\n실행할 예시를 선택하세요 (1-6): ").strip()
    
    if choice in examples:
        name, func = examples[choice]
        print(f"\n➡️  {name} 예시를 시작합니다...")
        asyncio.run(func())
    else:
        print("❌ 유효하지 않은 선택입니다")
