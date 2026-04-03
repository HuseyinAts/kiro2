"""
Gorsel Uretim Motoru (Matplotlib/Plotly Entegrasyonu)
REQ-48.45-48.48: Graph generation, Geometry figure generation, Chart and diagram creation

Bu modul matematik ve fen sorulari icin gorseller uretir:
fonksiyon grafikleri, geometrik sekiller, pasta/cubuk grafikler.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class VisualGenerationEngine:
    """
    Gorsel Uretim Motoru (Matplotlib/Plotly Entegrasyonu)
    REQ-48.45-48.48: Graph generation, Geometry figure generation, Chart and diagram creation
    """

    def __init__(self):
        """Matplotlib ve Plotly entegrasyonu"""
        self.matplotlib_available = False
        self.plotly_available = False
        self.plt = None
        self.go = None
        self.px = None

        try:
            import matplotlib

            matplotlib.use("Agg")  # GUI olmadan calismasi icin
            import matplotlib.pyplot as plt

            self.plt = plt
            self.matplotlib_available = True
            logger.info("Matplotlib basariyla yuklendi")
        except ImportError:
            logger.warning("Matplotlib yuklu degil")

        try:
            import plotly.express as px
            import plotly.graph_objects as go

            self.go = go
            self.px = px
            self.plotly_available = True
            logger.info("Plotly basariyla yuklendi")
        except ImportError:
            logger.warning("Plotly yuklu degil")

    def generate_function_graph(
        self,
        function_str: str,
        x_range: tuple = (-10, 10),
        title: str = "Fonksiyon Grafigi",
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """
        REQ-48.46: Graph generation - Matematiksel fonksiyonlari gorsellestirmek

        Args:
            function_str: Fonksiyon string'i (orn: "x**2 + 2*x + 1")
            x_range: X ekseni araligi
            title: Grafik basligi
            output_path: Kaydedilecek dosya yolu

        Returns:
            Grafik bilgileri
        """
        if not self.matplotlib_available:
            return {"success": False, "error": "Matplotlib yuklu degil"}

        try:
            import numpy as np

            # X degerlerini olustur
            x = np.linspace(x_range[0], x_range[1], 400)

            # Fonksiyonu degerlendir — guvenli AST whitelist
            import ast
            import operator

            _SAFE_OPS = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
            }
            _SAFE_FUNCS = {
                "sin": np.sin,
                "cos": np.cos,
                "tan": np.tan,
                "sqrt": np.sqrt,
                "abs": np.abs,
                "log": np.log,
                "exp": np.exp,
                "pi": np.pi,
                "e": np.e,
            }

            def _safe_eval_node(node, x_val):
                if isinstance(node, ast.Expression):
                    return _safe_eval_node(node.body, x_val)
                if isinstance(node, ast.Constant):
                    if not isinstance(node.value, (int, float)):
                        raise ValueError("Sadece sayisal sabitler desteklenir")
                    return node.value
                if isinstance(node, ast.Name):
                    if node.id == "x":
                        return x_val
                    if node.id in _SAFE_FUNCS:
                        return _SAFE_FUNCS[node.id]
                    raise ValueError(f"Tanimsiz degisken: {node.id}")
                if isinstance(node, ast.BinOp):
                    op = _SAFE_OPS.get(type(node.op))
                    if op is None:
                        raise ValueError(
                            f"Desteklenmeyen operator: {type(node.op).__name__}"
                        )
                    return op(
                        _safe_eval_node(node.left, x_val),
                        _safe_eval_node(node.right, x_val),
                    )
                if isinstance(node, ast.UnaryOp):
                    op = _SAFE_OPS.get(type(node.op))
                    if op is None:
                        raise ValueError(
                            f"Desteklenmeyen operator: {type(node.op).__name__}"
                        )
                    return op(_safe_eval_node(node.operand, x_val))
                if isinstance(node, ast.Call):
                    func = _safe_eval_node(node.func, x_val)
                    if not callable(func):
                        raise ValueError("Cagrilabilir degil")
                    args = [_safe_eval_node(a, x_val) for a in node.args]
                    return func(*args)
                raise ValueError(f"Desteklenmeyen ifade: {type(node).__name__}")

            tree = ast.parse(function_str, mode="eval")
            y = _safe_eval_node(tree, x)

            # Grafik olustur
            fig, ax = self.plt.subplots(figsize=(10, 6))
            ax.plot(x, y, "b-", linewidth=2)
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color="k", linewidth=0.5)
            ax.axvline(x=0, color="k", linewidth=0.5)
            ax.set_xlabel("x", fontsize=12)
            ax.set_ylabel("f(x)", fontsize=12)
            ax.set_title(title, fontsize=14, fontweight="bold")

            # Kaydet
            if output_path:
                self.plt.savefig(output_path, dpi=150, bbox_inches="tight")
                logger.info(f"Grafik kaydedildi: {output_path}")

            self.plt.close()

            return {
                "success": True,
                "output_path": output_path,
                "function": function_str,
                "x_range": x_range,
            }

        except Exception as e:
            logger.error(f"Grafik olusturma hatasi: {e}")
            return {"success": False, "error": str(e)}

    def generate_geometry_figure(
        self,
        shape_type: str,
        parameters: dict[str, Any],
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """
        REQ-48.47: Geometry figure - Geometrik sekilleri cizmek

        Args:
            shape_type: Sekil tipi (triangle, circle, rectangle, vb.)
            parameters: Sekil parametreleri
            output_path: Kaydedilecek dosya yolu

        Returns:
            Sekil bilgileri
        """
        if not self.matplotlib_available:
            return {"success": False, "error": "Matplotlib yuklu degil"}

        try:
            from matplotlib.patches import Circle, Polygon, Rectangle

            fig, ax = self.plt.subplots(figsize=(8, 8))
            ax.set_aspect("equal")
            ax.grid(True, alpha=0.3)

            if shape_type == "circle":
                # Daire ciz
                radius = parameters.get("radius", 5)
                center = parameters.get("center", (0, 0))
                circle = Circle(
                    center, radius, fill=False, edgecolor="blue", linewidth=2
                )
                ax.add_patch(circle)
                ax.set_xlim(center[0] - radius - 2, center[0] + radius + 2)
                ax.set_ylim(center[1] - radius - 2, center[1] + radius + 2)

            elif shape_type == "rectangle":
                # Dikdortgen ciz
                width = parameters.get("width", 6)
                height = parameters.get("height", 4)
                bottom_left = parameters.get("bottom_left", (0, 0))
                rect = Rectangle(
                    bottom_left,
                    width,
                    height,
                    fill=False,
                    edgecolor="blue",
                    linewidth=2,
                )
                ax.add_patch(rect)
                ax.set_xlim(bottom_left[0] - 2, bottom_left[0] + width + 2)
                ax.set_ylim(bottom_left[1] - 2, bottom_left[1] + height + 2)

            elif shape_type == "triangle":
                # Ucgen ciz
                vertices = parameters.get("vertices", [(0, 0), (4, 0), (2, 3)])
                triangle = Polygon(vertices, fill=False, edgecolor="blue", linewidth=2)
                ax.add_patch(triangle)

                # Sinirlari ayarla
                x_coords = [v[0] for v in vertices]
                y_coords = [v[1] for v in vertices]
                ax.set_xlim(min(x_coords) - 1, max(x_coords) + 1)
                ax.set_ylim(min(y_coords) - 1, max(y_coords) + 1)

            ax.set_xlabel("x", fontsize=12)
            ax.set_ylabel("y", fontsize=12)
            ax.set_title(
                f"{shape_type.capitalize()} Sekli", fontsize=14, fontweight="bold"
            )

            # Kaydet
            if output_path:
                self.plt.savefig(output_path, dpi=150, bbox_inches="tight")
                logger.info(f"Geometrik sekil kaydedildi: {output_path}")

            self.plt.close()

            return {
                "success": True,
                "output_path": output_path,
                "shape_type": shape_type,
                "parameters": parameters,
            }

        except Exception as e:
            logger.error(f"Geometrik sekil olusturma hatasi: {e}")
            return {"success": False, "error": str(e)}

    def generate_chart(
        self,
        chart_type: str,
        data: dict[str, Any],
        title: str = "Grafik",
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """
        REQ-48.48: Chart/Diagram - Veri gorsellestirmesi yapmak

        Args:
            chart_type: Grafik tipi (bar, pie, line, scatter)
            data: Veri
            title: Baslik
            output_path: Kaydedilecek dosya yolu

        Returns:
            Grafik bilgileri
        """
        if not self.matplotlib_available:
            return {"success": False, "error": "Matplotlib yuklu degil"}

        try:
            fig, ax = self.plt.subplots(figsize=(10, 6))

            if chart_type == "bar":
                # Cubuk grafik
                categories = data.get("categories", [])
                values = data.get("values", [])
                ax.bar(categories, values, color="steelblue")
                ax.set_ylabel("Deger", fontsize=12)

            elif chart_type == "pie":
                # Pasta grafik
                labels = data.get("labels", [])
                sizes = data.get("sizes", [])
                ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
                ax.axis("equal")

            elif chart_type == "line":
                # Cizgi grafik
                x_data = data.get("x", [])
                y_data = data.get("y", [])
                ax.plot(x_data, y_data, marker="o", linewidth=2, markersize=6)
                ax.set_xlabel("X", fontsize=12)
                ax.set_ylabel("Y", fontsize=12)
                ax.grid(True, alpha=0.3)

            elif chart_type == "scatter":
                # Nokta grafik
                x_data = data.get("x", [])
                y_data = data.get("y", [])
                ax.scatter(x_data, y_data, s=100, alpha=0.6, c="steelblue")
                ax.set_xlabel("X", fontsize=12)
                ax.set_ylabel("Y", fontsize=12)
                ax.grid(True, alpha=0.3)

            ax.set_title(title, fontsize=14, fontweight="bold")

            # Kaydet
            if output_path:
                self.plt.savefig(output_path, dpi=150, bbox_inches="tight")
                logger.info(f"Grafik kaydedildi: {output_path}")

            self.plt.close()

            return {
                "success": True,
                "output_path": output_path,
                "chart_type": chart_type,
            }

        except Exception as e:
            logger.error(f"Grafik olusturma hatasi: {e}")
            return {"success": False, "error": str(e)}

    def generate_interactive_plot(
        self, plot_type: str, data: dict[str, Any], title: str = "Interaktif Grafik"
    ) -> dict[str, Any]:
        """
        Plotly ile interaktif grafik olustur

        Args:
            plot_type: Grafik tipi
            data: Veri
            title: Baslik

        Returns:
            HTML string veya dosya yolu
        """
        if not self.plotly_available:
            return {"success": False, "error": "Plotly yuklu degil"}

        try:
            if plot_type == "line":
                fig = self.go.Figure()
                fig.add_trace(
                    self.go.Scatter(
                        x=data.get("x", []),
                        y=data.get("y", []),
                        mode="lines+markers",
                        name="Veri",
                    )
                )

            elif plot_type == "bar":
                fig = self.go.Figure()
                fig.add_trace(
                    self.go.Bar(x=data.get("categories", []), y=data.get("values", []))
                )

            else:
                # Default: line
                fig = self.go.Figure()
                fig.add_trace(
                    self.go.Scatter(
                        x=data.get("x", []),
                        y=data.get("y", []),
                        mode="lines+markers",
                        name="Veri",
                    )
                )

            fig.update_layout(
                title=title, xaxis_title="X", yaxis_title="Y", hovermode="closest"
            )

            # HTML olarak dondur
            html_str = fig.to_html(include_plotlyjs="cdn")

            return {"success": True, "html": html_str, "plot_type": plot_type}

        except Exception as e:
            logger.error(f"Interaktif grafik olusturma hatasi: {e}")
            return {"success": False, "error": str(e)}
