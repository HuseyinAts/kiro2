"""
Visual Content Generator - Phase 1-4: Complete Visual Questions System

This service generates visual content for questions:
- Phase 1: Markdown tables (statistics, data comparison, schedules) ✓
- Phase 2: Graphs (line, bar, pie, scatter, histogram) ✓
- Phase 3: Geometry figures (triangles, circles, shapes) ✓
- Phase 4: Maps & Diagrams (geographic maps, flowcharts, Venn diagrams, timelines) ✓

Usage:
    generator = VisualContentGenerator()

    # Generate table (Phase 1)
    table_data = generator.generate_table(
        subject="Matematik",
        topic="İstatistik",
        data_type="frequency_table"
    )

    # Generate graph (Phase 2)
    graph_data = generator.generate_graph(
        subject="Fizik",
        topic="Hareket",
        graph_type="line"
    )

    # Generate geometry (Phase 3)
    geometry_data = generator.generate_geometry(
        subject="Matematik",
        topic="Geometri",
        geometry_type="triangle",
        shape_subtype="right_triangle"
    )

    # Generate map/diagram (Phase 4)
    map_data = generator.generate_map_diagram(
        subject="Coğrafya",
        topic="Türkiye Bölgeleri",
        diagram_type="geographic_map",
        diagram_subtype="turkey_regions"
    )

    question_with_visual = generator.create_question_with_visual(
        stem="Aşağıdaki şekle göre...",
        visual_content=geometry_data
    )
"""

import random
from typing import Literal

from services.geometry_generator import GeometryGenerator
from services.graph_generator import GraphGenerator
from services.map_diagram_generator import MapDiagramGenerator


