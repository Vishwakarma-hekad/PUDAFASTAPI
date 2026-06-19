
from shapely.geometry import Polygon, Point
from shapely.strtree import STRtree
import re

class RoomVentilationAreaDetail:
    """
        RoomVentilationInfo processes DXF modelspace data to extract room-level
        ventilation details using geometric analysis.

        This class identifies rooms, windows, slab cutouts, floors, and buildings
        from DXF layers and computes ventilation area based on spatial relationships.

        Key Features:
            - Maps text labels to corresponding polygons (rooms, floors, buildings)
            - Computes room dimensions using bounding box
            - Calculates ventilation area from windows and slab cutouts
            - Uses Shapely geometry operations for spatial analysis
            - Supports optimized querying using STRtree spatial index

        Ventilation Logic:
            - A window/slab polygon contributes to ventilation if it satisfies:
                * Fully inside the room
                * Touching the room boundary
                * Partially overlapping the room
            - This is handled using:
                room_polygon.intersects(winslab_poly)

        Data Sources (DXF Layers):
            - _Room → Room boundaries and labels
            - _Window → Window polygons
            - _SlabCutoutVoid → Slab openings
            - _BuildingName → Building boundaries and labels
            - _Floor → Floor boundaries and labels

        Notes:
            - Only closed polylines with valid geometry are processed
            - Invalid or malformed polygons are safely skipped
            - Bounding box filtering is used for performance optimization
            - STRtree spatial indexing is initialized for faster spatial queries

        Args:
            msp: DXF modelspace object (from ezdxf)

        Methods:
            - get_assigned_polylabel: Maps text labels to polygons
            - get_poly_inside: Finds child polygons inside a parent polygon
            - calculate_ventilation: Computes ventilation area for a room
            - get_room_dimensions_bbox: Calculates room dimensions
            - get_details: Main method to generate final structured output

        Returns (from get_details):
            List[dict]: Each dict contains building, floor, room info along with
            area, dimensions, ventilation area, and status.
        """

    def __init__(self, msp):
        self.room_poly_entities = msp.query("LWPOLYLINE[layer=='_Room']")
        self.room_text_entities = msp.query("TEXT MTEXT[layer=='_Room']")

        self.window_poly_entities = msp.query("LWPOLYLINE[layer=='_Window']")
        self.slabvoid_poly_entities= msp.query("LWPOLYLINE[layer=='_SlabCutoutVoid']")
        self.bldg_poly_entities = msp.query("LWPOLYLINE[layer=='_BuildingName']")
        self.bldg_text_entities = msp.query("TEXT MTEXT[layer=='_BuildingName']")

        self.floor_poly_entities = msp.query("LWPOLYLINE[layer=='_Floor']")
        self.floor_text_entities = msp.query("TEXT MTEXT[layer=='_Floor']")

        # Precompute window polygons + spatial index
        self.window_polygons = [
            Polygon(w.get_points("xy"))
            for w in self.window_poly_entities if w.closed
        ]

        self.window_index = STRtree(self.window_polygons)

        self.slabvoid_polygons = [
            Polygon(w.get_points("xy"))
            for w in self.slabvoid_poly_entities if w.closed
        ]
        self.slabvoid_index = STRtree(self.slabvoid_polygons)

    def clean_room_text(self,text: str) -> str:
        # Remove DXF formatting codes
        text = re.sub(r'\\[A-Za-z0-9.;]+', ' ', text)

        # Normalize base text
        text = text.replace("^J", " ").replace("\n", " ").strip()

        # Fix hyphen spacing
        text = re.sub(r'([A-Z]+)-', r'\1 - ', text)

        # Fix missing space: mm25' → mm 25'
        text = re.sub(r'(mm)(\d+\'\s*\d*")', r'\1 \2', text)

        # Fix missing space: 7880mm → 7880 mm
        text = re.sub(r'(\d)(mm)', r'\1 \2', text)

        # Normalize 'x'
        text = re.sub(r'\s*x\s*', ' x ', text)

        # Replace escaped quotes
        text = text.replace('\\"', '"')

        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    # -----------------------------
    # Map text to polygons (optimized)
    # -----------------------------
    def get_assigned_polylabel(self, poly_entities, text_entities):
        results = []

        # Pre-create text points
        text_data = []
        for t in text_entities:
            text = t.dxf.text if t.dxftype() == "TEXT" else t.plain_text()

            clean_text=self.clean_room_text(text)

            text_data.append((
                Point(t.dxf.insert.x, t.dxf.insert.y),
                clean_text
            ))

        for poly_entity in poly_entities:
            if not poly_entity.closed:
                continue

            points = poly_entity.get_points("xy")
            if len(points) < 3:
                continue

            polygon = Polygon(points)
            poly_id = poly_entity.dxf.handle

            # Fast filter using bounding box
            minx, miny, maxx, maxy = polygon.bounds

            for text_point, cl_text in text_data:
                x, y = text_point.x, text_point.y

                # quick bbox check
                if not (minx <= x <= maxx and miny <= y <= maxy):
                    continue

                if polygon.contains(text_point):

                    results.append({
                        "id": poly_id,
                        "label": cl_text,
                        "polygon": polygon
                    })
                    break  # stop after first match

        return results

    # -----------------------------
    # Fast polygon inside check
    # -----------------------------
    def get_poly_inside(self, parent_poly, children):
        result = []

        minx, miny, maxx, maxy = parent_poly.bounds

        for child in children:
            poly = child["polygon"]

            cminx, cminy, cmaxx, cmaxy = poly.bounds

            # bounding box filter first
            if not (minx <= cminx and maxx >= cmaxx and miny <= cminy and maxy >= cmaxy):
                continue

            if parent_poly.contains(poly):
                result.append(child)

        return result

    def calculate_ventilation(self, room_polygon):
        ventilation_area = 0.0

        # safety check
        if not isinstance(room_polygon, Polygon):
            return 0.0

        for windowslab in list(self.window_poly_entities)+list(self.slabvoid_poly_entities):

            if not windowslab.closed:
                continue

            pts = windowslab.get_points("xy")

            # validate points
            if not pts or len(pts) < 3:
                continue

            try:
                winslab_poly = Polygon(pts)

                # skip invalid polygons
                if not winslab_poly.is_valid:
                    continue

                # use intersects instead of distance
                if room_polygon.intersects(winslab_poly):
                    ventilation_area += winslab_poly.area

            except Exception:
                continue  # skip bad geometry safely

        return round(ventilation_area, 2)

    def get_room_dimensions_bbox(self, polygon):
        minx, miny, maxx, maxy = polygon.bounds
        return round(max(maxx - minx, maxy - miny), 2), round(min(maxx - minx, maxy - miny), 2)

    # -----------------------------
    # Main processing (optimized)
    # -----------------------------
    def get_details(self):

        building_data = self.get_assigned_polylabel(
            self.bldg_poly_entities, self.bldg_text_entities
        )

        floor_data = self.get_assigned_polylabel(
            self.floor_poly_entities, self.floor_text_entities
        )

        room_data = self.get_assigned_polylabel(
            self.room_poly_entities, self.room_text_entities
        )

        final_res = []

        for room in room_data:
            room_label=room["label"]

            room_polygon = room["polygon"]

            # find parent floor
            floor = next((f for f in floor_data if f["polygon"].contains(room_polygon)), None)

            # find parent building
            bldg = next((b for b in building_data if b["polygon"].contains(room_polygon)), None)

            if not floor or not bldg:
                continue

            room_length, room_width = self.get_room_dimensions_bbox(room_polygon)
            ventilation_area = self.calculate_ventilation(room_polygon)
            # print(f"ROOM LABEL:{room_label}")
            res={
                "BLDG_ID": bldg["id"],
                "BLDG_LABEL": bldg["label"],
                "FLOOR_ID": floor["id"],
                "FLOOR_LABEL": floor["label"],
                "BUILDNG_FLOOR": bldg["label"] + "-" + floor["label"],
                "ROOM_DWG_REFERENCE": room["id"],
                "ROOM_NAME": room_label,
                "DWG_ROOM_AREA": str(round(room_length * room_width, 2)),
                "ROOM_AREA": str(round(room_polygon.area, 2)),
                "ROOM_MIN_REQUIRED_LENGTH": "1.0",
                "PROPOSED_LENGTH": str(room_length),
                "ROOM_MIN_REQUIRED_WIDTH": "1.0",
                "PROPOSED_WIDTH": str(room_width),
                "VENTILATION_AREA": str(ventilation_area),
                "STATUS": "OK" if room_width >= 1.0 and room_length >= 1.0 else "Not OK",
            }

            final_res.append(res)

        return final_res


# # -----------------------------
# # MAIN
# # -----------------------------
# if __name__ == "__main__":
#     import ezdxf
#     import os
#
#     folder_path = r"G:\MyProjects\BPConnectProject\BPConnectAPI\DXF_files"
#     file_name = "327a816ce5cf7304-PALLAVISCHOOLFINAL.dxf"
#     try:
#         dxf_path = os.path.join(folder_path, file_name)
#
#         dxf_file = ezdxf.readfile(dxf_path)
#         model_space = dxf_file.modelspace()
#
#         roominfo_obj = RoomVentilationAreaDetail(model_space)
#         roomInfo_data = roominfo_obj.get_details()
#
#         print(f"Room Ventilation Area Details:\n{roomInfo_data}")
#         # for item in roomInfo_data:
#         #     print(item)
#
#     except FileNotFoundError:
#         print("File Not Found Error")