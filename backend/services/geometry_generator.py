"""
GeometryGenerator Service - Phase 3: Geometry

Generates SVG geometric figures for OSYM-style visual questions.

Supported geometry types:
1. Triangles (Ucgenler) - Right, isosceles, equilateral, scalene
2. Circles (Daireler) - Complete circles, sectors, segments
3. Quadrilaterals (Dortgenler) - Squares, rectangles, trapezoids, parallelograms
4. Polygons (Cokgenler) - Regular polygons (pentagon, hexagon, octagon)
5. 3D Shapes (3B Sekiller) - Prisms, pyramids, cylinders, cones, spheres

Usage:
    generator = GeometryGenerator()
    geometry_data = generator.generate_geometry(
        geometry_type="triangle",
        shape_subtype="right_triangle",
        dimensions={"base": 6, "height": 8},
        labels={"vertex_labels": ["A", "B", "C"]},
        show_measurements=True
    )
"""

import io
import math
from typing import Dict, Optional, Literal, Any
import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Wedge, Polygon as MplPolygon
import numpy as np

# OSYM Style Configuration
OSYM_GEOMETRY_STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "white",
    "axes.linewidth": 0,
    "axes.grid": False,
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "text.color": "black",
    "xtick.bottom": False,
    "xtick.top": False,
    "ytick.left": False,
    "ytick.right": False,
}


