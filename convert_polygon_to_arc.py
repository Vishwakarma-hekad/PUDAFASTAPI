from shapely.geometry import Polygon,LineString
import numpy as np
from shapely.ops import linemerge,snap,unary_union,polygonize
class ConvertPolygonToARC:
    def convert_arc_to_linestring(self,arc_center, arc_radius, start_angle_deg, end_angle_deg):

        center_x = float(arc_center[0])
        center_y = float(arc_center[1])

        start_angle = float(start_angle_deg) % 360.0
        end_angle = float(end_angle_deg) % 360.0

        # Ensure counter-clockwise sweep
        if end_angle <= start_angle:
            end_angle += 360.0

        segment_count = max(256, int(arc_radius * 8))

        theta_values = np.deg2rad(np.linspace(start_angle, end_angle, segment_count))

        x_coords = center_x + arc_radius * np.cos(theta_values)
        y_coords = center_y + arc_radius * np.sin(theta_values)

        return LineString(np.column_stack((x_coords, y_coords)))
    # -------------------------------------------------
    # Merge LINE + ARC entities into Polygon
    # -------------------------------------------------
    def Polygon_Merger_ARC(self,dxf_entity):
        # Only process closed LWPOLYLINE
        if dxf_entity.dxftype() != "LWPOLYLINE" or not dxf_entity.closed:
            return Polygon()  # safe empty polygon
        # -------------------------------------------------
        # STEP 1: Detect ARC in polygon
        # -------------------------------------------------
        arc_found = False

        for entity in dxf_entity.virtual_entities():
            if entity.dxftype() == "ARC":
                arc_found = True
                break

        # -------------------------------------------------
        # STEP 2: If NO ARC → Return simple polygon
        # -------------------------------------------------
        if not arc_found:
            poly_points = [(pt[0], pt[1]) for pt in dxf_entity.get_points()]
            if len(poly_points) > 3:
                polygon_points = Polygon(poly_points)
                return polygon_points

        # -------------------------------------------------
        # STEP 3: ARC FOUND → Execute Your Existing Logic
        # -------------------------------------------------
        boundary_segments = []

        for entity in dxf_entity.virtual_entities():

            entity_type = entity.dxftype()

            # -------- LINE --------
            if entity_type == "LINE":

                start_point = entity.dxf.start
                end_point = entity.dxf.end

                line_segment = LineString([(start_point[0], start_point[1]), (end_point[0], end_point[1])])

                boundary_segments.append(line_segment)

            # -------- ARC --------
            elif entity_type == "ARC":

                arc_segment = self.convert_arc_to_linestring(
                    entity.dxf.center,
                    entity.dxf.radius,
                    entity.dxf.start_angle,
                    entity.dxf.end_angle
                )

                boundary_segments.append(arc_segment)

        if not boundary_segments:
            return Polygon()

        # -------------------------------------------------
        # Merge all segments
        # -------------------------------------------------
        merged_geometry = unary_union(boundary_segments)

        merged_geometry = snap(merged_geometry, merged_geometry, 1e-4)

        merged_geometry = linemerge(merged_geometry)

        # -------------------------------------------------
        # Create polygons
        # -------------------------------------------------
        polygon_list = list(polygonize(merged_geometry))

        if not polygon_list:
            # Fallback buffer method
            buffered_boundaries = unary_union([segment.buffer(0.001).boundary for segment in boundary_segments])
            polygon_list = list(polygonize(buffered_boundaries))

            if not polygon_list:
                return Polygon()

        # -------------------------------------------------
        # Detect outer boundary and holes
        # -------------------------------------------------
        polygon_list.sort(key=lambda poly: poly.area, reverse=True)

        outer_boundary = polygon_list[0]
        hole_boundaries = []

        for poly in polygon_list[1:]:
            if outer_boundary.contains(poly):
                hole_boundaries.append(poly.exterior.coords)

        final_polygon = Polygon(outer_boundary.exterior.coords, hole_boundaries)

        if not final_polygon.is_valid:
            final_polygon = final_polygon.buffer(0)

        return final_polygon

polygon2arc=ConvertPolygonToARC()