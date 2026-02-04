"""
Task 108: Whiteboard Service

Service for managing interactive whiteboard with drawing tools and math equations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from models.live_session import (
    WhiteboardSession,
    WhiteboardStroke,
    WhiteboardEquation,
    WhiteboardToolType,
)

logger = logging.getLogger(__name__)


class WhiteboardService:
    """
    Service for whiteboard management

    Task 108.3: Interactive whiteboard with drawing tools and math equation editor
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Whiteboard Session Management
    # ============================================================

    async def create_whiteboard(
        self,
        session_id: UUID,
        name: str = "Whiteboard",
        background_color: str = "#FFFFFF",
        grid_enabled: bool = True,
    ) -> WhiteboardSession:
        """Create new whiteboard for live session"""
        whiteboard = WhiteboardSession(
            session_id=session_id,
            name=name,
            background_color=background_color,
            grid_enabled=grid_enabled,
        )

        self.db.add(whiteboard)
        await self.db.commit()
        await self.db.refresh(whiteboard)

        logger.info(f"Whiteboard created: {whiteboard.id} for session {session_id}")
        return whiteboard

    async def get_whiteboard(self, whiteboard_id: UUID) -> Optional[WhiteboardSession]:
        """Get whiteboard by ID"""
        query = select(WhiteboardSession).where(WhiteboardSession.id == whiteboard_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_session_whiteboards(
        self, session_id: UUID
    ) -> List[WhiteboardSession]:
        """Get all whiteboards for a session"""
        query = (
            select(WhiteboardSession)
            .where(WhiteboardSession.session_id == session_id)
            .order_by(WhiteboardSession.created_at)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_whiteboard(
        self, whiteboard_id: UUID, **kwargs
    ) -> Optional[WhiteboardSession]:
        """Update whiteboard settings"""
        whiteboard = await self.get_whiteboard(whiteboard_id)
        if not whiteboard:
            return None

        for key, value in kwargs.items():
            if hasattr(whiteboard, key):
                setattr(whiteboard, key, value)

        whiteboard.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(whiteboard)

        return whiteboard

    async def add_page(self, whiteboard_id: UUID) -> Optional[WhiteboardSession]:
        """Add new page to whiteboard"""
        whiteboard = await self.get_whiteboard(whiteboard_id)
        if not whiteboard:
            return None

        whiteboard.page_count += 1
        whiteboard.current_page = whiteboard.page_count

        await self.db.commit()
        await self.db.refresh(whiteboard)

        return whiteboard

    async def set_current_page(
        self, whiteboard_id: UUID, page_number: int
    ) -> Optional[WhiteboardSession]:
        """Change current page"""
        whiteboard = await self.get_whiteboard(whiteboard_id)
        if not whiteboard:
            return None

        if page_number < 1 or page_number > whiteboard.page_count:
            raise ValueError(f"Invalid page number: {page_number}")

        whiteboard.current_page = page_number

        await self.db.commit()
        await self.db.refresh(whiteboard)

        return whiteboard

    # ============================================================
    # Task 108.3: Drawing Tools
    # ============================================================

    async def add_stroke(
        self,
        whiteboard_id: UUID,
        user_id: UUID,
        tool_type: WhiteboardToolType,
        page_number: int,
        path_data: Optional[List[Dict[str, float]]] = None,
        shape_type: Optional[str] = None,
        shape_data: Optional[Dict[str, Any]] = None,
        text_content: Optional[str] = None,
        color: str = "#000000",
        width: float = 2.0,
        opacity: float = 1.0,
        font_size: int = 16,
        font_family: str = "Arial",
        z_index: int = 0,
    ) -> WhiteboardStroke:
        """
        Add drawing stroke to whiteboard

        Supports:
        - Pen/Highlighter: path_data with x,y points
        - Shapes: shape_type and shape_data
        - Text: text_content with font properties
        - Eraser: path_data for erasing area
        """
        stroke = WhiteboardStroke(
            whiteboard_id=whiteboard_id,
            user_id=user_id,
            page_number=page_number,
            tool_type=tool_type,
            color=color,
            width=width,
            opacity=opacity,
            path_data=path_data or [],
            shape_type=shape_type,
            shape_data=shape_data or {},
            text_content=text_content,
            font_size=font_size,
            font_family=font_family,
            z_index=z_index,
        )

        self.db.add(stroke)
        await self.db.commit()
        await self.db.refresh(stroke)

        return stroke

    async def get_page_strokes(
        self, whiteboard_id: UUID, page_number: int, include_deleted: bool = False
    ) -> List[WhiteboardStroke]:
        """Get all strokes for a specific page"""
        query = select(WhiteboardStroke).where(
            WhiteboardStroke.whiteboard_id == whiteboard_id,
            WhiteboardStroke.page_number == page_number,
        )

        if not include_deleted:
            query = query.where(WhiteboardStroke.is_deleted == False)

        query = query.order_by(WhiteboardStroke.z_index, WhiteboardStroke.created_at)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_stroke(self, stroke_id: UUID, soft_delete: bool = True) -> bool:
        """Delete stroke (soft or hard delete)"""
        if soft_delete:
            query = select(WhiteboardStroke).where(WhiteboardStroke.id == stroke_id)
            result = await self.db.execute(query)
            stroke = result.scalar_one_or_none()

            if stroke:
                stroke.is_deleted = True
                await self.db.commit()
                return True
            return False
        else:
            query = delete(WhiteboardStroke).where(WhiteboardStroke.id == stroke_id)
            result = await self.db.execute(query)
            await self.db.commit()
            return result.rowcount > 0

    async def clear_page(self, whiteboard_id: UUID, page_number: int) -> int:
        """Clear all strokes from a page (soft delete)"""
        query = select(WhiteboardStroke).where(
            WhiteboardStroke.whiteboard_id == whiteboard_id,
            WhiteboardStroke.page_number == page_number,
            WhiteboardStroke.is_deleted == False,
        )
        result = await self.db.execute(query)
        strokes = result.scalars().all()

        count = 0
        for stroke in strokes:
            stroke.is_deleted = True
            count += 1

        await self.db.commit()
        return count

    # ============================================================
    # Task 108.3: Math Equation Editor
    # ============================================================

    async def add_equation(
        self,
        whiteboard_id: UUID,
        user_id: UUID,
        page_number: int,
        x: float,
        y: float,
        latex_code: str,
        font_size: int = 20,
        color: str = "#000000",
        z_index: int = 0,
    ) -> WhiteboardEquation:
        """
        Add math equation to whiteboard

        LaTeX equation will be rendered on client side using libraries like:
        - KaTeX
        - MathJax
        """
        # Render LaTeX to SVG (placeholder - would use actual rendering library)
        rendered_svg = await self._render_latex_to_svg(latex_code, font_size, color)

        equation = WhiteboardEquation(
            whiteboard_id=whiteboard_id,
            user_id=user_id,
            page_number=page_number,
            x=x,
            y=y,
            latex_code=latex_code,
            rendered_svg=rendered_svg,
            font_size=font_size,
            color=color,
            z_index=z_index,
        )

        self.db.add(equation)
        await self.db.commit()
        await self.db.refresh(equation)

        logger.info(f"Equation added: {equation.id}")
        return equation

    async def update_equation(
        self,
        equation_id: UUID,
        latex_code: Optional[str] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        font_size: Optional[int] = None,
        color: Optional[str] = None,
    ) -> Optional[WhiteboardEquation]:
        """Update equation"""
        query = select(WhiteboardEquation).where(WhiteboardEquation.id == equation_id)
        result = await self.db.execute(query)
        equation = result.scalar_one_or_none()

        if not equation:
            return None

        if latex_code is not None:
            equation.latex_code = latex_code
            # Re-render with new LaTeX
            equation.rendered_svg = await self._render_latex_to_svg(
                latex_code, font_size or equation.font_size, color or equation.color
            )

        if x is not None:
            equation.x = x
        if y is not None:
            equation.y = y
        if font_size is not None:
            equation.font_size = font_size
        if color is not None:
            equation.color = color

        equation.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(equation)

        return equation

    async def get_page_equations(
        self, whiteboard_id: UUID, page_number: int, include_deleted: bool = False
    ) -> List[WhiteboardEquation]:
        """Get all equations for a specific page"""
        query = select(WhiteboardEquation).where(
            WhiteboardEquation.whiteboard_id == whiteboard_id,
            WhiteboardEquation.page_number == page_number,
        )

        if not include_deleted:
            query = query.where(WhiteboardEquation.is_deleted == False)

        query = query.order_by(
            WhiteboardEquation.z_index, WhiteboardEquation.created_at
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_equation(
        self, equation_id: UUID, soft_delete: bool = True
    ) -> bool:
        """Delete equation"""
        if soft_delete:
            query = select(WhiteboardEquation).where(
                WhiteboardEquation.id == equation_id
            )
            result = await self.db.execute(query)
            equation = result.scalar_one_or_none()

            if equation:
                equation.is_deleted = True
                await self.db.commit()
                return True
            return False
        else:
            query = delete(WhiteboardEquation).where(
                WhiteboardEquation.id == equation_id
            )
            result = await self.db.execute(query)
            await self.db.commit()
            return result.rowcount > 0

    # ============================================================
    # Export & Snapshot
    # ============================================================

    async def get_page_content(
        self, whiteboard_id: UUID, page_number: int
    ) -> Dict[str, Any]:
        """Get complete page content (strokes + equations)"""
        strokes = await self.get_page_strokes(whiteboard_id, page_number)
        equations = await self.get_page_equations(whiteboard_id, page_number)

        return {
            "page_number": page_number,
            "strokes": [
                {
                    "id": str(stroke.id),
                    "tool_type": stroke.tool_type,
                    "color": stroke.color,
                    "width": stroke.width,
                    "opacity": stroke.opacity,
                    "path_data": stroke.path_data,
                    "shape_type": stroke.shape_type,
                    "shape_data": stroke.shape_data,
                    "text_content": stroke.text_content,
                    "font_size": stroke.font_size,
                    "font_family": stroke.font_family,
                    "z_index": stroke.z_index,
                }
                for stroke in strokes
            ],
            "equations": [
                {
                    "id": str(eq.id),
                    "x": eq.x,
                    "y": eq.y,
                    "latex_code": eq.latex_code,
                    "rendered_svg": eq.rendered_svg,
                    "font_size": eq.font_size,
                    "color": eq.color,
                    "z_index": eq.z_index,
                }
                for eq in equations
            ],
        }

    async def save_snapshot(
        self, whiteboard_id: UUID, snapshot_url: str
    ) -> Optional[WhiteboardSession]:
        """Save snapshot URL of whiteboard"""
        whiteboard = await self.get_whiteboard(whiteboard_id)
        if not whiteboard:
            return None

        whiteboard.snapshot_url = snapshot_url
        await self.db.commit()
        await self.db.refresh(whiteboard)

        return whiteboard

    # ============================================================
    # Collaborative Features
    # ============================================================

    async def get_active_users(self, whiteboard_id: UUID) -> List[UUID]:
        """
        Get list of users currently drawing on whiteboard

        This would be implemented with WebSocket tracking in production
        """
        # Placeholder: Return users who have drawn in last 5 minutes
        five_mins_ago = datetime.utcnow() - timedelta(minutes=5)

        query = (
            select(WhiteboardStroke.user_id)
            .where(
                WhiteboardStroke.whiteboard_id == whiteboard_id,
                WhiteboardStroke.created_at >= five_mins_ago,
            )
            .distinct()
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # Helper Methods
    # ============================================================

    async def _render_latex_to_svg(
        self, latex_code: str, font_size: int, color: str
    ) -> str:
        """
        Render LaTeX to SVG

        PLACEHOLDER: Integrate with LaTeX rendering library in production
        Options:
        - KaTeX server-side rendering
        - MathJax server-side
        - matplotlib.mathtext
        """
        # Production implementation example:
        # from pylatexenc.latexwalker import LatexWalker
        # from pylatexenc.latex2text import LatexNodes2Text
        # Or use external service

        # Mock SVG for development
        return f'<svg xmlns="http://www.w3.org/2000/svg"><text x="0" y="{font_size}" font-size="{font_size}" fill="{color}">{latex_code}</text></svg>'

    async def export_to_pdf(self, whiteboard_id: UUID, output_path: str) -> str:
        """
        Export whiteboard to PDF

        PLACEHOLDER: Implement PDF generation in production
        """
        # Production implementation would:
        # 1. Render each page
        # 2. Convert SVG strokes to PDF
        # 3. Render LaTeX equations
        # 4. Combine into multi-page PDF
        # 5. Return file path/URL

        whiteboard = await self.get_whiteboard(whiteboard_id)
        if not whiteboard:
            raise ValueError("Whiteboard not found")

        # Mock implementation
        logger.info(f"Exporting whiteboard {whiteboard_id} to PDF: {output_path}")
        return output_path


from datetime import timedelta  # Add missing import