class GeometryGenerator:
    """
    Generate OSYM-style geometric figures in SVG format
    """

    def __init__(self):
        """Initialize GeometryGenerator with OSYM styling"""
        plt.style.use("default")
        plt.rcParams.update(OSYM_GEOMETRY_STYLE)

    def generate_geometry(
        self,
        geometry_type: Literal[
            "triangle", "circle", "quadrilateral", "polygon", "3d_shape"
        ],
        shape_subtype: str,
        dimensions: Dict[str, float],
        labels: Optional[Dict[str, Any]] = None,
        show_measurements: bool = True,
        show_angles: bool = False,
        style: str = "osym",
    ) -> Dict:
        """
        Generate geometric figure and return visual_content structure

        Args:
            geometry_type: Type of geometry ("triangle", "circle", "quadrilateral", "polygon", "3d_shape")
            shape_subtype: Specific shape (e.g., "right_triangle", "square", "sphere")
            dimensions: Shape dimensions (depends on geometry_type)
            labels: Vertex labels, measurement labels, etc.
            show_measurements: Whether to show length/area measurements
            show_angles: Whether to show angle measurements
            style: Style preset ("osym" for OSYM style)

        Returns:
            Dict with visual_content structure:
            {
                "type": "geometry",
                "format": "svg",
                "content": "<svg>...</svg>",
                "data": {...},
                "metadata": {...}
            }
        """
        # Validate geometry_type
        valid_types = ["triangle", "circle", "quadrilateral", "polygon", "3d_shape"]
        if geometry_type not in valid_types:
            raise ValueError(f"Invalid geometry_type. Must be one of: {valid_types}")

        # Default labels
        if labels is None:
            labels = {}

        # Generate geometry based on type
        if geometry_type == "triangle":
            svg_content = self._generate_triangle(
                shape_subtype, dimensions, labels, show_measurements, show_angles
            )
        elif geometry_type == "circle":
            svg_content = self._generate_circle(
                shape_subtype, dimensions, labels, show_measurements
            )
        elif geometry_type == "quadrilateral":
            svg_content = self._generate_quadrilateral(
                shape_subtype, dimensions, labels, show_measurements, show_angles
            )
        elif geometry_type == "polygon":
            svg_content = self._generate_polygon(
                shape_subtype, dimensions, labels, show_measurements
            )
        elif geometry_type == "3d_shape":
            svg_content = self._generate_3d_shape(
                shape_subtype, dimensions, labels, show_measurements
            )
        else:
            raise ValueError(f"Geometry type '{geometry_type}' not implemented")

        # Prepare metadata
        metadata = {
            "geometry_type": geometry_type,
            "shape_subtype": shape_subtype,
            "dimensions": dimensions,
            "description": self._generate_description(
                geometry_type, shape_subtype, dimensions
            ),
        }

        # Return visual_content structure
        return {
            "type": "geometry",
            "format": "svg",
            "content": svg_content,
            "data": {"dimensions": dimensions, "labels": labels},
            "metadata": metadata,
        }

    # ===== TRIANGLE GENERATION =====

    def _generate_triangle(
        self,
        subtype: str,
        dimensions: Dict[str, float],
        labels: Dict[str, Any],
        show_measurements: bool,
        show_angles: bool,
    ) -> str:
        """
        Generate triangle SVG

        Subtypes:
        - "right_triangle": Dik üçgen (base, height)
        - "isosceles_triangle": İkizkenar üçgen (base, equal_side)
        - "equilateral_triangle": Eşkenar üçgen (side)
        - "scalene_triangle": Çeşitkenar üçgen (side_a, side_b, side_c)
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_aspect("equal")
        ax.axis("off")

        if subtype == "right_triangle":
            base = dimensions.get("base", 6)
            height = dimensions.get("height", 8)

            # Vertices: Right angle at origin
            vertices = np.array([[0, 0], [base, 0], [0, height]])

            # Draw triangle
            triangle = MplPolygon(vertices, fill=False, edgecolor="black", linewidth=2)
            ax.add_patch(triangle)

            # Right angle marker
            marker_size = 0.5
            right_angle_square = MplPolygon(
                [
                    [0, 0],
                    [marker_size, 0],
                    [marker_size, marker_size],
                    [0, marker_size],
                ],
                fill=False,
                edgecolor="black",
                linewidth=1,
            )
            ax.add_patch(right_angle_square)

            # Vertex labels
            vertex_labels = labels.get("vertex_labels", ["A", "B", "C"])
            ax.text(-0.5, -0.5, vertex_labels[0], fontsize=14, fontweight="bold")
            ax.text(base + 0.3, -0.5, vertex_labels[1], fontsize=14, fontweight="bold")
            ax.text(
                -0.5, height + 0.3, vertex_labels[2], fontsize=14, fontweight="bold"
            )

            # Measurements
            if show_measurements:
                ax.text(base / 2, -0.8, f"{base} cm", fontsize=11, ha="center")
                ax.text(
                    -1.0,
                    height / 2,
                    f"{height} cm",
                    fontsize=11,
                    ha="center",
                    rotation=90,
                    va="center",
                )

                # Hypotenuse
                hypotenuse = math.sqrt(base**2 + height**2)
                mid_x, mid_y = base / 2, height / 2
                ax.text(mid_x + 0.8, mid_y + 0.5, f"{hypotenuse:.1f} cm", fontsize=11)

            ax.set_xlim(-2, base + 2)
            ax.set_ylim(-2, height + 2)

        elif subtype == "equilateral_triangle":
            side = dimensions.get("side", 8)

            # Vertices: Centered equilateral triangle
            height = side * math.sqrt(3) / 2
            vertices = np.array([[-side / 2, 0], [side / 2, 0], [0, height]])

            triangle = MplPolygon(vertices, fill=False, edgecolor="black", linewidth=2)
            ax.add_patch(triangle)

            # Vertex labels
            vertex_labels = labels.get("vertex_labels", ["A", "B", "C"])
            ax.text(
                -side / 2 - 0.5, -0.5, vertex_labels[0], fontsize=14, fontweight="bold"
            )
            ax.text(
                side / 2 + 0.3, -0.5, vertex_labels[1], fontsize=14, fontweight="bold"
            )
            ax.text(
                0,
                height + 0.5,
                vertex_labels[2],
                fontsize=14,
                fontweight="bold",
                ha="center",
            )

            # Measurements
            if show_measurements:
                ax.text(0, -0.9, f"{side} cm", fontsize=11, ha="center")
                ax.text(
                    side / 4 + 0.8, height / 2, f"{side} cm", fontsize=11, rotation=60
                )
                ax.text(
                    -side / 4 - 0.8, height / 2, f"{side} cm", fontsize=11, rotation=-60
                )

            # Equal side markers
            self._add_equal_markers(ax, vertices[0], vertices[1], 1)
            self._add_equal_markers(ax, vertices[1], vertices[2], 1)
            self._add_equal_markers(ax, vertices[2], vertices[0], 1)

            ax.set_xlim(-side / 2 - 2, side / 2 + 2)
            ax.set_ylim(-2, height + 2)

        elif subtype == "isosceles_triangle":
            base = dimensions.get("base", 6)
            equal_side = dimensions.get("equal_side", 8)

            # Calculate height using Pythagorean theorem
            height = math.sqrt(equal_side**2 - (base / 2) ** 2)

            vertices = np.array([[-base / 2, 0], [base / 2, 0], [0, height]])

            triangle = MplPolygon(vertices, fill=False, edgecolor="black", linewidth=2)
            ax.add_patch(triangle)

            # Vertex labels
            vertex_labels = labels.get("vertex_labels", ["A", "B", "C"])
            ax.text(
                -base / 2 - 0.5, -0.5, vertex_labels[0], fontsize=14, fontweight="bold"
            )
            ax.text(
                base / 2 + 0.3, -0.5, vertex_labels[1], fontsize=14, fontweight="bold"
            )
            ax.text(
                0,
                height + 0.5,
                vertex_labels[2],
                fontsize=14,
                fontweight="bold",
                ha="center",
            )

            # Measurements
            if show_measurements:
                ax.text(0, -0.9, f"{base} cm", fontsize=11, ha="center")
                ax.text(base / 4 + 0.8, height / 2, f"{equal_side} cm", fontsize=11)
                ax.text(-base / 4 - 1.2, height / 2, f"{equal_side} cm", fontsize=11)

            # Equal side markers (two equal sides)
            self._add_equal_markers(ax, vertices[1], vertices[2], 2)
            self._add_equal_markers(ax, vertices[2], vertices[0], 2)

            ax.set_xlim(-base / 2 - 2, base / 2 + 2)
            ax.set_ylim(-2, height + 2)

        else:
            raise ValueError(f"Unknown triangle subtype: {subtype}")

        return self._fig_to_svg(fig)

    # ===== CIRCLE GENERATION =====

    def _generate_circle(
        self,
        subtype: str,
        dimensions: Dict[str, float],
        labels: Dict[str, Any],
        show_measurements: bool,
    ) -> str:
        """
        Generate circle SVG

        Subtypes:
        - "complete_circle": Complete circle with radius/diameter
        - "sector": Circular sector (pizza slice)
        - "segment": Circular segment
        """
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_aspect("equal")
        ax.axis("off")

        if subtype == "complete_circle":
            radius = dimensions.get("radius", 5)

            # Draw circle
            circle = plt.Circle(
                (0, 0), radius, fill=False, edgecolor="black", linewidth=2
            )
            ax.add_patch(circle)

            # Center point
            ax.plot(0, 0, "ko", markersize=5)
            ax.text(0.2, 0.2, "O", fontsize=14, fontweight="bold")

            # Radius line
            ax.plot([0, radius], [0, 0], "k-", linewidth=1.5)

            # Diameter line (optional)
            if dimensions.get("show_diameter", True):
                ax.plot([-radius, radius], [0, 0], "k--", linewidth=1)

            # Measurements
            if show_measurements:
                ax.text(radius / 2, -0.5, f"r = {radius} cm", fontsize=11, ha="center")
                if dimensions.get("show_diameter", True):
                    ax.text(
                        0, radius + 1.2, f"d = {2*radius} cm", fontsize=11, ha="center"
                    )

            ax.set_xlim(-radius - 2, radius + 2)
            ax.set_ylim(-radius - 2, radius + 2)

        elif subtype == "sector":
            radius = dimensions.get("radius", 5)
            angle = dimensions.get("angle", 60)  # degrees

            # Draw sector (wedge)
            wedge = Wedge(
                (0, 0), radius, 0, angle, fill=False, edgecolor="black", linewidth=2
            )
            ax.add_patch(wedge)

            # Radii
            angle_rad = math.radians(angle)
            ax.plot([0, radius], [0, 0], "k-", linewidth=1.5)
            ax.plot(
                [0, radius * math.cos(angle_rad)],
                [0, radius * math.sin(angle_rad)],
                "k-",
                linewidth=1.5,
            )

            # Center point
            ax.plot(0, 0, "ko", markersize=5)
            ax.text(0.2, -0.5, "O", fontsize=14, fontweight="bold")

            # Angle arc
            angle_arc = patches.Arc(
                (0, 0),
                radius * 0.4,
                radius * 0.4,
                angle=0,
                theta1=0,
                theta2=angle,
                edgecolor="black",
                linewidth=1,
                linestyle="--",
            )
            ax.add_patch(angle_arc)

            # Measurements
            if show_measurements:
                ax.text(radius / 2, -0.7, f"r = {radius} cm", fontsize=11, ha="center")
                ax.text(
                    radius * 0.25, radius * 0.15, f"{angle}°", fontsize=11, ha="center"
                )

            ax.set_xlim(-2, radius + 2)
            ax.set_ylim(-2, radius + 2)

        else:
            raise ValueError(f"Unknown circle subtype: {subtype}")

        return self._fig_to_svg(fig)

    # ===== QUADRILATERAL GENERATION =====

    def _generate_quadrilateral(
        self,
        subtype: str,
        dimensions: Dict[str, float],
        labels: Dict[str, Any],
        show_measurements: bool,
        show_angles: bool,
    ) -> str:
        """
        Generate quadrilateral SVG

        Subtypes:
        - "square": Square (side)
        - "rectangle": Rectangle (width, height)
        - "trapezoid": Trapezoid (base1, base2, height)
        - "parallelogram": Parallelogram (base, side, angle)
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_aspect("equal")
        ax.axis("off")

        if subtype == "square":
            side = dimensions.get("side", 6)

            vertices = np.array([[0, 0], [side, 0], [side, side], [0, side]])
            square = MplPolygon(vertices, fill=False, edgecolor="black", linewidth=2)
            ax.add_patch(square)

            # Right angle markers
            marker_size = 0.4
            for corner in [[0, 0], [side, 0], [side, side], [0, side]]:
                if corner == [0, 0]:
                    right_angle = MplPolygon(
                        [
                            [0, 0],
                            [marker_size, 0],
                            [marker_size, marker_size],
                            [0, marker_size],
                        ],
                        fill=False,
                        edgecolor="black",
                        linewidth=1,
                    )
                    ax.add_patch(right_angle)

            # Vertex labels
            vertex_labels = labels.get("vertex_labels", ["A", "B", "C", "D"])
            ax.text(-0.5, -0.5, vertex_labels[0], fontsize=14, fontweight="bold")
            ax.text(side + 0.3, -0.5, vertex_labels[1], fontsize=14, fontweight="bold")
            ax.text(
                side + 0.3, side + 0.3, vertex_labels[2], fontsize=14, fontweight="bold"
            )
            ax.text(-0.5, side + 0.3, vertex_labels[3], fontsize=14, fontweight="bold")

            # Measurements
            if show_measurements:
                ax.text(side / 2, -0.8, f"{side} cm", fontsize=11, ha="center")
                ax.text(
                    -1.0,
                    side / 2,
                    f"{side} cm",
                    fontsize=11,
                    ha="center",
                    rotation=90,
                    va="center",
                )

            # Equal side markers
            self._add_equal_markers(ax, vertices[0], vertices[1], 1)
            self._add_equal_markers(ax, vertices[1], vertices[2], 1)
            self._add_equal_markers(ax, vertices[2], vertices[3], 1)
            self._add_equal_markers(ax, vertices[3], vertices[0], 1)

            ax.set_xlim(-2, side + 2)
            ax.set_ylim(-2, side + 2)

        elif subtype == "rectangle":
            width = dimensions.get("width", 8)
            height = dimensions.get("height", 5)

            vertices = np.array([[0, 0], [width, 0], [width, height], [0, height]])
            rectangle = MplPolygon(vertices, fill=False, edgecolor="black", linewidth=2)
            ax.add_patch(rectangle)

            # Right angle marker
            marker_size = 0.4
            right_angle = MplPolygon(
                [
                    [0, 0],
                    [marker_size, 0],
                    [marker_size, marker_size],
                    [0, marker_size],
                ],
                fill=False,
                edgecolor="black",
                linewidth=1,
            )
            ax.add_patch(right_angle)

            # Vertex labels
            vertex_labels = labels.get("vertex_labels", ["A", "B", "C", "D"])
            ax.text(-0.5, -0.5, vertex_labels[0], fontsize=14, fontweight="bold")
            ax.text(width + 0.3, -0.5, vertex_labels[1], fontsize=14, fontweight="bold")
            ax.text(
                width + 0.3,
                height + 0.3,
                vertex_labels[2],
                fontsize=14,
                fontweight="bold",
            )
            ax.text(
                -0.5, height + 0.3, vertex_labels[3], fontsize=14, fontweight="bold"
            )

            # Measurements
            if show_measurements:
                ax.text(width / 2, -0.8, f"{width} cm", fontsize=11, ha="center")
                ax.text(
                    -1.0,
                    height / 2,
                    f"{height} cm",
                    fontsize=11,
                    ha="center",
                    rotation=90,
                    va="center",
                )

            ax.set_xlim(-2, width + 2)
            ax.set_ylim(-2, height + 2)

        elif subtype == "trapezoid":
            base1 = dimensions.get("base1", 8)
            base2 = dimensions.get("base2", 5)
            height = dimensions.get("height", 4)

            # Vertices: Centered trapezoid
            offset = (base1 - base2) / 2
            vertices = np.array(
                [[0, 0], [base1, 0], [base1 - offset, height], [offset, height]]
            )
            trapezoid = MplPolygon(vertices, fill=False, edgecolor="black", linewidth=2)
            ax.add_patch(trapezoid)

            # Vertex labels
            vertex_labels = labels.get("vertex_labels", ["A", "B", "C", "D"])
            ax.text(-0.5, -0.5, vertex_labels[0], fontsize=14, fontweight="bold")
            ax.text(base1 + 0.3, -0.5, vertex_labels[1], fontsize=14, fontweight="bold")
            ax.text(
                base1 - offset + 0.3,
                height + 0.3,
                vertex_labels[2],
                fontsize=14,
                fontweight="bold",
            )
            ax.text(
                offset - 0.5,
                height + 0.3,
                vertex_labels[3],
                fontsize=14,
                fontweight="bold",
            )

            # Measurements
            if show_measurements:
                ax.text(base1 / 2, -0.8, f"{base1} cm", fontsize=11, ha="center")
                ax.text(
                    offset + base2 / 2,
                    height + 0.6,
                    f"{base2} cm",
                    fontsize=11,
                    ha="center",
                )

                # Height line (dashed)
                ax.plot([offset, offset], [0, height], "k--", linewidth=1)
                ax.text(
                    offset - 0.8,
                    height / 2,
                    f"h = {height} cm",
                    fontsize=11,
                    rotation=90,
                    va="center",
                )

            # Parallel markers
            self._add_parallel_markers(ax, vertices[0], vertices[1], 1, offset=-0.3)
            self._add_parallel_markers(ax, vertices[3], vertices[2], 1, offset=0.3)

            ax.set_xlim(-2, base1 + 2)
            ax.set_ylim(-2, height + 2)

        else:
            raise ValueError(f"Unknown quadrilateral subtype: {subtype}")

        return self._fig_to_svg(fig)

    # ===== POLYGON GENERATION =====

    def _generate_polygon(
        self,
        subtype: str,
        dimensions: Dict[str, float],
        labels: Dict[str, Any],
        show_measurements: bool,
    ) -> str:
        """
        Generate polygon SVG

        Subtypes:
        - "pentagon": Regular pentagon (side)
        - "hexagon": Regular hexagon (side)
        - "octagon": Regular octagon (side)
        """
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_aspect("equal")
        ax.axis("off")

        # Map subtypes to number of sides
        sides_map = {
            "pentagon": 5,
            "hexagon": 6,
            "octagon": 8,
        }

        if subtype not in sides_map:
            raise ValueError(f"Unknown polygon subtype: {subtype}")

        n_sides = sides_map[subtype]
        side_length = dimensions.get("side", 5)

        # Calculate vertices for regular polygon
        # Radius of circumscribed circle
        radius = side_length / (2 * math.sin(math.pi / n_sides))

        angles = np.linspace(0, 2 * np.pi, n_sides, endpoint=False) + np.pi / 2
        vertices = np.array(
            [[radius * np.cos(angle), radius * np.sin(angle)] for angle in angles]
        )

        # Draw polygon
        polygon = MplPolygon(vertices, fill=False, edgecolor="black", linewidth=2)
        ax.add_patch(polygon)

        # Center point
        ax.plot(0, 0, "ko", markersize=5)
        ax.text(0.2, 0.2, "O", fontsize=14, fontweight="bold")

        # Vertex labels
        vertex_labels = labels.get(
            "vertex_labels", [chr(65 + i) for i in range(n_sides)]
        )  # A, B, C, ...
        for i, (x, y) in enumerate(vertices):
            offset = 0.5
            label_x = x + offset * np.sign(x) if abs(x) > 0.1 else x
            label_y = y + offset * np.sign(y) if abs(y) > 0.1 else y + offset
            ax.text(
                label_x,
                label_y,
                vertex_labels[i],
                fontsize=14,
                fontweight="bold",
                ha="center",
            )

        # Measurements
        if show_measurements:
            # Show one side length
            mid_x = (vertices[0][0] + vertices[1][0]) / 2
            mid_y = (vertices[0][1] + vertices[1][1]) / 2
            ax.text(mid_x, mid_y - 0.6, f"{side_length} cm", fontsize=11, ha="center")

        # Equal side markers (all sides equal)
        for i in range(n_sides):
            self._add_equal_markers(ax, vertices[i], vertices[(i + 1) % n_sides], 1)

        ax.set_xlim(-radius - 2, radius + 2)
        ax.set_ylim(-radius - 2, radius + 2)

        return self._fig_to_svg(fig)

    # ===== 3D SHAPE GENERATION =====

    def _generate_3d_shape(
        self,
        subtype: str,
        dimensions: Dict[str, float],
        labels: Dict[str, Any],
        show_measurements: bool,
    ) -> str:
        """
        Generate 3D shape SVG using custom SVG (perspective projection)

        Subtypes:
        - "rectangular_prism": Rectangular prism (width, height, depth)
        - "cube": Cube (side)
        - "cylinder": Cylinder (radius, height)
        - "cone": Cone (radius, height)
        - "sphere": Sphere (radius)
        """
        if subtype == "cube":
            return self._generate_cube_svg(dimensions, labels, show_measurements)
        elif subtype == "rectangular_prism":
            return self._generate_rectangular_prism_svg(
                dimensions, labels, show_measurements
            )
        elif subtype == "cylinder":
            return self._generate_cylinder_svg(dimensions, labels, show_measurements)
        elif subtype == "sphere":
            return self._generate_sphere_svg(dimensions, labels, show_measurements)
        else:
            raise ValueError(f"Unknown 3D shape subtype: {subtype}")

    def _generate_cube_svg(
        self,
        dimensions: Dict[str, float],
        labels: Dict[str, Any],
        show_measurements: bool,
    ) -> str:
        """Generate cube with isometric perspective"""
        side = dimensions.get("side", 5)

        # Isometric projection angles
        angle_x = math.radians(30)
        angle_y = math.radians(30)

        # Scale for isometric view
        iso_x = side * math.cos(angle_x)
        iso_y = side * math.sin(angle_y)

        # Define vertices in 3D space, then project to 2D
        # Front face: (0,0,0), (s,0,0), (s,s,0), (0,s,0)
        # Back face: (0,0,s), (s,0,s), (s,s,s), (0,s,s)

        # Projected vertices (isometric)
        vertices_2d = {
            "A": (0, 0),  # Front bottom-left
            "B": (side, 0),  # Front bottom-right
            "C": (side, side),  # Front top-right
            "D": (0, side),  # Front top-left
            "E": (iso_x, -iso_y),  # Back bottom-left
            "F": (side + iso_x, -iso_y),  # Back bottom-right
            "G": (side + iso_x, side - iso_y),  # Back top-right
            "H": (iso_x, side - iso_y),  # Back top-left
        }

        svg_width = side + iso_x + 100
        svg_height = side + 100

        svg = f"""<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <g transform="translate(40, 60)">
        <!-- Front face -->
        <path d="M {vertices_2d['A'][0]},{vertices_2d['A'][1]} L {vertices_2d['B'][0]},{vertices_2d['B'][1]} L {vertices_2d['C'][0]},{vertices_2d['C'][1]} L {vertices_2d['D'][0]},{vertices_2d['D'][1]} Z"
              fill="none" stroke="black" stroke-width="2"/>

        <!-- Back face -->
        <path d="M {vertices_2d['E'][0]},{vertices_2d['E'][1]} L {vertices_2d['F'][0]},{vertices_2d['F'][1]} L {vertices_2d['G'][0]},{vertices_2d['G'][1]} L {vertices_2d['H'][0]},{vertices_2d['H'][1]} Z"
              fill="none" stroke="black" stroke-width="2"/>

        <!-- Connecting edges -->
        <line x1="{vertices_2d['A'][0]}" y1="{vertices_2d['A'][1]}" x2="{vertices_2d['E'][0]}" y2="{vertices_2d['E'][1]}" stroke="black" stroke-width="2"/>
        <line x1="{vertices_2d['B'][0]}" y1="{vertices_2d['B'][1]}" x2="{vertices_2d['F'][0]}" y2="{vertices_2d['F'][1]}" stroke="black" stroke-width="2"/>
        <line x1="{vertices_2d['C'][0]}" y1="{vertices_2d['C'][1]}" x2="{vertices_2d['G'][0]}" y2="{vertices_2d['G'][1]}" stroke="black" stroke-width="2"/>
        <line x1="{vertices_2d['D'][0]}" y1="{vertices_2d['D'][1]}" x2="{vertices_2d['H'][0]}" y2="{vertices_2d['H'][1]}" stroke="black" stroke-width="2"/>

        <!-- Measurements -->"""

        if show_measurements:
            svg += f"""
        <text x="{side/2}" y="{-5}" text-anchor="middle" font-size="12" font-family="Arial">{side} cm</text>
        <text x="{-15}" y="{side/2}" text-anchor="middle" font-size="12" font-family="Arial" transform="rotate(-90, -15, {side/2})">{side} cm</text>
        <text x="{side + iso_x/2 + 5}" y="{-iso_y/2 - 5}" text-anchor="middle" font-size="12" font-family="Arial">{side} cm</text>"""

        svg += """
    </g>
</svg>"""

        return svg

    def _generate_rectangular_prism_svg(
        self,
        dimensions: Dict[str, float],
        labels: Dict[str, Any],
        show_measurements: bool,
    ) -> str:
        """Generate rectangular prism with isometric perspective"""
        width = dimensions.get("width", 6)
        height = dimensions.get("height", 4)
        depth = dimensions.get("depth", 5)

        angle_x = math.radians(30)
        angle_y = math.radians(30)

        iso_x = depth * math.cos(angle_x)
        iso_y = depth * math.sin(angle_y)

        vertices_2d = {
            "A": (0, 0),
            "B": (width, 0),
            "C": (width, height),
            "D": (0, height),
            "E": (iso_x, -iso_y),
            "F": (width + iso_x, -iso_y),
            "G": (width + iso_x, height - iso_y),
            "H": (iso_x, height - iso_y),
        }

        svg_width = width + iso_x + 100
        svg_height = height + 100

        svg = f"""<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <g transform="translate(40, 60)">
        <path d="M {vertices_2d['A'][0]},{vertices_2d['A'][1]} L {vertices_2d['B'][0]},{vertices_2d['B'][1]} L {vertices_2d['C'][0]},{vertices_2d['C'][1]} L {vertices_2d['D'][0]},{vertices_2d['D'][1]} Z"
              fill="none" stroke="black" stroke-width="2"/>
        <path d="M {vertices_2d['E'][0]},{vertices_2d['E'][1]} L {vertices_2d['F'][0]},{vertices_2d['F'][1]} L {vertices_2d['G'][0]},{vertices_2d['G'][1]} L {vertices_2d['H'][0]},{vertices_2d['H'][1]} Z"
              fill="none" stroke="black" stroke-width="2"/>
        <line x1="{vertices_2d['A'][0]}" y1="{vertices_2d['A'][1]}" x2="{vertices_2d['E'][0]}" y2="{vertices_2d['E'][1]}" stroke="black" stroke-width="2"/>
        <line x1="{vertices_2d['B'][0]}" y1="{vertices_2d['B'][1]}" x2="{vertices_2d['F'][0]}" y2="{vertices_2d['F'][1]}" stroke="black" stroke-width="2"/>
        <line x1="{vertices_2d['C'][0]}" y1="{vertices_2d['C'][1]}" x2="{vertices_2d['G'][0]}" y2="{vertices_2d['G'][1]}" stroke="black" stroke-width="2"/>
        <line x1="{vertices_2d['D'][0]}" y1="{vertices_2d['D'][1]}" x2="{vertices_2d['H'][0]}" y2="{vertices_2d['H'][1]}" stroke="black" stroke-width="2"/>"""

        if show_measurements:
            svg += f"""
        <text x="{width/2}" y="{-5}" text-anchor="middle" font-size="12" font-family="Arial">{width} cm</text>
        <text x="{-15}" y="{height/2}" text-anchor="middle" font-size="12" font-family="Arial" transform="rotate(-90, -15, {height/2})">{height} cm</text>
        <text x="{width + iso_x/2 + 5}" y="{-iso_y/2 - 5}" text-anchor="middle" font-size="12" font-family="Arial">{depth} cm</text>"""

        svg += """
    </g>
</svg>"""

        return svg

    def _generate_cylinder_svg(
        self,
        dimensions: Dict[str, float],
        labels: Dict[str, Any],
        show_measurements: bool,
    ) -> str:
        """Generate cylinder with perspective"""
        radius = dimensions.get("radius", 3)
        height = dimensions.get("height", 6)

        ellipse_ry = radius * 0.3  # Perspective compression

        svg_width = radius * 2 + 100
        svg_height = height + radius + 100

        svg = f"""<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <g transform="translate({radius + 40}, 40)">
        <!-- Top ellipse -->
        <ellipse cx="0" cy="0" rx="{radius}" ry="{ellipse_ry}" fill="none" stroke="black" stroke-width="2"/>

        <!-- Bottom ellipse -->
        <ellipse cx="0" cy="{height}" rx="{radius}" ry="{ellipse_ry}" fill="none" stroke="black" stroke-width="2"/>

        <!-- Side lines -->
        <line x1="{-radius}" y1="0" x2="{-radius}" y2="{height}" stroke="black" stroke-width="2"/>
        <line x1="{radius}" y1="0" x2="{radius}" y2="{height}" stroke="black" stroke-width="2"/>"""

        if show_measurements:
            svg += f"""
        <text x="0" y="{-ellipse_ry - 10}" text-anchor="middle" font-size="12" font-family="Arial">r = {radius} cm</text>
        <text x="{radius + 15}" y="{height/2}" text-anchor="start" font-size="12" font-family="Arial">h = {height} cm</text>"""

        svg += """
    </g>
</svg>"""

        return svg

    def _generate_sphere_svg(
        self,
        dimensions: Dict[str, float],
        labels: Dict[str, Any],
        show_measurements: bool,
    ) -> str:
        """Generate sphere with great circles"""
        radius = dimensions.get("radius", 5)

        svg_width = radius * 2 + 100
        svg_height = radius * 2 + 100

        ellipse_ry = radius * 0.3

        svg = f"""<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <g transform="translate({radius + 50}, {radius + 50})">
        <!-- Main circle -->
        <circle cx="0" cy="0" r="{radius}" fill="none" stroke="black" stroke-width="2"/>

        <!-- Horizontal great circle (equator) -->
        <ellipse cx="0" cy="0" rx="{radius}" ry="{ellipse_ry}" fill="none" stroke="black" stroke-width="1" stroke-dasharray="3,3"/>

        <!-- Vertical great circle (meridian) -->
        <ellipse cx="0" cy="0" rx="{ellipse_ry}" ry="{radius}" fill="none" stroke="black" stroke-width="1" stroke-dasharray="3,3"/>

        <!-- Center point -->
        <circle cx="0" cy="0" r="2" fill="black"/>
        <text x="5" y="5" font-size="12" font-family="Arial" font-weight="bold">O</text>

        <!-- Radius -->
        <line x1="0" y1="0" x2="{radius}" y2="0" stroke="black" stroke-width="1.5"/>"""

        if show_measurements:
            svg += f"""
        <text x="{radius/2}" y="-5" text-anchor="middle" font-size="12" font-family="Arial">r = {radius} cm</text>"""

        svg += """
    </g>
</svg>"""

        return svg

    # ===== HELPER METHODS =====

    def _add_equal_markers(
        self, ax, point1: np.ndarray, point2: np.ndarray, num_marks: int
    ):
        """Add equal side markers (small perpendicular lines)"""
        mid_x = (point1[0] + point2[0]) / 2
        mid_y = (point1[1] + point2[1]) / 2

        # Direction perpendicular to the side
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        length = math.sqrt(dx**2 + dy**2)

        # Perpendicular direction (rotated 90 degrees)
        perp_x = -dy / length
        perp_y = dx / length

        marker_length = 0.2
        spacing = 0.15

        for i in range(num_marks):
            offset = (i - (num_marks - 1) / 2) * spacing
            start_x = mid_x + offset * (dx / length) - marker_length * perp_x
            start_y = mid_y + offset * (dy / length) - marker_length * perp_y
            end_x = mid_x + offset * (dx / length) + marker_length * perp_x
            end_y = mid_y + offset * (dy / length) + marker_length * perp_y

            ax.plot([start_x, end_x], [start_y, end_y], "k-", linewidth=1.5)

    def _add_parallel_markers(
        self,
        ax,
        point1: np.ndarray,
        point2: np.ndarray,
        num_marks: int,
        offset: float = 0,
    ):
        """Add parallel side markers (arrows)"""
        mid_x = (point1[0] + point2[0]) / 2
        mid_y = (point1[1] + point2[1]) / 2

        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        length = math.sqrt(dx**2 + dy**2)

        perp_x = -dy / length
        perp_y = dx / length

        arrow_x = mid_x + offset * perp_x
        arrow_y = mid_y + offset * perp_y

        arrow_props = dict(arrowstyle="->", lw=1, color="black")
        ax.annotate(
            "",
            xy=(arrow_x + 0.3 * dx / length, arrow_y + 0.3 * dy / length),
            xytext=(arrow_x - 0.3 * dx / length, arrow_y - 0.3 * dy / length),
            arrowprops=arrow_props,
        )

    def _fig_to_svg(self, fig) -> str:
        """Convert matplotlib figure to SVG string"""
        svg_buffer = io.StringIO()
        fig.savefig(svg_buffer, format="svg", bbox_inches="tight", dpi=100)
        plt.close(fig)
        svg_content = svg_buffer.getvalue()
        svg_buffer.close()
        return svg_content

    def _generate_description(
        self, geometry_type: str, shape_subtype: str, dimensions: Dict
    ) -> str:
        """Generate accessible description of the geometry"""
        descriptions = {
            "triangle": f"{shape_subtype.replace('_', ' ').title()}. Üç kenarli geometrik sekil.",
            "circle": f"{shape_subtype.replace('_', ' ').title()}. Daire veya daire parcasi.",
            "quadrilateral": f"{shape_subtype.replace('_', ' ').title()}. Dört kenarli geometrik sekil.",
            "polygon": f"{shape_subtype.replace('_', ' ').title()}. Cok kenarli düzgün geometrik sekil.",
            "3d_shape": f"{shape_subtype.replace('_', ' ').title()}. Üç boyutlu geometrik cisim.",
        }
        return descriptions.get(geometry_type, f"Geometrik sekil: {shape_subtype}")


