"""
Laneige Ranking Insight Agent (Hybrid Ver.)

Phase 1: 자동 리포트 생성 (Push)
Phase 2: 대화형 분석 모드 (Pull)
"""

import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown

# Load environment variables
load_dotenv()

console = Console()

# 전역 변수
products_df = None
ranking_engine = None
vector_store = None
chat_engine = None


def initialize():
    """시스템 초기화"""
    global products_df, ranking_engine, vector_store, chat_engine

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # 데이터 로드
        task = progress.add_task("Loading product data...", total=None)
        from backend.data.loader import load_all_products
        products_df = load_all_products()
        progress.update(task, description=f"Loaded {len(products_df)} products")

        # 랭킹 엔진 초기화
        task = progress.add_task("Initializing ranking engine...", total=None)
        from backend.mock_engine.ranking_engine import MockRankingEngine
        ranking_engine = MockRankingEngine(products_df)
        progress.update(task, description="Ranking engine ready")

        # 벡터 스토어 초기화
        task = progress.add_task("Loading vector store...", total=None)
        from backend.rag.vector_store import ProductVectorStore
        vector_store = ProductVectorStore()

        # 라네즈 제품만 벡터 스토어에 추가 (없으면)
        if vector_store.count() == 0:
            laneige_products = products_df[products_df['is_laneige'] == True]
            vector_store.add_products(laneige_products)
        progress.update(task, description=f"Vector store: {vector_store.count()} products")

        # 챗 엔진 초기화
        task = progress.add_task("Initializing chat engine...", total=None)
        from backend.chat.chat_engine import ChatEngine
        chat_engine = ChatEngine(
            vector_store=vector_store,
            ranking_engine=ranking_engine
        )
        progress.update(task, description="Chat engine ready")


def phase1_generate_report() -> str:
    """Phase 1: 데이터 수집 및 엑셀 리포트 자동 생성"""

    console.print("\n[bold blue]Phase 1: 랭킹 데이터 수집 및 리포트 생성[/bold blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # 랭킹 생성
        task = progress.add_task("Generating ranking history (30 days)...", total=None)
        ranking_data = ranking_engine.generate_all_categories(days=30)
        progress.update(task, description=f"Generated {len(ranking_data)} categories")

        # 엑셀 리포트 생성
        task = progress.add_task("Creating Excel report...", total=None)
        from backend.report.excel_generator import ExcelReportGenerator
        generator = ExcelReportGenerator()
        filepath = generator.create_ranking_report(ranking_data)
        progress.update(task, description="Excel report created")

    # 요약 테이블 출력
    console.print("\n[bold green]Report Generated Successfully![/bold green]")
    console.print(f"File: [cyan]{filepath}[/cyan]\n")

    # 라네즈 요약
    table = Table(title="LANEIGE Ranking Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Product", style="white")
    table.add_column("Avg Rank", justify="right", style="green")
    table.add_column("Best Rank", justify="right", style="yellow")
    table.add_column("TOP 5 Days", justify="right", style="magenta")

    for category, df in ranking_data.items():
        summary = ranking_engine.get_laneige_summary(category)
        for product, stats in summary.items():
            table.add_row(
                category.replace("_", " ").title(),
                product,
                str(stats['avg_rank']),
                str(stats['best_rank']),
                str(stats['top5_days'])
            )

    console.print(table)

    return filepath


def phase2_chat_mode():
    """Phase 2: RAG 기반 대화형 분석"""

    console.print("\n" + "="*50)
    console.print(Panel.fit(
        "[bold blue]Phase 2: 대화형 분석 모드[/bold blue]\n"
        "랭킹 데이터 기반 AI 인사이트를 제공합니다.",
        border_style="blue"
    ))

    # 환영 메시지
    welcome = chat_engine.get_welcome_message()
    console.print(Markdown(welcome))

    # API 키 체크
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("\n[yellow]Warning: ANTHROPIC_API_KEY가 설정되지 않았습니다.[/yellow]")
        console.print("[yellow]Mock 응답이 제공됩니다. 실제 분석을 위해 .env 파일에 API 키를 설정해주세요.[/yellow]\n")

    # 대화 루프
    while True:
        try:
            user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]대화를 종료합니다.[/yellow]")
            break

        if not user_input:
            continue

        if user_input.lower() in ['exit', 'quit', '종료', 'q']:
            console.print("\n[yellow]대화를 종료합니다. 감사합니다![/yellow]")
            break

        # 분석 중 표시
        with console.status("[bold green]분석 중..."):
            response = chat_engine.chat(user_input)

        # 응답 출력
        console.print(f"\n[bold green]Agent:[/bold green]")
        console.print(Markdown(response))


def main():
    """메인 실행"""

    # 타이틀
    console.print(Panel.fit(
        "[bold magenta]LANEIGE Ranking Insight Agent[/bold magenta]\n"
        "[dim]글로벌 뷰티 플랫폼 랭킹 분석 AI 에이전트[/dim]\n\n"
        "[cyan]Amazon US[/cyan] | [cyan]@COSME JP[/cyan]",
        border_style="magenta",
        padding=(1, 4)
    ))

    try:
        # 초기화
        console.print("\n[bold]Initializing system...[/bold]")
        initialize()
        console.print("[green]System ready![/green]\n")

        # Phase 1: 자동 리포트 생성
        report_path = phase1_generate_report()

        # Phase 2: 대화형 분석
        phase2_chat_mode()

    except KeyboardInterrupt:
        console.print("\n[yellow]프로그램을 종료합니다.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    main()
