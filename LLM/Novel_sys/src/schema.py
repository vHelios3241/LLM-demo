from __future__ import annotations

from pydantic import BaseModel, Field


class Chapter(BaseModel):
    """小说中的一个章节。"""

    order: int = Field(..., ge=1, description="章节序号")
    title: str = Field(..., min_length=1, description="章节标题")
    outline: str = Field(..., descreption="章节大纲") 
    plot_points: list[str] = Field(
        default_factory=list,
        description="本章要写的情节要点",
    )
    clues: list[str] = Field(
        default_factory=list,
        description="可选的线索，写作阶段可逐步补充",
    )
    body: str = Field(
        default="",
        description="正文内容；规划阶段可为空，写作阶段逐步填充",
    )


class Novel(BaseModel):
    """一部小说的整体数据结构。"""

    title: str = Field(..., min_length=1, description="小说标题")
    theme: str = Field(..., min_length=1, description="小说主题")
    full_summary: str = Field(..., min_length=1, description="小说全文概括")
    chapters: list[Chapter] = Field(
        default_factory=list,
        description="小说章节列表",
    )