class VisualContentGenerator:
    """Generates visual content (tables, graphs, diagrams) for questions"""

    def __init__(self):
        """Initialize visual content generator"""
        self.visual_types = {
            "table": self.generate_table,
            "graph": self.generate_graph,  # Phase 2 - IMPLEMENTED
            "geometry": self.generate_geometry,  # Phase 3 - IMPLEMENTED
            "map_diagram": self.generate_map_diagram,  # Phase 4 - IMPLEMENTED
        }
        self.graph_generator = GraphGenerator()  # Phase 2: Graph support
        self.geometry_generator = GeometryGenerator()  # Phase 3: Geometry support
        self.map_diagram_generator = MapDiagramGenerator()  # Phase 4: Maps & Diagrams

    # ==================== PHASE 1: TABLES ====================

    def generate_table(
        self,
        subject: str,
        topic: str,
        data_type: Literal[
            "frequency_table",
            "comparison_table",
            "schedule_table",
            "statistics_table",
            "price_table",
            "grade_table",
        ] = "frequency_table",
        rows: int = 4,
        columns: int = 3,
    ) -> dict:
        """
        Generate markdown table for questions

        Args:
            subject: Question subject (Matematik, Türkçe, etc.)
            topic: Question topic (İstatistik, Veri Analizi, etc.)
            data_type: Type of table to generate
            rows: Number of data rows (excluding header)
            columns: Number of columns

        Returns:
            Visual content dict with markdown table
        """
        if data_type == "frequency_table":
            return self._generate_frequency_table(rows)
        if data_type == "comparison_table":
            return self._generate_comparison_table(rows, columns)
        if data_type == "statistics_table":
            return self._generate_statistics_table()
        if data_type == "price_table":
            return self._generate_price_table(rows)
        if data_type == "grade_table":
            return self._generate_grade_table(rows)
        if data_type == "schedule_table":
            return self._generate_schedule_table()
        return self._generate_generic_table(rows, columns)

    def _generate_frequency_table(self, rows: int = 4) -> dict:
        """Generate frequency distribution table"""
        # Example: Age distribution, test scores, etc.
        categories = ["A", "B", "C", "D", "E"][:rows]
        frequencies = [random.randint(5, 25) for _ in range(rows)]

        # Build markdown table
        headers = ["Kategori", "Frekans", "Yüzde (%)"]
        total = sum(frequencies)

        table_rows = []
        for i, (cat, freq) in enumerate(zip(categories, frequencies)):
            percentage = round((freq / total) * 100, 1)
            table_rows.append(f"| {cat} | {freq} | {percentage} |")

        markdown = self._build_markdown_table(headers, table_rows)

        return {
            "type": "table",
            "format": "markdown",
            "content": markdown,
            "data": {
                "categories": categories,
                "frequencies": frequencies,
                "total": total,
            },
            "metadata": {
                "caption": "Tablo 1: Frekans Dağılımı",
                "alt_text": "Frequency distribution table",
                "rows": rows,
                "columns": len(headers),
            },
        }

    def _generate_comparison_table(self, rows: int = 4, columns: int = 3) -> dict:
        """Generate comparison table (products, options, features)"""
        headers = ["Ürün"] + [f"Özellik {i+1}" for i in range(columns - 1)]

        table_rows = []
        for i in range(rows):
            row_data = [f"Ürün {chr(65+i)}"]  # A, B, C, D
            for j in range(columns - 1):
                value = random.choice(["Evet", "Hayır", f"{random.randint(10, 100)}"])
                row_data.append(value)
            table_rows.append("| " + " | ".join(row_data) + " |")

        markdown = self._build_markdown_table(headers, table_rows)

        return {
            "type": "table",
            "format": "markdown",
            "content": markdown,
            "metadata": {
                "caption": "Tablo 1: Ürün Karşılaştırması",
                "alt_text": "Product comparison table",
                "rows": rows,
                "columns": columns,
            },
        }

    def _generate_statistics_table(self) -> dict:
        """Generate statistics summary table"""
        stats = [
            ("Ortalama", round(random.uniform(50, 90), 2)),
            ("Medyan", round(random.uniform(45, 85), 2)),
            ("Mod", random.randint(40, 90)),
            ("Standart Sapma", round(random.uniform(5, 15), 2)),
            ("Varyans", round(random.uniform(25, 225), 2)),
        ]

        headers = ["İstatistik", "Değer"]
        table_rows = [f"| {name} | {value} |" for name, value in stats]

        markdown = self._build_markdown_table(headers, table_rows)

        return {
            "type": "table",
            "format": "markdown",
            "content": markdown,
            "data": {"statistics": dict(stats)},
            "metadata": {
                "caption": "Tablo 1: İstatistiksel Özet",
                "alt_text": "Statistical summary table",
                "rows": len(stats),
                "columns": len(headers),
            },
        }

    def _generate_price_table(self, rows: int = 4) -> dict:
        """Generate price/cost table"""
        products = ["Kalem", "Defter", "Silgi", "Kalemtraş", "Cetvel"][:rows]

        headers = ["Ürün", "Fiyat (₺)", "Miktar", "Toplam (₺)"]
        table_rows = []

        for product in products:
            price = random.randint(5, 50)
            quantity = random.randint(1, 10)
            total = price * quantity
            table_rows.append(f"| {product} | {price} | {quantity} | {total} |")

        markdown = self._build_markdown_table(headers, table_rows)

        return {
            "type": "table",
            "format": "markdown",
            "content": markdown,
            "metadata": {
                "caption": "Tablo 1: Fiyat Listesi",
                "alt_text": "Price list table",
                "rows": rows,
                "columns": len(headers),
            },
        }

    def _generate_grade_table(self, rows: int = 5) -> dict:
        """Generate student grades table"""
        students = [f"Öğrenci {i+1}" for i in range(rows)]
        subjects = ["Matematik", "Türkçe", "Fen"]

        headers = ["Öğrenci"] + subjects + ["Ortalama"]
        table_rows = []

        for student in students:
            grades = [random.randint(50, 100) for _ in range(len(subjects))]
            avg = round(sum(grades) / len(grades), 1)
            row = f"| {student} | " + " | ".join(map(str, grades)) + f" | {avg} |"
            table_rows.append(row)

        markdown = self._build_markdown_table(headers, table_rows)

        return {
            "type": "table",
            "format": "markdown",
            "content": markdown,
            "metadata": {
                "caption": "Tablo 1: Öğrenci Notları",
                "alt_text": "Student grades table",
                "rows": rows,
                "columns": len(headers),
            },
        }

    def _generate_schedule_table(self) -> dict:
        """Generate schedule/timetable"""
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        times = ["09:00-10:00", "10:00-11:00", "11:00-12:00"]

        headers = ["Saat"] + days
        table_rows = []

        subjects = ["Matematik", "Türkçe", "Fen", "Sosyal", "İngilizce", "Beden"]

        for time in times:
            row_subjects = [random.choice(subjects) for _ in range(len(days))]
            row = f"| {time} | " + " | ".join(row_subjects) + " |"
            table_rows.append(row)

        markdown = self._build_markdown_table(headers, table_rows)

        return {
            "type": "table",
            "format": "markdown",
            "content": markdown,
            "metadata": {
                "caption": "Tablo 1: Ders Programı",
                "alt_text": "Class schedule table",
                "rows": len(times),
                "columns": len(headers),
            },
        }

    def _generate_generic_table(self, rows: int = 4, columns: int = 3) -> dict:
        """Generate generic data table"""
        headers = [f"Sütun {i+1}" for i in range(columns)]
        table_rows = []

        for i in range(rows):
            row_data = [f"Veri {i+1}-{j+1}" for j in range(columns)]
            table_rows.append("| " + " | ".join(row_data) + " |")

        markdown = self._build_markdown_table(headers, table_rows)

        return {
            "type": "table",
            "format": "markdown",
            "content": markdown,
            "metadata": {
                "caption": "Tablo 1: Veri Tablosu",
                "alt_text": "Generic data table",
                "rows": rows,
                "columns": columns,
            },
        }

    def _build_markdown_table(self, headers: list[str], rows: list[str]) -> str:
        """Build markdown table from headers and rows"""
        # Header row
        header_row = "| " + " | ".join(headers) + " |"

        # Separator row
        separator = "|" + "|".join([" --- " for _ in headers]) + "|"

        # Combine all
        table = "\n".join([header_row, separator] + rows)

        return table

    # ==================== PHASE 2: GRAPHS ====================

    def generate_graph(
        self,
        subject: str,
        topic: str,
        graph_type: Literal["line", "bar", "pie", "scatter", "histogram"] = "line",
        complexity: str = "medium",
    ) -> dict:
        """
        Generate contextual graph for question

        Args:
            subject: Question subject (Fizik, Matematik, Coğrafya, etc.)
            topic: Question topic (Hareket, İstatistik, etc.)
            graph_type: Type of graph to generate
            complexity: Complexity level (simple, medium, complex)

        Returns:
            Visual content dict with SVG graph
        """
        # Generate context-aware data based on subject and graph type
        if graph_type == "line":
            data = self._generate_line_data(subject, topic, complexity)
            title = f"Grafik 1: {topic}"
            x_label = self._get_x_label(subject, graph_type)
            y_label = self._get_y_label(subject, graph_type)
        elif graph_type == "bar":
            data = self._generate_bar_data(subject, topic, complexity)
            title = f"Grafik 1: {topic} Karşılaştırması"
            x_label = "Kategoriler"
            y_label = self._get_y_label(subject, graph_type)
        elif graph_type == "pie":
            data = self._generate_pie_data(subject, topic, complexity)
            title = f"Grafik 1: {topic} Dağılımı"
            x_label = ""
            y_label = ""
        elif graph_type == "scatter":
            data = self._generate_scatter_data(subject, topic, complexity)
            title = f"Grafik 1: {topic}"
            x_label = self._get_x_label(subject, graph_type)
            y_label = self._get_y_label(subject, graph_type)
        elif graph_type == "histogram":
            data = self._generate_histogram_data(subject, topic, complexity)
            title = f"Grafik 1: {topic} Frekans Dağılımı"
            x_label = "Değer Aralıkları"
            y_label = "Frekans"
        else:
            raise ValueError(f"Unknown graph_type: {graph_type}")

        # Generate graph using GraphGenerator
        return self.graph_generator.generate_graph(
            graph_type=graph_type,
            data=data,
            title=title,
            x_label=x_label,
            y_label=y_label,
        )

    def _generate_line_data(self, subject: str, topic: str, complexity: str) -> dict:
        """Generate realistic line graph data based on subject"""
        if "fizik" in subject.lower() or "hareket" in topic.lower():
            # Physics: Motion graphs (time vs velocity/position)
            x = list(range(6))
            y = [0, 10, 20, 25, 35, 40]
            return {"x": x, "y": y}
        if "matematik" in subject.lower():
            # Math: Function graphs
            x = list(range(-5, 6))
            y = [x_val**2 for x_val in x]
            return {"x": x, "y": y}
        # Generic trend data
        x = list(range(2015, 2021))
        y = [random.randint(50, 100) for _ in x]
        return {"x": x, "y": y}

    def _generate_bar_data(self, subject: str, topic: str, complexity: str) -> dict:
        """Generate realistic bar chart data based on subject"""
        if "matematik" in subject.lower() or "istatistik" in topic.lower():
            # Statistics comparison
            categories = ["A", "B", "C", "D"]
            values = [random.randint(10, 30) for _ in categories]
            return {
                "categories": categories,
                "values": values,
                "orientation": "vertical",
            }
        if "cografya" in subject.lower():
            # Geographic data
            categories = ["Bölge 1", "Bölge 2", "Bölge 3"]
            values = [random.randint(100, 500) for _ in categories]
            return {
                "categories": categories,
                "values": values,
                "orientation": "vertical",
            }
        # Generic categories
        categories = ["Grup A", "Grup B", "Grup C", "Grup D"]
        values = [random.randint(15, 40) for _ in categories]
        return {
            "categories": categories,
            "values": values,
            "orientation": "vertical",
        }

    def _generate_pie_data(self, subject: str, topic: str, complexity: str) -> dict:
        """Generate realistic pie chart data based on subject"""
        if "cografya" in subject.lower() or "nufus" in topic.lower():
            # Population distribution
            labels = ["Kıta A", "Kıta B", "Kıta C", "Kıta D"]
            values = [30, 25, 25, 20]
            return {"labels": labels, "values": values, "show_percentages": True}
        if "turkce" in subject.lower():
            # Literary analysis
            labels = ["Roman", "Hikaye", "Şiir", "Deneme"]
            values = [35, 30, 20, 15]
            return {"labels": labels, "values": values, "show_percentages": True}
        # Generic distribution
        labels = ["A", "B", "C", "D"]
        values = [40, 30, 20, 10]
        return {"labels": labels, "values": values, "show_percentages": True}

    def _generate_scatter_data(self, subject: str, topic: str, complexity: str) -> dict:
        """Generate realistic scatter plot data based on subject"""
        if "matematik" in subject.lower() or "korelasyon" in topic.lower():
            # Math: Correlation data
            x = [1, 2, 3, 4, 5, 6, 7, 8]
            y = [2.1, 3.8, 6.3, 7.9, 10.2, 12.1, 13.8, 16.1]
            return {"x": x, "y": y, "show_trendline": True}
        # Generic correlation
        x = list(range(1, 11))
        y = [x_val * 2 + random.uniform(-1, 1) for x_val in x]
        return {"x": x, "y": y, "show_trendline": True}

    def _generate_histogram_data(
        self, subject: str, topic: str, complexity: str
    ) -> dict:
        """Generate realistic histogram data based on subject"""
        if "biyoloji" in subject.lower():
            # Biology: Measurement distribution
            values = [random.randint(150, 200) for _ in range(50)]
            return {"values": values, "bins": 8}
        if "matematik" in subject.lower():
            # Math: Score distribution
            values = [random.randint(0, 100) for _ in range(40)]
            return {"values": values, "bins": 10}
        # Generic frequency distribution
        values = [random.randint(10, 50) for _ in range(30)]
        return {"values": values, "bins": 6}

    def _get_x_label(self, subject: str, graph_type: str) -> str:
        """Get appropriate X-axis label based on subject"""
        if "fizik" in subject.lower():
            return "Zaman (s)"
        if "matematik" in subject.lower():
            return "x"
        if "cografya" in subject.lower():
            return "Yıl"
        return "X Ekseni"

    def _get_y_label(self, subject: str, graph_type: str) -> str:
        """Get appropriate Y-axis label based on subject"""
        if "fizik" in subject.lower():
            return "Hız (m/s)"
        if "matematik" in subject.lower():
            if graph_type == "bar":
                return "Frekans"
            return "y"
        if "cografya" in subject.lower():
            return "Değer"
        return "Y Ekseni"

    # ==================== PHASE 3: GEOMETRY ====================

    def generate_geometry(
        self,
        subject: str,
        topic: str,
        geometry_type: Literal[
            "triangle", "circle", "quadrilateral", "polygon", "3d_shape"
        ] = "triangle",
        shape_subtype: str | None = None,
        complexity: str = "medium",
    ) -> dict:
        """
        Generate contextual geometry figure for question

        Args:
            subject: Question subject (Matematik, Fizik, etc.)
            topic: Question topic (Geometri, Açılar, etc.)
            geometry_type: Type of geometry to generate
            shape_subtype: Specific shape (auto-selected if None)
            complexity: Complexity level (simple, medium, complex)

        Returns:
            Visual content dict with SVG geometry
        """
        # Auto-select shape_subtype if not provided
        if shape_subtype is None:
            shape_subtype = self._select_shape_subtype(geometry_type, subject, topic)

        # Generate context-aware dimensions and labels
        dimensions = self._generate_geometry_dimensions(
            geometry_type, shape_subtype, subject, topic, complexity
        )
        labels = self._generate_geometry_labels(geometry_type, shape_subtype)

        # Determine whether to show measurements and angles
        show_measurements = (
            "geometri" in topic.lower()
            or "alan" in topic.lower()
            or "cevre" in topic.lower()
        )
        show_angles = "aci" in topic.lower() or "trigonometri" in topic.lower()

        # Generate geometry using GeometryGenerator
        return self.geometry_generator.generate_geometry(
            geometry_type=geometry_type,
            shape_subtype=shape_subtype,
            dimensions=dimensions,
            labels=labels,
            show_measurements=show_measurements,
            show_angles=show_angles,
        )

    def _select_shape_subtype(
        self, geometry_type: str, subject: str, topic: str
    ) -> str:
        """Auto-select appropriate shape subtype based on context"""
        if geometry_type == "triangle":
            if "dik" in topic.lower() or "pisagor" in topic.lower():
                return "right_triangle"
            if "eskenar" in topic.lower():
                return "equilateral_triangle"
            if "ikizkenar" in topic.lower():
                return "isosceles_triangle"
            return "right_triangle"  # Default

        if geometry_type == "circle":
            if "dilim" in topic.lower() or "sektor" in topic.lower():
                return "sector"
            return "complete_circle"

        if geometry_type == "quadrilateral":
            if "kare" in topic.lower():
                return "square"
            if "dikdortgen" in topic.lower():
                return "rectangle"
            if "yamuk" in topic.lower():
                return "trapezoid"
            return "rectangle"  # Default

        if geometry_type == "polygon":
            if "besgen" in topic.lower():
                return "pentagon"
            if "altigen" in topic.lower():
                return "hexagon"
            if "sekizgen" in topic.lower():
                return "octagon"
            return "hexagon"  # Default

        if geometry_type == "3d_shape":
            if "kup" in topic.lower() or "zar" in topic.lower():
                return "cube"
            if "dikdortgen" in topic.lower() and "prizma" in topic.lower():
                return "rectangular_prism"
            if "silindir" in topic.lower():
                return "cylinder"
            if "kure" in topic.lower():
                return "sphere"
            return "cube"  # Default

        return "square"  # Fallback

    def _generate_geometry_dimensions(
        self,
        geometry_type: str,
        shape_subtype: str,
        subject: str,
        topic: str,
        complexity: str,
    ) -> dict[str, float]:
        """Generate realistic dimensions based on geometry type and context"""
        import random

        if geometry_type == "triangle":
            if shape_subtype == "right_triangle":
                # Pythagorean triples for realistic problems
                triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17)]
                base, height, _ = random.choice(triples)
                return {"base": float(base), "height": float(height)}
            if shape_subtype == "equilateral_triangle":
                side = random.choice([4, 5, 6, 8, 10])
                return {"side": float(side)}
            if shape_subtype == "isosceles_triangle":
                base = random.randint(4, 8)
                equal_side = random.randint(6, 12)
                return {"base": float(base), "equal_side": float(equal_side)}
            return {"base": 6.0, "height": 8.0}

        if geometry_type == "circle":
            if shape_subtype == "complete_circle":
                radius = random.choice([3, 4, 5, 6, 7])
                return {"radius": float(radius), "show_diameter": True}
            if shape_subtype == "sector":
                radius = random.choice([4, 5, 6])
                angle = random.choice([30, 45, 60, 90, 120])
                return {"radius": float(radius), "angle": float(angle)}
            return {"radius": 5.0}

        if geometry_type == "quadrilateral":
            if shape_subtype == "square":
                side = random.choice([4, 5, 6, 8, 10])
                return {"side": float(side)}
            if shape_subtype == "rectangle":
                width = random.randint(6, 12)
                height = random.randint(4, 8)
                return {"width": float(width), "height": float(height)}
            if shape_subtype == "trapezoid":
                base1 = random.randint(8, 12)
                base2 = random.randint(4, 7)
                height = random.randint(4, 6)
                return {
                    "base1": float(base1),
                    "base2": float(base2),
                    "height": float(height),
                }
            return {"width": 8.0, "height": 5.0}

        if geometry_type == "polygon":
            side = random.choice([4, 5, 6, 7])
            return {"side": float(side)}

        if geometry_type == "3d_shape":
            if shape_subtype == "cube":
                side = random.choice([4, 5, 6, 8])
                return {"side": float(side)}
            if shape_subtype == "rectangular_prism":
                width = random.randint(5, 10)
                height = random.randint(4, 8)
                depth = random.randint(4, 8)
                return {
                    "width": float(width),
                    "height": float(height),
                    "depth": float(depth),
                }
            if shape_subtype == "cylinder":
                radius = random.choice([3, 4, 5])
                height = random.randint(6, 10)
                return {"radius": float(radius), "height": float(height)}
            if shape_subtype == "sphere":
                radius = random.choice([4, 5, 6, 7])
                return {"radius": float(radius)}
            return {"side": 5.0}

        return {}  # Fallback

    def _generate_geometry_labels(
        self, geometry_type: str, shape_subtype: str
    ) -> dict[str, list[str]]:
        """Generate vertex labels for geometry"""
        if geometry_type == "triangle":
            return {"vertex_labels": ["A", "B", "C"]}
        if geometry_type == "quadrilateral":
            return {"vertex_labels": ["A", "B", "C", "D"]}
        if geometry_type == "polygon":
            n_sides = {"pentagon": 5, "hexagon": 6, "octagon": 8}.get(shape_subtype, 6)
            return {
                "vertex_labels": [chr(65 + i) for i in range(n_sides)]
            }  # A, B, C, ...
        return {}

    # ==================== PHASE 4: MAPS & DIAGRAMS ====================

    def generate_map_diagram(
        self,
        subject: str,
        topic: str,
        diagram_type: Literal[
            "geographic_map", "process_diagram", "classification_diagram", "timeline"
        ] = "geographic_map",
        diagram_subtype: str | None = None,
        complexity: str = "medium",
    ) -> dict:
        """
        Generate contextual map or diagram for question

        Args:
            subject: Question subject (Coğrafya, Tarih, Matematik, etc.)
            topic: Question topic
            diagram_type: Type of diagram
            diagram_subtype: Specific diagram (auto-selected if None)
            complexity: Complexity level (simple, medium, complex)

        Returns:
            Visual content dict with SVG map/diagram
        """
        # Auto-select diagram_subtype if not provided
        if diagram_subtype is None:
            diagram_subtype = self._select_diagram_subtype(diagram_type, subject, topic)

        # Generate context-aware content
        content = self._generate_diagram_content(
            diagram_type, diagram_subtype, subject, topic, complexity
        )

        # Generate map/diagram using MapDiagramGenerator
        return self.map_diagram_generator.generate_diagram(
            diagram_type=diagram_type,
            diagram_subtype=diagram_subtype,
            content=content,
            labels=None,  # Use default labels
            show_legend=True,
        )

    def _select_diagram_subtype(
        self, diagram_type: str, subject: str, topic: str
    ) -> str:
        """Auto-select appropriate diagram subtype based on context"""
        topic_lower = topic.lower()
        subject_lower = subject.lower()

        if diagram_type == "geographic_map":
            if "bölge" in topic_lower or "coğrafi" in topic_lower:
                return "turkey_regions"
            if "şehir" in topic_lower or "il" in topic_lower:
                return "turkey_cities"
            if "kıta" in topic_lower or "dünya" in topic_lower:
                return "continents"
            return "turkey_regions"  # Default

        if diagram_type == "process_diagram":
            if "döngü" in topic_lower or "cycle" in topic_lower:
                return "cycle_diagram"
            if "sistem" in topic_lower:
                return "system_diagram"
            return "flowchart"  # Default

        if diagram_type == "classification_diagram":
            if (
                "sınıflandırma" in topic_lower
                or "tür" in topic_lower
                or "taksonomi" in topic_lower
            ):
                return "tree_diagram"
            if "küme" in topic_lower or "venn" in topic_lower:
                return "venn_diagram"
            if "matris" in topic_lower or "karşılaştırma" in topic_lower:
                return "matrix_diagram"
            return "venn_diagram"  # Default for Matematik

        if diagram_type == "timeline":
            return "horizontal_timeline"  # Default

        return "turkey_regions"  # Fallback

    def _generate_diagram_content(
        self,
        diagram_type: str,
        diagram_subtype: str,
        subject: str,
        topic: str,
        complexity: str,
    ) -> dict:
        """Generate contextual content for diagram"""

        if diagram_type == "geographic_map":
            return self._generate_geographic_map_content(
                diagram_subtype, subject, topic
            )

        if diagram_type == "process_diagram":
            return self._generate_process_diagram_content(
                diagram_subtype, subject, topic
            )

        if diagram_type == "classification_diagram":
            return self._generate_classification_diagram_content(
                diagram_subtype, subject, topic
            )

        if diagram_type == "timeline":
            return self._generate_timeline_content(diagram_subtype, subject, topic)

        return {}

    def _generate_geographic_map_content(
        self, subtype: str, subject: str, topic: str
    ) -> dict:
        """Generate content for geographic maps"""
        if subtype == "turkey_regions":
            # Randomly select 1-3 regions to highlight
            all_regions = [
                "Marmara",
                "Ege",
                "Akdeniz",
                "İç Anadolu",
                "Karadeniz",
                "Doğu Anadolu",
                "Güneydoğu Anadolu",
            ]
            num_highlight = random.randint(1, 3)
            highlight = random.sample(all_regions, num_highlight)
            return {
                "title": "Türkiye Coğrafi Bölgeleri",
                "highlight_regions": highlight,
            }

        if subtype == "turkey_cities":
            # Select 3-5 cities
            all_cities = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya"]
            num_cities = random.randint(3, 5)
            cities = random.sample(all_cities, num_cities)
            return {"title": "Türkiye Büyük Şehirleri", "cities": cities}

        if subtype == "continents":
            # Highlight 1-2 continents
            all_continents = [
                "Asya",
                "Avrupa",
                "Afrika",
                "Kuzey Amerika",
                "Güney Amerika",
                "Avustralya",
            ]
            num_highlight = random.randint(1, 2)
            highlight = random.sample(all_continents, num_highlight)
            return {"title": "Dünya Kıtaları", "highlight_continents": highlight}

        return {}

    def _generate_process_diagram_content(
        self, subtype: str, subject: str, topic: str
    ) -> dict:
        """Generate content for process diagrams"""
        if subtype == "flowchart":
            # Example: Water cycle
            return {
                "title": "Su Döngüsü",
                "nodes": [
                    {
                        "id": "start",
                        "type": "oval",
                        "text": "Su Kaynakları",
                        "x": 5,
                        "y": 10,
                        "width": 3,
                        "height": 1.2,
                    },
                    {
                        "id": "evap",
                        "type": "rectangle",
                        "text": "Buharlaşma",
                        "x": 5,
                        "y": 8,
                        "width": 3,
                        "height": 1.2,
                    },
                    {
                        "id": "cond",
                        "type": "rectangle",
                        "text": "Yoğunlaşma",
                        "x": 5,
                        "y": 6,
                        "width": 3,
                        "height": 1.2,
                    },
                    {
                        "id": "precip",
                        "type": "rectangle",
                        "text": "Yağış",
                        "x": 5,
                        "y": 4,
                        "width": 3,
                        "height": 1.2,
                    },
                    {
                        "id": "end",
                        "type": "oval",
                        "text": "Su Kaynaklarına Dönüş",
                        "x": 5,
                        "y": 2,
                        "width": 3,
                        "height": 1.2,
                    },
                ],
                "edges": [
                    {"from": "start", "to": "evap"},
                    {"from": "evap", "to": "cond"},
                    {"from": "cond", "to": "precip"},
                    {"from": "precip", "to": "end"},
                ],
            }

        if subtype == "cycle_diagram":
            return {
                "title": "Döngüsel Süreç",
                "steps": [
                    {"text": "1. Aşama"},
                    {"text": "2. Aşama"},
                    {"text": "3. Aşama"},
                    {"text": "4. Aşama"},
                ],
            }

        if subtype == "system_diagram":
            return {
                "title": "Sistem Bileşenleri",
                "components": [
                    {
                        "id": "comp1",
                        "text": "Bileşen A",
                        "x": 2.5,
                        "y": 5,
                        "width": 2.5,
                        "height": 1.5,
                    },
                    {
                        "id": "comp2",
                        "text": "Bileşen B",
                        "x": 7.5,
                        "y": 5,
                        "width": 2.5,
                        "height": 1.5,
                    },
                    {
                        "id": "comp3",
                        "text": "Bileşen C",
                        "x": 5,
                        "y": 2.5,
                        "width": 2.5,
                        "height": 1.5,
                    },
                ],
                "connections": [
                    {"from": "comp1", "to": "comp2", "label": "Veri Akışı"},
                    {"from": "comp2", "to": "comp3", "label": "İşlem"},
                ],
            }

        return {}

    def _generate_classification_diagram_content(
        self, subtype: str, subject: str, topic: str
    ) -> dict:
        """Generate content for classification diagrams"""
        if subtype == "tree_diagram":
            return {
                "title": "Canlı Sınıflandırması",
                "tree": {
                    "root": "Canlılar",
                    "levels": [
                        {"nodes": ["Hayvanlar", "Bitkiler"]},
                        {
                            "nodes": [
                                "Omurgalılar",
                                "Omurgasızlar",
                                "Tohumlu",
                                "Tohumsuz",
                            ]
                        },
                    ],
                },
            }

        if subtype == "venn_diagram":
            # Generate sets with elements
            set1_only = [str(random.randint(1, 10)) for _ in range(2)]
            set2_only = [str(random.randint(11, 20)) for _ in range(2)]
            intersection = [str(random.randint(21, 30)) for _ in range(2)]

            return {
                "title": "Küme Diyagramı",
                "sets": [
                    {"label": "A", "only": set1_only},
                    {"label": "B", "only": set2_only},
                ],
                "intersection": intersection,
            }

        if subtype == "matrix_diagram":
            return {
                "title": "2x2 Karşılaştırma Matrisi",
                "rows": 2,
                "cols": 2,
                "cells": {
                    "0,0": "Yüksek\nKalite",
                    "0,1": "Yüksek\nMaliyet",
                    "1,0": "Düşük\nKalite",
                    "1,1": "Düşük\nMaliyet",
                },
                "x_label": "Maliyet",
                "y_label": "Kalite",
            }

        return {}

    def _generate_timeline_content(
        self, subtype: str, subject: str, topic: str
    ) -> dict:
        """Generate content for timelines"""
        # Turkish Republic history
        events = [
            {"year": 1920, "event": "TBMM Açıldı"},
            {"year": 1923, "event": "Cumhuriyet İlan Edildi"},
            {"year": 1928, "event": "Harf Devrimi"},
            {"year": 1934, "event": "Soyadı Kanunu"},
            {"year": 1945, "event": "BM Üyeliği"},
        ]

        # Randomly select 3-5 events
        num_events = random.randint(3, 5)
        selected_events = random.sample(events, num_events)
        selected_events = sorted(selected_events, key=lambda x: x["year"])

        return {"title": "Türkiye Cumhuriyeti Tarihi", "events": selected_events}

    # ==================== HELPER METHODS ====================

    def create_question_with_visual(
        self, stem: str, visual_content: dict, options: list[str], correct_answer: str
    ) -> dict:
        """
        Create a complete question with visual content

        Args:
            stem: Question text
            visual_content: Visual content dict from generate_table()
            options: Answer options (A, B, C, D, E)
            correct_answer: Correct answer letter

        Returns:
            Complete question dict with visual_content field
        """
        return {
            "stem": stem,
            "options": options,
            "correct_answer": correct_answer,
            "visual_content": visual_content,
        }

    def get_table_example_for_prompt(self, data_type: str = "frequency_table") -> str:
        """
        Get example table for LLM prompt

        This helps the LLM understand markdown table format
        """
        example = self.generate_table("Matematik", "İstatistik", data_type, rows=3)

        prompt_text = f"""
ÖRNEK TABLO FORMATI:

{example['content']}

Tablolar markdown formatında olmalıdır:
- | ile sütunlar ayrılır
- İlk satır: başlıklar
- İkinci satır: ayırıcı (| --- | --- |)
- Sonraki satırlar: veriler
"""
        return prompt_text


