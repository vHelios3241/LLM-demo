# uv add click

from __future__ import annotations

import sys

import click

from LLM.src.export import export_markdown, export_word
from LLM.src.pipeline import run as pipeline_run


@click.command()
@click.argument("theme")
@click.option(
    "--chapters",
    "-c",
    default=3,
    show_default=True,
    type=int,
    help="要写的章节数量",
)
@click.option(
    "--format",
    "-f",
    "fmt",
    default="all",
    type=click.Choice(["markdown", "word", "all"], case_sensitive=False),
    help="导出格式",
)
@click.option(
    "--output",
    "-o",
    default="output",
    show_default=True,
    help="输出目录",
)
def main(theme: str, chapters: int, fmt: str, output: str) -> None:
    """🖋️  用 AI 辅助创作一本完整的小说。"""
    try:
        result = pipeline_run(theme, chapters, output_dir=output)
    except Exception as e:
        click.echo(f"❌ 生成失败：{e}", err=True)
        sys.exit(1)

    novel = result["novel"]
    errors: list[str] = result["errors"]

    # ── 按用户选择的格式导出 ──
    export_md = fmt in ("markdown", "all")
    export_docx = fmt in ("word", "all")

    if export_md or export_docx:
        click.echo("\n📁 正在导出……")

    if export_md:
        try:
            md_path = export_markdown(novel, output)
            click.echo(f"   ✅ Markdown -> {md_path}")
        except Exception as e:
            click.echo(f"   ⚠️  Markdown 导出失败：{e}", err=True)

    if export_docx:
        try:
            docx_path = export_word(novel, output)
            click.echo(f"   ✅ Word      -> {docx_path}")
        except Exception as e:
            click.echo(f"   ⚠️  Word 导出失败：{e}", err=True)

    # ── 最终报告 ──
    total = len(novel.chapters)
    success = total - len(errors)
    click.echo()
    click.echo("=" * 40)
    click.echo(f"📚 《{novel.title}》 生成完毕")
    click.echo(f"   总章节：{total} ｜ 成功：{success} ｜ 失败：{len(errors)}")
    if errors:
        click.echo("\n失败详情：")
        for err in errors:
            click.echo(f"  • {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()