# Example usage and testing
if __name__ == "__main__":
    generator = GeometryGenerator()

    print("\n" + "=" * 70)
    print("GEOMETRY GENERATOR - TEST SUITE")
    print("=" * 70 + "\n")

    # Test 1: Right Triangle
    print("[TEST 1] Right Triangle...")
    triangle_data = generator.generate_geometry(
        geometry_type="triangle",
        shape_subtype="right_triangle",
        dimensions={"base": 6, "height": 8},
        labels={"vertex_labels": ["A", "B", "C"]},
        show_measurements=True,
        show_angles=False,
    )
    print(
        f"  [OK] Right triangle generated, SVG length: {len(triangle_data['content'])} chars"
    )

    # Test 2: Complete Circle
    print("[TEST 2] Complete Circle...")
    circle_data = generator.generate_geometry(
        geometry_type="circle",
        shape_subtype="complete_circle",
        dimensions={"radius": 5, "show_diameter": True},
        show_measurements=True,
    )
    print(f"  [OK] Circle generated, SVG length: {len(circle_data['content'])} chars")

    # Test 3: Square
    print("[TEST 3] Square...")
    square_data = generator.generate_geometry(
        geometry_type="quadrilateral",
        shape_subtype="square",
        dimensions={"side": 6},
        labels={"vertex_labels": ["A", "B", "C", "D"]},
        show_measurements=True,
    )
    print(f"  [OK] Square generated, SVG length: {len(square_data['content'])} chars")

    # Test 4: Regular Hexagon
    print("[TEST 4] Regular Hexagon...")
    hexagon_data = generator.generate_geometry(
        geometry_type="polygon",
        shape_subtype="hexagon",
        dimensions={"side": 5},
        show_measurements=True,
    )
    print(f"  [OK] Hexagon generated, SVG length: {len(hexagon_data['content'])} chars")

    # Test 5: Cube (3D)
    print("[TEST 5] Cube (3D)...")
    cube_data = generator.generate_geometry(
        geometry_type="3d_shape",
        shape_subtype="cube",
        dimensions={"side": 5},
        show_measurements=True,
    )
    print(f"  [OK] Cube generated, SVG length: {len(cube_data['content'])} chars")

    print("\n" + "=" * 70)
    print("[SUCCESS] All 5 geometry types generated successfully!")
    print("=" * 70 + "\n")