# ==================== DEMO / TESTING ====================

if __name__ == "__main__":
    # Demo usage
    generator = VisualContentGenerator()

    print("=" * 60)
    print("PHASE 1: TABLE GENERATION DEMO")
    print("=" * 60)

    # Test frequency table
    print("\n1. Frequency Table:")
    freq_table = generator.generate_table("Matematik", "İstatistik", "frequency_table")
    print(freq_table["content"])

    # Test comparison table
    print("\n2. Comparison Table:")
    comp_table = generator.generate_table(
        "Matematik", "Veri Analizi", "comparison_table"
    )
    print(comp_table["content"])

    # Test statistics table
    print("\n3. Statistics Table:")
    stats_table = generator.generate_table(
        "Matematik", "İstatistik", "statistics_table"
    )
    print(stats_table["content"])

    # Test price table
    print("\n4. Price Table:")
    price_table = generator.generate_table("Matematik", "Problemler", "price_table")
    print(price_table["content"])

    # Complete question example
    print("\n5. Complete Question with Table:")
    question = generator.create_question_with_visual(
        stem="Aşağıdaki tabloda öğrencilerin yaş dağılımı verilmiştir. Buna göre mod kaçtır?",
        visual_content=freq_table,
        options=["A) 15", "B) 16", "C) 17", "D) 18", "E) 19"],
        correct_answer="B",
    )
    print(f"Stem: {question['stem']}")
    print(f"\n{question['visual_content']['content']}")
    print(f"\nOptions: {question['options']}")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)
