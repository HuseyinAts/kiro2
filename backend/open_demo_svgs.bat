@echo off
echo Opening demo SVG files in browser...
echo.

start "" "demo_map_diagram_Q1_turkey_regions.svg"
timeout /t 2 /nobreak > nul

start "" "demo_map_diagram_Q2_flowchart.svg"
timeout /t 2 /nobreak > nul

start "" "demo_map_diagram_Q3_venn_diagram.svg"

echo.
echo All 3 demo SVG files opened in browser!
echo.
echo Check:
echo - Turkey Regions Map (should show 7 regions)
echo - Water Cycle Flowchart (should show process nodes)
echo - Venn Diagram (should show 3 overlapping circles)
echo.
pause
