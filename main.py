#!/usr/bin/env python3
"""
미국 증시 뉴스 요약 및 투자 인사이트 Multi-Agent Agent
"""

from agent import USMarketNewsAgent

def main():
    agent = USMarketNewsAgent()
    success = agent.run()

    if success:
        print("\n 분석이 완료되었습니다!")
        return 0

    print("\n 분석 중 오류가 발생했습니다.")
    return 1

if __name__ == "__main__":
    exit(main())